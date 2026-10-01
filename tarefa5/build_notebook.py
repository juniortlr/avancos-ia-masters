"""Build and execute the review notebook against real saved experiment outputs.

Usage: python build_notebook.py [--no-execute]
The HPO is not silently rerun: the notebook executes reconstruction/analysis cells.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import nbformat as nbf
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parent


def build():
    nb=nbf.v4.new_notebook()
    nb.metadata.update({'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                        'language_info':{'name':'python','version':sys.version.split()[0]}})
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s,**metadata):cells.append(nbf.v4.new_code_cell(s,metadata=metadata))
    def figure(stem):code(f"show_figure({stem!r})")
    def text(key):code(f"display(Markdown(analysis['narrative'][{key!r}]))")

    md('# Tarefa 5 — Otimização de hiperparâmetros\n\n'
       '**Avanços em IA — EELT7025, PPGEE/UFPR**\n\n'
       '**Integrantes:** Adriely Teixeira de Paula; Betina Zynger Capaverde; Emilio Gaudeda Junior.\n\n'
       '**Dataset:** Concrete Compressive Strength (UCI 165). **Modelo:** GradientBoostingRegressor. '
       '**Alvo:** resistência à compressão, em MPa.\n\n'
       'Este notebook contém resultados reais dos experimentos, suas análises e o código completo empregado. '
       'As células de reconstrução foram executadas a partir dos registros salvos. O HPO foi executado pelo engine '
       'em processos separados; não é executado uma segunda vez para gerar esta entrega. '
       'A execução e as limitações são auditáveis nos CSVs, JSONs e logs anexos.\n\n'
       'O protocolo e o orçamento foram fixados antes de observar os resultados, seguindo o framework '
       '[rnd-superpowers, commit f68892c8](https://github.com/juniortlr/rnd-superpowers/commit/f68892c8b7adba358b8aa437eec00a89fe88d340). '
       'Não foram encontrados comentários do professor nos trabalhos anteriores; as correções de metodologia '
       'adotadas decorrem da nossa revisão técnica, sem atribuí-las a feedback docente.')
    md('## Como reproduzir\n\n'
       'Para visualizar, basta abrir este notebook: as tabelas e imagens estão incorporadas nas saídas. '
       'Para executar a análise sem refazer o HPO, extraia o pacote completo na mesma pasta e instale '
       'as dependências de `requirements-lock.txt` (Python compatível com o ambiente registrado). '
       'Execute as células em ordem.\n\n'
       'Para repetir **todos os experimentos**, altere `RUN_EXPERIMENTS=True` abaixo. Os fontes completos '
       'estão incorporados nas células `%%writefile`; se o pacote não estiver presente, podem reconstruir os scripts '
       'em uma pasta vazia. A obtenção inicial de dados exige internet. '
       'Os budgets incluem milhares de fits; a reconstrução de gráficos é muito mais rápida. '
       'Tempos dependem do hardware e da carga do sistema. As execuções anteriores são preservadas pelo engine.')
    code("""from pathlib import Path
import os, sys, json, subprocess
import numpy as np
import pandas as pd
from IPython.display import display, Markdown, Image, HTML

# Caminhos relativos: nenhuma referência à máquina do autor.
ROOT = Path.cwd()
if (ROOT / 'tarefa5' / 'experiment.py').exists():
    ROOT = ROOT / 'tarefa5'
os.chdir(ROOT)
RUN_EXPERIMENTS = False
CV_JOBS = 5
print('Pasta dos artefatos:', ROOT)
print('Python:', sys.version.split()[0])""")
    md('### Código executável incorporado\n\n'
       'As duas células seguintes escrevem exatamente os fontes usados nesta versão. '
       'O experimento mantém o teste fora da seleção de hiperparâmetros; os gráficos só leem resultados existentes. '
       'A saída de escrita não constitui execução do HPO. Consulte as funções dos métodos para verificar cada configuração.')
    # Full runnable sources, not just links to a machine-local file.
    for filename in ['experiment.py','plot_results.py']:
        code('%%writefile '+filename+'\n'+(ROOT/filename).read_text(encoding='utf-8'),jupyter={'source_hidden':True})
    code("""# Preserve the canonical LF bytes on Windows as well as Linux/macOS.
