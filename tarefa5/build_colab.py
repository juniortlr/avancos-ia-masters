"""Build a standalone Colab launcher without touching archived results.

python build_colab.py --ref <immutable-data-commit>
The launcher contains its bootstrap, installs scientific packages in a separate
Python 3.12 venv and uses the kernel only for standard-library presentation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import nbformat

ROOT=Path(__file__).resolve().parent
REPOSITORY='https://github.com/juniortlr/avancos-ia-masters.git'
REPO_SLUG='juniortlr/avancos-ia-masters'
ARCHIVE_REF='02d110722f2aee6f9d684faa748afcd932821477'

BOOTSTRAP=r'''
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, html, importlib.util, json, math, os, platform, re
import shutil, signal, subprocess, sys, tempfile, time, uuid
from IPython.display import display, Markdown, Image, HTML, FileLink

if MODO not in ('analise_arquivada', 'experimento_completo'):
    raise ValueError('Escolha um dos dois modos documentados.')
BASE = (Path('/content') if Path('/content').is_dir() else Path.cwd()) / 'aula05_colab'
BASE.mkdir(parents=True, exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
RUN_DIR = BASE / 'runs' / (RUN_ID + '-' + MODO)
RUN_DIR.mkdir(parents=True, exist_ok=False)
LOG_DIR = RUN_DIR / 'logs'
LOG_DIR.mkdir()
# Ray creates AF_UNIX sockets below its temp directory. Keep this path short.
RAY_TEMP = Path(tempfile.gettempdir()) / ('a05r-' + uuid.uuid4().hex[:8])
RAY_TEMP.mkdir(exist_ok=False)
ENV = os.environ.copy()
for inherited in ['PYTHONPATH','PYTHONHOME']:
    ENV.pop(inherited,None)
ENV.update({'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
            'NUMEXPR_NUM_THREADS':'1','PYTHONNOUSERSITE':'1','PYTHONUNBUFFERED':'1',
            'MPLBACKEND':'Agg','PIP_PROGRESS_BAR':'off',
            'RAY_USAGE_STATS_ENABLED':'0','MPLCONFIGDIR':str(RUN_DIR/'.matplotlib'),
            'RAY_TMPDIR':str(RAY_TEMP)})
EVENTS = []

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def write_json(path, data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def run_command(args, name, cwd=None, timeout=3600, env=None):
    """Bound a process group; retain its exact command, log and exit status."""
    args=[str(a) for a in args]
    log=LOG_DIR/(name+'.log')
    started=time.monotonic()
    record={'stage':name,'command':args,'started_utc':datetime.now(timezone.utc).isoformat(),
            'timeout_seconds':timeout,'log':str(log.relative_to(RUN_DIR)),'status':'running'}
    EVENTS.append(record);write_json(RUN_DIR/'execution-events.json',EVENTS)
    print(f'[{name}] iniciado. Log: {log.name}',flush=True)
    pos=0;shown=time.monotonic()
    with log.open('wb') as target:
        proc=subprocess.Popen(args,cwd=cwd,env=env or ENV,stdout=target,stderr=subprocess.STDOUT,
                              start_new_session=(os.name=='posix'))
        try:
            while proc.poll() is None:
                elapsed=time.monotonic()-started
                if elapsed>timeout:
                    if os.name=='posix': os.killpg(proc.pid,signal.SIGTERM)
                    else: proc.terminate()
                    try:proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        if os.name=='posix':os.killpg(proc.pid,signal.SIGKILL)
                        else:proc.kill()
                    record['status']='timeout'
                    raise TimeoutError(f'{name} ultrapassou {timeout:.0f} s; evidências parciais preservadas em {RUN_DIR}')
                if time.monotonic()-shown>=5:
                    data=log.read_bytes()
                    if len(data)>pos:print(data[pos:].decode('utf-8',errors='replace'),end='',flush=True);pos=len(data)
                    else:print(f'[{name}] {elapsed:.0f} s...',flush=True)
                    shown=time.monotonic()
                time.sleep(.5)
            target.flush()
            data=log.read_bytes()
            if len(data)>pos:print(data[pos:].decode('utf-8',errors='replace'),end='',flush=True)
            record['returncode']=proc.returncode
            record['status']='complete' if proc.returncode==0 else 'failed'
            if proc.returncode:
                raise RuntimeError(f'{name} falhou com exit {proc.returncode}; consulte {log}')
        finally:
            if proc.poll() is None:
                if os.name=='posix':os.killpg(proc.pid,signal.SIGTERM)
                else:proc.terminate()
            record['elapsed_seconds']=time.monotonic()-started
            if record['status']=='running':record['status']='interrupted'
            write_json(RUN_DIR/'execution-events.json',EVENTS)
    return log

def capture(args,env=None):
    return subprocess.check_output([str(a) for a in args],env=env or ENV,text=True).strip()

SOURCE=BASE/'sources'/RUN_ID
SOURCE.parent.mkdir(exist_ok=True)
run_command(['git','init',SOURCE],'git-init',timeout=60)
run_command(['git','-C',SOURCE,'remote','add','origin',REPO_URL],'git-origin',timeout=60)
run_command(['git','-C',SOURCE,'fetch','--depth','1','origin',REPO_REF],'git-fetch',timeout=600)
run_command(['git','-C',SOURCE,'checkout','--detach','FETCH_HEAD'],'git-checkout',timeout=60)
RESOLVED_COMMIT=capture(['git','-C',SOURCE,'rev-parse','HEAD'])
if re.fullmatch(r'[0-9a-fA-F]{40}',REPO_REF) and RESOLVED_COMMIT.lower()!=REPO_REF.lower():
    raise RuntimeError('O commit recebido não corresponde ao SHA solicitado.')
ARCHIVE=SOURCE/'tarefa5'
for required in ['experiment.py','plot_results.py','data/uci165_raw.csv','data/data-contract.json','results/metrics.csv']:
    if not (ARCHIVE/required).is_file():raise FileNotFoundError(f'Commit sem material obrigatório: tarefa5/{required}')
print('Commit efetivamente obtido:',RESOLVED_COMMIT)

# Available CPU means affinity plus cgroup quota, not just os.cpu_count().
limits=[os.cpu_count() or 1]
if hasattr(os,'sched_getaffinity'):limits.append(len(os.sched_getaffinity(0)))
try:
    q,period=Path('/sys/fs/cgroup/cpu.max').read_text().split()
    if q!='max':limits.append(max(1,math.floor(int(q)/int(period))))
except (OSError,ValueError):pass
AVAILABLE_CPUS=max(1,min(limits))
CV_JOBS=max(1,min(5,AVAILABLE_CPUS,int(MAX_CPU_FOLDS)))
free_gib=shutil.disk_usage(BASE).free/(1024**3)
if free_gib<1.5:raise RuntimeError(f'Espaço livre insuficiente para ambiente isolado: {free_gib:.2f} GiB.')
print(f'CPU disponível: {AVAILABLE_CPUS}; folds paralelos: {CV_JOBS}; livre: {free_gib:.1f} GiB. GPU não utilizada.')

for name in ['experiment.py','plot_results.py','study-protocol.md','search-budget.json']:
    if (ARCHIVE/name).exists():shutil.copy2(ARCHIVE/name,RUN_DIR/name)

if MODO=='analise_arquivada':
    shutil.copytree(ARCHIVE/'data',RUN_DIR/'data')
    # Evidence required by verify/plots; model pickles and Ray runtime internals are not loaded.
    shutil.copytree(ARCHIVE/'results',RUN_DIR/'results',
                    ignore=shutil.ignore_patterns('model.joblib','ray-storage','*_superseded_*','__pycache__'))
else:
    (RUN_DIR/'data').mkdir()
    if DADOS=='snapshot_publicado':
        for name in ['uci165_raw.csv','uci_metadata.json']:
            if (ARCHIVE/'data'/name).exists():shutil.copy2(ARCHIVE/'data'/name,RUN_DIR/'data'/name)
    elif DADOS!='nova_consulta_uci':raise ValueError('Fonte dos dados desconhecida.')

# Never rewrite original files. Every installation and derived output is under BASE.
(RUN_DIR/'requirements-colab.txt').write_text(REQUIREMENTS_TEXT,encoding='utf-8')
selected=[];section='analysis'
for line in REQUIREMENTS_TEXT.splitlines():
    if line.strip()=='# [experiments]':section='experiments'
    if line.strip() and not line.lstrip().startswith('#'):
        if section=='analysis' or MODO=='experimento_completo':selected.append(line.strip())
(RUN_DIR/'requirements-selected.txt').write_text('\n'.join(selected)+'\n',encoding='utf-8')

VENV=BASE/'environments'/('py312-'+hashlib.sha256('\n'.join(selected).encode()).hexdigest()[:16])
VENV_PY=VENV/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
VENV.parent.mkdir(exist_ok=True)
venv_ready=False
if VENV_PY.exists():
    try:
        venv_ready=(capture([VENV_PY,'-c','import sys,pip;print("%s.%s"%sys.version_info[:2])'])=='3.12')
    except (OSError,subprocess.CalledProcessError):pass
if not venv_ready:
    candidates=[sys.executable,shutil.which('python3.12')]
    python312=None
    for candidate in candidates:
        if candidate:
            try:
                if capture([candidate,'-c','import sys;print("%s.%s"%sys.version_info[:2])'])=='3.12':python312=candidate;break
            except (OSError,subprocess.CalledProcessError):pass
    if python312:
        try:
            run_command([python312,'-m','venv',VENV],'create-venv',timeout=300)
            venv_ready=True
        except RuntimeError:
            print('venv/ensurepip indisponível neste Python; recuperação isolada via uv. Consulte create-venv.log.')
    if not venv_ready:
        # uv is a bootstrap utility installed in an isolated target, not in the kernel.
        tools_dir=BASE/'bootstrap-tools'
        run_command([sys.executable,'-m','pip','install','--no-cache-dir','--target',tools_dir,'uv'],
                    'install-uv-bootstrap',timeout=600)
        uv_env=ENV.copy();uv_env.update({'PYTHONPATH':str(tools_dir),
            'UV_CACHE_DIR':str(BASE/'uv-cache'),'UV_PYTHON_INSTALL_DIR':str(BASE/'python'),
            'UV_PYTHON_BIN_DIR':str(BASE/'python-bin')})
        run_command([sys.executable,'-m','uv','venv','--python',python312 or '3.12','--seed','--allow-existing',VENV],
                    'create-python312-venv',timeout=900,env=uv_env)
        (RUN_DIR/'uv-version.txt').write_text(capture([sys.executable,'-m','uv','--version'],env=uv_env),encoding='utf-8')
run_command([VENV_PY,'-m','pip','install','--no-cache-dir','-r',RUN_DIR/'requirements-selected.txt'],
            'install-scientific-dependencies',timeout=1800)
run_command([VENV_PY,'-m','pip','check'],'pip-check',timeout=120)
(RUN_DIR/'environment-freeze.txt').write_text(capture([VENV_PY,'-m','pip','freeze']),encoding='utf-8')
runtime=json.loads(capture([VENV_PY,'-c','import sys,platform,json;print(json.dumps({"python":sys.version,"platform":platform.platform()}))']))
MANIFEST={'mode':MODO,'repo_url':REPO_URL,'requested_ref':REPO_REF,'resolved_commit':RESOLVED_COMMIT,
    'created_utc':datetime.now(timezone.utc).isoformat(),'kernel_python':sys.version,
    'experiment_runtime':runtime,'cv_jobs_requested':CV_JOBS,'available_cpus':AVAILABLE_CPUS,
    'data_origin':DADOS if MODO=='experimento_completo' else 'archived_snapshot',
    'time_limit_hours':MAX_HORAS,'ray_trials':40,'ray_max_concurrent_trials':1,
    'ray_temp_dir':str(RAY_TEMP),
    'ray_resources':'at most CV_JOBS local CPUs; no GPU or remote cluster',
    'parallelism_note':'The archived engine contains a static original-run parallelism description mentioning 5 workers. For newly computed results, use each result cv_jobs and this manifest as the actual count; Ray receives the same count.',
    'code_sha256':{n:sha256(RUN_DIR/n) for n in ['experiment.py','plot_results.py']},
    'original_archive_untouched':True,'validation_scope':'This run logs its own execution; hosted Colab testing is not implied by local Linux tests.'}
write_json(RUN_DIR/'colab-run-manifest.json',MANIFEST)
print('Ambiente científico isolado:',VENV_PY)
print('Artefatos desta execução:',RUN_DIR)
'''

EXECUTION=r'''
deadline=time.monotonic()+float(MAX_HORAS)*3600
def execute_engine(arguments,label):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('Orçamento de parede esgotado; resultados parciais estão preservados.')
    run_command([VENV_PY,RUN_DIR/'experiment.py',*arguments],label,cwd=RUN_DIR,timeout=remaining)

if MODO=='experimento_completo':
    # All required methods and all supplemental procedures; no archived score reuse.
    execute_engine(['prepare'],'01-prepare')
    execute_engine(['supplement','--jobs',str(CV_JOBS)],'02-supplement')
    execute_engine(['run','--method','all','--jobs',str(CV_JOBS)],'03-all-methods')
    execute_engine(['sample','--jobs',str(CV_JOBS)],'04-optuna-half-training')
    execute_engine(['robustness','--jobs',str(CV_JOBS),'--resume'],'05-robustness')
    # --resume above reuses only seed42 just generated within this new run.
execute_engine(['verify'],'06-verify')
run_command([VENV_PY,RUN_DIR/'plot_results.py'],'07-reconstruct-analysis',cwd=RUN_DIR,
            timeout=max(1,deadline-time.monotonic()))
analysis=json.loads((RUN_DIR/'results'/'analysis.json').read_text(encoding='utf-8'))
if len(analysis['metrics'])!=15:raise RuntimeError('A tabela precisa conter os 12 métodos e três variantes.')
if set(analysis.get('robustness_by_method',{})) != {analysis['best_cv_method'],analysis['best_test_method']}:
    raise RuntimeError('Faltou uma das séries de robustez dos vencedores.')
for method,stats in analysis['robustness_by_method'].items():
    if sorted(int(row['seed']) for row in stats['rows']) != [0,7,21,42,99]:
        raise RuntimeError(f'Robustez incompleta para {method}.')
if MODO=='experimento_completo':
    # The original plotting source proposes Optuna based on the original study.
    # Do not silently turn that historical judgement into a new recommendation.
    analysis['archived_recommendation_not_transferred']=analysis.pop('recommendation',None)
    analysis['narrative'].pop('recommendation',None)
    analysis['recommendation']={'status':'requires_interpretation_of_new_run',
        'formal_cv_selection':analysis['best_cv_method'],
        'descriptive_test_winner':analysis['best_test_method'],
        'reason':'The original Optuna operational judgement is not automatically transferred to a new runtime.'}
    write_json(RUN_DIR/'results'/'analysis.json',analysis)
MANIFEST['status']='complete'
MANIFEST['figure_count']=len(list((RUN_DIR/'figures').glob('*.png')))
MANIFEST['completed_utc']=datetime.now(timezone.utc).isoformat()
write_json(RUN_DIR/'colab-run-manifest.json',MANIFEST)
print(f'Concluído: {len(analysis["metrics"])} métodos/variantes, {MANIFEST["figure_count"]} figuras.')
print('Os tempos da análise arquivada permanecem os da execução original; não são um benchmark deste Colab.'
      if MODO=='analise_arquivada' else 'Tempos novos são específicos deste runtime e de CV_JOBS, sem comparação direta com os tempos Windows arquivados.')
'''

DISPLAY_HELPERS=r'''
def table_rows(rows,columns=None,quality=False):
    rows=list(rows)
    if not rows:return display(Markdown('Sem linhas disponíveis.'))
    columns=columns or list(rows[0])
    out=['<table style="border-collapse:collapse;font-size:13px"><tr>']
    out.extend('<th style="padding:6px;border:1px solid #aaa">'+html.escape(str(c))+'</th>' for c in columns)
    out.append('</tr>')
    for row in rows:
        out.append('<tr>')
        for c in columns:
            value=row.get(c,'');background='white'
            if quality and c in ('cv_rmse','test_rmse','test_mae','test_r2','total_seconds'):
                values=[float(r[c]) for r in rows]
                best=max(values) if c=='test_r2' else min(values)
                if math.isclose(float(value),best,rel_tol=1e-10,abs_tol=1e-12):
                    background='#fff2b0' if c=='total_seconds' else '#bbdfb5'
            if isinstance(value,float):value=f'{value:.6g}'
            out.append(f'<td style="padding:6px;border:1px solid #ccc;background:{background}">'+html.escape(str(value))+'</td>')
        out.append('</tr>')
    display(HTML(''.join(out)+'</table>'))

def csv_table(relative,columns=None):
    with (RUN_DIR/relative).open(encoding='utf-8-sig',newline='') as f:table_rows(csv.DictReader(f),columns)

def figure(stem):display(Image(filename=str(RUN_DIR/'figures'/(stem+'.png'))))
def finding(key):display(Markdown(analysis['narrative'][key]))
def methods(names=None):
    rows=analysis['metrics']
    if names:rows=[r for r in rows if r['method'] in names]
    table_rows(rows,['method','cv_rmse','test_rmse','test_mae','test_r2','total_seconds','n_evaluations'],quality=True)

display(Markdown('**Modo:** '+MODO+' · **commit dos materiais:** `'+RESOLVED_COMMIT+'`.'))
display(Markdown('**Original preservado:** [notebook executado da entrega](https://github.com/'+REPO_SLUG+'/blob/'+RESOLVED_COMMIT+'/tarefa5/Aula05_Tarefa5_Resultados.ipynb).'))
'''

def build(ref):
    requirements=(ROOT/'requirements-colab.txt').read_text(encoding='utf-8')
    nb=nbformat.v4.new_notebook()
    nb.metadata={'colab':{'name':'Aula05_Tarefa5_Colab.ipynb','provenance':[]},
                 'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},
                 'language_info':{'name':'python'}}
    cells=[]
    def md(s):cells.append(nbformat.v4.new_markdown_cell(s))
    def code(s,**meta):cells.append(nbformat.v4.new_code_cell(s,metadata=meta))
    def fig(stem):code(f'figure({stem!r})')
    def finding(key):code(f'finding({key!r})')
    md('# Aula 05 — Otimização de hiperparâmetros no Google Colab\n\n'
       '**Avanços em IA — EELT7025, PPGEE/UFPR**\n\n'
       '**Adriely Teixeira de Paula · Betina Zynger Capaverde · Emilio Gaudeda Junior**\n\n'
       'Concrete Compressive Strength (UCI 165) · GradientBoostingRegressor · resistência em MPa.\n\n'
       'Escolha o modo abaixo e use **Ambiente de execução → Executar tudo**. Não é necessário enviar arquivos. '
       'O bootstrap baixa os materiais do GitHub e registra o commit efetivamente recebido. '
       'Use runtime **CPU**; este estudo não usa GPU.\n\n'
       '- **analise_arquivada** (padrão): verifica os dados/resultados publicados e recalcula tabelas, análises e figuras, sem repetir HPO.\n'
       '- **experimento_completo**: executa todos os 15 métodos/variantes, controles Dummy/Ridge, Optuna com 50% do treino, robustez dos vencedores com cinco seeds, verificação e gráficos, em pasta nova.\n\n'
       'O ambiente científico é um **venv Python 3.12 isolado**. As dependências do kernel Colab permanecem intactas. '
       'Uma versão diferente de Python pode exigir o download de Python 3.12 via uv. '
       'A primeira instalação demora alguns minutos; o tempo dos experimentos varia com os recursos disponíveis. '
       'Colab pode encerrar sessões: não há técnica para contornar limites, e logs/resultados parciais ficam preservados enquanto o runtime existir.')
    code(f'''# @title Configuração
MODO = "analise_arquivada" # @param ["analise_arquivada", "experimento_completo"]
DADOS = "snapshot_publicado" # @param ["snapshot_publicado", "nova_consulta_uci"]
MAX_CPU_FOLDS = 5 # @param {{type:"integer"}}
MAX_HORAS = 6 # @param {{type:"number"}}
REPO_URL = {REPOSITORY!r}
REPO_REF = {ref!r} # @param {{type:"string"}}
REPO_SLUG = {REPO_SLUG!r}
REQUIREMENTS_TEXT = {requirements!r}
if not 1 <= int(MAX_CPU_FOLDS) <= 5: raise ValueError('MAX_CPU_FOLDS deve estar entre 1 e 5.')
if not 0 < float(MAX_HORAS) <= 12: raise ValueError('MAX_HORAS deve estar em (0,12].')
''')
    md('## 1. Baixar materiais e preparar ambiente isolado\n\n'
       'O snapshot publicado conserva os dados e o split usados no relatório. No modo integral, a opção '
       '`nova_consulta_uci` refaz `fetch_ucirepo(id=165)`; uma mudança futura da fonte pode alterar os resultados. '
       'O script limita o paralelismo à CPU disponível e usa no máximo um trial Ray por vez. '
       'Os 40 trials Ray e seus estágios ASHA permanecem completos; o teto de parede interrompe com erro explícito, sem fingir conclusão.')
    code(BOOTSTRAP)
    md('## 2. Executar o modo escolhido\n\n'
       'No modo integral, todas as buscas começam sem resultados prévios. Apenas a seed 42 recém-calculada '
       'é reutilizada na robustez. As tabelas do arquivo original nunca são sobrescritas. '
       'A ordem inclui explicitamente `supplement`, que estava ausente do atalho de reprodução do notebook local original.')
    code(EXECUTION)
    md('## 3. Resultados e respostas aos exercícios\n\n'
       'As células seguintes usam somente os artefatos da pasta desta execução. O kernel apenas apresenta JSON, CSV e PNG; '
       'todos os cálculos científicos ocorreram no venv. A seleção formal usa CV; o menor RMSE de teste é um vencedor descritivo '
       'exigido pelo enunciado, com o viés de seleção explicitado.')
    code(DISPLAY_HELPERS)
    md('### Exercício 1 — dados, baseline e buscas clássicas\n\n'
       'Duplicatas exatas de X+y são removidas antes do split 80/20 com seed 42. Mediana e StandardScaler são ajustados '
       'dentro de cada fold do pipeline. O alvo mantém MPa. O CV usa cinco folds embaralhados com seed 42; '
       'a EDA usa somente o treino, enquanto a tabela de qualidade/describe caracteriza a fonte integral.')
    code("contract=json.loads((RUN_DIR/'data'/'data-contract.json').read_text(encoding='utf-8'))\ndisplay(HTML('<pre>'+html.escape(json.dumps(contract,ensure_ascii=False,indent=2))+'</pre>'))\ncsv_table('data/quality-summary.csv')\ncsv_table('data/describe_raw.csv')")
    finding('feature_overlap');fig('01_eda_distributions');fig('02_eda_correlations')
    md('**Itens 2–5.** O GBR baseline mantém os defaults sklearn, exceto a seed. Grid tem 36 pontos; Random avalia 30 '
       'da mesma grade. As curvas seguem a ordem registrada em `cv_results_`, sem prometer ordem cronológica de término de fits paralelos. '
       'No heatmap, n_estimators é fixado no melhor valor da grade. Correlações Spearman usam RMSE positivo (menor é melhor).')
    code("methods(['baseline','grid','random'])\ncsv_table('results/supplemental-baselines.csv')")
    fig('03_baseline_predictions');fig('04_grid_random_convergence');finding('random_vs_grid')
    fig('05_grid_heatmap');finding('heatmap');fig('06_random_spearman');finding('spearman');finding('grid_preference')
    code("for row in analysis['metrics']:\n    if row['method'] in ['baseline','grid','random']:\n        display(Markdown('**'+row['method']+'** — parâmetros: `'+row['params_json']+'`; tempo de busca '+str(row['search_seconds'])+' s; refit '+str(row['refit_seconds'])+' s.'))")
    md('### Exercício 2 — GP manual, bibliotecas e metaheurísticas\n\n'
       '**Item 6.** GP Matérn 5/2, cinco pontos iniciais e dez aquisições EI, n_estimators=100. '
       'A aquisição é maximizada aproximadamente numa malha 61×61. Cada figura mostra o posterior anterior à avaliação seguinte: '
       'média/σ em 2D, corte no subsample do candidato e EI no mesmo corte. Só observações exatamente nesse corte aparecem nele.')
    for i in range(1,11):fig(f'gp_iteration_{i:02d}')
    finding('gp');fig('07_gp_comparison');code("methods(['grid','random','gp_manual'])")
    md('**Item 7.** skopt GP+EI/Matérn 5/2; bayes_opt GP+UCB κ=2,576; Optuna TPE; Hyperopt TPE/loguniform; '
       'Ray Tune OptunaSearch+ASHA. São 40 trials por biblioteca. Ray reporta recursos 0,25/0,50/0,75/1,00 com warm_start; '
       'apenas trials completos podem vencer. A tabela separa avaliações completas, podas e trabalho CV real.')
    code("table_rows([r for r in analysis['metrics'] if r['method'] in ['bayessearch','bayesopt','optuna','hyperopt','ray']],['method','cv_rmse','test_rmse','total_seconds','n_evaluations','completed_trials','pruned_trials','cv_fits','trained_trees_cv'])")
    fig('08_bayesian_convergence')
    md('**Item 8.** GA: população 20, 15 gerações, crossover 0,7 e mutação 0,25, genes inteiros. '
       'DE: duas estratégias, popsize10×3 dimensões, maxiter15, sem polish; pode terminar antes por tolerância. '
       'PSO: 20 partículas, inicialização +15 atualizações, c1=c2=1,5; inércias 0,4/0,7/0,9. '
       'As variantes compartilham inicialização; médias PSO são fitness corrente, não pbest.')
    fig('09_ga_generations');finding('ga');fig('10_de_convergence');finding('de');fig('11_pso_inertia');finding('pso')
    md('### 9. Dashboard comparativo e diagnóstico\n\n'
       'Verde: melhor qualidade; amarelo: menor tempo. O radar inclui os 12 métodos principais; as três variantes adicionais '
       'ficam na tabela e nos gráficos de sensibilidade. Todos os eixos do radar são normalizados para maior=melhor. '
       'A fronteira de Pareto minimiza erro e segundos e preserva empates.')
    code("methods()\ntable_rows(analysis['metrics'],['method','params_json','cv_jobs','n_evaluations','completed_trials','pruned_trials','cv_fits','trained_trees_cv'])")
    fig('12_comparison_table');fig('13_radar');finding('radar');fig('14_pareto');finding('baseline_gain');finding('scope');finding('spaces')
    fig('15_best_predictions_residuals');finding('residuals');fig('16_feature_importance');finding('feature_importance')
    md('### 10. Importâncias, robustez e custo-benefício\n\n'
       'A comparação amostral usa 50% do treino e o mesmo holdout. Robustez repete o HPO inteiro com seeds 0,7,21,42,99 '
       'para o vencedor por teste e o por CV, se distintos. As duas séries são resumidas separadamente. '
       'Isso mede aleatoriedade computacional condicional ao dataset; não equivale a cinco datasets ou a um IC de generalização.')
    fig('18_optuna_importances');finding('optuna_importance');code("csv_table('results/sample-comparison.csv',['method','sample_fraction','train_rows','cv_rmse','test_rmse','total_seconds'])\ncsv_table('results/robustness.csv')\ncsv_table('results/robustness-summary.csv')")
    fig('17_robustness');finding('robustness');finding('uncertainty')
    md('Eficiência = melhoria relativa do RMSE sobre baseline / tempo adicional. Baseline e denominadores não positivos '
       'são indefinidos, sem divisão por zero nem epsilon.')
    code("table_rows(analysis['efficiency'])")
    code("""if MODO=='analise_arquivada':
    finding('recommendation')
