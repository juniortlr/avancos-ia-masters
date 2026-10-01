"""Build the Aula 05 report from completed, recorded experiments only.

No placeholder or synthetic outcome is allowed. Run after the experiment and
artifact builders have produced their JSON, CSV and PNG files.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


def esc(value):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
                    "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
                    "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(c, c) for c in str(value))


def num(value, digits=4):
    if value is None:
        return r"\textemdash"
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"Non-finite result in report: {value}")
    return f"{value:.{digits}f}".replace(".", "{,}")


def pct(value, digits=2):
    return num(100 * float(value), digits) + r"\%"


def pv(value):
    value = float(value)
    if not 0 <= value <= 1:
        raise ValueError(f"Invalid p-value {value}")
    if value == 0:
        return r"$<10^{-300}$ (limite numérico)"
    if value < .001:
        mantissa, exponent = f"{value:.2e}".split("e")
        return "$" + mantissa.replace(".", "{,}") + r"\times10^{" + str(int(exponent)) + "}$"
    return "$" + num(value, 4) + "$"


def read_json(path):
    with Path(path).open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class Report:
    def __init__(self, root):
        self.root = Path(root)
        self.parts = []
        self.blocks = []
        self.figure_paths = []
        self.labels = set()

    def add(self, latex, record=True):
        self.parts.append(latex.strip() + "\n")
        if record:
            self.blocks.append({"kind": "latex", "text": latex.strip()})

    def section(self, title):
        self.add(r"\section{" + esc(title) + "}")

    def subsection(self, title, toc=True):
        self.add((r"\subsection{" if toc else r"\subsection*{") + esc(title) + "}")

    def table(self, headers, rows, caption, spec=None, small=True, label=None):
        spec = spec or ("l" + "r" * (len(headers) - 1))
        latex = [r"\begin{table}[H]", r"\centering", r"\caption{" + caption + "}"]
        if label:
            self.check_label(label)
            latex.append(r"\label{" + label + "}")
        if small:
            latex.append(r"\small")
        latex += [r"\resizebox{\textwidth}{!}{%", r"\begin{tabular}{" + spec + "}",
                  r"\toprule", " & ".join(headers) + r" \\", r"\midrule"]
        latex.extend(" & ".join(str(x) for x in row) + r" \\" for row in rows)
        latex += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
        self.add("\n".join(latex), record=False)
        self.blocks.append({"kind": "table", "headers": headers, "rows": rows, "caption": caption})

    def check_label(self, label):
        if label in self.labels:
            raise ValueError(f"Duplicate label: {label}")
        self.labels.add(label)

    def figure(self, path, caption, label, width="0.98", height="0.68"):
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        if not candidate.is_file():
            raise FileNotFoundError(f"Required report figure is missing: {candidate}")
        relative = candidate.resolve().relative_to(self.root.resolve()).as_posix()
        self.figure_paths.append(relative)
        self.check_label(label)
        self.add(r"\begin{figure}[H]" + "\n" + r"\centering" + "\n" +
                 r"\includegraphics[width=" + width + r"\textwidth,height=" + height +
                 r"\textheight,keepaspectratio]{\detokenize{" + relative + "}}\n" +
                 r"\caption{" + caption + "}\n" + r"\label{" + label + "}\n" + r"\end{figure}", record=False)
        self.blocks.append({"kind": "figure", "path": str(candidate.resolve()), "caption": caption,
                            "width": float(width), "height": float(height)})

    def finish(self, filename):
        document = "\n".join(self.parts)
        if re.search(r"\[PREENCHER\]|TODO|INSERIR FIGURA|a implementar", document):
            raise ValueError("Unfinished content in final report")
        filename.write_text(document, encoding="utf-8")
        return filename


PREAMBLE = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[brazilian]{babel}
\usepackage{amsmath,amssymb,graphicx,booktabs,caption,float,geometry,hyperref}
\usepackage[table]{xcolor}
\usepackage{enumitem,array,longtable,microtype}
\geometry{margin=2.5cm}
\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}
\setlength{\emergencystretch}{3em}
\definecolor{bestgreen}{RGB}{215,240,218}
\definecolor{timeyellow}{RGB}{255,242,179}
\title{\Large\textbf{Avanços em Inteligência Artificial}\\
\large EELT7025 --- PPGEE, UFPR\\[0.3cm]
\normalsize Exercícios da Aula 05\\
\normalsize Otimização de hiperparâmetros na resistência à compressão do concreto}
\author{\parbox{\textwidth}{\centering Adriely Teixeira de Paula\\
Betina Zynger Capaverde\\Emilio Gaudeda Junior}}
\date{30 de setembro de 2026}
\begin{document}
\maketitle
\tableofcontents
\newpage
"""


BIBLIOGRAPHY = r"""
\begin{thebibliography}{99}
\bibitem{uci} Yeh, I. (1998). \emph{Concrete Compressive Strength} [Dataset].
UCI Machine Learning Repository. DOI: \href{https://doi.org/10.24432/C5PK67}{10.24432/C5PK67}.
\bibitem{rnd} juniortlr. \emph{rnd-superpowers}, versão fixada no commit
\texttt{f68892c8b7adba358b8aa437eec00a89fe88d340}.
\url{https://github.com/juniortlr/rnd-superpowers/commit/f68892c8b7adba358b8aa437eec00a89fe88d340}.
\bibitem{aula} Coelho, L. dos S. (2026). \emph{Aula 05: Otimização de hiperparâmetros}.
EELT7025, PPGEE, Universidade Federal do Paraná. Notebook fornecido na disciplina.
\bibitem{sklearn} Scikit-learn. \emph{GradientBoostingRegressor; Pipeline; GridSearchCV;
RandomizedSearchCV}. Documentação oficial.
\url{https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html}.
\bibitem{bergstra} Bergstra, J.; Bengio, Y. (2012). Random search for hyper-parameter
optimization. \emph{Journal of Machine Learning Research}, 13, 281--305.
\url{https://jmlr.org/papers/v13/bergstra12a.html}.
\bibitem{gp} Rasmussen, C. E.; Williams, C. K. I. (2006).
\emph{Gaussian Processes for Machine Learning}. MIT Press.
\url{https://gaussianprocess.org/gpml/}.
\bibitem{skopt} Scikit-optimize. \emph{BayesSearchCV}. Documentação oficial.
\url{https://scikit-optimize.readthedocs.io/en/stable/modules/generated/skopt.BayesSearchCV.html}.
\bibitem{bayesopt} Bayesian-optimization. \emph{BayesianOptimization}.
\url{https://github.com/bayesian-optimization/BayesianOptimization}.
\bibitem{optuna} Akiba, T. et al. (2019). Optuna: a next-generation hyperparameter
optimization framework. \emph{KDD}, 2623--2631. DOI:10.1145/3292500.3330701.
Documentação de importância: \url{https://optuna.readthedocs.io/en/stable/reference/generated/optuna.importance.get_param_importances.html}.
\bibitem{hyperopt} Bergstra, J.; Bardenet, R.; Bengio, Y.; Kégl, B. (2011).
Algorithms for hyper-parameter optimization. \emph{Advances in Neural Information Processing Systems}, 24.
\bibitem{ray} Ray Tune. \emph{OptunaSearch e ASHAScheduler}. Documentação oficial.
\url{https://docs.ray.io/en/latest/tune/api/doc/ray.tune.schedulers.ASHAScheduler.html}.
\bibitem{deap} DEAP. \emph{Evolutionary algorithms made easy}. Documentação oficial.
\url{https://deap.readthedocs.io/en/master/}.
\bibitem{de} Storn, R.; Price, K. (1997). Differential evolution: a simple and efficient
heuristic for global optimization over continuous spaces. \emph{Journal of Global Optimization}, 11, 341--359.
DOI:10.1023/A:1008202821328.
\bibitem{pso} Kennedy, J.; Eberhart, R. (1995). Particle swarm optimization.
\emph{ICNN'95}, 4, 1942--1948. DOI:10.1109/ICNN.1995.488968.
\end{thebibliography}
\end{document}
"""


METHODS = {
    "baseline": "Baseline", "grid": "Grid Search", "random": "Random Search",
    "gp_manual": "GP manual", "bayessearch": "skopt (GP + EI)",
    "bayesopt": r"bayes\_opt (GP + UCB)", "optuna": "Optuna (TPE)",
    "hyperopt": "Hyperopt (TPE)", "ray": "Ray (Optuna + ASHA)", "ga": "GA (DEAP)",
    "de_best1bin": "DE best1bin", "de_rand1bin": "DE rand1bin",
    "pso_w07": "PSO w=0,7", "pso_w04": "PSO w=0,4", "pso_w09": "PSO w=0,9",
}
MAIN = [k for k in METHODS if k not in {"de_rand1bin", "pso_w04", "pso_w09"}]
FEATURE_PT = {
    "Cement": "Cimento", "Blast Furnace Slag": "Escória", "Fly Ash": "Cinza volante",
    "Water": "Água", "Superplasticizer": "Superplastificante", "Coarse Aggregate": "Agregado graúdo",
    "Fine Aggregate": "Agregado miúdo", "Age": "Idade", "target_mpa": "Resistência",
}


def name(method):
    return METHODS[method]


def feature_name(feature):
    return esc(FEATURE_PT.get(feature, feature))


def params_text(result):
    p = result["best_params"]
    return (r"$\eta=" + num(p["learning_rate"]) + r"$, $s=" + num(p["subsample"], 3)
            + r"$ e $N=" + str(int(p["n_estimators"])) + "$")


