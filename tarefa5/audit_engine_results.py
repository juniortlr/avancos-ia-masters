"""Independent delivery audit: recompute saved predictions and winning CV fits."""
from pathlib import Path
import json
import math
import sys
import time
import numpy as np
import pandas as pd
import joblib
from sklearn.base import clone
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
EXPECTED = {'baseline':1,'grid':36,'random':30,'gp_manual':15,'bayessearch':40,
            'bayesopt':40,'optuna':40,'hyperopt':40,'ray':40,'pso_w07':320,
            'pso_w04':320,'pso_w09':320}

def main():
    started = time.perf_counter()
    z = np.load(ROOT/'data/prepared.npz', allow_pickle=False)
    tr, te = z['train_ids'], z['test_ids']
    folds = [(z[f'fold_{i}_train'], z[f'fold_{i}_valid']) for i in range(5)]
    assert not set(tr)&set(te)
    assert np.array_equal(np.sort(np.concatenate([v for _,v in folds])), np.arange(len(tr)))
    results=[]
    for folder in sorted((ROOT/'results').glob('*/seed_42')):
        if not (folder/'result.json').exists():
            continue
        r=json.loads((folder/'result.json').read_text(encoding='utf8'))
        assert r['status']=='complete', (folder, r.get('error'))
        m=r['method']
        trials=pd.read_csv(folder/'trials.csv')
        saved=pd.read_csv(folder/'predictions.csv')
        model=joblib.load(folder/'model.joblib')
        assert np.array_equal(saved.source_row.to_numpy(), z['source_ids'][te]), m
        assert np.allclose(saved.y_true,z['y'][te],rtol=0,atol=1e-12), m
        prediction=model.predict(z['X'][te])
        assert np.allclose(prediction,saved.y_pred,rtol=0,atol=1e-9), m
        metrics={'test_rmse':math.sqrt(mean_squared_error(saved.y_true,prediction)),
                 'test_mae':mean_absolute_error(saved.y_true,prediction),
                 'test_r2':r2_score(saved.y_true,prediction)}
        for k,v in metrics.items():
            assert math.isclose(v,r[k],rel_tol=0,abs_tol=1e-9),(m,k,v,r[k])
        assert len(trials)==r['n_evaluations'],m
        if m in EXPECTED:
            assert len(trials)==EXPECTED[m], (m,len(trials))
        eligible=trials[(trials.status=='complete')&(trials.resource>=1)]
        best=eligible.loc[eligible.cv_rmse.idxmin()]
        for hp in ['learning_rate','subsample','n_estimators']:
            assert math.isclose(float(model.named_steps['model'].get_params()[hp]),float(best[hp]),abs_tol=1e-10),(m,hp)
        with threadpool_limits(1),joblib.parallel_config(backend='loky',n_jobs=5,inner_max_num_threads=1):
            cv=-cross_val_score(clone(model),z['X'][tr],z['y'][tr],cv=folds,
                                scoring='neg_root_mean_squared_error',n_jobs=5,error_score='raise')
        assert math.isclose(cv.mean(),r['cv_rmse'],rel_tol=0,abs_tol=1e-8),(m,cv.mean(),r['cv_rmse'])
        results.append({'method':m,'predictions_match_model':True,'test_metrics_recomputed':True,
                        'winning_cv_recomputed':float(cv.mean()),'recorded_cv':r['cv_rmse']})
        print(f'Audited {m}: CV={cv.mean():.8f}',flush=True)
    assert len(results)==15, f'Expected15 methods and variants; got{len(results)}'
    robustness=pd.read_csv(ROOT/'results/robustness.csv')
    for m,rows in robustness.groupby('method'):
        assert set(rows.seed)=={0,7,21,42,99},m
        for row in rows.itertuples():
            r=json.loads((ROOT/f'results/{m}/seed_{row.seed}/result.json').read_text(encoding='utf8'))
            assert math.isclose(r['test_rmse'],row.test_rmse,abs_tol=1e-10)
    all_results={'status':'passed','checks':results,'robustness_seeds_verified':True,
                 'seconds':time.perf_counter()-started,
                 'scope':'AI-assisted independent recomputation of artifact consistency; not human peer review or validation of generalization.'}
    (ROOT/'results/independent-audit.json').write_text(json.dumps(all_results,indent=2),encoding='utf8')
    print(json.dumps({'audit':'passed','methods':len(results)}),flush=True)

if __name__=='__main__':
    main()