else:
    display(Markdown('**Interpretação desta nova execução:** campeão CV = '+analysis['method_labels'][analysis['best_cv_method']]+
        '; vencedor descritivo no teste = '+analysis['method_labels'][analysis['best_test_method']]+
        '. Compare qualidade, tempo e facilidade de integração antes de escolher o método operacional. '
        'A recomendação Optuna do relatório original é uma análise daquele resultado e não é automaticamente transferida para este novo runtime.'))
""")
    md('## Código integral, proveniência e exportação\n\n'
       'O engine e a análise abaixo são exatamente os fontes baixados do commit registrado. Nenhum arquivo Windows '
       'é necessário; os caminhos são criados no runtime. O SHA dos fontes, versões instaladas, comandos, limites e logs '
       'acompanham a execução. Tempos novos com menos CPUs não devem ser comparados diretamente ao benchmark original com cinco workers.')
    code("for name in ['experiment.py','plot_results.py']:\n    display(HTML('<details><summary>'+html.escape(name)+' — código completo</summary><pre>'+html.escape((RUN_DIR/name).read_text(encoding='utf-8'))+'</pre></details>'))\ndisplay(HTML('<pre>'+html.escape(json.dumps(MANIFEST,ensure_ascii=False,indent=2))+'</pre>'))")
    code("""archive_path=Path(shutil.make_archive(str(BASE/('Aula05-'+RUN_ID)), 'zip', RUN_DIR))