def table_metrics(report, results, methods, caption, color=False):
    cols = ["cv_rmse", "test_rmse", "test_mae", "test_r2", "total_seconds"]
    extrema = {c: (max if c == "test_r2" else min)(results[m][c] for m in methods) for c in cols}
    rows = []
    for m in methods:
        r = results[m]
        row = [name(m)]
        for c in cols:
            cell = num(r[c], 3 if c == "total_seconds" else 4)
            if color and math.isclose(r[c], extrema[c], abs_tol=1e-10, rel_tol=1e-10):
                cell = r"\cellcolor{" + ("timeyellow" if c == "total_seconds" else "bestgreen") + "}" + cell
            row.append(cell)
        row.append(str(r["n_evaluations"]))
        rows.append(row)
    report.table(["Método", "CV RMSE", "Teste RMSE", "Teste MAE", r"Teste $R^2$", "Tempo (s)", "Aval."],
                 rows, caption, spec="lrrrrrr")


def build(root):
    root = Path(root)
    analysis = read_json(root / "results" / "analysis.json")
    contract = read_json(root / "data" / "data-contract.json")
    results = {m: read_json(root / "results" / m / "seed_42" / "result.json") for m in METHODS}
    if any(r.get("status") != "complete" for r in results.values()):
        raise ValueError("All required primary experiments must be complete")
    fingerprints = {r["data_fingerprint"] for r in results.values()}
    if len(fingerprints) != 1:
        raise ValueError("Experiments were not evaluated on the same frozen data/split")
    robustness = pd.read_csv(root / "results" / "robustness.csv")
    cv_winner = min(results, key=lambda m: results[m]["cv_rmse"])
    test_winner = min(results, key=lambda m: results[m]["test_rmse"])
    for winner in {cv_winner, test_winner}:
        if set(robustness.loc[robustness.method == winner, "seed"]) != {0, 7, 21, 42, 99}:
            raise ValueError(f"Incomplete five-seed robustness for {winner}")
    half = read_json(root / "results" / "sample50" / "optuna" / "seed_42" / "result.json")
    if half["status"] != "complete":
        raise ValueError("Optuna sample-size comparison is incomplete")
    quality = pd.read_csv(root / "data" / "quality-summary.csv")
    desc = pd.read_csv(root / "data" / "describe_raw.csv", index_col=0)
    trials = {m: pd.read_csv(root / "results" / m / "seed_42" / "trials.csv") for m in METHODS}
    env = results["baseline"]["environment"]
    gr = analysis["grid_random"]
    gp = analysis["gp_iterations"]
    if len(gp) != 10:
        raise ValueError("Ten recorded GP acquisitions are required")
    image_dir = root / "Figuras_Aula5"
    image_dir.mkdir(exist_ok=True)
    report = Report(root)

    def fig(stem, caption, height="0.65"):
        source = root / "figures" / (stem + ".png")
        target = image_dir / source.name
        if source.is_file():
            shutil.copy2(source, target)
        report.figure(target, caption, "fig:" + stem.replace("_", "-"), height=height)

    b = results["baseline"]
    report.add(PREAMBLE)
    report.section("Protocolo, objetivo e rastreabilidade")
    report.add(r"Comparamos estratégias de otimização de hiperparâmetros (HPO) de um único "
               r"\texttt{GradientBoostingRegressor} sobre o dataset \emph{Concrete Compressive Strength}, "
               r"UCI 165, com resistência à compressão em MPa\cite{uci}. Os dois exercícios usam o mesmo "
               r"conjunto de dados, a mesma divisão treino/teste e os mesmos cinco folds. O objetivo é "
               r"medir qualidade preditiva e custo; não foi fornecido um limiar industrial de erro aceitável.")
    report.add(r"O protocolo local e o orçamento foram fixados antes dos resultados em "
               r"\texttt{study-protocol.md} e \texttt{search-budget.json}, seguindo práticas de investigação "
               r"do \emph{rnd-superpowers}, no commit solicitado\cite{rnd}. A referência da disciplina "
               r"orienta os itens 1--10\cite{aula}. As lições das tarefas anteriores foram incorporadas "
               r"como verificação do inventário completo, registro das exclusões e confronto entre "
               r"conclusões e resultados. Não havia comentário docente disponível nas fontes nem no "
               r"painel de revisão consultado; essa revisão não é atribuída ao professor.")
    report.add(r"\textbf{Desenho da comparação.} É um estudo computacional exploratório em um dataset "
               r"e um holdout. A configuração de cada método é escolhida pelo RMSE médio de validação "
               r"cruzada, isto é, a média dos cinco RMSEs de folds, não o RMSE de previsões "
               r"out-of-fold agrupadas; o teste apenas avalia essa configuração. A seleção posterior do menor RMSE "
               r"de teste, exigida nos itens 9.4 e 10.2, é descritiva e informada pelos resultados. "
               r"A seleção pelo menor CV é apresentada separadamente da recomendação operacional, "
               r"que pondera qualidade e custo após os resultados. Não se afirma superioridade estatística "
               r"universal nem validação confirmatória independente depois dessa seleção.")
    report.add(r"\textbf{Tempo e recursos.} Cada tempo total soma busca/CV e um ajuste final; instalação, "
               r"download, gráficos, previsão de teste e serialização final ficam fora. Para o baseline, "
               r"o total inclui CV e fit, e o fit é informado separadamente. Usaram-se " +
               str(b["cv_jobs"]) + r" folds concorrentes, estimadores com limite de uma thread "
               r"e métodos executados sequencialmente em CPU local. O pool loky de processos foi "
               r"aquecido fora do cronômetro; Ray usa cinco threads de folds dentro de um trial. "
               r"Os tempos incluem overhead "
               r"dos otimizadores e refletem esta execução, sujeitos à carga da máquina.")

    report.section("Exercício 1 — preparação, baseline e buscas clássicas")
    report.subsection("1. Carregamento, qualidade e pré-processamento")
    report.add(r"Os dados foram obtidos por \texttt{ucimlrepo.fetch\_ucirepo(id=165)}. O arquivo bruto "
               f"contém {contract['raw_shape'][0]} linhas e {contract['raw_shape'][1]} colunas "
               r"(oito preditores e um alvo). Foram removidas " + str(contract["exact_duplicate_rows_removed"]) +
               r" duplicatas exatas da linha completa, conservando a primeira ocorrência; restaram " +
               str(contract["clean_shape"][0]) + r" observações. Zero é um valor válido dos ingredientes, "
               r"não um código de ausência. Nenhuma observação foi removida com base no erro do modelo.")
    qrows = [[feature_name(row.column), esc(row.dtype), str(int(row.missing_count)), pct(row.missing_fraction)]
             for row in quality.itertuples(index=False)]
    report.table(["Variável", "Tipo lido", "Ausentes", "Proporção"], qrows,
                 "Qualidade de todas as colunas no arquivo bruto.", spec="llrr")
    drows = []
    for c in desc:
        drows.append([feature_name(c), str(int(desc.loc["count", c])), num(desc.loc["mean", c], 2),
                      num(desc.loc["std", c], 2), num(desc.loc["min", c], 2), num(desc.loc["25%", c], 2),
                      num(desc.loc["50%", c], 2), num(desc.loc["75%", c], 2), num(desc.loc["max", c], 2)])
    report.table(["Variável", "$n$", "Média", "DP", "Mín.", "$Q_1$", "Mediana", "$Q_3$", "Máx."],
                 drows, "Estatísticas descritivas brutas. Ingredientes em kg/m$^3$, idade em dias e alvo em MPa.",
                 spec="lrrrrrrrr")
    report.add(r"A limpeza precedeu a divisão aleatória 80/20 com \texttt{random\_state=42}: " +
               str(contract["train_rows"]) + r" observações de treino e " + str(contract["test_rows"]) +
               r" de teste. A validação usa \texttt{KFold(5, shuffle=True, random\_state=42)} "
               r"com índices congelados. Imputação por mediana, \texttt{StandardScaler} e GBR são "
               r"um único pipeline ajustado dentro de cada fold e, no refit, somente no treino. "
               r"A imputação é uma regra preventiva; sua necessidade efetiva está na tabela de ausentes. "
               r"A padronização é exigida pelo enunciado, embora as árvores não dependam dela. "
               r"O alvo não é padronizado, preservando MPa nas métricas.")
    report.add(r"O \texttt{describe()} global exigido pelo roteiro expõe estatísticas agregadas de todo "
               r"o arquivo; a EDA gráfica substantiva abaixo usa apenas o treino. A unidade é uma "
               r"observação de composição e idade do concreto. A divisão por linha não comprova "
               r"independência entre misturas relacionadas; faltam identificadores de lote para "
               r"avaliar generalização entre laboratórios ou lotes desconhecidos.")
    prepared = np.load(root / "data" / "prepared.npz", allow_pickle=False)
    cleaned = pd.read_csv(root / "data" / "clean.csv")
    development = cleaned.iloc[prepared["train_ids"]]
    holdout = cleaned.iloc[prepared["test_ids"]]
    train_vectors = set(map(tuple, development[contract["features"]].to_numpy()))
    test_vectors = set(map(tuple, holdout[contract["features"]].to_numpy()))
    shared_vectors = train_vectors & test_vectors
    train_shared = sum(tuple(x) in shared_vectors for x in development[contract["features"]].to_numpy())
    test_shared = sum(tuple(x) in shared_vectors for x in holdout[contract["features"]].to_numpy())
    if shared_vectors:
        report.add(r"\textbf{Sobreposição de composições.} Depois de remover duplicatas completas "
                   r"de preditores e alvo, a auditoria encontrou " + str(len(shared_vectors)) +
                   r" vetores de preditores idênticos presentes em treino e teste, envolvendo " +
                   str(train_shared) + r" linhas de treino e " + str(test_shared) +
                   r" de teste, com respostas distintas nas linhas não duplicadas. Podem ser "
                   r"medições relacionadas da mesma composição e idade. Assim, o holdout por linha "
                   r"avalia observações retidas; ele não valida previsão para receitas inéditas. "
                   r"Uma avaliação por grupos de composição é uma extensão necessária para essa "
                   r"outra pergunta, não executada nem substituída pelo split exigido aqui.")
    target_development = development["target_mpa"]
    associations = development[contract["features"] + ["target_mpa"]].corr()["target_mpa"].drop("target_mpa")
    associated = associations.abs().idxmax()
    report.add(r"No treino, a resistência tem mediana " + num(target_development.median(), 2) +
               r"\,MPa, intervalo observado $[" + num(target_development.min(), 2) + ";" +
               num(target_development.max(), 2) + r"]$ MPa e assimetria " + num(target_development.skew(), 3) +
               r". A associação linear marginal de maior módulo com o alvo foi de " + feature_name(associated) +
               r", $r=" + num(associations[associated], 3) + r"$. O scatter e o mapa de calor "
               r"complementam esse resumo: relações não lineares ou interações podem ser úteis "
               r"ao GBR mesmo quando a correlação marginal é menor.")
    fig("01_eda_distributions", "Distribuição do alvo e relação entre cimento e resistência no conjunto de treino.")
    fig("02_eda_correlations", "Correlações no treino; associações descritivas não identificam efeitos causais.")

    report.subsection("2. Modelo baseline sem otimização")
    report.add(r"A referência usa os parâmetros padrão do scikit-learn\cite{sklearn}, exceto "
               r"\texttt{random\_state=42}; nos três hiperparâmetros comparados, " + params_text(b) +
               r". O tempo exclusivo de treinamento final foi " + num(b["baseline_fit_seconds"], 4) +
               r"\,s; CV mais treinamento levou " + num(b["total_seconds"], 3) + r"\,s.")
    table_metrics(report, results, ["baseline"], "Baseline: métricas em MPa, exceto $R^2$, tempo total e avaliação CV.")
    fig("03_baseline_predictions", "Baseline: resistência observada versus prevista no holdout; a diagonal representa previsão exata.")
    supplemental_path = root / "results" / "supplemental-baselines.csv"
    if supplemental_path.is_file():
        supplemental = pd.read_csv(supplemental_path)
        supplemental_names = {"dummy_mean": "Preditor da média", "ridge_alpha1": r"Ridge $\alpha=1$"}
        report.table(["Referência adicional", "CV RMSE", "Teste RMSE", "Teste MAE", r"Teste $R^2$", "Tempo (s)"],
                     [[supplemental_names.get(x.method, esc(x.method)), num(x.cv_rmse), num(x.test_rmse),
                       num(x.test_mae), num(x.test_r2), num(x.total_seconds, 3)] for x in supplemental.itertuples()],
                     "Referências suplementares no mesmo split e folds, sem busca de hiperparâmetros.", spec="lrrrrr")
        report.add(r"Essas referências foram executadas depois da comparação principal, para "
                   r"contextualizar a dificuldade preditiva sem interferir nos tempos dos métodos. "
                   r"O preditor da média ignora as features; Ridge fornece uma referência linear "
                   r"com regularização fixa. O baseline exigido continua sendo o GBR com defaults, "
                   r"e é ele que define as razões de ganho e eficiência no restante do relatório.")

    report.subsection("3. Busca em grade e espaço de hiperparâmetros")
    report.table(["Hiperparâmetro", "Domínio", "Valores da grade"], [
        [r"Taxa $\eta$ (learning\_rate)", "$[0{,}03;0{,}20]$, log", "$0{,}03;0{,}10;0{,}20$"],
        [r"Fração $s$ (subsample)", "$[0{,}60;1{,}00]$", "$0{,}60;0{,}80;1{,}00$"],
        [r"Árvores $N$ (n\_estimators)", "$[50;200]$, inteiro", "$50;100;150;200$"],
    ], "Espaço fixado prospectivamente; demais hiperparâmetros permanecem nos defaults.", spec="lll")
    g = results["grid"]
    report.add(r"O produto cartesiano tem $3\times3\times4=36$ candidatos. O "
               r"\texttt{GridSearchCV} avalia todos com cinco folds e "
               r"\texttt{neg\_root\_mean\_squared\_error}; os sinais são revertidos neste relatório. "
               r"O menor CV RMSE foi " + num(g["cv_rmse"]) + r"\,MPa, em " + params_text(g) +
               r", após " + num(g["total_seconds"], 3) + r"\,s incluindo refit. Os limites são os "
               r"mesmos dos métodos contínuos posteriores, mas a grade tem apenas estes pontos; "
               r"isso impede tratar as resoluções de busca como idênticas.")
    fig("05_grid_heatmap", r"RMSE CV em função de taxa de aprendizado e subsample, fixando $N=" +
        str(int(gr["heatmap_fixed_n_estimators"])) + r"$ no ótimo da grade.")
    # This derived quantity is recomputed from the recorded grid slice so text is
    # independent of serialization choices in the plotting script.
    heat = trials["grid"]
    heat = heat[heat.n_estimators == g["best_params"]["n_estimators"]]
    effect_values = []
    for sub, subframe in heat.groupby("subsample"):
        subframe = subframe.sort_values("learning_rate")
        effect_values.append((float(sub), float(subframe.iloc[-1].cv_rmse - subframe.iloc[0].cv_rmse)))
    interaction = (r"A diferença entre esses efeitos evidencia dependência do efeito da taxa em relação "
                   r"ao subsample no corte observado. " if max(e for s, e in effect_values) - min(e for s, e in effect_values) > 1e-8
                   else r"Esses efeitos extremos praticamente iguais não evidenciam interação neste contraste. ")
    report.add(r"Ao aumentar $\eta$ de 0,03 para 0,20, a mudança do RMSE no corte foi " +
               "; ".join("$" + num(e, 4) + r"\,$MPa para $s=" + num(s, 2) + "$" for s, e in effect_values) +
               ". " + interaction + r"A grade esparsa permite descrever regiões melhores "
               r"e piores, mas não demonstrar suavidade global ou contar ótimos locais no domínio contínuo.")

    report.subsection("4. Busca aleatória, convergência e sensibilidade")
    r = results["random"]
    report.add(r"O \texttt{RandomizedSearchCV} sorteou 30 candidatos sem reposição da mesma grade, "
               r"com seed 42 e os mesmos folds. A melhor configuração foi " + params_text(r) +
               r", CV RMSE " + num(r["cv_rmse"]) + r"\,MPa e tempo total " + num(r["total_seconds"], 3) + r"\,s.")
    fig("04_grid_random_convergence", r"Melhor CV RMSE acumulado na ordem registrada dos candidatos em \texttt{cv\_results\_}. O eixo conta avaliações, não segundos nem a ordem de término dos fits paralelos.")
    match = gr["random_first_match_evaluation"]
    match_text = ("igualou o mínimo da grade na avaliação " + str(int(match)) if match is not None
                  else "não alcançou o mínimo da grade em suas 30 avaliações")
    report.add("A busca aleatória " + match_text + r". Não pode superar estritamente o mínimo "
               r"CV de uma grade exaustiva quando usa um subconjunto de seus candidatos, os mesmos "
               r"folds e a mesma seed do estimador. Sua possível vantagem está em alcançar qualidade "
               r"semelhante com menos avaliações. Essa restrição não determina a ordenação no holdout.")
    spearman = gr["spearman"]
    report.table(["Hiperparâmetro", r"$\rho$ de Spearman", "$p$ exploratório", "$n$"],
                 [[esc(x["hyperparameter"]), num(x["rho"]), pv(x["p_exploratory"]), str(x["n"])] for x in spearman],
                 "Associação entre valor do hiperparâmetro e RMSE CV nos 30 candidatos aleatórios.", spec="lrrr")
    strongest = max(spearman, key=lambda x: abs(x["rho"]))
    report.add(r"A maior associação monotônica em módulo foi de \texttt{" + esc(strongest["hyperparameter"]) +
               r"}, com $\rho=" + num(strongest["rho"]) + r"$. Como o score está em RMSE positivo, "
               r"sinal negativo associa valores maiores a erro menor. Spearman é marginal: não "
               r"isola interações, não estabelece causalidade e não garante importância universal. "
               r"Taxa de aprendizado e número de árvores controlam conjuntamente a intensidade do "
               r"boosting; subsample altera a aleatoriedade de ajuste, tornando dependência do contexto plausível.")
    fig("06_random_spearman", "Correlações de Spearman empíricas; barras em módulo não são efeitos causais.")

    report.subsection("5. Síntese do exercício 1")
    table_metrics(report, results, ["baseline", "grid", "random"],
                  "Métodos clássicos: CV/teste em MPa, tempo CV+refit e avaliações efetivas.")
    classical = min(["grid", "random"], key=lambda m: (results[m]["test_rmse"], results[m]["total_seconds"]))
    gain = (b["test_rmse"] - results[classical]["test_rmse"]) / b["test_rmse"]
    classical_tied = math.isclose(results["grid"]["test_rmse"], results["random"]["test_rmse"], abs_tol=1e-10)
    report.add(r"\textbf{A otimização trouxe ganho e compensa o custo?} O melhor teste entre as buscas "
               r"clássicas " + ("empatou entre Grid e Random; o Random teve menor tempo, com " if classical_tied
                                else "foi o de " + name(classical) + ", com ") +
               ("redução" if gain >= 0 else "aumento") + " de " + pct(abs(gain)) +
               r" no RMSE e custo adicional de " + num(results[classical]["total_seconds"] - b["total_seconds"], 3) +
               r"\,s. A decisão econômica depende da "
               r"tolerância de erro e da frequência de retreinamento, não informadas.")
    report.add(r"\textbf{Quando Grid Search é preferível?} Em espaços discretos pequenos, nos quais "
               r"a cobertura completa é viável e uma superfície comparável precisa ser inspecionada. "
               r"Em dimensões maiores, o custo cresce multiplicativamente; busca aleatória distribui "
               r"um orçamento fixo de modo mais flexível\cite{bergstra}.")
    report.add(r"\textbf{O heatmap revela interação?} Os efeitos extremos da taxa, acima quantificados "
               r"para cada subsample, não são assumidos constantes. O corte mantém o número de "
               r"árvores no ótimo; suas conclusões são locais a esse corte e aos níveis avaliados.")

    build_exercise2(report, root, analysis, results, trials, robustness, half, contract, cv_winner, test_winner, fig)
    build_appendix(report, results, contract, env, analysis, fig)
    report.add(BIBLIOGRAPHY)
    output = report.finish(root / "Exercício_Aula5.tex")
    (root / "report-blocks.json").write_text(json.dumps(report.blocks, ensure_ascii=False, indent=2), encoding="utf-8")
    pdf_output = root / "output" / "pdf" / "Exercicio_Aula5.pdf"
    pdf_output.parent.mkdir(parents=True, exist_ok=True)
    render_pdf(report.blocks, pdf_output)
    (root / "latex-build-manifest.json").write_text(json.dumps({"source": output.name,
        "figures": report.figure_paths, "methods": list(results), "best_cv_method": cv_winner,
        "best_test_method": test_winner, "source_data_fingerprint": next(iter(fingerprints)),
        "placeholder_check": "passed", "pdf": pdf_output.relative_to(root).as_posix(),
        "pdf_export": "ReportLab from shared semantic blocks; not compiled from TeX",
        "compilation": "LaTeX source not compiled"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def latex_plain(source, markup=False):
    """Translate the report's deliberately limited TeX vocabulary for ReportLab.

    Math is rendered as readable Unicode/linear notation. Unknown TeX commands
    cause a build failure so equations cannot silently disappear.
    """
    s = str(source)
    s = re.sub(r"\\cellcolor\{[^}]+\}", "", s)
    s = re.sub(r"\\cite\{([^}]+)\}", lambda m: " [" + ", ".join(
        str(CITATION_NUMBERS[k.strip()]) for k in m.group(1).split(",")) + "]", s)
    s = s.replace(r"\hat y", "ŷ").replace(r"\hat{y}", "ŷ").replace(r"\bar\sigma", "σ médio")
    s = s.replace(r"\alpha", "α")
    s = s.replace(r"\bar{x}", "média(x)")
    # Unwrap innermost formatting commands repeatedly, retaining bold/italics.
    for _ in range(20):
        old = s
        s = re.sub(r"\\(textbf|textit|emph|texttt|mathrm|mathbf|text|operatorname|path)\{([^{}]*)\}",
                   lambda m: (("<b>" + m.group(2) + "</b>") if markup and m.group(1) == "textbf" else
                              ("<i>" + m.group(2) + "</i>") if markup and m.group(1) in {"textit", "emph"}
                              else " " + m.group(2) + " "), s)
        s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", lambda m: "(" + m.group(1) + ")/(" + m.group(2) + ")", s)
        s = re.sub(r"\\href\{([^{}]*)\}\{([^{}]*)\}", lambda m: m.group(2) + " (" + m.group(1) + ")", s)
        s = re.sub(r"\\url\{([^{}]*)\}", lambda m: m.group(1), s)
        if old == s:
            break
    mapping = {"eta": "η", "sigma": "σ", "mu": "μ", "xi": "ξ", "phi": "φ", "Phi": "Φ",
               "kappa": "κ", "nu": "ν", "rho": "ρ", "Delta": "Δ", "times": "×", "pm": "±",
               "in": "∈", "ldots": "...", "min": "min", "max": "max", "textemdash": "-",
               "textbackslash": "/", "textasciitilde": "~", "textasciicircum": "^", "left": "",
               "right": "", "noindent": "", "small": "", "ttfamily": "", "par": "",
               "textwidth": "", "textheight": "", "quad": " ", "qquad": "  "}
    s = re.sub(r"\\([A-Za-z]+)", lambda m: mapping.get(m.group(1), "\\" + m.group(1)), s)
    s = s.replace(r"\[", " ").replace(r"\]", " ").replace(r"\!", "")
    s = s.replace(r"\\", "<br/>" if markup else " ").replace(r"\,", " ")
    if markup:
        # Subscripts are math syntax only; preserve underscores in file names,
        # parameter names and URLs outside $...$ delimiters.
        s = re.sub(r"\$([^$]*)\$", lambda m: "$" + re.sub(r"(?<!\\)_([A-Za-z0-9])",
                   r"<sub>\1</sub>", m.group(1)) + "$", s)
    for c in "_%&$#{}":
        s = s.replace("\\" + c, c)
    s = s.replace("$", "").replace("{,}", ",")
    if markup:
        s = re.sub(r"\^\{([^{}]+)\}", r"<super>\1</super>", s)
        s = re.sub(r"_\{([^{}]+)\}", r"<sub>\1</sub>", s)
        s = re.sub(r"\^(\d+)", r"<super>\1</super>", s)
    s = s.replace("{", "").replace("}", "")
    s = s.replace("---", "-").replace("--", "-").replace("—", "-").replace("–", "-")
    unknown = re.findall(r"\\[A-Za-z]+", s)
    if unknown:
        raise ValueError(f"Unsupported TeX in PDF export: {unknown}; source={source}")
    if markup:
        # Escape data but retain only markup created above.
        s = html.escape(s, quote=False)
        for tag in ["b", "/b", "i", "/i", "super", "/super", "sub", "/sub", "br/"]:
            s = s.replace("&lt;" + tag + "&gt;", "<" + tag + ">")
    return s.strip()


CITATION_NUMBERS = {k: i + 1 for i, k in enumerate(re.findall(r"\\bibitem\{([^}]+)\}", BIBLIOGRAPHY))}


def render_pdf(blocks, output):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
                                  PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
    from reportlab.platypus.tableofcontents import TableOfContents
    from PIL import Image as PILImage

    fonts = Path("C:/Windows/Fonts")
    font_files = [("ReportArial", "arial.ttf"), ("ReportArial-Bold", "arialbd.ttf"),
                  ("ReportArial-Italic", "ariali.ttf"), ("ReportArial-BoldItalic", "arialbi.ttf")]
    if not (fonts / "arial.ttf").is_file():
        import matplotlib
        fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        font_files = [("ReportArial", "DejaVuSans.ttf"), ("ReportArial-Bold", "DejaVuSans-Bold.ttf"),
                      ("ReportArial-Italic", "DejaVuSans-Oblique.ttf"),
                      ("ReportArial-BoldItalic", "DejaVuSans-BoldOblique.ttf")]
    for fontname, filename in font_files:
        if fontname not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(fontname, str(fonts / filename)))
    pdfmetrics.registerFontFamily("ReportArial", normal="ReportArial", bold="ReportArial-Bold",
                                  italic="ReportArial-Italic", boldItalic="ReportArial-BoldItalic")
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "ReportArial"
    styles.add(ParagraphStyle("BodyAula", fontName="ReportArial", fontSize=10.6, leading=14.7,
                              spaceAfter=8, alignment=TA_LEFT, splitLongWords=True))
    styles.add(ParagraphStyle("SectionAula", parent=styles["Heading1"], fontName="ReportArial-Bold",
                              fontSize=15, leading=19, spaceBefore=14, spaceAfter=9, keepWithNext=True))
    styles.add(ParagraphStyle("SubsectionAula", parent=styles["Heading2"], fontName="ReportArial-Bold",
                              fontSize=12.1, leading=16, spaceBefore=12, spaceAfter=8, keepWithNext=True))
    styles.add(ParagraphStyle("CaptionAula", fontName="ReportArial", fontSize=9, leading=12,
                              spaceBefore=5, spaceAfter=9, alignment=TA_LEFT))
    styles.add(ParagraphStyle("CellAula", fontName="ReportArial", fontSize=7.8, leading=10.5,
                              spaceAfter=0, splitLongWords=True))
    styles.add(ParagraphStyle("HeadCellAula", parent=styles["CellAula"], fontName="ReportArial-Bold"))
    styles.add(ParagraphStyle("ReferenceAula", parent=styles["BodyAula"], fontSize=9.2, leading=12.4))
    width, height = A4
    margin = 2.5 * cm
    available_width = width - 2 * margin
    available_height = height - 2 * margin

    class AulaDoc(BaseDocTemplate):
        def afterFlowable(self, flowable):
            if isinstance(flowable, Paragraph) and flowable.style.name in {"SectionAula", "SubsectionAula"}:
                level = 0 if flowable.style.name == "SectionAula" else 1
                title = flowable.getPlainText()
                key = f"section-{self.seq.nextf('heading')}"
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(title, key, level=level, closed=True)
                if not title.startswith("Aquisição "):
                    self.notify("TOCEntry", (level, title, self.page, key))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("ReportArial", 8)
        canvas.setFillColor(colors.HexColor("#60666C"))
        canvas.drawString(margin, 1.35 * cm, "UFPR - EELT7025 | Aula 05")
        canvas.drawRightString(width - margin, 1.35 * cm, str(doc.page))
        canvas.restoreState()

    doc = AulaDoc(str(output), pagesize=A4, leftMargin=margin, rightMargin=margin,
                  topMargin=margin, bottomMargin=margin, title="Exercícios da Aula 05 - Otimização de hiperparâmetros",
                  author="Adriely Teixeira de Paula; Betina Zynger Capaverde; Emilio Gaudeda Junior")
    frame = Frame(margin, margin, available_width, available_height, id="body", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id="normal", frames=[frame], onPage=footer))
    story = []
    title_style = ParagraphStyle("TitleAula", fontName="ReportArial-Bold", fontSize=22, leading=29,
                                 alignment=TA_CENTER, spaceAfter=18)
    centered = ParagraphStyle("CenteredAula", parent=styles["BodyAula"], alignment=TA_CENTER,
                               fontSize=12, leading=18, spaceAfter=15)
    story.extend([Spacer(1, 1.3 * cm), Paragraph("Avanços em Inteligência Artificial", title_style),
                  Paragraph("EELT7025 - PPGEE, UFPR", centered), Spacer(1, .5 * cm),
                  Paragraph("Exercícios da Aula 05", centered),
                  Paragraph("Otimização de hiperparâmetros na resistência à compressão do concreto", centered),
                  Spacer(1, 1.4 * cm), Paragraph("Adriely Teixeira de Paula<br/>Betina Zynger Capaverde<br/>Emilio Gaudeda Junior", centered),
                  Spacer(1, 1.2 * cm), Paragraph("30 de setembro de 2026", centered), PageBreak()])
    story.append(Paragraph("Sumário", title_style))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("TOC0", fontName="ReportArial-Bold", fontSize=10, leading=12.5, spaceBefore=5),
                       ParagraphStyle("TOC1", fontName="ReportArial", fontSize=9, leading=11.5, leftIndent=14, spaceBefore=1)]
    story += [toc, PageBreak()]

    def keep_with_heading(flowables):
        # KeepTogether does not automatically propagate a preceding heading's
        # keepWithNext in all ReportLab layouts. Include it explicitly.
        heading_styles = {"SectionAula", "SubsectionAula"}
        while story and isinstance(story[-1], Paragraph) and story[-1].style.name in heading_styles:
            flowables.insert(0, story.pop())
        return KeepTogether(flowables)

    section_index, subsection_index, figure_index, table_index, equation_index = 0, 0, 0, 0, 0
    appendix = False
    for block in blocks:
        kind = block["kind"]
        if kind == "latex":
            text = block["text"]
            if r"\documentclass" in text:
                continue
            if text in {r"\clearpage", r"\newpage"}:
                story.append(PageBreak())
                continue
            if r"\appendix" in text:
                appendix, section_index, subsection_index = True, 0, 0
                story.append(PageBreak())
                continue
            if r"\begin{thebibliography}" in text:
                story.append(PageBreak())
                story.append(Paragraph("Referências", styles["SectionAula"]))
                entries = re.split(r"\\bibitem\{([^}]+)\}", text)[1:]
                for pos in range(0, len(entries), 2):
                    key, entry = entries[pos], entries[pos+1]
                    entry = entry.split(r"\end{thebibliography}")[0].strip()
                    story.append(Paragraph("[" + str(CITATION_NUMBERS[key]) + "] " + latex_plain(entry, markup=True), styles["ReferenceAula"]))
                continue
            section = re.fullmatch(r"\\section\{(.*)\}", text, flags=re.S)
            subsection = re.fullmatch(r"\\subsection\*?\{(.*)\}", text, flags=re.S)
            if section:
                section_index += 1
                subsection_index = 0
                number = chr(64+section_index) if appendix else str(section_index)
                story.append(Paragraph(number + ". " + latex_plain(section.group(1), markup=True), styles["SectionAula"]))
            elif subsection:
                subsection_index += 1
                story.append(Paragraph(latex_plain(subsection.group(1), markup=True), styles["SubsectionAula"]))
            else:
                for piece in re.split(r"(\\\[.*?\\\])", text, flags=re.S):
                    if not piece.strip():
                        continue
                    if piece.startswith(r"\["):
                        os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp" / "matplotlib"))
                        import matplotlib
                        matplotlib.use("Agg")
                        import matplotlib.pyplot as plt
                        equation_index += 1
                        equation_path = ROOT / "tmp" / "pdfs" / f"equation-{equation_index}.png"
                        equation_path.parent.mkdir(parents=True, exist_ok=True)
                        fig_math = plt.figure(figsize=(8, .85))
                        fig_math.text(.5, .5, "$" + piece[2:-2] + "$", ha="center", va="center", fontsize=14)
                        fig_math.savefig(equation_path, dpi=210, bbox_inches="tight", pad_inches=.08)
                        plt.close(fig_math)
                        with PILImage.open(equation_path) as raster:
                            iw, ih = raster.size
                        factor = min(available_width/iw, 65/ih)
                        story.extend([Image(str(equation_path), width=iw*factor, height=ih*factor), Spacer(1, 8)])
                    else:
                        story.append(Paragraph(latex_plain(piece, markup=True), styles["BodyAula"]))
        elif kind == "table":
            table_index += 1
            headers, rows = block["headers"], block["rows"]
            rendered = [[Paragraph(latex_plain(v, markup=True), styles["HeadCellAula"]) for v in headers]]
            rendered += [[Paragraph(latex_plain(v, markup=True), styles["CellAula"]) for v in row] for row in rows]
            ncols = len(headers)
            first_width = min(150, max(82, available_width * (.30 if ncols < 7 else .24)))
            col_widths = [first_width] + [(available_width-first_width)/(ncols-1)]*(ncols-1)
            table = Table(rendered, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
            commands = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0,0),(-1,-1),4),
                        ("RIGHTPADDING", (0,0),(-1,-1),4), ("TOPPADDING",(0,0),(-1,-1),5),
                        ("BOTTOMPADDING",(0,0),(-1,-1),5), ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EDF1F4")),
                        ("LINEABOVE",(0,0),(-1,0),.8,colors.HexColor("#333333")),
                        ("LINEBELOW",(0,0),(-1,0),.5,colors.HexColor("#777777")),
                        ("LINEBELOW",(0,-1),(-1,-1),.8,colors.HexColor("#333333"))]
            for ri, row in enumerate(rows, 1):
                for ci, cell in enumerate(row):
                    if r"\cellcolor{bestgreen}" in str(cell):
                        commands.append(("BACKGROUND", (ci,ri), (ci,ri), colors.HexColor("#D7F0DA")))
                    if r"\cellcolor{timeyellow}" in str(cell):
                        commands.append(("BACKGROUND", (ci,ri), (ci,ri), colors.HexColor("#FFF2B3")))
            table.setStyle(TableStyle(commands))
            caption = Paragraph("Tabela " + str(table_index) + ". " + latex_plain(block["caption"], markup=True), styles["CaptionAula"])
            story.extend([keep_with_heading([caption, table]), Spacer(1, 8)])
        elif kind == "figure":
            figure_index += 1
            with PILImage.open(block["path"]) as raster:
                iw, ih = raster.size
            maxw = available_width * block["width"]
            maxh = available_height * block["height"]
            factor = min(maxw / iw, maxh / ih)
            graphic = Image(block["path"], width=iw*factor, height=ih*factor)
            caption = Paragraph("Figura " + str(figure_index) + ". " + latex_plain(block["caption"], markup=True), styles["CaptionAula"])
            story.extend([keep_with_heading([graphic, caption]), Spacer(1, 6)])
    doc.multiBuild(story)


