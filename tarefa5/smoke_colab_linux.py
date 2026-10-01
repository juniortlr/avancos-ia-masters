"""Focused Linux portability check, not a new full study or hosted Colab claim.

Run with the isolated scientific Python after installing requirements-colab.txt:
  python smoke_colab_linux.py --archive /path/to/checkout/tarefa5 --output /tmp/a05-smoke
Creates a fresh output directory. Never modifies the archived study.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=2)
    args=parser.parse_args()
    if sys.platform!='linux':parser.error('This check is specifically for Linux.')
    if not 1<=args.jobs<=5:parser.error('--jobs must be between 1 and 5')
    source=args.archive.resolve();out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    (out/'logs').mkdir();(out/'data').mkdir()
    engine=source/'experiment.py'
    archived_engine_hash=hashlib.sha256(engine.read_bytes()).hexdigest()
    shutil.copy2(engine,out/'experiment.py')
    for name in ['uci165_raw.csv','uci_metadata.json']:
        if (source/'data'/name).exists():shutil.copy2(source/'data'/name,out/'data'/name)
    ray_temp=Path(tempfile.gettempdir())/('a05r-'+uuid.uuid4().hex[:8]);ray_temp.mkdir()
    env=os.environ.copy()
    env.update({'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
        'NUMEXPR_NUM_THREADS':'1','PYTHONNOUSERSITE':'1','PYTHONUNBUFFERED':'1',
        'RAY_USAGE_STATS_ENABLED':'0','RAY_TMPDIR':str(ray_temp)})
    commands=[['prepare'],['supplement','--jobs',str(args.jobs)],
        ['run','--method','baseline,optuna,ray','--jobs',str(args.jobs)],
        ['sample','--jobs',str(args.jobs)],['verify']]
    events=[]
    for number,arguments in enumerate(commands,1):
        log=out/'logs'/f'{number:02d}-{arguments[0]}.log'
        command=[sys.executable,str(out/'experiment.py'),*arguments]
        start=time.monotonic();print('Running',arguments,flush=True)
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run(command,cwd=out,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=2400)
        events.append({'command':command,'returncode':result.returncode,'seconds':time.monotonic()-start,'log':str(log)})
        (out/'smoke-commands.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
        if result.returncode:raise RuntimeError(f'Failed {arguments[0]}: see {log}')
    results={method:json.loads((out/'results'/method/'seed_42'/'result.json').read_text()) for method in ['baseline','optuna','ray']}
    for name,result in results.items():
        assert result['status']=='complete',name
        assert result['cv_jobs']==args.jobs,name
        assert result['n_evaluations']==(1 if name=='baseline' else 40),name
        assert result['completed_trials']+result['pruned_trials']==result['n_evaluations'],name
    half=json.loads((out/'results'/'sample50'/'optuna'/'seed_42'/'result.json').read_text())
    assert half['sample_fraction']==.5 and half['n_evaluations']==40 and half['cv_jobs']==args.jobs
    assert hashlib.sha256(engine.read_bytes()).hexdigest()==archived_engine_hash
    report={'status':'passed','scope':'Focused Linux run of baseline, Optuna40, Ray40/ASHA, supplemental controls, Optuna50% and structural verify at limited CPU. Not the full15-method suite and not hosted Google Colab.',
        'python':sys.version,'platform':platform.platform(),'cv_jobs':args.jobs,'ray_temp':str(ray_temp),
        'archived_engine_sha256':archived_engine_hash,'original_engine_unchanged':True,
        'versions':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','optuna','ray','hyperopt']},
        'methods':{n:{k:r[k] for k in ['cv_rmse','test_rmse','cv_jobs','n_evaluations','completed_trials','pruned_trials','total_seconds']} for n,r in results.items()},
        'half_training':{k:half[k] for k in ['train_rows','test_rows','sample_fraction','n_evaluations','cv_jobs']}}
    (out/'linux-smoke-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
