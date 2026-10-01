"""Read-only arithmetic audit of saved experimental outputs; never fits a model."""
from __future__ import annotations
import argparse
import collections
import csv
import datetime
import hashlib
import itertools
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
METHODS = ["baseline", "grid", "random", "gp_manual", "bayessearch", "bayesopt",
           "optuna", "hyperopt", "ray", "ga", "de_best1bin", "de_rand1bin",
           "pso_w07", "pso_w04", "pso_w09"]
EXPECTED = {"baseline": 1, "grid": 36, "random": 30, "gp_manual": 15,
            "bayessearch": 40, "bayesopt": 40, "optuna": 40, "hyperopt": 40,
            "ray": 40, "pso_w07": 320, "pso_w04": 320, "pso_w09": 320}


def rows(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def params(row):
    return tuple(float(row[k]) for k in ["learning_rate", "subsample", "n_estimators"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-all", action="store_true")
    args = parser.parse_args()
    checks = []
    def add(name, ok, detail=None):
        checks.append({"check": name, "status": "pass" if bool(ok) else "fail", "detail": detail})
    contract = json.loads((ROOT / "data/data-contract.json").read_text(encoding="utf-8"))
    for filename, expected in contract["sha256"].items():
        add("input_sha256:" + filename, hashlib.sha256((ROOT / "data" / filename).read_bytes()).hexdigest() == expected)
    manifest = rows(ROOT / "data/split-manifest.csv")
    train_ids = {int(r["source_row"]) for r in manifest if r["split"] == "train"}
    test_ids = {int(r["source_row"]) for r in manifest if r["split"] == "test"}
    fold_counts = {str(k): sum(r["split"] == "train" and r["validation_fold"] == str(k) for r in manifest) for k in range(5)}
    add("holdout_disjoint", not train_ids & test_ids)
    add("fold_partition", sum(fold_counts.values()) == len(train_ids), fold_counts)
    by_method, complete = {}, []
    code_groups = collections.defaultdict(list)
    for method in METHODS:
        folder = RESULTS / method / "seed_42"
        if not (folder / "result.json").exists():
            continue
        result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        if result.get("status") != "complete":
            continue
        complete.append(method)
        code_groups[result["code_sha256"]].append(method)
        trial = rows(folder / "trials.csv")
        by_method[method] = trial
        add(method + ":trial_count", len(trial) == result["n_evaluations"] and
            (method not in EXPECTED or len(trial) == EXPECTED[method]), len(trial))
        add(method + ":fold_mean", all(abs(sum(float(t[f"fold_{k}"]) for k in range(5))/5 - float(t["cv_rmse"])) < 1e-10 for t in trial))
        add(method + ":parameters_in_domain", all(.03-1e-12 <= float(t["learning_rate"]) <= .2+1e-12
            and .6-1e-12 <= float(t["subsample"]) <= 1.+1e-12 and 50 <= float(t["n_estimators"]) <= 200
            and float(t["n_estimators"]).is_integer() for t in trial))
        eligible = [t for t in trial if t["status"] == "complete" and float(t["resource"]) >= 1]
        selected = min(eligible, key=lambda t: float(t["cv_rmse"]))
        add(method + ":selection", abs(float(selected["cv_rmse"]) - result["cv_rmse"]) < 1e-10 and
            all(abs(float(selected[k]) - value) < 1e-10 for k, value in result["best_params"].items()))
        predicted = rows(folder / "predictions.csv")
        yy = [float(p["y_true"]) for p in predicted]
        pp = [float(p["y_pred"]) for p in predicted]
        mse = sum((a-b)**2 for a, b in zip(yy, pp)) / len(yy)
        mae = sum(abs(a-b) for a, b in zip(yy, pp)) / len(yy)
        mean = sum(yy)/len(yy)
        r2 = 1 - sum((a-b)**2 for a, b in zip(yy, pp)) / sum((a-mean)**2 for a in yy)
        add(method + ":test_metrics", max(abs(math.sqrt(mse)-result["test_rmse"]), abs(mae-result["test_mae"]), abs(r2-result["test_r2"])) < 1e-10)
        add(method + ":test_rows", {int(p["source_row"]) for p in predicted} == test_ids)
        add(method + ":residual_definition", all(abs(float(p["residual"]) - (float(p["y_true"]) - float(p["y_pred"]))) < 1e-10 for p in predicted))
        add(method + ":timing", result["search_seconds"] >= 0 and result["refit_seconds"] >= 0 and
            abs(result["total_seconds"] - result["search_seconds"] - result["refit_seconds"]) < 1e-10)
        add(method + ":fixed_protocol", result["fold_seed"] == 42 and result["split_seed"] == 42 and result["cv_jobs"] == 5)
        if method != "ray":
            add(method + ":cv_work", result["cv_fits"] == 5*len(trial) and
                result["trained_trees_cv"] == 5*sum(int(t["n_estimators"]) for t in trial))
        if method in {"ga", "pso_w07", "pso_w04", "pso_w09"}:
            history = rows(folder / "generations.csv")
            add(method + ":generations", [int(h["generation"]) for h in history] == list(range(16)) and
                int(history[-1]["evaluations"]) == len(trial))
            key = "best_ever" if method == "ga" else "best"
            bests = [float(h[key]) for h in history]
            add(method + ":incumbent_monotonic", all(b <= a+1e-12 for a, b in zip(bests, bests[1:])))
            if method.startswith("pso"):
                add(method + ":current_swarm_mean", all(abs(float(history[i]["mean"]) -
                    sum(float(t["cv_rmse"]) for t in trial[i*20:(i+1)*20])/20) < 1e-10 for i in range(16)))
            else:
                add(method + ":integer_encoding", all(abs((math.log(float(t["learning_rate"])/.03)/math.log(.2/.03))*1000 -
                    round((math.log(float(t["learning_rate"])/.03)/math.log(.2/.03))*1000)) < 1e-7 and
                    abs(((float(t["subsample"])-.6)/.4)*1000 - round(((float(t["subsample"])-.6)/.4)*1000)) < 1e-7 for t in trial))
        if method.startswith("de_"):
            de = json.loads((folder / "de-result.json").read_text(encoding="utf-8"))
            add(method + ":actual_nfev", de["nfev"] == len(trial) == 30*(de["nit"]+1) and de["nit"] <= 15 and not de["polish"])
    if "grid" in by_method:
        add("grid:full_cartesian", {params(t) for t in by_method["grid"]} ==
            set(itertools.product([.03, .1, .2], [.6, .8, 1.], [50, 100, 150, 200])))
    if "grid" in by_method and "random" in by_method:
        lookup = {params(t): t for t in by_method["grid"]}
        add("random:grid_subset_identical_folds", all(params(t) in lookup and
            all(abs(float(t[f"fold_{k}"]) - float(lookup[params(t)][f"fold_{k}"])) < 1e-10 for k in range(5)) for t in by_method["random"]))
    ray_detail = None
    if "ray" in by_method:
        folder = RESULTS / "ray/seed_42"
        result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        stages = rows(folder / "ray-stages.csv")
        grouped = collections.defaultdict(list)
        for stage in stages:
            grouped[stage["trial_id"]].append(stage)
        add("ray:trial_ids", len(grouped) == 40)
        add("ray:monotonic_stage_prefix", all([float(s["resource"]) for s in ss] == [.25, .5, .75, 1.][:len(ss)] for ss in grouped.values()))
        increments_ok = True
        for ss in grouped.values():
            previous = 0
            for s in ss:
                trees = int(s["trees"])
                increments_ok &= trees == math.ceil(float(s["n_estimators"])*float(s["resource"])) and trees-previous == int(s["incremental_trees"])
                previous = trees
        add("ray:actual_tree_increments", increments_ok)
        trees = 5*sum(int(s["incremental_trees"]) for s in stages)
        add("ray:work_totals", result["cv_fits"] == 5*len(stages) and result["trained_trees_cv"] == trees)
        add("ray:pruning_status", all((float(t["resource"]) == 1.) == (t["status"] == "complete") for t in by_method["ray"]))
        ray_detail = {"trials": 40, "stage_rows": len(stages), "complete": result["completed_trials"],
                      "pruned": result["pruned_trials"], "incremental_cv_fits": 5*len(stages), "new_cv_trees": trees}
    groups = collections.defaultdict(list)
    for row in rows(ROOT / "data/clean.csv"):
        groups[tuple(float(row[k]) for k in contract["features"])].append(int(row["source_row"]))
    overlap = [ids for ids in groups.values() if len(ids) > 1 and set(ids)&train_ids and set(ids)&test_ids]
    # Verify the exact upstream procedure files, not a claim of installed integration.
    vendor = ROOT.parent / "vendor/rnd-superpowers"
    framework_manifest = json.loads((vendor / "SOURCE-MANIFEST.json").read_text(encoding="utf-8"))
    framework_ok = []
    for item in framework_manifest["files"]:
        content = (vendor / item["path"]).read_bytes()
        blob_sha = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        valid = blob_sha == item["git_blob_sha1"] and len(content) == item["size"]
        framework_ok.append(valid)
        add("framework:" + item["path"], valid)
    add("framework:requested_commit", framework_manifest["commit"] == "f68892c8b7adba358b8aa437eec00a89fe88d340")
    for sha in code_groups:
        snapshot = ROOT / "code_versions" / f"experiment_{sha[:8]}.py"
        add("code_snapshot:" + sha[:8], snapshot.exists() and hashlib.sha256(snapshot.read_bytes()).hexdigest() == sha)
    robustness_detail = None
    if (RESULTS / "robustness.csv").exists():
        selection = json.loads((RESULTS / "selection-record.json").read_text(encoding="utf-8"))
        aggregate = rows(RESULTS / "metrics.csv")
        add("selection:cv_winner", selection["selected_by_cv"] == min(aggregate, key=lambda r: float(r["cv_rmse"]))["method"])
        add("selection:test_winner_descriptive", selection["descriptive_best_by_test"] == min(aggregate, key=lambda r: float(r["test_rmse"]))["method"])
        robustness_rows = rows(RESULTS / "robustness.csv")
        expected_pairs = set(itertools.product({selection["selected_by_cv"], selection["descriptive_best_by_test"]}, [0, 7, 21, 42, 99]))
        add("robustness:all_method_seed_pairs", {(r["method"], int(r["seed"])) for r in robustness_rows} == expected_pairs and len(robustness_rows) == len(expected_pairs))
        for rr in robustness_rows:
            method, seed = rr["method"], int(rr["seed"])
            folder = RESULTS / method / f"seed_{seed}"
            result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
            trial = rows(folder / "trials.csv")
            add(f"robustness:{method}:{seed}:full_procedure", len(trial) == int(rr["n_evaluations"]) and len(trial) >= 20 and
                result["cv_fits"] == 5*len(trial) and result["fold_seed"] == 42 and result["split_seed"] == 42 and result["seed"] == seed)
            add(f"robustness:{method}:{seed}:selected_cv", abs(min(float(t["cv_rmse"]) for t in trial)-result["cv_rmse"]) < 1e-10)
            add(f"robustness:{method}:{seed}:aggregate_matches", all(abs(float(rr[k])-result[k]) < 1e-10 for k in
                ["cv_rmse", "test_rmse", "test_mae", "test_r2", "search_seconds", "refit_seconds", "total_seconds"]))
            predicted = rows(folder / "predictions.csv")
            error = [float(p["y_true"])-float(p["y_pred"]) for p in predicted]
            add(f"robustness:{method}:{seed}:rmse_holdout", abs(math.sqrt(sum(e*e for e in error)/len(error))-result["test_rmse"]) < 1e-10 and
                {int(p["source_row"]) for p in predicted} == test_ids)
        summary = rows(RESULTS / "robustness-summary.csv")
        for row in summary:
            values = [float(r["test_rmse"]) for r in robustness_rows if r["method"] == row["method"]]
            add("robustness:sample_sd:" + row["method"], abs(statistics.mean(values)-float(row["mean"])) < 1e-10 and
                abs(statistics.stdev(values)-float(row["std"])) < 1e-10 and len(values) == int(row["count"]) == 5)
        robustness_detail = {"selection": selection, "summary": summary, "new_hpo_runs": len(expected_pairs)-2}
    sample_detail = None
    sample_folder = RESULTS / "sample50/optuna/seed_42"
    if (sample_folder / "result.json").exists():
        sample = json.loads((sample_folder / "result.json").read_text(encoding="utf-8"))
        trial = rows(sample_folder / "trials.csv")
        sampled = rows(sample_folder / "sample-indices.csv")
        indices = [int(r["development_position"]) for r in sampled]
        add("sample50:development_subset", len(indices) == len(set(indices)) == sample["train_rows"] == len(train_ids)//2 and
            all(0 <= i < len(train_ids) for i in indices))
        add("sample50:budget", len(trial) == sample["n_evaluations"] == 40 and sample["cv_fits"] == 200)
        predicted = rows(sample_folder / "predictions.csv")
        error = [float(r["y_true"])-float(r["y_pred"]) for r in predicted]
        add("sample50:same_test_and_rmse", {int(r["source_row"]) for r in predicted} == test_ids and
            abs(math.sqrt(sum(e*e for e in error)/len(error))-sample["test_rmse"]) < 1e-10)
        for label, folder in [("full", RESULTS / "optuna/seed_42"), ("half", sample_folder)]:
            importance = rows(folder / "optuna_importances.csv")
            add("optuna:importance_normalization:" + label, {r["hyperparameter"] for r in importance} ==
                {"learning_rate", "subsample", "n_estimators"} and all(float(r["importance"]) >= 0 for r in importance) and
                abs(sum(float(r["importance"]) for r in importance)-1) < 1e-10)
        sample_detail = {"train_rows": sample["train_rows"], "test_rows": sample["test_rows"], "cv_rmse": sample["cv_rmse"], "test_rmse": sample["test_rmse"]}
    missing = sorted(set(METHODS)-set(complete))
    if args.require_all:
        add("all_methods_completed", not missing, missing)
    output = {"audit_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "completed_methods": complete,
              "missing_methods": missing, "checks": checks, "code_groups": dict(code_groups),
              "feature_vectors_crossing_holdout": overlap, "ray": ray_detail,
              "framework": {"commit": framework_manifest["commit"], "verified_files": sum(framework_ok), "total_files": len(framework_ok), "scope": "Exact core source subset; validation example directory not copied"},
              "robustness": robustness_detail, "sample50": sample_detail,
              "scope": "Saved-data arithmetic audit only; no model fitted. Other processes may conduct separate dynamic audits."}
    path = ROOT / "self-review-evidence-final.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    failures = [c for c in checks if c["status"] == "fail"]
    print(json.dumps({"methods": len(complete), "checks": len(checks), "failures": failures, "missing": missing}))
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