# %%writefile uses the host's native newline; normalize before any verification.
for script_name in ['experiment.py', 'plot_results.py']:
    p = ROOT / script_name
    p.write_bytes(p.read_bytes().replace(b'\\r\\n', b'\\n'))
print('Fontes incorporados gravados em UTF-8, com finais de linha LF.')""")
    code("""if RUN_EXPERIMENTS:
    commands = [
        ['prepare'], ['run', '--method', 'all', '--jobs', str(CV_JOBS)],
        ['sample', '--jobs', str(CV_JOBS)],
        ['robustness', '--jobs', str(CV_JOBS), '--resume'], ['verify']
    ]
    for command in commands:
        subprocess.run([sys.executable, 'experiment.py', *command], check=True)
else:
    print('HPO não repetido: reconstruindo e verificando os resultados reais salvos.')
if not (ROOT / 'results' / 'metrics.csv').exists():
    raise FileNotFoundError('Extraia o pacote completo ou altere RUN_EXPERIMENTS=True para gerar resultados.')
subprocess.run([sys.executable, 'experiment.py', 'verify'], check=True)
subprocess.run([sys.executable, 'plot_results.py'], check=True)
analysis = json.loads((ROOT / 'results' / 'analysis.json').read_text(encoding='utf-8'))
metrics = pd.read_csv(ROOT / 'results' / 'metrics.csv')
contract = json.loads((ROOT / 'data' / 'data-contract.json').read_text(encoding='utf-8'))
def show_figure(stem):
    p = ROOT / 'figures' / (stem + '.png')
    if not p.exists(): raise FileNotFoundError(p)
    display(Image(filename=str(p)))
def show_csv(relative, **kwargs):
    display(pd.read_csv(ROOT / relative, **kwargs))
def method_result(method):
    return json.loads((ROOT / 'results' / method / 'seed_42' / 'result.json').read_text(encoding='utf-8'))
print('Métodos principais e variantes presentes:', len(metrics))""")
    md('## Contrato experimental e prevenção de erros\n\n'
       'Split 80/20 com seed 42 após a remoção determinística de duplicatas exatas. '
       '`KFold(5, shuffle=True, random_state=42)` no treino, idêntico entre buscas. '
       'Mediana e StandardScaler ajustados **dentro** do pipeline e de cada fold; y mantém MPa. '
       'O scaler é exigido pela atividade, embora árvores não dependam dele. '
       'Não ajustamos transformadores antes do split.\n\n'
       'O espaço completo tem learning_rate ∈ [0,03; 0,20], subsample ∈ [0,60; 1,00] e '
       'n_estimators ∈ {50,…,200}. Grid/Random usam a mesma grade de 36 pontos; '
       'métodos contínuos compartilham os limites e não o conjunto exato de candidatos. '
       'GP manual usa dois contínuos e fixa n_estimators=100. '
       'Não alteramos silenciosamente espaços, seeds, folds ou critérios de refit.\n\n'
       'O tempo comparativo inclui busca CV e refit; o baseline também inclui seu CV. '
       'Seu tempo de treinamento puro é reportado separadamente. '
       'O número de avaliações é medido: fitness reutilizado no GA não é um novo fit, '
       'podas ASHA não equivalem a uma validação integral, e DE pode terminar antes de maxiter.')
    code("display(pd.Series(contract, name='Contrato dos dados').to_frame())")
    text('feature_overlap')
    code("display(pd.DataFrame(analysis['feature_overlap']['rows']))")
    md('## Exercício 1\n\n### 1. Carregamento, qualidade e EDA')
    code("show_csv('data/quality-summary.csv')\nshow_csv('data/describe_raw.csv')")
    code("print('Shape original:', contract['raw_shape'])\nprint('Shape após limpeza:', contract['clean_shape'])\nprint('Duplicatas exatas removidas:', contract['exact_duplicate_rows_removed'])\nprint('Treino/teste:', contract['train_rows'], contract['test_rows'])")
    md('A EDA a seguir usa apenas o treino. Zeros em ingredientes não são codificados como ausentes. '
       'A imputação é preventiva quando não há faltantes; a taxa observada está na tabela acima. '
       'O scatter seleciona a feature com maior correlação absoluta com o alvo **no treino**; '
       'esse critério descritivo não altera o espaço ou os modelos.')
    figure('01_eda_distributions');figure('02_eda_correlations')
    md('### 2. Baseline sem otimização')
    code("display(metrics[metrics.method == 'baseline'][['method','cv_rmse','test_rmse','test_mae','test_r2','baseline_fit_seconds','search_seconds','total_seconds']])")
    figure('03_baseline_predictions')
    code("p=ROOT/'results'/'supplemental-baselines.csv'\nif p.exists(): display(pd.read_csv(p))")
    md('Os modelos Dummy e Ridge acima, quando presentes, são controles auxiliares. '
       'O baseline obrigatório da comparação permanece GBR com os defaults sklearn e seed 42.')
    md('### 3–4. Grid Search, Random Search e superfície do espaço')
    md('A convergência acumula os candidatos na ordem registrada em `cv_results_`. '
       'Com folds paralelos, isso não equivale necessariamente à cronologia de término de cada fit; '
       'a grade também não tem uma dinâmica adaptativa própria.')
    code("display(metrics[metrics.method.isin(['grid','random'])][['method','cv_rmse','test_rmse','test_mae','test_r2','total_seconds','n_evaluations','params_json']])")
    figure('04_grid_random_convergence');text('random_vs_grid')
    figure('05_grid_heatmap');text('heatmap')
    code("display(pd.DataFrame(analysis['grid_random']['spearman']))")
    figure('06_random_spearman');text('spearman')
    md('### 5. Síntese do exercício 1')
    code("display(metrics[metrics.method.isin(['baseline','grid','random'])][['method','cv_rmse','test_rmse','total_seconds','n_evaluations']])")
    code("""b=metrics.set_index('method').loc['baseline']