print('Pacote com resultados, dados, fontes, figuras, manifesto e logs:',archive_path)
try:
    from google.colab import files
    files.download(str(archive_path))
except ImportError:
    display(FileLink(str(archive_path)))
""")
    md('Referências de infraestrutura: [FAQ oficial do Colab](https://research.google.com/colaboratory/faq.html), '
       '[runtime e Python do Colab](https://github.com/googlecolab/backend-info), '
       '[ambientes venv](https://docs.python.org/3/library/venv.html), '
       '[instalação do Ray Tune](https://docs.ray.io/en/latest/ray-overview/installation.html), '
       '[Python isolado via uv](https://docs.astral.sh/uv/guides/install-python/). '
       'Fonte do dataset: [UCI 165](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength). '
       'Framework: [rnd-superpowers no commit solicitado](https://github.com/juniortlr/rnd-superpowers/commit/f68892c8b7adba358b8aa437eec00a89fe88d340).')
    nb.cells=cells
    return nb

def main():
    p=argparse.ArgumentParser();p.add_argument('--ref',default=ARCHIVE_REF);p.add_argument('--output',type=Path,default=ROOT/'Aula05_Tarefa5_Colab.ipynb');args=p.parse_args()
    nb=build(args.ref);nbformat.validate(nb);nbformat.write(nb,args.output)
    print(args.output)
    print(f'https://colab.research.google.com/github/{REPO_SLUG}/blob/main/tarefa5/Aula05_Tarefa5_Colab.ipynb')

if __name__=='__main__':main()
