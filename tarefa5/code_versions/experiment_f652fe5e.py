"""Aula 05: reproducible bounded hyperparameter-optimization experiments.

Run from a fresh process; no source notebook cell or upstream script is executed.
The split and five CV folds are fixed independently of optimizer/model seed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import random
import shutil
import sys
import time
import traceback
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import joblib
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import differential_evolution
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, RandomizedSearchCV, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FRAMEWORK_COMMIT = "f68892c8b7adba358b8aa437eec00a89fe88d340"
GRID = {"learning_rate": [0.03, 0.1, 0.2], "subsample": [0.6, 0.8, 1.0],
        "n_estimators": [50, 100, 150, 200]}
METHODS = ["baseline", "grid", "random", "gp_manual", "bayessearch", "bayesopt",
           "optuna", "hyperopt", "ray", "ga", "de_best1bin", "de_rand1bin",
           "pso_w07", "pso_w04", "pso_w09"]
MAIN_METHODS = [m for m in METHODS if m not in {"de_rand1bin", "pso_w04", "pso_w09"}]
_WORKER_WARMUP_SECONDS = None
TRIAL_FIELDS = ["method", "seed", "trial", "cv_rmse", "learning_rate", "subsample",
                "n_estimators", "seconds", "elapsed_seconds", "status", "resource",
                "fold_0", "fold_1", "fold_2", "fold_3", "fold_4", "duration_kind"]


def native(value):
    if isinstance(value, dict):
        return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [native(v) for v in value]
    if isinstance(value, np.ndarray):
        return native(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(native(value), ensure_ascii=False, indent=2,
                                    allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def event(path, kind, **details):
    record = {"utc": datetime.now(timezone.utc).isoformat(), "event": kind, **details}
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(native(record), ensure_ascii=False, allow_nan=False) + "\n")


def parameters(p):
    """One shared decoding rule for objectives and final fitting."""
    return {"learning_rate": float(np.clip(p["learning_rate"], .03, .2)),
            "subsample": float(np.clip(p["subsample"], .6, 1.0)),
            "n_estimators": int(np.clip(np.rint(p["n_estimators"]), 50, 200))}


def decode_unit(u):
    u = np.clip(np.asarray(u, dtype=float), 0, 1)
    return parameters({"learning_rate": .03 * (.2 / .03) ** u[0],
                       "subsample": .6 + .4 * u[1],
                       "n_estimators": 50 + 150 * u[2]})


def pipeline(p=None, seed=42, warm_start=False):
    kw = dict(p or {})
    return Pipeline([("imputer", SimpleImputer(strategy="median")),
                     ("scaler", StandardScaler()),
                     ("model", GradientBoostingRegressor(random_state=seed,
                                                          warm_start=warm_start, **kw))])


def environment():
    packages = ["numpy", "pandas", "scipy", "scikit-learn", "joblib", "threadpoolctl",
                "ucimlrepo", "scikit-optimize", "bayesian-optimization", "optuna",
                "hyperopt", "ray", "deap", "matplotlib", "seaborn"]
    versions = {}
    for p in packages:
        try:
            versions[p] = importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError:
            versions[p] = "not-installed"
    return {"python": sys.version, "platform": platform.platform(),
            "processor": platform.processor(), "logical_cpus": os.cpu_count(),
            "packages": versions, "thread_limits": 1}


def prepare():
    """Fetch UCI 165 once, preserve bytes, deduplicate complete exact rows, freeze split."""
    DATA.mkdir(parents=True, exist_ok=True)
    source = DATA / "uci165_raw.csv"
    if not source.exists():
        from ucimlrepo import fetch_ucirepo
        dataset = fetch_ucirepo(id=165)
        X = dataset.data.features.copy()
        y = dataset.data.targets.iloc[:, 0].rename("target_mpa")
        pd.concat([X, y], axis=1).to_csv(source, index=False)
        write_json(DATA / "uci_metadata.json", dict(dataset.metadata))
    raw = pd.read_csv(source)
    if "target_mpa" not in raw:
        raw = raw.rename(columns={raw.columns[-1]: "target_mpa"})
    assert raw.shape[1] == 9, "Expected eight UCI 165 predictors plus target"
    assert not raw["target_mpa"].isna().any(), "Missing targets need an explicit amendment"
    assert all(pd.api.types.is_numeric_dtype(raw[c]) for c in raw), "Unexpected nonnumeric fields"
    duplicated = raw.duplicated(keep="first")
    clean = raw.loc[~duplicated].copy()
    source_ids = clean.index.to_numpy(dtype=int)
    clean.insert(0, "source_row", source_ids)
    clean.to_csv(DATA / "clean.csv", index=False)
    train_ids, test_ids = train_test_split(np.arange(len(clean)), test_size=.2, random_state=42)
    feature_names = [c for c in raw.columns if c != "target_mpa"]
    X = clean[feature_names].to_numpy(dtype=float)
    y = clean["target_mpa"].to_numpy(dtype=float)
    folds = list(KFold(5, shuffle=True, random_state=42).split(train_ids))
    payload = dict(X=X, y=y, train_ids=train_ids, test_ids=test_ids, source_ids=source_ids,
                   feature_names=np.asarray(feature_names, dtype=str))
    for k, (tr, va) in enumerate(folds):
        payload[f"fold_{k}_train"] = tr
        payload[f"fold_{k}_valid"] = va
    np.savez_compressed(DATA / "prepared.npz", **payload)
    split = pd.DataFrame({"clean_index": np.arange(len(clean)), "source_row": source_ids,
                          "split": "test", "validation_fold": -1})
    split.loc[train_ids, "split"] = "train"
    for k, (_, va) in enumerate(folds):
        split.loc[train_ids[va], "validation_fold"] = k
    split.to_csv(DATA / "split-manifest.csv", index=False)
    pd.DataFrame({"column": raw.columns, "dtype": raw.dtypes.astype(str).values,
                  "missing_count": raw.isna().sum().values,
                  "missing_fraction": raw.isna().mean().values}).to_csv(DATA / "quality-summary.csv", index=False)
    # The assignment explicitly requests whole-data describe; disclose this prior aggregate exposure.
    raw.describe().to_csv(DATA / "describe_raw.csv")
    clean.iloc[train_ids].drop(columns="source_row").describe().to_csv(DATA / "describe_train.csv")
    write_json(DATA / "data-contract.json", {
        "dataset": "UCI 165 Concrete Compressive Strength", "url": "https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength",
        "target_unit": "MPa", "raw_shape": raw.shape, "clean_shape": [len(clean), 9],
        "exact_duplicate_rows_removed": int(duplicated.sum()), "train_rows": len(train_ids),
        "test_rows": len(test_ids), "split_seed": 42, "fold_seed": 42, "folds": 5,
        "features": feature_names, "missing_policy": "Median imputation inside every training fold; target not scaled",
        "duplicates_policy": "Only complete exactly identical feature+target rows removed before split",
        "prior_outcome_exposure": "Whole-data shape/dtypes/missingness/describe required by assignment; substantive EDA restricted to development set",
        "generalization_limit": "Random row split; no batch IDs available to verify independence of related mixes",
        "sha256": {p.name: digest(p) for p in [source, DATA / "clean.csv", DATA / "split-manifest.csv", DATA / "prepared.npz"]},
        "framework_commit": FRAMEWORK_COMMIT})
    write_json(DATA / "environment.json", environment())
    print(json.dumps({"prepared": True, "raw": len(raw), "clean": len(clean),
                      "train": len(train_ids), "test": len(test_ids)}), flush=True)


def _touch_worker(i):
    import sklearn
    a = np.full((256, 256), float(i + 1))
    return os.getpid(), float(np.dot(a, a)[0, 0])


def warm_workers(jobs):
    """Exclude and disclose process-pool initialization, once per CLI process."""
    global _WORKER_WARMUP_SECONDS
    if _WORKER_WARMUP_SECONDS is None:
        start = time.perf_counter()
        with joblib.parallel_config(backend="loky", n_jobs=jobs, inner_max_num_threads=1):
            joblib.Parallel(n_jobs=jobs)(joblib.delayed(_touch_worker)(i) for i in range(jobs * 2))
        _WORKER_WARMUP_SECONDS = time.perf_counter() - start


class Objective:
    def __init__(self, method, seed, jobs, out, sample_fraction=1.0):
        self.method, self.seed, self.jobs, self.out = method, seed, jobs, Path(out)
        z = np.load(DATA / "prepared.npz", allow_pickle=False)
        self.feature_names = z["feature_names"].tolist()
        self.train_ids, self.test_ids = z["train_ids"], z["test_ids"]
        self.X, self.y = z["X"][self.train_ids], z["y"][self.train_ids]
        self.Xtest, self.ytest = z["X"][self.test_ids], z["y"][self.test_ids]
        self.source_test_ids = z["source_ids"][self.test_ids]
        self.folds = [(z[f"fold_{k}_train"], z[f"fold_{k}_valid"]) for k in range(5)]
        self.sample_fraction = sample_fraction
        if sample_fraction < 1:
            chosen = np.sort(np.random.default_rng(42).choice(len(self.X),
                            size=int(len(self.X) * sample_fraction), replace=False))
            self.X, self.y = self.X[chosen], self.y[chosen]
            self.folds = list(KFold(5, shuffle=True, random_state=42).split(self.X))
            pd.DataFrame({"development_position": chosen}).to_csv(self.out / "sample-indices.csv", index=False)
        self.rows = []
        self.started = time.perf_counter()
        self.cv_fits = 0
        self.trained_trees = 0

    def record(self, p, score, scores, seconds, status="complete", resource=1., duration_kind="objective_wall"):
        p = p or {"learning_rate": .1, "subsample": 1., "n_estimators": 100}
        row = {"method": self.method, "seed": self.seed, "trial": len(self.rows) + 1,
               "cv_rmse": float(score), **p, "seconds": float(seconds),
               "elapsed_seconds": time.perf_counter() - self.started, "status": status,
               "resource": float(resource), "duration_kind": duration_kind}
        row.update({f"fold_{k}": float(s) for k, s in enumerate(scores)})
        self.rows.append(row)
        path = self.out / "trials.csv"
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=TRIAL_FIELDS)
            if len(self.rows) == 1:
                writer.writeheader()
            writer.writerow(row)
        event(self.out / "events.jsonl", "candidate", **row)
        if len(self.rows) == 1 or len(self.rows) % 10 == 0:
            print(f"{self.method} seed={self.seed} n={len(self.rows)} rmse={score:.6f}", flush=True)
        return float(score)

    def __call__(self, p):
        p = parameters(p) if p else {}
        t0 = time.perf_counter()
        try:
            with threadpool_limits(1), joblib.parallel_config(backend="loky", n_jobs=self.jobs, inner_max_num_threads=1):
                scores = -cross_val_score(pipeline(p, self.seed), self.X, self.y, cv=self.folds,
                    scoring="neg_root_mean_squared_error", n_jobs=self.jobs, error_score="raise")
        except Exception as exc:
            event(self.out / "events.jsonl", "candidate_failed", params=p, error=repr(exc))
            raise
        self.cv_fits += 5
        self.trained_trees += 5 * p.get("n_estimators", 100)
        return self.record(p, np.mean(scores), scores, time.perf_counter() - t0)

    def best(self):
        eligible = [r for r in self.rows if r["status"] == "complete" and r["resource"] >= 1]
        if not eligible:
            raise RuntimeError("No full-resource candidate available for selection")
        row = min(eligible, key=lambda r: r["cv_rmse"])
        return parameters(row), row["cv_rmse"]


def searchcv(obj, method):
    common = dict(estimator=pipeline(seed=obj.seed), scoring="neg_root_mean_squared_error",
                  cv=obj.folds, n_jobs=obj.jobs, refit=False, return_train_score=False,
                  error_score="raise")
    space = {"model__" + k: v for k, v in GRID.items()}
    if method == "grid":
        search = GridSearchCV(param_grid=space, **common)
    elif method == "random":
        search = RandomizedSearchCV(param_distributions=space, n_iter=30, random_state=obj.seed, **common)
    else:
        from skopt import BayesSearchCV
        from skopt.space import Integer, Real
        from skopt.learning import GaussianProcessRegressor as SkoptGP
        from skopt.learning.gaussian_process.kernels import ConstantKernel as CK, Matern as MK
        kernel = CK(1., (.01, 100)) * MK([1., 1., 1.], (.01, 100), nu=2.5)
        surrogate = SkoptGP(kernel=kernel, normalize_y=True, noise="gaussian",
                            n_restarts_optimizer=2, random_state=obj.seed)
        continuous = {"model__learning_rate": Real(.03, .2, prior="log-uniform"),
                      "model__subsample": Real(.6, 1.), "model__n_estimators": Integer(50, 200)}
        search = BayesSearchCV(search_spaces=continuous, n_iter=40, random_state=obj.seed,
                    optimizer_kwargs={"base_estimator": surrogate, "acq_func": "EI",
                                      "acq_optimizer": "sampling", "n_initial_points": 10,
                                      "acq_optimizer_kwargs": {"n_points": 4096}}, **common)
    with threadpool_limits(1), joblib.parallel_config(backend="loky", n_jobs=obj.jobs, inner_max_num_threads=1):
        search.fit(obj.X, obj.y)
    cv = search.cv_results_
    pd.DataFrame(cv).to_csv(obj.out / "searchcv-results.csv", index=False)
    for i, candidate in enumerate(cv["params"]):
        p = {k.removeprefix("model__"): v for k, v in candidate.items()}
        folds = [-cv[f"split{k}_test_score"][i] for k in range(5)]
        obj.record(parameters(p), -cv["mean_test_score"][i], folds,
                   cv["mean_fit_time"][i] + cv["mean_score_time"][i],
                   duration_kind="mean_fold_fit_plus_score; scheduled_candidate_order")
    obj.cv_fits = 5 * len(obj.rows)
    obj.trained_trees = 5 * sum(int(r["n_estimators"]) for r in obj.rows)
    if method == "bayessearch":
        joblib.dump(search.optimizer_results_, obj.out / "optimizer-results.joblib")


def gp_manual(obj):
    rng = np.random.default_rng(obj.seed)
    observed_u, observed_y = [], []
    axis = np.linspace(0, 1, 61)
    aa, bb = np.meshgrid(axis, axis, indexing="xy")
    grid_u = np.column_stack([aa.ravel(), bb.ravel()])
    def evaluate(u):
        p = decode_unit([u[0], u[1], 1 / 3])  # Fixed prospectively: n_estimators=100.
        observed_u.append(np.array(u))
        observed_y.append(obj(p))
    for u in rng.random((5, 2)):
        evaluate(u)
    for iteration in range(1, 11):
        gp = GaussianProcessRegressor(kernel=ConstantKernel(1, (.01, 100)) *
                Matern([.3, .3], (.01, 100), nu=2.5) + WhiteKernel(1e-6, (1e-10, .1)),
                normalize_y=True, n_restarts_optimizer=2, random_state=obj.seed)
        with threadpool_limits(1):
            gp.fit(observed_u, observed_y)
            mu, sigma = gp.predict(grid_u, return_std=True)
        improvement = np.min(observed_y) - mu - .01
        z = improvement / np.maximum(sigma, 1e-12)
        ei = improvement * stats.norm.cdf(z) + sigma * stats.norm.pdf(z)
        ei[sigma <= 1e-12] = 0.
        distance = np.min(np.linalg.norm(grid_u[:, None, :] - np.asarray(observed_u)[None, :, :], axis=2), axis=1)
        ei[distance < 1e-8] = -1.
        next_u = grid_u[int(np.argmax(ei))]
        slice_u = np.column_stack([np.linspace(0, 1, 201), np.full(201, next_u[1])])
        slice_mu, slice_sigma = gp.predict(slice_u, return_std=True)
        slice_improvement = np.min(observed_y) - slice_mu - .01
        slice_z = slice_improvement / np.maximum(slice_sigma, 1e-12)
        slice_ei = slice_improvement * stats.norm.cdf(slice_z) + slice_sigma * stats.norm.pdf(slice_z)
        slice_ei[slice_sigma <= 1e-12] = 0.
        np.savez_compressed(obj.out / f"gp_snapshot_{iteration:02d}.npz", grid_u=grid_u,
            mu=mu, sigma=sigma, ei=ei, observed_u=np.asarray(observed_u),
            observed_y=np.asarray(observed_y), next_u=next_u, fixed_n_estimators=100,
            slice_u=slice_u, slice_mu=slice_mu, slice_sigma=slice_sigma,
            slice_ei=slice_ei, next_ei=float(np.max(ei)), xi=.01)
        evaluate(next_u)


def bayesopt(obj):
    from bayes_opt import BayesianOptimization, acquisition
    def target(log_lr, subsample, n_estimators):
        return -obj({"learning_rate": np.exp(log_lr), "subsample": subsample,
                     "n_estimators": n_estimators})
    bo = BayesianOptimization(f=target, pbounds={"log_lr": (np.log(.03), np.log(.2)),
         "subsample": (.6, 1.), "n_estimators": (50., 200.)}, random_state=obj.seed,
         acquisition_function=acquisition.UpperConfidenceBound(kappa=2.576),
         verbose=0, allow_duplicate_points=True)
    bo.set_gp_params(kernel=Matern(nu=2.5), normalize_y=True)
    bo.maximize(init_points=5, n_iter=35)
    write_json(obj.out / "bayesopt-history.json", bo.res)


def optuna_search(obj):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=obj.seed))
    def target(trial):
        return obj({"learning_rate": trial.suggest_float("learning_rate", .03, .2, log=True),
                    "subsample": trial.suggest_float("subsample", .6, 1.),
                    "n_estimators": trial.suggest_int("n_estimators", 50, 200)})
    study.optimize(target, n_trials=40, n_jobs=1)
    study.trials_dataframe().to_csv(obj.out / "optuna-trials.csv", index=False)
    joblib.dump(study, obj.out / "optuna-study.joblib")
    importance = optuna.importance.get_param_importances(study,
        evaluator=optuna.importance.FanovaImportanceEvaluator(seed=obj.seed))
    pd.DataFrame([{"hyperparameter": k, "importance": v} for k, v in importance.items()]).to_csv(
        obj.out / "optuna_importances.csv", index=False)


def hyperopt_search(obj):
    from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
    trials = Trials()
    def target(p):
        return {"loss": obj(p), "status": STATUS_OK}
    fmin(target, space={"learning_rate": hp.loguniform("learning_rate", np.log(.03), np.log(.2)),
                       "subsample": hp.uniform("subsample", .6, 1.),
                       "n_estimators": hp.quniform("n_estimators", 50, 200, 1)},
         algo=tpe.suggest, max_evals=40, trials=trials,
         rstate=np.random.default_rng(obj.seed), show_progressbar=False, verbose=False)
    joblib.dump(trials, obj.out / "hyperopt-trials.joblib")


def ga_search(obj):
    from deap import algorithms, base, creator, tools
    random.seed(obj.seed)
    if not hasattr(creator, "Aula5FitnessMin"):
        creator.create("Aula5FitnessMin", base.Fitness, weights=(-1.,))
        creator.create("Aula5Individual", list, fitness=creator.Aula5FitnessMin)
    box = base.Toolbox()
    def make_individual():
        return creator.Aula5Individual([random.randint(0, 1000), random.randint(0, 1000), random.randint(50, 200)])
    def evaluate(ind):
        return (obj(decode_unit([ind[0] / 1000, ind[1] / 1000, (ind[2] - 50) / 150])),)
    box.register("individual", make_individual)
    box.register("population", tools.initRepeat, list, box.individual)
    box.register("evaluate", evaluate)
    box.register("mate", tools.cxTwoPoint)
    box.register("mutate", tools.mutUniformInt, low=[0, 0, 50], up=[1000, 1000, 200], indpb=1/3)
    box.register("select", tools.selTournament, tournsize=3)
    population = box.population(n=20)
    hall = tools.HallOfFame(1)
    history = []
    for generation in range(16):
        if generation:
            population = algorithms.varAnd(box.select(population, len(population)), box, cxpb=.7, mutpb=.25)
        for ind in population:
            if not ind.fitness.valid:
                ind.fitness.values = box.evaluate(ind)
        hall.update(population)
        fitness = [ind.fitness.values[0] for ind in population]
        history.append({"generation": generation, "best": min(fitness), "mean": np.mean(fitness),
                        "best_ever": hall[0].fitness.values[0],
                        "diversity": len(set(map(tuple, population))) / len(population),
                        "evaluations": len(obj.rows)})
        pd.DataFrame(history).to_csv(obj.out / "generations.csv", index=False)


def de_search(obj, strategy):
    history = []
    def callback(x, convergence):
        history.append({"generation": len(history) + 1, "best": min(r["cv_rmse"] for r in obj.rows),
                        "evaluations": len(obj.rows), "convergence": convergence})
        pd.DataFrame(history).to_csv(obj.out / "generations.csv", index=False)
        return False
    result = differential_evolution(lambda u: obj(decode_unit(u)), bounds=[(0, 1)] * 3,
        strategy=strategy, maxiter=15, popsize=10, mutation=(.5, 1), recombination=.7,
        polish=False, seed=obj.seed, callback=callback, workers=1, updating="immediate")
    write_json(obj.out / "de-result.json", {"x": result.x, "fun": result.fun, "nfev": result.nfev,
               "nit": result.nit, "message": result.message, "population_size": 30,
               "polish": False, "tol": .01, "atol": 0.})


def pso_search(obj, inertia):
    rng = np.random.default_rng(obj.seed)
    x = rng.random((20, 3))
    velocity = rng.uniform(-.1, .1, size=x.shape)
    pbest = x.copy()
    pscore = np.full(20, np.inf)
    gbest = None
    gscore = np.inf
    history = []
    for generation in range(16):
        if generation:
            velocity = inertia * velocity + 1.5 * rng.random(x.shape) * (pbest - x) + 1.5 * rng.random(x.shape) * (gbest - x)
            proposed = x + velocity
            hit = (proposed < 0) | (proposed > 1)
            x = np.clip(proposed, 0, 1)
            velocity[hit] = 0.  # Boundary handling is identical in all inertia variants.
        current = np.asarray([obj(decode_unit(u)) for u in x])
        improved = current < pscore
        pbest[improved], pscore[improved] = x[improved], current[improved]
        index = int(np.argmin(pscore))
        if pscore[index] < gscore:
            gbest, gscore = pbest[index].copy(), float(pscore[index])
        history.append({"generation": generation, "best": gscore, "mean": np.mean(current),
                        "current_best": np.min(current), "diversity": np.mean(np.std(x, axis=0)),
                        "evaluations": len(obj.rows), "inertia": inertia})
        pd.DataFrame(history).to_csv(obj.out / "generations.csv", index=False)


def ray_search(obj):
    """Actual ASHA with progressive warm-start trees and five fold workers."""
    import ray
    from ray import tune
    from ray.tune.schedulers import ASHAScheduler
    from ray.tune.search.optuna import OptunaSearch
    X, y, folds, seed, jobs = obj.X, obj.y, obj.folds, obj.seed, obj.jobs
    stages = []
    class StageLogger(tune.Callback):
        def on_trial_result(self, iteration, trials, trial, result, **info):
            row = {"trial_id": trial.trial_id, "learning_rate": trial.config["learning_rate"],
                   "subsample": trial.config["subsample"], "n_estimators": trial.config["n_estimators"],
                   **{k: result.get(k) for k in ["cv_rmse", "resource", "trees", "incremental_trees", "stage_seconds"]}}
            stages.append(row)
            pd.DataFrame(stages).to_csv(obj.out / "ray-stages.csv", index=False)
            event(obj.out / "events.jsonl", "ray_stage", **row)
    def train(config):
        p = parameters(config)
        models = [pipeline({**p, "n_estimators": max(1, int(math.ceil(p["n_estimators"] * .25)))}, seed,
                           warm_start=True) for _ in folds]
        previous = 0
        for resource in [.25, .5, .75, 1.]:
            t0 = time.perf_counter()
            trees = int(math.ceil(p["n_estimators"] * resource))
            def train_fold(k):
                tr, va = folds[k]
                models[k].set_params(model__n_estimators=trees)
                with threadpool_limits(1):
                    models[k].fit(X[tr], y[tr])
                    prediction = models[k].predict(X[va])
                return float(np.sqrt(mean_squared_error(y[va], prediction)))
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                scores = list(pool.map(train_fold, range(5)))
            tune.report({"cv_rmse": float(np.mean(scores)), "resource": resource,
                         "trees": trees, "incremental_trees": trees - previous,
                         "stage_seconds": time.perf_counter() - t0,
                         **{f"fold_{k}": s for k, s in enumerate(scores)}})
            previous = trees
    ray.init(num_cpus=jobs, include_dashboard=False, ignore_reinit_error=True, log_to_driver=False)
    try:
        analysis = tune.run(train, config={"learning_rate": tune.loguniform(.03, .2),
                    "subsample": tune.uniform(.6, 1.), "n_estimators": tune.randint(50, 201)},
            metric="cv_rmse", mode="min", num_samples=40,
            search_alg=OptunaSearch(metric="cv_rmse", mode="min", seed=seed),
            scheduler=ASHAScheduler(time_attr="resource", metric="cv_rmse", mode="min",
                                    max_t=1., grace_period=.25, reduction_factor=2),
            resources_per_trial={"cpu": jobs}, max_concurrent_trials=1,
            storage_path=str((obj.out / "ray-storage").resolve()), name="asha",
            callbacks=[StageLogger()], verbose=0, log_to_file=True,
            raise_on_failed_trial=True)
        for trial in analysis.trials:
            r = trial.last_result
            resource = float(r.get("resource", 0))
            status = "complete" if resource >= 1 else "pruned"
            p = parameters(trial.config)
            records = [s for s in stages if s["trial_id"] == trial.trial_id]
            obj.record(p, r["cv_rmse"], [r[f"fold_{k}"] for k in range(5)],
                       sum(s["stage_seconds"] for s in records), status, resource,
                       "sum_incremental_stage_wall")
        obj.cv_fits = 5 * len(stages)
        obj.trained_trees = 5 * sum(int(s["incremental_trees"]) for s in stages)
    finally:
        ray.shutdown()


def aggregate():
    RESULTS.mkdir(exist_ok=True)
    rows = []
    for method in METHODS:
        path = RESULTS / method / "seed_42" / "result.json"
        if path.exists():
            r = json.loads(path.read_text(encoding="utf-8"))
            if r.get("status") == "complete":
                row = {k: v for k, v in r.items() if not isinstance(v, (dict, list))}
                row["params_json"] = json.dumps(r["best_params"], sort_keys=True)
                rows.append(row)
    if rows:
        pd.DataFrame(rows).to_csv(RESULTS / "metrics.csv", index=False)
    importance = RESULTS / "optuna" / "seed_42" / "optuna_importances.csv"
    if importance.exists():
        shutil.copy2(importance, RESULTS / "optuna_importances.csv")


def run_method(method, seed=42, jobs=5, resume=False, sample_fraction=1., root=None):
    out = (Path(root) if root else RESULTS) / method / f"seed_{seed}"
    result_path = out / "result.json"
    contract = json.loads((DATA / "data-contract.json").read_text(encoding="utf-8"))
    for filename, expected in contract["sha256"].items():
        if digest(DATA / filename) != expected:
            raise RuntimeError(f"Input changed after prepare: {filename}; inspect and explicitly prepare a new version")
    data_fingerprint = digest(DATA / "clean.csv") + ":" + digest(DATA / "split-manifest.csv")
    if result_path.exists() and resume:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if (result.get("status") == "complete" and result.get("data_fingerprint") == data_fingerprint
                and result.get("sample_fraction") == sample_fraction and result.get("cv_jobs") == jobs):
            print(f"Resume: completed {method} seed={seed}", flush=True)
            return result
    if out.exists() and any(out.iterdir()):
        archived = out.parent / (out.name + "_superseded_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        out.rename(archived)
    out.mkdir(parents=True, exist_ok=True)
    warm_workers(jobs)
    event(out / "events.jsonl", "started", method=method, seed=seed, jobs=jobs)
    obj = Objective(method, seed, jobs, out, sample_fraction)
    started = time.perf_counter()
    try:
        if method == "baseline":
            obj({})
        elif method in {"grid", "random", "bayessearch"}:
            searchcv(obj, method)
        elif method == "gp_manual":
            gp_manual(obj)
        elif method == "bayesopt":
            bayesopt(obj)
        elif method == "optuna":
            optuna_search(obj)
        elif method == "hyperopt":
            hyperopt_search(obj)
        elif method == "ray":
            ray_search(obj)
        elif method == "ga":
            ga_search(obj)
        elif method.startswith("de_"):
            de_search(obj, method.removeprefix("de_"))
        elif method.startswith("pso_"):
            pso_search(obj, {"pso_w07": .7, "pso_w04": .4, "pso_w09": .9}[method])
        else:
            raise ValueError(method)
        search_seconds = time.perf_counter() - started
        best_params, cv_rmse = obj.best()
        # Baseline truly uses sklearn defaults; recorded default values are descriptive.
        model = pipeline({} if method == "baseline" else best_params, seed)
        refit_start = time.perf_counter()
        with threadpool_limits(1):
            model.fit(obj.X, obj.y)
        refit_seconds = time.perf_counter() - refit_start
        prediction_start = time.perf_counter()
        prediction = model.predict(obj.Xtest)
        prediction_seconds = time.perf_counter() - prediction_start
        residual = obj.ytest - prediction
        pd.DataFrame({"source_row": obj.source_test_ids, "y_true": obj.ytest,
                      "y_pred": prediction, "residual": residual}).to_csv(out / "predictions.csv", index=False)
        pd.DataFrame({"feature": obj.feature_names,
                      "importance": model.named_steps["model"].feature_importances_}).to_csv(out / "feature_importance.csv", index=False)
        shapiro = stats.shapiro(residual)
        joblib.dump(model, out / "model.joblib")
        unique = len({json.dumps(parameters(r), sort_keys=True) for r in obj.rows})
        result = {"status": "complete", "method": method, "seed": seed, "cv_rmse": cv_rmse,
                  "test_rmse": float(np.sqrt(mean_squared_error(obj.ytest, prediction))),
                  "test_mae": float(mean_absolute_error(obj.ytest, prediction)),
                  "test_r2": float(r2_score(obj.ytest, prediction)),
                  "search_seconds": search_seconds, "refit_seconds": refit_seconds,
                  "total_seconds": search_seconds + refit_seconds,
                  "prediction_seconds": prediction_seconds, "baseline_fit_seconds": refit_seconds if method == "baseline" else None,
                  "n_evaluations": len(obj.rows), "unique_candidates": unique,
                  "cv_fits": obj.cv_fits, "trained_trees_cv": obj.trained_trees,
                  "completed_trials": sum(r["status"] == "complete" for r in obj.rows),
                  "pruned_trials": sum(r["status"] == "pruned" for r in obj.rows),
                  "full_resource_evaluations": sum(r["resource"] >= 1 for r in obj.rows),
                  "best_params": best_params, "cv_jobs": jobs, "split_seed": 42, "fold_seed": 42,
                  "train_rows": len(obj.X), "test_rows": len(obj.Xtest), "sample_fraction": sample_fraction,
                  "data_fingerprint": data_fingerprint, "framework_commit": FRAMEWORK_COMMIT,
                  "code_sha256": digest(__file__), "shapiro_statistic": float(shapiro.statistic),
                  "worker_startup_seconds_excluded": _WORKER_WARMUP_SECONDS,
                  "parallelism": "5 loky processes for CV; Ray uses5 threads inside1 trial; native libraries limited to1 thread",
                  "shapiro_pvalue": float(shapiro.pvalue), "environment": environment(),
                  "timing_definition": "HPO/CV plus one development refit; excludes data fetch, test prediction, serialization and plots",
                  "test_interpretation": "Comparative educational evaluation; choosing winner by test is descriptive and outcome-informed"}
        write_json(result_path, result)
        event(out / "events.jsonl", "completed", cv_rmse=cv_rmse, test_rmse=result["test_rmse"], total_seconds=result["total_seconds"])
        if root is None and seed == 42:
            aggregate()
        print(json.dumps({k: result[k] for k in ["method", "seed", "cv_rmse", "test_rmse", "total_seconds", "n_evaluations"]}), flush=True)
        return result
    except Exception as exc:
        write_json(result_path, {"status": "failed", "method": method, "seed": seed,
            "error": repr(exc), "traceback": traceback.format_exc(), "elapsed_seconds": time.perf_counter() - started,
            "completed_candidates": len(obj.rows), "data_fingerprint": data_fingerprint})
        event(out / "events.jsonl", "failed", error=repr(exc))
        raise


def robustness(jobs, resume):
    metrics = pd.read_csv(RESULTS / "metrics.csv")
    missing = set(METHODS) - set(metrics.method)
    if missing:
        raise RuntimeError(f"Finish main experiments first: {sorted(missing)}")
    cv_winner = str(metrics.loc[metrics.cv_rmse.idxmin(), "method"])
    test_winner = str(metrics.loc[metrics.test_rmse.idxmin(), "method"])
    write_json(RESULTS / "selection-record.json", {"selected_by_cv": cv_winner,
        "descriptive_best_by_test": test_winner, "selection_before_robustness": True,
        "seeds": [0, 7, 21, 42, 99], "fixed": ["holdout split seed42", "CV folds seed42", "dataset"],
        "varied": ["optimizer random seed", "GradientBoostingRegressor random_state"],
        "limitation": "Test-winner selection is outcome-informed; five-seed spread measures procedure randomness conditional on fixed data, not population uncertainty"})
    rows = []
    for method in dict.fromkeys([cv_winner, test_winner]):
        for seed in [0, 7, 21, 42, 99]:
            r = run_method(method, seed, jobs, resume=resume or seed == 42)
            rows.append({k: r[k] for k in ["method", "seed", "cv_rmse", "test_rmse", "test_mae", "test_r2",
                                           "search_seconds", "refit_seconds", "total_seconds", "n_evaluations"]})
            pd.DataFrame(rows).to_csv(RESULTS / "robustness.csv", index=False)
    summary = pd.DataFrame(rows).groupby("method").test_rmse.agg(["mean", "std", "min", "max", "count"])
    summary.to_csv(RESULTS / "robustness-summary.csv")


def sample_comparison(jobs, resume):
    full = RESULTS / "optuna" / "seed_42" / "result.json"
    if not full.exists():
        raise RuntimeError("Run full-development Optuna before its subsample comparison")
    r = run_method("optuna", 42, jobs, resume, .5, RESULTS / "sample50")
    f = json.loads(full.read_text(encoding="utf-8"))
    pd.DataFrame([{k: v for k, v in x.items() if not isinstance(v, (dict, list))} for x in [f, r]]).to_csv(
        RESULTS / "sample-comparison.csv", index=False)


def supplemental_baselines(jobs):
    """Simple scientific references, supplementary to the assignment's GBR baseline."""
    out = RESULTS / "supplemental"
    out.mkdir(parents=True, exist_ok=True)
    warm_workers(jobs)
    obj = Objective("supplemental", 42, jobs, out)
    rows = []
    for name, estimator in [("dummy_mean", DummyRegressor(strategy="mean")), ("ridge_alpha1", Ridge(alpha=1.))]:
        model = Pipeline([("imputer", SimpleImputer(strategy="median")),
                          ("scaler", StandardScaler()), ("model", estimator)])
        t0 = time.perf_counter()
        with threadpool_limits(1), joblib.parallel_config(backend="loky", n_jobs=jobs, inner_max_num_threads=1):
            cv = -cross_val_score(model, obj.X, obj.y, cv=obj.folds,
                                 scoring="neg_root_mean_squared_error", n_jobs=jobs, error_score="raise")
        cv_seconds = time.perf_counter() - t0
        t0 = time.perf_counter()
        with threadpool_limits(1):
            model.fit(obj.X, obj.y)
        fit_seconds = time.perf_counter() - t0
        predicted = model.predict(obj.Xtest)
        rows.append({"method": name, "cv_rmse": np.mean(cv), "test_rmse": np.sqrt(mean_squared_error(obj.ytest, predicted)),
                     "test_mae": mean_absolute_error(obj.ytest, predicted), "test_r2": r2_score(obj.ytest, predicted),
                     "search_seconds": cv_seconds, "refit_seconds": fit_seconds, "total_seconds": cv_seconds + fit_seconds})
    pd.DataFrame(rows).to_csv(RESULTS / "supplemental-baselines.csv", index=False)
    print(json.dumps(native(rows)), flush=True)