def build_exercise2(report, root, analysis, results, trials, robustness, half, contract, cv_winner, test_winner, fig):
    report.section("Exercício 2 — otimização Bayesiana, metaheurísticas e avaliação")
    report.subsection("6. Processo Gaussiano e Expected Improvement")
    gp = results["gp_manual"]
    snapshots = analysis["gp_iterations"]
    report.add(r"O loop manual usa $\eta$ em escala logarítmica e subsample, com $N=100$ "
               r"fixado antes da execução. Cinco pontos aleatórios inicializam o GP; dez aquisições "
               r"posteriores totalizam 15 avaliações. O kernel é Matérn $\nu=5/2$ com amplitude "
               r"e componente de ruído ajustáveis\cite{gp}. A aquisição minimiza RMSE por "
               r"Expected Improvement (EI), com $\xi=0{,}01$:")
    report.add(r"\[ I(x)=f_{\min}-\mu(x)-\xi,\qquad"
               r"\mathrm{EI}(x)=I(x)\Phi\!\left(\frac{I(x)}{\sigma(x)}\right)"
               r"+\sigma(x)\phi\!\left(\frac{I(x)}{\sigma(x)}\right).\]")
    report.add(r"O máximo de EI é aproximado numa malha $61\times61$ do domínio normalizado, "
               r"evitando repetir pontos já observados. Isso é uma otimização discreta da aquisição "
               r"no espaço contínuo, não uma garantia de máximo global analítico. A transformação "
               r"de coordenadas é $\eta=0{,}03(0{,}20/0{,}03)^{u_1}$ e $s=0{,}60+0{,}40u_2$.")
    gp_rows = [[str(x["iteration"]), str(x["n_previous"]), num(x["mean_sigma"]),
                num(x["max_ei"]), num(x["previous_best_rmse"]),
                num(x["next_learning_rate"]), num(x["next_subsample"])] for x in snapshots]
    report.table(["Iter.", "Obs. prévias", r"$\bar\sigma$", "EI máxima", "Melhor prévio", r"Próx. $\eta$", "Próx. $s$"],
                 gp_rows, "Dez aquisições: posterior registrado antes da nova avaliação. RMSE e incerteza em MPa.",
                 spec="rrrrrrr")
    first, last = snapshots[0], snapshots[-1]
    increases = sum(snapshots[i]["mean_sigma"] > snapshots[i-1]["mean_sigma"] for i in range(1, len(snapshots)))
    report.add(r"A incerteza média da malha passou de " + num(first["mean_sigma"]) + " para " +
               num(last["mean_sigma"]) + r"\,MPa, com " + str(increases) + r" aumentos entre "
               r"iterações consecutivas. Ela não precisa diminuir monotonicamente, porque os "
               r"hiperparâmetros do kernel são reajustados e novas observações podem revelar "
               r"estrutura inesperada. A EI máxima passou de " + num(first["max_ei"]) + " para " +
               num(last["max_ei"]) + r". O critério busca equilibrar regiões promissoras e incerteza "
               r"segundo o modelo; dez passos não provam convergência ao ótimo verdadeiro.")
    recent = snapshots[-3:]
    report.add(r"Nas três últimas aquisições, a taxa proposta esteve em $[" +
               num(min(x["next_learning_rate"] for x in recent)) + ";" +
               num(max(x["next_learning_rate"] for x in recent)) + r"]$ e o subsample em $[" +
               num(min(x["next_subsample"] for x in recent)) + ";" +
               num(max(x["next_subsample"] for x in recent)) +
               r"]$. Esses candidatos descrevem onde a EI concentrou a exploração final; "
               r"a localização ótima real permanece desconhecida.")
    report.add(r"O melhor GP manual obteve CV RMSE " + num(gp["cv_rmse"]) + r"\,MPa e teste " +
               num(gp["test_rmse"]) + r"\,MPa em " + params_text(gp) +
               r". Comparado às 36 avaliações da grade e 30 da busca aleatória, usou 15; "
               r"a diferença de qualidade está na tabela e figura seguintes. A economia de avaliações "
               r"não é comparação isolada de eficiência do algoritmo: o GP explora apenas dois "
               r"hiperparâmetros, enquanto os demais exploram três.")
    table_metrics(report, results, ["grid", "random", "gp_manual"], "Comparação do GP manual com as buscas clássicas.")
    fig("07_gp_comparison", "Convergência do GP manual e comparação com Grid/Random; o GP mantém 100 árvores.")
    report.add(r"As dez figuras individuais estão no apêndice de aquisições. Cada uma exibe "
               r"posterior, observações e EI com o candidato escolhido. O corte $\mu\pm2\sigma$ "
               r"mantém o subsample do próximo candidato; as observações reais aparecem no mapa "
               r"bidimensional, sem projetar pontos de outros subsamples sobre essa curva. A banda caracteriza incerteza "
               r"do surrogate, não intervalo de previsão da resistência do concreto.")

    report.subsection("7. Cinco bibliotecas de otimização Bayesiana")
    libraries = ["bayessearch", "bayesopt", "optuna", "hyperopt", "ray"]
    report.table(["Biblioteca", "Configuração executada", "Trials iniciados"], [
        ["scikit-optimize", "GP Matérn 5/2; EI; 10 iniciais", str(results["bayessearch"]["n_evaluations"])],
        [r"bayes\_opt", r"GP; UCB $\kappa=2{,}576$; 5 iniciais + 35", str(results["bayesopt"]["n_evaluations"])],
        ["Optuna", "TPE; minimizar RMSE; seed 42", str(results["optuna"]["n_evaluations"])],
        ["Hyperopt", r"TPE; \texttt{hp.loguniform} para $\eta$", str(results["hyperopt"]["n_evaluations"])],
        ["Ray Tune", "OptunaSearch + ASHA; recurso progressivo", str(results["ray"]["n_evaluations"])],
    ], "Bibliotecas aplicadas aos três hiperparâmetros do espaço completo.", spec="llr")
    report.add(r"Foram usados GP e aquisição explicitamente configurados no skopt\cite{skopt} "
               r"e no bayes\_opt\cite{bayesopt}; TPE orientou Optuna\cite{optuna} e "
               r"Hyperopt\cite{hyperopt}. Cada biblioteca iniciou 40 candidatos. Os métodos contínuos "
               r"compartilham os limites da grade; valores intermediários são admissíveis, e a taxa "
               r"é amostrada em escala logarítmica. O inteiro $N$ usa a mesma regra de conversão na "
               r"avaliação e no ajuste final, evitando comparar um candidato com um refit diferente.")
    ray = results["ray"]
    stages = pd.read_csv(root / "results" / "ray" / "seed_42" / "ray-stages.csv")
    report.add(r"\textbf{ASHA efetivo.} O recurso é a fração do número de árvores proposto, "
               r"com estágios $0{,}25;0{,}50;0{,}75;1{,}00$, warm start e RMSE nos cinco folds "
               r"a cada estágio. O scheduler tem grace period 0,25 e fator de redução 2; apenas "
               r"candidatos com recurso completo podem vencer\cite{ray}. Houve " +
               str(ray["full_resource_evaluations"]) + r" avaliações completas e " + str(ray["pruned_trials"]) +
               r" podas, com " + str(len(stages)) + r" relatórios intermediários e " + str(ray["cv_fits"]) +
               r" chamadas de fit por fold/estágio. Ao todo foram construídas " + str(ray["trained_trees_cv"]) +
               r" árvores nos folds, descontando árvores reaproveitadas pelo warm start. Candidatos "
               r"parciais não equivalem a candidatos completos; seus scores não definem o vencedor.")
    report.add(r"O tempo de busca do Ray inclui a inicialização do serviço, ao passo que o pool "
               r"loky foi aquecido fora do cronômetro. A comparação de custo reflete essa convenção "
               r"operacional declarada; não é um benchmark puro de tempo de treinamento nem prevê "
               r"o custo de uma sessão persistente já inicializada.")
    table_metrics(report, results, libraries, "Cinco bibliotecas: melhor CV completo e métricas do refit no teste.")
    fig("08_bayesian_convergence", "Convergência das cinco bibliotecas. Para ASHA, interpretar separadamente trabalho parcial e candidato completo.")
    lib_best = min(libraries, key=lambda m: results[m]["cv_rmse"])
    lib_fast = min(libraries, key=lambda m: results[m]["total_seconds"])
    report.add("Entre as bibliotecas, " + name(lib_best) + r" retornou o menor CV RMSE (" +
               num(results[lib_best]["cv_rmse"]) + r"\,MPa), enquanto " + name(lib_fast) +
               r" teve o menor tempo total (" + num(results[lib_fast]["total_seconds"], 3) +
               r"\,s). O melhor CV depende da trajetória adaptativa e do orçamento de 40 trials; "
               r"esta comparação não demonstra que a mesma ordenação se repetiria em outro dataset.")

    report.subsection("8. Metaheurísticas: GA, DE e PSO")
    report.add(r"\textbf{8.1. Algoritmo genético.} DEAP\cite{deap}, população 20, 15 gerações, "
               r"crossover de dois pontos com probabilidade 0,7, mutação uniforme inteira com "
               r"probabilidade 0,25 e probabilidade por gene $1/3$, seleção por torneio de tamanho 3. "
               r"Os genes são $g_1,g_2\in\{0,\ldots,1000\}$ e $g_3\in\{50,\ldots,200\}$; "
               r"a decodificação usa $u_1=g_1/1000$, $u_2=g_2/1000$, $N=g_3$. "
               r"O melhor indivíduo é preservado em Hall of Fame. Fitness herdados válidos não "
               r"são recalculados; a contagem corresponde às chamadas efetivamente realizadas.")
    generations = pd.read_csv(root / "results" / "ga" / "seed_42" / "generations.csv")
    ga = results["ga"]
    ga_summary = analysis["ga_summary"]
    report.add("O GA realizou " + str(ga["n_evaluations"]) + r" avaliações e " + str(ga["unique_candidates"]) +
               r" candidatos distintos. A diversidade, fração de genótipos distintos na população, "
               r"passou de " + pct(generations.iloc[0].diversity) + " para " + pct(generations.iloc[-1].diversity) +
               r". O maior intervalo sem melhoria acumulada durou " +
               str(ga_summary["longest_stagnation_generations"]) + r" gerações, da " +
               str(ga_summary["longest_stagnation_from_generation"]) + " à " +
               str(ga_summary["longest_stagnation_through_generation"]) +
               r"; o ganho na última geração foi de apenas " +
               num(ga_summary["final_generation_improvement_mpa"], 6) + r"\,MPa. "
               r"A contração da diversidade junto à estagnação sugere risco de convergência prematura, "
               r"mas não prova um ótimo local nem quantifica a distância ao ótimo global desconhecido.")
    fig("09_ga_generations", "GA: fitness mínimo, médio e melhor acumulado, acompanhados da diversidade por geração.")
    report.add(r"\textbf{8.2. Evolução diferencial.} Foram executadas as estratégias "
               r"\texttt{best1bin} e \texttt{rand1bin}, com \texttt{maxiter=15}, "
               r"\texttt{popsize=10}, mutação em $[0{,}5;1{,}0]$ e recombinação 0,7\cite{de}. "
               r"O popsize multiplica a dimensão: são 30 indivíduos, não dez. A busca usa coordenadas "
               r"normalizadas, sem polish, atualização imediata e tolerância padrão 0,01. "
               r"O critério de dispersão pode encerrar antes de 15 gerações.")
    de_rows = []
    for m in ["de_best1bin", "de_rand1bin"]:
        detail = read_json(root / "results" / m / "seed_42" / "de-result.json")
        de_rows.append([name(m), str(detail["nit"]), str(detail["nfev"]), num(results[m]["cv_rmse"]),
                        num(results[m]["total_seconds"], 3)])
    report.table(["Estratégia", "Gerações", "Avaliações", "CV RMSE", "Tempo (s)"], de_rows,
                 "Término efetivo da evolução diferencial.", spec="lrrrr")
    fig("10_de_convergence", "DE: melhor RMSE CV acumulado em best1bin e rand1bin.")
    de_best = min(["de_best1bin", "de_rand1bin"], key=lambda m: results[m]["cv_rmse"])
    report.add("Nesta execução, " + name(de_best) + r" atingiu o menor CV RMSE: " +
               num(results[de_best]["cv_rmse"]) + r"\,MPa. A estratégia best1bin usa o melhor vetor "
               r"como base e tende a intensificar busca local; rand1bin usa uma base aleatória. "
               r"A curva mostra o efeito realizado aqui; uma seed não permite transformar essa "
               r"diferença em superioridade geral de uma estratégia.")
    de_profiles = []
    for method in ["de_best1bin", "de_rand1bin"]:
        history = np.minimum.accumulate(trials[method].cv_rmse.to_numpy())
        last_improvement = int(np.flatnonzero(np.r_[True, np.diff(history) < -1e-10])[-1] + 1)
        de_profiles.append(name(method) + ": " + num(history[min(99, len(history)-1)]) +
                           r"\,MPa após 100 avaliações, último ganho na avaliação " + str(last_improvement))
    report.add(r"O perfil observado foi: " + "; ".join(de_profiles) +
               r". O patamar final de cada curva deve ser interpretado junto à tolerância de parada, "
               r"não como comprovação de convergência ao ótimo global.")
    report.add(r"\textbf{8.3. Enxame de partículas.} Implementação explícita das atualizações "
               r"de velocidade e posição\cite{pso}, com 20 partículas, 15 atualizações, "
               r"$c_1=c_2=1{,}5$ e inércias $w\in\{0{,}4;0{,}7;0{,}9\}$. A inicialização "
               r"também é avaliada: $20(15+1)=320$ chamadas por variante. A posição fica em "
               r"$[0,1]^3$; ao atingir uma borda, a coordenada é truncada e sua velocidade zerada. "
               r"O gráfico usa média do fitness corrente do enxame, não média dos melhores pessoais.")
    pso_methods = ["pso_w04", "pso_w07", "pso_w09"]
    table_metrics(report, results, pso_methods, "Sensibilidade do PSO à inércia, com os demais parâmetros e orçamento iguais.")
    fig("11_pso_inertia", "PSO: trajetória de gbest e média do enxame corrente para as três inércias.")
    pso_best = min(pso_methods, key=lambda m: results[m]["cv_rmse"])
    report.add("A menor validação entre as três inércias foi de " + name(pso_best) + ", " +
               num(results[pso_best]["cv_rmse"]) + r"\,MPa. Inércia maior mantém mais da velocidade "
               r"anterior; menor inércia reduz esse impulso. As curvas registram o compromisso "
               r"observado entre exploração e estabilização, sem assumir monotonicidade do fitness médio.")
    pso_profiles = []
    for method in pso_methods:
        history = pd.read_csv(root / "results" / method / "seed_42" / "generations.csv").set_index("generation")
        pso_profiles.append(name(method) + ": " + num(history.loc[5, "best"]) + ", " +
                            num(history.loc[10, "best"]) + " e " + num(history.loc[15, "best"]))
    report.add(r"A evolução do gbest nas iterações 5, 10 e 15 foi, em MPa: " +
               "; ".join(pso_profiles) + r". Essa comparação quantifica a velocidade e os patamares "
               r"nesta seed; uma configuração de inércia não é universalmente preferível.")

    report.subsection("9. Dashboard comparativo e diagnósticos finais")
    table_metrics(report, results, list(METHODS),
                  "Comparação completa e variantes: verde marca melhores métricas e amarelo o menor tempo total; erros em MPa.", color=True)
    report.add(r"A tabela contém os 12 métodos principais e as três variantes adicionais de "
               r"DE/PSO. A coluna Aval. conta candidatos registrados; em Ray inclui podas, "
               r"cujo trabalho parcial é discriminado anteriormente e no apêndice. Os orçamentos "
               r"diferentes são exigidos pelo roteiro. Vantagens em qualidade com muitas avaliações "
               r"não devem ser atribuídas somente ao otimizador.")
    fig("13_radar", "Radar dos 12 métodos principais: maior é melhor em todos os eixos; os limites são os do conjunto exibido.")
    radar_best = min(MAIN, key=lambda m: results[m]["test_rmse"])
    radar_fast = min(MAIN, key=lambda m: results[m]["total_seconds"])
    report.add(r"Nos erros, o radar inverte a normalização min--max; em $R^2$ e $1/t$, "
               r"preserva a orientação crescente. A área de um polígono depende da escala e não "
               r"é uma métrica agregada validada. Para o mesmo alvo de teste, $R^2$ e RMSE "
               r"induzem a mesma ordenação e não são eixos independentes de qualidade. "
               r"Entre os 12 métodos principais exibidos, " + name(radar_best) + r" tem o menor RMSE de teste (" +
               num(results[radar_best]["test_rmse"]) + r"\,MPa); " + name(radar_fast) + r" tem o menor tempo total. "
               r"Os demais eixos e os compromissos de qualidade são avaliados na tabela, sem impor "
               r"um peso econômico arbitrário a cada dimensão.")
    fig("14_pareto", "Qualidade versus custo: ambas as coordenadas são minimizadas; a fronteira identifica os métodos não dominados.")
    pareto = analysis["pareto_methods"]
    report.add("A fronteira de Pareto observada contém " + ", ".join(name(m) for m in pareto) +
               r". Um método é dominado quando outro tem RMSE e tempo não maiores, com ao menos "
               r"uma melhora estrita. Empates são preservados. A fronteira pode mudar com hardware, "
               r"seed, orçamento ou outro conjunto de teste.")
    best = results[test_winner]
    report.add(r"\textbf{9.4. Melhor resultado descritivo no teste:} " + name(test_winner) +
               ", em " + params_text(best) + r". As previsões do mesmo refit alimentam RMSE, "
               r"MAE, $R^2$, resíduos e importância; não houve ajuste de hiperparâmetros a partir desses diagnósticos.")
    fig("15_best_predictions_residuals", r"Vencedor descritivo no holdout: observado versus previsto e distribuição dos resíduos $y-\hat y$.")
    pred = pd.read_csv(root / "results" / test_winner / "seed_42" / "predictions.csv")
    report.add(r"Em " + str(len(pred)) + r" resíduos, a média foi " + num(pred.residual.mean()) +
               r"\,MPa e o desvio padrão amostral " + num(pred.residual.std(ddof=1)) +
               r"\,MPa. Shapiro--Wilk: $W=" + num(best["shapiro_statistic"]) + r"$, $p=$" +
               pv(best["shapiro_pvalue"]) + ". " +
               (r"Rejeita-se a hipótese de normalidade ao nível exploratório de 5\%. " if best["shapiro_pvalue"] < .05
                else r"Não se rejeita normalidade ao nível exploratório de 5\%; isso não a comprova. ") +
               r"O diagnóstico se refere aos resíduos, não à distribuição marginal do alvo; "
               r"não normalidade não invalida automaticamente o GBR ou as métricas de erro.")
    fig("16_feature_importance", "Importância das features do GBR final por redução acumulada de impureza.")
    importance = pd.read_csv(root / "results" / test_winner / "seed_42" / "feature_importance.csv").sort_values("importance", ascending=False)
    top = importance.head(3)
    report.add("Os três maiores valores foram " + "; ".join(feature_name(x.feature) + " (" +
               pct(x.importance) + ")" for x in top.itertuples()) + r". Essa importância descreve "
               r"o modelo ajustado, pode se distribuir entre variáveis correlacionadas e não mede "
               r"efeito causal de um ingrediente sobre a resistência.")

    report.subsection("10. Importância, robustez, custo-benefício e recomendação")
    full_imp = pd.read_csv(root / "results" / "optuna" / "seed_42" / "optuna_importances.csv").set_index("hyperparameter").importance
    half_imp = pd.read_csv(root / "results" / "sample50" / "optuna" / "seed_42" / "optuna_importances.csv").set_index("hyperparameter").importance
    report.add(r"\textbf{10.1. Importância dos hiperparâmetros.} Foi utilizado "
               r"\texttt{get\_param\_importances} do Optuna com avaliador fANOVA e seed 42\cite{optuna}. "
               r"O HPO principal usa todas as " + str(results["optuna"]["train_rows"]) +
               r" linhas de treino; outra busca de 40 trials usa uma subamostra aleatória de " +
               str(half["train_rows"]) + r" linhas, preservando o holdout. Não se inclui o teste "
               r"no que se chama treino integral. Os folds da subamostra seguem a mesma regra, "
               r"mas suas observações diferem; a comparação é uma sensibilidade ao tamanho do treino.")
    report.table(["Hiperparâmetro", "Treino integral", "Metade do treino"],
                 [[esc(k), pct(full_imp[k]), pct(half_imp[k])] for k in full_imp.index],
                 "Importâncias normalizadas fANOVA após 40 trials Optuna em cada tamanho.", spec="lrr")
    fig("18_optuna_importances", r"Comparação da importância dos hiperparâmetros com treino integral e subamostra de 50\%.")
    full_top, half_top = full_imp.idxmax(), half_imp.idxmax()
    report.add(r"O principal hiperparâmetro no treino integral foi \texttt{" + esc(full_top) +
               r"} e na subamostra foi \texttt{" + esc(half_top) + r"}. O RMSE de teste do Optuna "
               r"passou de " + num(half["test_rmse"]) + r"\,MPa na subamostra para " +
               num(results["optuna"]["test_rmse"]) + r"\,MPa no treino integral. Essas importâncias "
               r"dependem do espaço, dos trials observados e do avaliador; não são uma propriedade "
               r"fixa do dataset nem são diretamente equivalentes às correlações marginais de Spearman.")
    report.add(r"\textbf{10.2. Robustez do procedimento.} Os vencedores por CV e por teste foram "
               r"submetidos ao procedimento completo de busca nas seeds $\{0,7,21,42,99\}$, "
               r"mantendo dados, holdout e folds. Variaram as seeds do otimizador e do GBR. "
               r"A execução principal de seed 42 foi reutilizada. Se os vencedores coincidem, "
               r"há apenas uma série de cinco repetições, sem duplicação de custo.")
    rob_rows = [[name(x.method), str(int(x.seed)), num(x.cv_rmse), num(x.test_rmse), num(x.total_seconds, 3)]
                for x in robustness.sort_values(["method", "seed"]).itertuples()]
    report.table(["Método", "Seed", "CV RMSE", "Teste RMSE", "Tempo (s)"], rob_rows,
                 "Reexecuções completas do HPO com dados e partições fixos.", spec="lrrrr")
    fig("17_robustness", "RMSE de teste do vencedor descritivo nas cinco seeds; não é intervalo de confiança de generalização.")
    for method, values in robustness.groupby("method"):
        scores = values.test_rmse
        report.add(name(method) + ": RMSE de teste médio $" + num(scores.mean()) + r"\pm" +
                   num(scores.std(ddof=1)) + r"$ MPa (desvio padrão amostral, $n=5$), intervalo observado "
                   r"$[" + num(scores.min()) + ";" + num(scores.max()) + r"]$ MPa. A variação relativa "
                   r"$\mathrm{DP}/\mathrm{média}$ foi " + pct(scores.std(ddof=1)/scores.mean()) +
                   r". São cinco aleatoriedades de um mesmo dataset; a dispersão não quantifica "
                   r"incerteza entre populações, lotes ou outros conjuntos de teste.")
    relative_spreads = robustness.groupby("method").test_rmse.agg(["mean", "std"])
    max_spread = (relative_spreads["std"] / relative_spreads["mean"]).max()
    report.add(r"A maior dispersão relativa foi " + pct(max_spread) +
               r" do RMSE médio. Isso indica estabilidade relativa às cinco seeds estudadas no "
               r"holdout fixo, com a faixa de variação acima explicitada; não assegura estabilidade "
               r"em produção nem sustenta interpretar diferenças de centésimos de MPa como decisivas.")
    report.add(r"\textbf{10.3. Custo-benefício computacional.} Para erro menor ser melhor, "
               r"a razão exigida é\[E_m=\frac{(\mathrm{RMSE}_0-\mathrm{RMSE}_m)/\mathrm{RMSE}_0}"
               r"{t_m-t_0}.\]Ela usa segundos adicionais de busca/CV+refit. O baseline é indefinido; "
               r"denominadores não positivos também não recebem uma divisão artificial por epsilon.")
    efficiency_rows, efficiencies = [], {}
    b = results["baseline"]
    for method in METHODS:
        result = results[method]
        improvement = (b["test_rmse"] - result["test_rmse"]) / b["test_rmse"]
        delta = result["total_seconds"] - b["total_seconds"]
        ratio = improvement / delta if method != "baseline" and delta > 0 else None
        if ratio is not None:
            efficiencies[method] = ratio
        efficiency_rows.append([name(method), pct(improvement), num(delta, 3), num(ratio, 7)])
    report.table(["Método", "Ganho relativo", r"$\Delta t$ (s)", r"$E_m$ (s$^{-1}$)"], efficiency_rows,
                 "Eficiência relativa ao baseline; traço significa razão não definida.", spec="lrrr")
    efficiency_best = max(efficiencies, key=efficiencies.get)
    report.add("A maior razão definida foi a de " + name(efficiency_best) + r", $E=" +
               num(efficiencies[efficiency_best], 7) + r"\,$s$^{-1}$. Essa razão responde ao ganho "
               r"marginal por tempo adicional nesta máquina; pode favorecer ganhos pequenos e "
               r"baratos, e não inclui inferência, manutenção ou valor econômico do erro.")
    report.add(r"\textbf{10.4. Recomendação justificada (até dez linhas).}")
    chosen = results["optuna"]
    report.add(r"Adotaria Optuna TPE como opção operacional: CV de " + num(chosen["cv_rmse"]) +
               r"\,MPa, teste de " + num(chosen["test_rmse"]) + r"\,MPa e " + num(chosen["total_seconds"], 3) +
               r"\,s em " + str(chosen["n_evaluations"]) + r" avaliações. A API padronizada facilita "
               r"integração ao pipeline e reprodução com seeds, versões e logs. Este é um julgamento "
               r"pós-resultados de custo e qualidade: a seleção por CV permanece " + name(cv_winner) +
               r", e o vencedor descritivo do teste é " + name(test_winner) +
               r". Antes de produção, validaria em novos lotes e confrontaria o erro com a tolerância de engenharia.")