for key in ['grid','random']:
    r=metrics.set_index('method').loc[key]
    gain=100*(b.test_rmse-r.test_rmse)/b.test_rmse
    display(Markdown(f'**{key}:** variação relativa do RMSE de teste: {gain:.2f}% de redução; '
                     f'custo total {r.total_seconds:.3f} s, contra {b.total_seconds:.3f} s do baseline. '
                     'O ganho é descritivo no holdout; a justificativa operacional depende da tolerância de erro e do custo disponível.'))
display(Markdown(analysis['narrative']['grid_preference']))
display(Markdown(analysis['narrative']['heatmap']))""")
    md('## Exercício 2\n\n### 6. GP manual com Expected Improvement\n\n'
       'Cinco pontos iniciais e dez aquisições EI, kernel Matérn ν=2,5. '
       'Cada figura foi salva antes de avaliar o próximo candidato: mapa de média e incerteza, '
       'corte posterior no subsample escolhido e EI no mesmo corte. '
       'As observações estão no mapa 2D; só observações com o mesmo subsample aparecem no corte. '
       'Média ±2σ é incerteza do surrogate condicionado aos dados/kernel, não intervalo de confiança da generalização do GBR.')
    for i in range(1,11):figure(f'gp_iteration_{i:02d}')
    code("display(pd.DataFrame(analysis['gp_iterations']))")
    text('gp');figure('07_gp_comparison')
    code("display(metrics[metrics.method.isin(['grid','random','gp_manual'])][['method','cv_rmse','test_rmse','total_seconds','n_evaluations']])")
    md('A comparação de contagem deve considerar que GP manual explora um subespaço 2D com 15 avaliações, '
       'enquanto Grid/Random variam também n_estimators. Maior eficiência aparente não isola o efeito da aquisição.')
    md('### 7. Cinco bibliotecas de otimização Bayesiana\n\n'
       'skopt: GP Matérn 5/2 + EI; bayes_opt: GP + UCB κ=2,576; '
       'Optuna: TPESampler; Hyperopt: tpe.suggest, LR loguniform; '
       'Ray: OptunaSearch + ASHAScheduler. Todos iniciam 40 candidatos. '
       'Ray informa métricas nos recursos crescentes 0,25; 0,50; 0,75; 1,00, '
       'frações do número de árvores de cada candidato. Árvores são incrementadas por warm_start. '
       'Somente candidatos que completam o recurso 1,00 competem como melhor configuração.')
    code("display(metrics[metrics.method.isin(['bayessearch','bayesopt','optuna','hyperopt','ray'])][['method','cv_rmse','test_rmse','test_mae','test_r2','search_seconds','refit_seconds','total_seconds','n_evaluations','completed_trials','pruned_trials','cv_fits','trained_trees_cv']])")
    figure('08_bayesian_convergence')
    md('A curva Ray mostra o melhor RMSE das avaliações completas; trials podados não são comparáveis '
       'ao score final. Contagens de fits e árvores expõem o trabalho parcial.')
    md('### 8. Metaheurísticas\n\n'
       'GA: 20 indivíduos, 15 gerações, crossover = 0,7 e mutação = 0,25; genes inteiros '
       'quantizam LR log e subsample em 1001 níveis e n_estimators em 151 níveis. '
       'Diversidade = genótipos distintos / população. '
       'DE: best1bin e rand1bin, maxiter = 15, popsize = 10 (30 indivíduos em 3D), '
       'mutation = (0,5; 1), recombination = 0,7, polish = False. '
       'PSO: 20 partículas, inicialização + 15 atualizações; c1 = c2 = 1,5; três inércias. '
       'As estratégias DE compartilham a população inicial; as variantes PSO compartilham '
       'posições e velocidades iniciais (seed 42). Nesses pares, altera-se apenas a estratégia '
       'ou inércia. Somente os métodos vencedores tiveram o procedimento repetido com cinco seeds.')
    figure('09_ga_generations');text('ga')
    figure('10_de_convergence');text('de')
    code("display(metrics[metrics.method.isin(['de_best1bin','de_rand1bin'])][['method','cv_rmse','test_rmse','total_seconds','n_evaluations']])\nfor method in ['de_best1bin','de_rand1bin']:\n    display(pd.Series(json.loads((ROOT/'results'/method/'seed_42'/'de-result.json').read_text())).to_frame(method))")
    figure('11_pso_inertia');text('pso')
    md('### 9. Dashboard e diagnóstico\n\n'
       'Verde destaca os melhores valores de qualidade; amarelo, o menor tempo. '
       'Os 12 métodos principais e três variantes são identificados separadamente. '
       'O radar usa os 12 principais e min-max em cada eixo; erros são invertidos e '
       '1/tempo favorece execução rápida. Todos os eixos apontam para maior=melhor. '
       'As escalas dependem dos métodos incluídos e não são notas absolutas.')
    figure('12_comparison_table')
    code("""from html import escape