def verify():
    contract = json.loads((DATA / "data-contract.json").read_text(encoding="utf-8"))
    for filename, expected_hash in contract["sha256"].items():
        assert digest(DATA / filename) == expected_hash, f"Input drift: {filename}"
    z = np.load(DATA / "prepared.npz", allow_pickle=False)
    assert not set(z["train_ids"]) & set(z["test_ids"])
    assert len(z["train_ids"]) + len(z["test_ids"]) == len(z["y"])
    for k in range(5):
        a, b = z[f"fold_{k}_train"], z[f"fold_{k}_valid"]
        assert not set(a) & set(b)
        assert len(a) + len(b) == len(z["train_ids"])
    expected = {"baseline": 1, "grid": 36, "random": 30, "gp_manual": 15,
                "bayessearch": 40, "bayesopt": 40, "optuna": 40, "hyperopt": 40,
                "ray": 40, "pso_w07": 320, "pso_w04": 320, "pso_w09": 320}
    checked = []
    for m in METHODS:
        folder = RESULTS / m / "seed_42"
        if not (folder / "result.json").exists():
            continue
        r = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        assert r["status"] == "complete", m
        trials = pd.read_csv(folder / "trials.csv")
        prediction = pd.read_csv(folder / "predictions.csv")
        assert len(trials) == r["n_evaluations"]
        if m in expected:
            assert len(trials) == expected[m], (m, len(trials))
        assert np.all(np.isfinite(trials.cv_rmse)), m
        eligible = trials[(trials.status == "complete") & (trials.resource >= 1)]
        assert np.isclose(eligible.cv_rmse.min(), r["cv_rmse"], atol=1e-10)
        assert np.isclose(np.sqrt(mean_squared_error(prediction.y_true, prediction.y_pred)), r["test_rmse"], atol=1e-10)
        checked.append(m)
    write_json(RESULTS / "verification.json", {"status": "passed", "methods_checked": checked,
               "limits": "Structural checks and metric traceability; not independent scientific validation"})
    print(json.dumps({"verified": checked}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run", "robustness", "sample", "supplement", "verify", "aggregate"])
    parser.add_argument("--method", default="all", help="One method or comma-separated method names")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--jobs", type=int, default=5)
    parser.add_argument("--resume", action="store_true", help="Reuse completed compatible methods; restart/preserve incomplete attempts")
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 5:
        parser.error("CV jobs must be between 1 and 5")
    if args.action == "prepare":
        prepare()
    elif args.action == "run":
        chosen = METHODS if args.method == "all" else args.method.split(",")
        if set(chosen) - set(METHODS):
            parser.error(f"Unknown methods: {set(chosen)-set(METHODS)}")
        for method in chosen:
            run_method(method, args.seed, args.jobs, args.resume)
    elif args.action == "robustness":
        robustness(args.jobs, args.resume)
    elif args.action == "sample":
        sample_comparison(args.jobs, args.resume)
    elif args.action == "supplement":
        supplemental_baselines(args.jobs)
    elif args.action == "verify":
        verify()
    elif args.action == "aggregate":
        aggregate()


if __name__ == "__main__":
    main()