def build_appendix(report, results, contract, env, analysis, fig):
    report.add(r"\clearpage\appendix")
    report.section("Parâmetros selecionados e contabilidade computacional")
    parameter_rows = []
    for method in METHODS:
        p = results[method]["best_params"]
        parameter_rows.append([name(method), num(p["learning_rate"], 6), num(p["subsample"], 6), str(p["n_estimators"])])
    report.table(["Método", r"learning\_rate", "subsample", r"n\_estimators"], parameter_rows,
                 "Melhores parâmetros por CV; baseline registra seus defaults.", spec="lrrr")
    report.table(["Método", "Busca/CV (s)", "Refit (s)", "Aval.", "Únicos", "Fits CV", "Completos", "Podados"],
        [[name(m), num(r["search_seconds"], 3), num(r["refit_seconds"], 4), str(r["n_evaluations"]),
          str(r["unique_candidates"]), str(r["cv_fits"]), str(r["full_resource_evaluations"]), str(r["pruned_trials"])]
         for m, r in results.items()],
        "Chamadas efetivas e tempos. No Ray, fit CV é uma chamada por fold/estágio, com warm start; não equivale a treinamento completo do zero.",
        spec="lrrrrrrr")
    report.add(r"O baseline usa perda quadrática, profundidade máxima 3 e demais parâmetros "
               r"padrão da versão registrada. Fora das três dimensões acima, os métodos preservam "
               r"esses parâmetros. Contagens distintas de candidatos e candidatos únicos mostram "
               r"revisitas; não foi aplicado cache de scores entre otimizadores para artificialmente "
               r"reduzir seu custo. O custo das sensibilidades é adicional à tabela principal.")
    report.section("Ambiente e evidências de reprodução")
    report.add(r"\textbf{Formato desta entrega.} O PDF foi exportado com ReportLab a partir dos mesmos "
               r"blocos de conteúdo usados para gerar a fonte LaTeX. O arquivo \texttt{.tex} e as figuras "
               r"acompanham a entrega; a compilação LaTeX não foi verificada neste ambiente. "
               r"A exportação PDF não constitui evidência de compilação do projeto TeX.")
    report.add("Python: " + esc(env["python"].splitlines()[0]) + r". Plataforma: " + esc(env["platform"]) +
               r". Processador: " + esc(env["processor"] or "identificador não disponibilizado pelo sistema") +
               r". CPUs lógicas detectadas: " + str(env["logical_cpus"]) + ".")
    report.table(["Biblioteca", "Versão instalada"], [[esc(k), esc(v)] for k, v in env["packages"].items()],
                 "Versões registradas na execução, distintas das versões futuras de documentação online.", spec="ll")
    report.add(r"São fornecidos notebook executado, código de experimentos, dados e contrato, "
               r"manifesto de split/folds, resultados por trial, previsões, figuras e fontes do relatório. "
               r"Os arquivos \texttt{result.json}, \texttt{trials.csv}, \texttt{predictions.csv} "
               r"e \texttt{analysis.json} conectam números e figuras à mesma execução. "
               r"Reexecutar o HPO pode alterar tempos; seeds controlam aleatoriedade, mas não "
               r"garantem igualdade bit a bit entre bibliotecas, versões e plataformas.")
    code_versions = {}
    for method, result in results.items():
        code_versions.setdefault(result["code_sha256"], []).append(method)
    report.add(r"Os registros por método guardam o SHA-256 integral do script executado. "
               r"Foram encontrados " + str(len(code_versions)) + r" hashes de código na comparação "
               r"principal. Um hash identifica o arquivo inteiro; uma diferença não implica "
               r"automaticamente mudança no algoritmo, mas deve ser confrontada ao histórico de alterações.")
    for sha, methods in code_versions.items():
        report.add(r"\noindent\textbf{" + ", ".join(name(m) for m in methods) + r"}:\\"
                   r"{\small\ttfamily\path{" + sha + r"}}\par")
    for filename, sha in contract["sha256"].items():
        report.add(r"\noindent\textbf{" + esc(filename) + r"}, SHA-256:\\"
                   r"{\small\ttfamily\path{" + sha + r"}}\par")
    report.add(r"A integridade estrutural foi conferida por índices de treino/teste disjuntos, "
               r"contagem de candidatos e recálculo de métricas a partir das previsões. Isso "
               r"não substitui validação científica independente. O compromisso metodológico "
               r"mais relevante é manter as limitações visíveis: um único dataset, budgets "
               r"diferentes, busca contínua versus grade discreta e seleção descritiva pelo teste.")
    report.add(r"\clearpage")
    report.section("Dez iterações do GP manual")
    for item in analysis["gp_iterations"]:
        i = int(item["iteration"])
        if i > 1:
            report.add(r"\clearpage")
        report.subsection("Aquisição " + str(i), toc=False)
        fig(f"gp_iteration_{i:02d}", "Posterior e EI antes da aquisição " + str(i) +
            r", com " + str(item["n_previous"]) + r" observações. Candidato: $\eta=" +
            num(item["next_learning_rate"]) + r"$, $s=" + num(item["next_subsample"]) +
            r"$. As observações reais são exibidas no mapa 2D; o corte mantém o subsample fixo e não projeta pontos de outras seções.", height="0.74")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(build(args.root))