quality=['cv_rmse','test_rmse','test_mae','test_r2']
table=metrics[['method',*quality,'total_seconds','n_evaluations']]
html_rows=['<tr>'+''.join('<th>'+escape(c)+'</th>' for c in table.columns)+'</tr>']
for _, row in table.iterrows():
    cells=[]
    for c in table.columns:
        bg='white'
        if c in quality:
            best=table[c].max() if c=='test_r2' else table[c].min()
            if np.isclose(row[c],best,rtol=1e-10,atol=1e-12): bg='#bbdfb5'
        if c=='total_seconds' and np.isclose(row[c],table[c].min()): bg='#fff2b0'
        value=f'{row[c]:.4f}' if c in quality+['total_seconds'] else str(row[c])
        cells.append(f'<td style="background:{bg};padding:6px;border:1px solid #ccc">'+escape(value)+'</td>')
    html_rows.append('<tr>'+''.join(cells)+'</tr>')
display(HTML('<table style="border-collapse:collapse">'+''.join(html_rows)+'</table>'))
display(metrics[['method','search_seconds','refit_seconds','total_seconds','n_evaluations','unique_candidates','cv_fits','completed_trials','pruned_trials','trained_trees_cv']])""")
    figure('13_radar');text('radar');figure('14_pareto')
    code("display(Markdown('**Fronteira de Pareto (RMSE teste e tempo):** '+', '.join(analysis['method_labels'][m] for m in analysis['pareto_methods'])+'. Empates são preservados; dominar exige melhora estrita em pelo menos um objetivo.'))")
    text('baseline_gain');text('scope')
    figure('15_best_predictions_residuals');text('residuals')
    figure('16_feature_importance');text('feature_importance')
    md('### 10. Sensibilidade e recomendação\n\n'
       'A importância Optuna é estimada a partir dos trials dessa busca, condicionada ao espaço e budget. '
       'A comparação amostral usa 50% do treino, mantendo o mesmo teste reservado. '
       'A análise principal usa todo o dataset elegível, não uma amostra escolhida após ver scores.')
    figure('18_optuna_importances')
    code("display(pd.DataFrame(analysis['optuna_importances']))\ndisplay(pd.DataFrame(analysis.get('sample_comparison',[])))")
    text('optuna_importance')
    md('#### Robustez do procedimento completo\n\n'
       'O vencedor descritivo no teste é repetido com seeds 0,7,21,42,99. '
       'Se o vencedor por CV for outro método, sua repetição é reportada separadamente. '
       'São refeitas as buscas inteiras: não apenas refits da mesma configuração. '
       'A seed42 principal é reutilizada explicitamente. Holdout e folds permanecem fixos; '
       'variam seed do otimizador e do estimador.')
    code("show_csv('results/robustness.csv')\nshow_csv('results/robustness-summary.csv')")
    figure('17_robustness');text('robustness');text('uncertainty')
    md('#### Eficiência computacional\n\n'
       '$$E_m=\\frac{(RMSE_b-RMSE_m)/RMSE_b}{t_m-t_b}.$$\n\n'
       'Usamos segundos totais de busca+refit. Para baseline ou diferença de tempo não positiva, '
       'a razão é indefinida e é mostrada como ausente; não dividimos por zero nem introduzimos epsilon.')
    code("display(pd.DataFrame(analysis['efficiency']))\nprint('Maior razão definida:', analysis['method_labels'][analysis['best_efficiency_method']])")
    md('#### Recomendação justificada (até dez linhas)')
    text('recommendation')
    md('## Parâmetros escolhidos, defaults, ambiente e rastreabilidade')
    code("for row in metrics.to_dict('records'):\n    display(Markdown('**'+analysis['method_labels'].get(row['method'],row['method'])+'**'))\n    display(pd.Series(json.loads(row['params_json']),name='Valor').to_frame())")
    code("from sklearn.ensemble import GradientBoostingRegressor\ndisplay(pd.Series(GradientBoostingRegressor(random_state=42).get_params(),name='Defaults GBR').to_frame())\ndisplay(pd.Series(method_result('baseline')['environment'],name='Ambiente').to_frame())")
    md('As fontes do experimento e da análise estão nas células executáveis iniciais. '
       'Artefatos do pacote: `data/` (dados, qualidade e split), `results/` '
       '(trials, previsões, métricas, logs, modelos e diagnósticos), `figures/`, '
       '`study-protocol.md`, `search-budget.json` e arquivo de versões. '
       'Os resultados são específicos deste dataset, protocolo e execução. '
       'Não foram enviados emails ou submetidos resultados ao professor automaticamente.')
    nb.cells=cells
    return nb


def main():
    p=argparse.ArgumentParser();p.add_argument('--no-execute',action='store_true');args=p.parse_args()
    path=ROOT/'Aula05_Tarefa5_Resultados.ipynb'
    nb=build();nbf.write(nb,path)
    if not args.no_execute:
        # Explicit Python kernel path avoids accidentally running a global environment.
        import tempfile, json, os
        with tempfile.TemporaryDirectory(prefix='tarefa5-kernel-') as tmp:
            kernel=Path(tmp)/'kernels'/'tarefa5';kernel.mkdir(parents=True)
            (kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Tarefa5 Python','language':'python'}))
            previous=os.environ.get('JUPYTER_PATH')
            previous_ipython=os.environ.get('IPYTHONDIR')
            os.environ['JUPYTER_PATH']=str(Path(tmp))+(os.pathsep+previous if previous else '')
            os.environ['IPYTHONDIR']=str(Path(tmp)/'ipython')
            nb.metadata.kernelspec={'display_name':'Tarefa5 Python','language':'python','name':'tarefa5'}
            try:
                client=NotebookClient(nb,timeout=180,kernel_name='tarefa5',resources={'metadata':{'path':str(ROOT)}})
                client.execute()
            finally:
                if previous is None:os.environ.pop('JUPYTER_PATH',None)
                else:os.environ['JUPYTER_PATH']=previous
                if previous_ipython is None:os.environ.pop('IPYTHONDIR',None)
                else:os.environ['IPYTHONDIR']=previous_ipython
                # Public notebook uses standard Python 3 kernel, retaining executed outputs.
                nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
                nbf.write(nb,path)
    print(path)


if __name__=='__main__':main()
