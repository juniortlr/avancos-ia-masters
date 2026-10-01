"""Validate launcher structure/presentation without retraining or changing evidence.

This local validation does not claim a hosted Google Colab execution. A separate
Linux notebook execution checks bootstrap/install/analysis integration.
"""
from __future__ import annotations
import ast
import csv
import hashlib
import html
import importlib.metadata
import json
import math
from pathlib import Path
import shutil
import tempfile
import time
from datetime import datetime, timezone
import nbformat
from IPython.display import Markdown, Image, HTML, FileLink
import build_colab

ROOT=Path(__file__).resolve().parent


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protected=[ROOT/'experiment.py',ROOT/'Aula05_Tarefa5_Resultados.ipynb',ROOT/'results'/'metrics.csv',ROOT/'results'/'analysis.json']
    before={p.name:checksum(p) for p in protected}
    notebook=nbformat.read(ROOT/'Aula05_Tarefa5_Colab.ipynb',as_version=4)
    nbformat.validate(notebook)
    code_cells=[c.source for c in notebook.cells if c.cell_type=='code']
    for i,source in enumerate(code_cells):
        ast.parse(source,filename=f'colab-cell-{i}')
        assert not source.startswith('!'),i
        assert 'C:/Users/' not in source and 'C:\\Users\\' not in source,i
    assert all(c.execution_count is None and not c.outputs for c in notebook.cells if c.cell_type=='code')
    config={}
    exec(code_cells[0],config)
    assert config['REPO_REF']==build_colab.ARCHIVE_REF
    assert len(config['REPO_REF'])==40

    real_analysis=json.loads((ROOT/'results'/'analysis.json').read_text(encoding='utf-8'))
    rendered=[]
    ns={'RUN_DIR':ROOT,'analysis':real_analysis,'display':rendered.append,'Markdown':Markdown,
        'Image':Image,'HTML':HTML,'FileLink':FileLink,'csv':csv,'html':html,'math':math,'json':json,
        'MODO':'analise_arquivada','RESOLVED_COMMIT':config['REPO_REF'],'REPO_SLUG':config['REPO_SLUG'],
        'MANIFEST':{'validation':'read-only local presentation smoke'}}
    presentation=code_cells[3:-1]  # exclude configuration/bootstrap/execution/export
    for i,source in enumerate(presentation):
        exec(compile(source,f'presentation-cell-{i}','exec'),ns)
    figure_count=sum(isinstance(v,Image) for v in rendered)
    assert figure_count==28,figure_count

    # Exercise the actual orchestration cell with a process recorder; this is a
    # control-flow check, not scientific execution or a replacement for Linux QA.
    flows={}
    for mode in ['analise_arquivada','experimento_completo']:
        with tempfile.TemporaryDirectory(prefix='aula05-flow-') as tmp:
            run_dir=Path(tmp);(run_dir/'results').mkdir();(run_dir/'figures').mkdir()
            shutil.copy2(ROOT/'results'/'analysis.json',run_dir/'results'/'analysis.json')
            commands=[]
            def record(args,name,**kwargs):commands.append({'name':name,'arguments':[str(a) for a in args]})
            def write_json(path,value):Path(path).write_text(json.dumps(value,allow_nan=False),encoding='utf-8')
            ctx={'MAX_HORAS':6,'time':time,'MODO':mode,'CV_JOBS':2,'RUN_DIR':run_dir,
                 'VENV_PY':Path('/isolated/bin/python'),'run_command':record,'json':json,
                 'MANIFEST':{},'datetime':datetime,'timezone':timezone,'write_json':write_json}
            exec(build_colab.EXECUTION,ctx)
            actions=[c['arguments'][2] for c in commands if c['arguments'][1].endswith('experiment.py')]
            expected=['verify'] if mode=='analise_arquivada' else ['prepare','supplement','run','sample','robustness','verify']
            assert actions==expected,(mode,actions)
            assert commands[-1]['arguments'][1].endswith('plot_results.py')
            if mode=='experimento_completo':
                assert 'recommendation' not in ctx['analysis']['narrative']
                assert ctx['analysis']['recommendation']['status']=='requires_interpretation_of_new_run'
                run_command=next(c for c in commands if c['name']=='03-all-methods')
                assert run_command['arguments'][3:]==['--method','all','--jobs','2']
            flows[mode]={'engine_actions':actions,'final_stage':commands[-1]['name']}

    installed={}
    for line in config['REQUIREMENTS_TEXT'].splitlines():
        if not line.strip() or line.startswith('#'):continue
        name,version=line.split('==');package=name.split('[')[0]
        installed[package]=importlib.metadata.version(package)
        assert installed[package]==version,(package,installed[package],version)
    after={p.name:checksum(p) for p in protected}
    assert before==after,'Original evidence changed during validation'
    report={'status':'passed','scope':'Notebook schema and Python syntax, real archived presentation, both orchestration control flows with recorded subprocess calls, requirements pins versus original environment. No hosted Colab or new full HPO claimed.',
            'code_cells_compiled':len(code_cells),'presentation_cells_executed':len(presentation),
            'images_loaded':figure_count,'display_objects':len(rendered),'flows':flows,
            'archive_ref':config['REPO_REF'],'original_files_unchanged':before,
            'installed_original_versions':installed,'notebook_sha256':checksum(ROOT/'Aula05_Tarefa5_Colab.ipynb')}
    (ROOT/'colab-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
