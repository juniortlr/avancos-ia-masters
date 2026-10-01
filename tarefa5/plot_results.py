"""Reconstruct exact figures and an analysis ledger from saved experimental evidence.

Run after experiment.py has produced results. This module never fits/tunes a model.
Figures use source CSV/NPZ values, not illustrative or fabricated observations.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import textwrap
import warnings
import numpy as np
import pandas as pd
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent / '.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
from scipy.stats import spearmanr, shapiro

ROOT = Path(__file__).resolve().parent
LABELS = {
    'baseline': 'Baseline', 'grid': 'Grid', 'random': 'Random',
    'gp_manual': 'GP manual', 'bayessearch': 'skopt EI', 'bayesopt': 'bayes_opt UCB',
    'optuna': 'Optuna TPE', 'hyperopt': 'Hyperopt TPE', 'ray': 'Ray + ASHA',
    'ga': 'GA', 'de_best1bin': 'DE best1bin', 'de_rand1bin': 'DE rand1bin',
    'pso_w07': 'PSO w=0,7', 'pso_w04': 'PSO w=0,4', 'pso_w09': 'PSO w=0,9',
}
ORDER = list(LABELS)
MAIN = [m for m in ORDER if m not in ('de_rand1bin','pso_w04','pso_w09')]
HP = ['learning_rate','subsample','n_estimators']
COLORS = dict(zip(ORDER, plt.get_cmap('tab20').colors[:len(ORDER)]))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12, 'axes.spines.top':False,
                     'axes.spines.right':False,'figure.dpi':130, 'savefig.dpi':180})


def clean_json(value):
    if isinstance(value,dict): return {str(k):clean_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)): return [clean_json(v) for v in value]
    if isinstance(value,(np.integer,)): return int(value)
    if isinstance(value,(np.floating,)): value=float(value)
    if isinstance(value,float) and not np.isfinite(value): return None
    if isinstance(value,Path): return str(value)
    return value


def save(fig,name,out):
    fig.savefig(out / f'{name}.png', bbox_inches='tight', facecolor='white')
    fig.savefig(out / f'{name}.pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)


def read_trials(base,method):
    p=base/method/'seed_42'/'trials.csv'
    if not p.exists(): return pd.DataFrame()
    return pd.read_csv(p)


def full_trials(t):
    if t.empty: return t
    if 'status' in t:
        complete=t['status'].astype(str).str.lower().isin(['complete','completed','ok','success'])
        if complete.any(): t=t[complete]
    return t[t.cv_rmse.notna()]


def pareto_mask(values):
    a=np.asarray(values,float)
    # Ties remain together: strict improvement in >=1 objective is required.
    return np.array([not np.any(np.all(a<=row,axis=1)&np.any(a<row,axis=1)) for row in a])


def norm_benefit(v,maximize=True):
    a=np.asarray(v,float)
    d=np.ptp(a)
    if d==0: return np.ones(len(a))
    z=(a-a.min())/d
    return z if maximize else 1-z


def convergence(base,methods,out,name,title):
    fig,ax=plt.subplots(figsize=(9,4.6))
    for m in methods:
        t=full_trials(read_trials(base,m))
        if t.empty: continue
        x=t['trial'].to_numpy() if 'trial' in t else np.arange(1,len(t)+1)
        if len(x) and min(x)==0: x=x+1
        ax.step(x,np.minimum.accumulate(t.cv_rmse),where='post',label=LABELS[m],color=COLORS[m])
    ax.set(xlabel='Candidatos avaliados (ordem registrada)',ylabel='Melhor RMSE CV acumulado (MPa)',title=title)
    ax.grid(alpha=.2);ax.legend(fontsize=11,ncol=2)
    save(fig,name,out)


def find_data(root):
    for name in ('clean.csv','data_clean.csv','clean_data.csv','concrete_clean.csv','dataset_clean.csv','cleaned.csv'):
        p=root/'data'/name
        if p.exists(): return pd.read_csv(p)
    candidates=list((root/'data').glob('*.csv'))
    for p in candidates:
        if any(x in p.name for x in ['raw','concrete','dataset']):
            d=pd.read_csv(p)
            if d.shape[1]>=9: return d.drop_duplicates()
    return None


def feature_overlap(root,analysis):
    p=root/'data'/'prepared.npz'
    if not p.exists():return
    with np.load(p) as z:
        X=z['X'];y=z['y'];train=z['train_ids'];test=z['test_ids'];features=z['feature_names'].tolist()
    train_keys={tuple(X[i]) for i in train};test_keys={tuple(X[i]) for i in test}
    shared=train_keys & test_keys
    rows=[]
    for key in sorted(shared):
        tr=[int(i) for i in train if tuple(X[i])==key];te=[int(i) for i in test if tuple(X[i])==key]
        rows.append({**dict(zip(features,key)),'train_rows':len(tr),'test_rows':len(te),'distinct_targets':int(len(set(y[tr+te]))),'train_row_ids':json.dumps(tr),'test_row_ids':json.dumps(te)})
    pd.DataFrame(rows).to_csv(root/'results'/'feature_overlap.csv',index=False)
    analysis['feature_overlap']={'shared_unique_feature_vectors':len(shared),'train_rows_in_shared_vectors':sum(r['train_rows'] for r in rows),'test_rows_in_shared_vectors':sum(r['test_rows'] for r in rows),'rows':rows,'limitation':'Random row split evaluates held-out observations, not unseen mixtures; exact duplicate X+y rows were removed but equal X with differing targets remain.'}


def plot_eda(root,out,analysis):
    d=find_data(root)
    if d is None:
        analysis['eda_status']='missing_data_csv';return
    # Only development observations enter exploratory plots. Whole-data diagnostics
    # remain available in the source-generated describe_raw/quality-summary files.
    prepared=root/'data'/'prepared.npz'
    if prepared.exists():
        with np.load(prepared) as z: d=d.iloc[z['train_ids']].copy()
    for c in list(d):
        if c.lower() in ['row_id','source_row','index'] or c.startswith('Unnamed:'): d=d.drop(columns=c)
    target=next((c for c in d if c.lower() in ['target','target_mpa','y','strength','concrete_compressive_strength']),d.columns[-1])
    numeric=d.select_dtypes('number')
    analysis['data_summary']={'shape':list(d.shape),'target':target,'dtypes':d.dtypes.astype(str).to_dict(),
        'missing_fraction':d.isna().mean().to_dict(),'describe':d.describe().to_dict()}
    d.describe().to_csv(root/'results'/'descriptive_statistics.csv')
    pd.DataFrame({'dtype':d.dtypes.astype(str),'missing_fraction':d.isna().mean()}).to_csv(root/'results'/'data_quality.csv')
    corr=numeric.corr()
    feature=corr[target].drop(target).abs().idxmax()
    analysis['eda_scatter_feature']=feature
    analysis['eda_scatter_correlation']=float(corr.loc[feature,target])
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    axes[0].hist(d[target],bins=28,color='#367da0',edgecolor='white')
    axes[0].set(xlabel='Resistência à compressão (MPa)',ylabel='Observações',title='Distribuição do alvo')
    axes[1].scatter(d[feature],d[target],s=12,alpha=.4,color='#287784')
    feature_unit='dias' if feature=='Age' else 'kg/m³'
    axes[1].set(xlabel=f'{feature} ({feature_unit})',ylabel='Resistência à compressão (MPa)',title='Associação descritiva; não causal')
    fig.tight_layout();save(fig,'01_eda_distributions',out)
    labels=[textwrap.fill(str(c),18) for c in corr]
    fig,ax=plt.subplots(figsize=(10,8))
    im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r')
    ax.set_xticks(range(len(corr)),labels,rotation=45,ha='right',fontsize=11)
    ax.set_yticks(range(len(corr)),labels,fontsize=11)
    for i in range(len(corr)):
        for j in range(len(corr)): ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',fontsize=11,color='white' if abs(corr.iloc[i,j])>.7 else 'black')
    fig.colorbar(im,ax=ax,shrink=.7,label='Correlação de Pearson')
    ax.set_title('Correlação no treino após remoção de duplicatas exatas')
    save(fig,'02_eda_correlations',out)


def prediction_columns(p):
    y=next((c for c in ('y_true','actual','y_test','target','y') if c in p),None)
    yh=next((c for c in ('y_pred','predicted','prediction','yhat') if c in p),None)
    if y is None or yh is None: raise ValueError(f'Unexpected predictions columns: {list(p)}')
    return p[y].to_numpy(),p[yh].to_numpy()


def predictions(base,method,out,name,analysis,diagnostic=False):
    p=base/method/'seed_42'/'predictions.csv'
    if not p.exists(): return
    y,yh=prediction_columns(pd.read_csv(p));r=y-yh
    fig,axes=plt.subplots(1,2 if diagnostic else 1,figsize=(10,4.2) if diagnostic else (5.5,4.6))
    ax=axes[0] if diagnostic else axes
    ax.scatter(y,yh,s=18,alpha=.6,c='#287784')
    lo=min(y.min(),yh.min());hi=max(y.max(),yh.max())
    ax.plot([lo,hi],[lo,hi],'k--',lw=1)
    ax.set(xlabel='Resistência real (MPa)',ylabel='Resistência prevista (MPa)',title=LABELS[method]+' — holdout')
    if diagnostic:
        stat,pv=shapiro(r)
        analysis['residuals']={'method':method,'n':len(r),'shapiro_W':float(stat),'shapiro_p':float(pv),'mean':float(r.mean()),'std_ddof1':float(r.std(ddof=1))}
        axes[1].hist(r,bins=24,color='#367da0',edgecolor='white')
        axes[1].axvline(0,c='black',ls='--',lw=1)
        axes[1].set(xlabel='Resíduo: real − previsto (MPa)',ylabel='Observações',title=f'Shapiro–Wilk: W={stat:.3f}; p={pv:.3g}')
    fig.tight_layout();save(fig,name,out)
    fi=base/method/'seed_42'/'feature_importance.csv'
    if diagnostic and fi.exists():
        f=pd.read_csv(fi)
        fc=next((c for c in ['feature','variable','name'] if c in f),f.columns[0]);vc=next((c for c in ['importance','value'] if c in f),f.columns[1])
        f=f.sort_values(vc)
        analysis['feature_importance']=f.to_dict('records')
        fig,ax=plt.subplots(figsize=(8,4.8))
        ax.barh(f[fc],f[vc],color='#367da0')
        ax.set(xlabel='Importância por redução de impureza (soma = 1)',title=LABELS[method]+' — importância no modelo final')
        save(fig,'16_feature_importance',out)


def grid_analysis(base,out,analysis):
    g=full_trials(read_trials(base,'grid'));r=full_trials(read_trials(base,'random'))
    if g.empty or r.empty:return
    optimum=g.loc[g.cv_rmse.idxmin()];n=int(optimum.n_estimators)
    h=g[np.isclose(g.n_estimators,n)].pivot_table(index='learning_rate',columns='subsample',values='cv_rmse',aggfunc='mean').sort_index()
    fig,ax=plt.subplots(figsize=(6.2,4.6))
    im=ax.imshow(h,cmap='viridis_r',aspect='auto')
    ax.set_xticks(range(len(h.columns)),[f'{v:.1f}' for v in h.columns]);ax.set_yticks(range(len(h)),[f'{v:g}' for v in h.index])
    for i in range(h.shape[0]):
        for j in range(h.shape[1]):ax.text(j,i,f'{h.iloc[i,j]:.3f}',ha='center',va='center',color='white' if h.iloc[i,j]>np.nanmedian(h.values) else 'black')
    ax.set(xlabel='subsample',ylabel='learning_rate',title=f'RMSE CV (MPa), n_estimators = {n}')
    fig.colorbar(im,ax=ax,label='RMSE CV (menor é melhor)');save(fig,'05_grid_heatmap',out)
    spearman=[]
    for hp in HP:
        rho,p=spearmanr(r[hp],r.cv_rmse)
        spearman.append({'hyperparameter':hp,'rho':float(rho),'p_exploratory':float(p),'n':len(r)})
    eq=np.flatnonzero(np.minimum.accumulate(r.cv_rmse.to_numpy())<=float(optimum.cv_rmse)+1e-10)
    gbest=g.loc[g.cv_rmse.idxmin(),HP].to_dict();rbest=r.loc[r.cv_rmse.idxmin(),HP].to_dict()
    # Difference of LR endpoints at every subsample: an observed discrete interaction summary.
    slopes=(h.iloc[-1]-h.iloc[0]).to_dict()
    analysis['grid_random']={'grid_best_cv_rmse':float(optimum.cv_rmse),'random_best_cv_rmse':float(r.cv_rmse.min()),
        'random_first_match_evaluation':int(eq[0]+1) if len(eq) else None,
        'grid_best_params':gbest,'random_best_params':rbest,'heatmap_fixed_n_estimators':n,
        'heatmap':{'learning_rate':list(h.index),'subsample':list(h.columns),'cv_rmse':h.values.tolist()},
        'endpoint_lr_effect_by_subsample':slopes,'spearman':spearman,
        'spearman_most_associated':max(spearman,key=lambda v:abs(v['rho']))['hyperparameter']}
    pd.DataFrame(spearman).to_csv(base/'random_spearman.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,3.7))
    ax.barh([v['hyperparameter'] for v in spearman],[v['rho'] for v in spearman],color=['#367da0' if v['rho']<0 else '#d47951' for v in spearman]);ax.axvline(0,color='black',lw=.8)
    ax.set(xlim=(-1,1),xlabel='Spearman com RMSE CV positivo',title='Random: associação marginal entre HP e erro')
    save(fig,'06_random_spearman',out)


def gp_figures(base,out,analysis):
    fs=sorted((base/'gp_manual'/'seed_42').glob('gp_snapshot_*.npz'))
    records=[]
    for i,p in enumerate(fs,1):
        z=np.load(p);grid=z['grid_u'];mu=z['mu'];sigma=z['sigma'];ei=z['ei'];obs=z['observed_u'];y=z['observed_y'];nxt=z['next_u'].reshape(2)
        n=int(round(np.sqrt(len(grid))))
        lr=.03*(.2/.03)**grid[:,0];ss=.6+.4*grid[:,1];xnext=.03*(.2/.03)**nxt[0];snext=.6+.4*nxt[1]
        if 'slice_u' in z:
            su=z['slice_u'];sm=z['slice_mu'];sd=z['slice_sigma'];se=z['slice_ei'];slice_note='corte exato'
        else:
            nearest=np.unique(grid[:,1])[np.argmin(abs(np.unique(grid[:,1])-nxt[1]))]
            mask=np.isclose(grid[:,1],nearest);su=grid[mask];sm=mu[mask];sd=sigma[mask];se=ei[mask];slice_note='corte na grade mais próxima'
        sort=np.argsort(su[:,0]);sx=.03*(.2/.03)**su[sort,0];sm=sm[sort];sd=sd[sort];se=se[sort]
        fig,axes=plt.subplots(2,2,figsize=(12,8))
        # Grid coordinates may be flattened in either meshgrid order; triangulation avoids assumed reshape.
        cm=axes[0,0].tricontourf(lr,ss,mu,levels=20,cmap='viridis_r')
        axes[0,0].scatter(.03*(.2/.03)**obs[:,0],.6+.4*obs[:,1],s=22,c='white',edgecolors='black',lw=.5,clip_on=False,zorder=4)
        axes[0,0].scatter([xnext],[snext],marker='*',s=130,c='#ff593f',edgecolors='black',label='Próximo ponto',clip_on=False,zorder=5)
        axes[0,0].axhline(snext,c='red',ls=':',lw=1);axes[0,0].legend(fontsize=13,loc='lower left')
        axes[0,0].set(xlabel='learning_rate (log)',ylabel='subsample',title='Média posterior (MPa)');axes[0,0].set_xscale('log')
        cb=fig.colorbar(cm,ax=axes[0,0]);cb.ax.tick_params(labelsize=13)
        cs=axes[0,1].tricontourf(lr,ss,sigma,levels=20,cmap='magma')
        axes[0,1].set(xlabel='learning_rate (log)',ylabel='subsample',title='Desvio padrão posterior (MPa)');axes[0,1].set_xscale('log')
        cb=fig.colorbar(cs,ax=axes[0,1]);cb.ax.tick_params(labelsize=13)
        axes[1,0].plot(sx,sm,c='#16788a',label='Média GP')
        axes[1,0].fill_between(sx,sm-2*sd,sm+2*sd,alpha=.2,color='#16788a',label='Média ± 2σ')
        on_slice=np.isclose(obs[:,1],nxt[1],rtol=0,atol=1e-10)
        if on_slice.any(): axes[1,0].scatter(.03*(.2/.03)**obs[on_slice,0],y[on_slice],marker='x',s=30,c='black',label='Observações neste corte')
        axes[1,0].axvline(xnext,c='#d34b32',ls='--',lw=1)
        axes[1,0].set_xscale('log');axes[1,0].set(xlabel='learning_rate (log)',ylabel='RMSE CV (MPa)',title=f'{slice_note}; subsample = {snext:.4f}')
        axes[1,0].legend(fontsize=13)
        axes[1,1].plot(sx,se,c='#7d5193');axes[1,1].axvline(xnext,c='#d34b32',ls='--',label='Próximo LR')
        axes[1,1].scatter([xnext],[float(z['next_ei']) if 'next_ei' in z else float(np.interp(xnext,sx,se))],c='#d34b32',s=45)
        axes[1,1].set_xscale('log');axes[1,1].set(xlabel='learning_rate (log)',ylabel='Expected Improvement (MPa)',title='EI no mesmo corte');axes[1,1].legend(fontsize=13)
        for ax in axes.ravel():
            ax.tick_params(axis='both',which='both',labelsize=14)
            ax.xaxis.label.set_size(14);ax.yaxis.label.set_size(14);ax.title.set_size(16)
            ax.xaxis.set_major_locator(FixedLocator([.03,.06,.1,.2]))
            ax.xaxis.set_major_formatter(FixedFormatter(['0,03','0,06','0,10','0,20']))
            ax.xaxis.set_minor_locator(NullLocator())
        fig.suptitle(f'GP manual — aquisição {i}/10; {len(obs)} observações anteriores',fontsize=18)
        fig.text(.5,.012,'Observações no mapa 2D; somente as do mesmo subsample entram no corte. n_estimators = 100.',ha='center',fontsize=14)
        fig.tight_layout(rect=(0,.035,1,.96));save(fig,f'gp_iteration_{i:02d}',out)
        records.append({'iteration':i,'n_previous':len(obs),'mean_sigma':float(np.mean(sigma)), 'max_ei':float(np.max(ei)),'previous_best_rmse':float(np.min(y)), 'next_learning_rate':float(xnext),'next_subsample':float(snext)})
    analysis['gp_iterations']=records
    if records:pd.DataFrame(records).to_csv(base/'gp_diagnostics.csv',index=False)


def evolutionary_figures(base,out,analysis):
    p=base/'ga'/'seed_42'/'generations.csv'
    if p.exists():
        g=pd.read_csv(p);analysis['ga_generations']=g.to_dict('records')
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        axes[0].plot(g.generation,g.best,'o-',label='Mínimo corrente');axes[0].plot(g.generation,g['mean'],'o-',label='Média corrente')
        axes[0].set(xlabel='Geração (0 = inicial)',ylabel='RMSE CV (MPa)',title='GA: fitness da população');axes[0].legend()
        axes[1].plot(g.generation,g.diversity,'o-',color='#82589b');axes[1].set(xlabel='Geração',ylabel='Proporção de genótipos distintos',title='GA: diversidade registrada')
        fig.tight_layout();save(fig,'09_ga_generations',out)
    convergence(base,['de_best1bin','de_rand1bin'],out,'10_de_convergence','Evolução diferencial: estratégias')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    trajectories={}
    for m in ['pso_w04','pso_w07','pso_w09']:
        p=base/m/'seed_42'/'generations.csv'
        if not p.exists():continue
        g=pd.read_csv(p);trajectories[m]=g.to_dict('records')
        axes[0].plot(g.generation,g.best,'o-',ms=3,label=LABELS[m],color=COLORS[m]);axes[1].plot(g.generation,g['mean'],'o-',ms=3,label=LABELS[m],color=COLORS[m])
    for ax in axes:ax.set(xlabel='Atualização (0 = inicial)',ylabel='RMSE CV (MPa)');ax.legend(fontsize=11);ax.grid(alpha=.2)
    axes[0].set_title('PSO: gbest acumulado');axes[1].set_title('PSO: fitness médio do enxame corrente')
    fig.tight_layout();save(fig,'11_pso_inertia',out);analysis['pso_generations']=trajectories


def comparative_figures(metrics,out,analysis):
    m=metrics.set_index('method')
    fig,ax=plt.subplots(figsize=(9.5,6.8));ax.axis('off')
    cols=['cv_rmse','test_rmse','test_mae','test_r2','total_seconds','n_evaluations']
    present=[c for c in cols if c in m]
    headers={'cv_rmse':'CV RMSE','test_rmse':'Teste RMSE','test_mae':'Teste MAE','test_r2':'Teste R²','total_seconds':'Tempo (s)','n_evaluations':'Avaliações'}
    values=[[LABELS.get(k,k)]+[f'{row[c]:.3f}' if c!='n_evaluations' else str(int(row[c])) for c in present] for k,row in m.iterrows()]
    table=ax.table(cellText=values,colLabels=['Método']+[headers[c] for c in present],loc='center',cellLoc='center',colWidths=[.23]+[.125]*len(present))
    table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,1.65)
    for j in range(len(present)+1):table[(0,j)].set_facecolor('#1c4a61');table[(0,j)].get_text().set_color('white')
    for j,c in enumerate(present,1):
        if c=='n_evaluations':continue
        best=m[c].max() if c=='test_r2' else m[c].min()
        for i,v in enumerate(m[c],1):
            if np.isclose(v,best,rtol=1e-10,atol=1e-12):table[(i,j)].set_facecolor('#fff2b0' if c=='total_seconds' else '#bbdfb5')
    ax.set_title('Comparação no mesmo holdout — RMSE/MAE em MPa',pad=10,fontsize=14)
    fig.text(.5,.04,'Verde: melhor métrica; amarelo: menor tempo total. Avaliações completas/parciais e custo CV detalhados nas tabelas auxiliares.',ha='center',fontsize=9)
    save(fig,'12_comparison_table',out)
    r=m.loc[[k for k in MAIN if k in m.index]]
    time=np.maximum(r.total_seconds.to_numpy(),np.finfo(float).tiny)
    z=np.column_stack([norm_benefit(r.test_rmse,False),norm_benefit(r.test_mae,False),norm_benefit(r.test_r2),norm_benefit(1/time)])
    angles=np.linspace(0,2*np.pi,4,endpoint=False);angles=np.r_[angles,angles[0]]
    fig,ax=plt.subplots(figsize=(8.4,7.2),subplot_kw={'projection':'polar'})
    fig.subplots_adjust(left=.12,right=.88,bottom=.26,top=.81)
    for i,k in enumerate(r.index):ax.plot(angles,np.r_[z[i],z[i,0]],lw=1.3,alpha=.9,label=LABELS[k],color=COLORS[k])
    ax.set_xticks(angles[:-1],['RMSE\ninvertido','MAE\ninvertido','R²','1 / tempo']);ax.set_ylim(0,1);ax.set_yticks([0,.25,.5,.75,1]);ax.set_title('Radar dos 12 métodos principais\nTodos os eixos: maior = melhor',pad=25)
    ax.tick_params(axis='x',pad=18)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.025),ncol=3,fontsize=10)
    fig.text(.5,.004,'Min-max entre os métodos exibidos; escala relativa, sem interpretação absoluta.',ha='center',fontsize=9)
    save(fig,'13_radar',out)
    analysis['radar']={'methods':list(r.index),'axes':['rmse_benefit','mae_benefit','r2_benefit','inverse_time_benefit'],'values':z.tolist()}
    pareto=pareto_mask(m[['test_rmse','total_seconds']]);analysis['pareto_methods']=m.index[pareto].tolist()
    fig,ax=plt.subplots(figsize=(10.5,6))
    offsets={'baseline':(-78,9),'grid':(10,10),'random':(-48,-18),'gp_manual':(10,-13),
             'bayessearch':(12,8),'bayesopt':(-64,3),'optuna':(-55,-14),'hyperopt':(10,9),
             'ray':(10,8),'ga':(15,-2),'de_best1bin':(25,24),'de_rand1bin':(-48,24),
             'pso_w07':(24,-20),'pso_w04':(-55,-33),'pso_w09':(20,13)}
    for i,(k,row) in enumerate(m.iterrows()):
        ax.scatter(row.test_rmse,row.total_seconds,c=[COLORS.get(k,'gray')],s=85,edgecolors='black' if pareto[i] else 'none',linewidth=1.8 if pareto[i] else 0,marker='D' if pareto[i] else 'o')
        ax.annotate(LABELS.get(k,k),(row.test_rmse,row.total_seconds),xytext=offsets.get(k,(6,8)),textcoords='offset points',fontsize=12,arrowprops={'arrowstyle':'-','color':'#999999','linewidth':.6})
    frontier=m.loc[pareto].sort_values('test_rmse')
    ax.plot(frontier.test_rmse,frontier.total_seconds,'k--',alpha=.4,lw=1)
    ax.set_yscale('log');ax.set(xlabel='RMSE no teste (MPa; menor = melhor)',ylabel='Tempo total (s; escala log; menor = melhor)',title='Qualidade × custo — losangos: fronteira de Pareto')
    ax.margins(x=.15,y=.13);ax.grid(alpha=.2);save(fig,'14_pareto',out)


def supplemental(base,out,analysis,include_robustness=True):
    p=base/'robustness.csv'
    if p.exists() and include_robustness:
        all_rows=pd.read_csv(p)
        analysis['robustness_by_method']={str(k):{'rows':v.to_dict('records'),'mean_rmse':float(v.test_rmse.mean()),'std_rmse_ddof1':float(v.test_rmse.std(ddof=1)),'min_rmse':float(v.test_rmse.min()),'max_rmse':float(v.test_rmse.max())} for k,v in all_rows.groupby('method')}
        d=all_rows[all_rows.method==analysis['best_test_method']].copy()
        analysis['robustness']=analysis['robustness_by_method'][analysis['best_test_method']]
        fig,ax=plt.subplots(figsize=(7.5,4))
        ax.bar(d.seed.astype(str),d.test_rmse,color='#367da0');ax.axhline(d.test_rmse.mean(),ls='--',c='#d47951',label=f'Média = {d.test_rmse.mean():.3f} MPa')
        ax.set(xlabel='Seed do procedimento HPO e modelo',ylabel='RMSE no mesmo holdout (MPa)',title=f'{LABELS[analysis["best_test_method"]]} — robustez: SD = {d.test_rmse.std(ddof=1):.3f} MPa');ax.legend()
        save(fig,'17_robustness',out)
    p=base/'optuna_importances.csv'
    if p.exists():
        d=pd.read_csv(p);d['training_fraction']=1.0
        p_half=base/'sample50'/'optuna'/'seed_42'/'optuna_importances.csv'
        if p_half.exists():
            half=pd.read_csv(p_half);half['training_fraction']=.5;d=pd.concat([d,half],ignore_index=True)
        analysis['optuna_importances']=d.to_dict('records')
        fc=next((c for c in ['hyperparameter','parameter','param'] if c in d),None)
        vc=next((c for c in ['importance','value'] if c in d),None)
        group=next((c for c in ['dataset','sample','training_fraction','scope','run'] if c in d),None)
        if fc and vc:
            fig,ax=plt.subplots(figsize=(8,4))
            if group:
                pivot=d.pivot_table(index=fc,columns=group,values=vc)
                if group=='training_fraction':pivot.columns=[f'{100*float(v):.0f}% do treino' for v in pivot.columns]
                pivot.plot.bar(ax=ax,rot=0);ax.legend(title='Dados usados')
            else:ax.bar(d[fc],d[vc],color='#367da0')
            ax.set(xlabel='Hiperparâmetro',ylabel='Importância relativa Optuna',title='Importância estimada por resultados da busca')
            save(fig,'18_optuna_importances',out)
    p=base/'sample-comparison.csv'
    if p.exists():analysis['sample_comparison']=pd.read_csv(p).to_dict('records')


def narrative(analysis,metrics):
    m=metrics.set_index('method');base=m.loc['baseline'];winner=m.loc[analysis['best_test_method']]
    gain=100*(base.test_rmse-winner.test_rmse)/base.test_rmse
    texts={
      'scope':'Comparação exploratória em um único holdout do UCI 165. A seleção por teste exigida pela atividade impede interpretar o vencedor como confirmação independente. Nenhum parâmetro foi retunado em função do teste.',
      'baseline_gain':f'O baseline apresentou RMSE de {base.test_rmse:.4f} MPa. O menor RMSE de teste foi {winner.test_rmse:.4f} MPa ({LABELS[analysis["best_test_method"]]}), redução descritiva de {gain:.2f}%. O custo total foi {winner.total_seconds:.3f} s contra {base.total_seconds:.3f} s; relevância industrial exige uma tolerância externa ao estudo.',
      'grid_preference':'Grid é útil quando há poucos hiperparâmetros, domínios discretos pequenos e necessidade de cobertura exaustiva e auditável. O número de combinações cresce multiplicativamente; a vantagem não é geral em dimensões maiores.',
      'spaces':'Grid e Random usam exatamente a mesma grade. Os demais métodos compartilham os limites, porém incluem candidatos contínuos ou quantizados; a comparação mistura estratégia, resolução e budget, portanto não isola o efeito causal do otimizador.',
      'uncertainty':'Os cinco folds orientam a seleção e não são cinco datasets independentes. As cinco seeds medem sensibilidade computacional no mesmo holdout, não incerteza completa de generalização. Não se conclui superioridade estatística universal.',
      'feature_importance':'A importância das features por redução de impureza descreve o modelo ajustado; não mede causalidade. Preditores correlacionados podem redistribuir a importância.',
    }
    overlap=analysis.get('feature_overlap')
    if overlap:
        texts['feature_overlap']=f'A auditoria encontrou {overlap["shared_unique_feature_vectors"]} vetores distintos de oito features presentes em treino e teste, envolvendo {overlap["train_rows_in_shared_vectors"]} linhas de treino e {overlap["test_rows_in_shared_vectors"]} de teste. Os alvos diferem, portanto essas linhas não eram duplicatas exatas de X+y. Mantivemos o split predefinido; o resultado descreve generalização para observações reservadas, não desempenho garantido em misturas inéditas. Uma avaliação por grupos de composição/idade seria necessária para essa outra pergunta.'
    gr=analysis.get('grid_random',{})
    if gr:
        eq=gr['random_first_match_evaluation']
        texts['random_vs_grid']=(f'Random igualou o ótimo CV da grade na avaliação {eq}.' if eq else 'Random não atingiu o ótimo CV da grade nas 30 avaliações.')+' Ele não pode superá-lo estritamente, pois amostra um subconjunto dos mesmos 36 candidatos sob folds e seed idênticos.'
        strongest=max(gr['spearman'],key=lambda v:abs(v['rho']))
        texts['spearman']=f'A maior associação marginal absoluta foi de {strongest["hyperparameter"]} (rho={strongest["rho"]:.3f}) com RMSE CV positivo. Sinal negativo associa valores maiores a erros menores. Correlação marginal não separa interações e não prova causalidade ou importância global.'
        effects=gr['endpoint_lr_effect_by_subsample']
        texts['heatmap']='No corte n_estimators='+str(gr['heatmap_fixed_n_estimators'])+', a mudança LR0,03→0,20 altera o RMSE em '+', '.join(f'{float(v):+.3f} MPa em subsample={k}' for k,v in effects.items())+'. Efeitos diferentes sugerem interação no conjunto discretizado; nove pontos não permitem demonstrar suavidade nem mapear todos os ótimos locais contínuos.'
    gp=analysis.get('gp_iterations',[])
    if gp:
        texts['gp']=f'A incerteza média posterior na malha passou de {gp[0]["mean_sigma"]:.4f} para {gp[-1]["mean_sigma"]:.4f} MPa entre os posteriors anterior à primeira e à décima aquisição. A mudança pode não ser monotônica, pois o kernel é reajustado. O melhor RMSE já observado nesses instantes passou de {gp[0]["previous_best_rmse"]:.4f} a {gp[-1]["previous_best_rmse"]:.4f} MPa. EI combina redução esperada do erro e incerteza; a maximização é aproximada na malha de 61 × 61 pontos, com xi = 0,01 MPa fixo. Não há garantia de ótimo global em 15 avaliações; o corte com 201 pontos apenas visualiza o posterior.'
    ga=analysis.get('ga_generations',[])
    if ga:
        best_ever=np.minimum.accumulate([r['best'] for r in ga]);improved=np.flatnonzero(np.diff(best_ever)<-1e-10)+1
        last=int(ga[int(improved[-1])]['generation']) if len(improved) else int(ga[0]['generation'])
        stagnant=int(ga[-1]['generation'])-last
        longest=run=0;end=None
        for i,change in enumerate(np.diff(best_ever),1):
            run=run+1 if change>=-1e-10 else 0
            if run>longest:longest=run;end=int(ga[i]['generation'])
        start=end-longest+1 if end is not None else None
        final_gain=float(best_ever[-2]-best_ever[-1]) if len(best_ever)>1 else 0.
        analysis['ga_summary']={'last_improvement_generation':last,'final_stagnant_generations':stagnant,'longest_stagnation_generations':longest,'longest_stagnation_from_generation':start,'longest_stagnation_through_generation':end,'final_generation_improvement_mpa':final_gain,'initial_diversity':ga[0]['diversity'],'final_diversity':ga[-1]['diversity']}
        texts['ga']=f'GA: diversidade registrada de {ga[0]["diversity"]:.4f} para {ga[-1]["diversity"]:.4f}, e melhor fitness corrente de {ga[0]["best"]:.4f} para {ga[-1]["best"]:.4f} MPa. O maior intervalo sem nova melhoria acumulada foi de {longest} gerações (da {start} à {end}); a melhoria na última geração foi de apenas {final_gain:.6f} MPa. Contração de diversidade com estagnação sugere risco de convergência prematura, mas não prova um ótimo local nem demonstra distância ao ótimo global desconhecido.'
    pso=analysis.get('pso_generations',{})
    if pso:
        texts['pso']='Melhor RMSE CV final por inércia: '+', '.join(f'{LABELS[k]}={v[-1]["best"]:.4f} MPa' for k,v in pso.items())+'. A média é calculada com fitness do enxame corrente. Uma seed por inércia não sustenta recomendação universal sobre w.'
    if 'de_best1bin' in m.index and 'de_rand1bin' in m.index:
        de1=m.loc['de_best1bin'];de2=m.loc['de_rand1bin']
        texts['de']=f'DE best1bin retornou RMSE CV {de1.cv_rmse:.4f} MPa em {int(de1.n_evaluations)} avaliações; rand1bin, {de2.cv_rmse:.4f} MPa em {int(de2.n_evaluations)}. Tempos totais: {de1.total_seconds:.3f} s e {de2.total_seconds:.3f} s. A curva explicita diferenças de rapidez e patamares; o término segue a tolerância padrão do SciPy ou maxiter = 15. A estratégia best1bin é orientada pelo melhor indivíduo corrente; rand1bin preserva uma base aleatória. Uma execução por estratégia não demonstra superioridade universal.'
    imports=analysis.get('optuna_importances',[])
    if imports:
        idf=pd.DataFrame(imports)
        leaders=[]
        for frac,v in idf.groupby('training_fraction'):
            top=v.loc[v.importance.idxmax()]
            leaders.append(f'{int(100*frac)}% do treino: {top.hyperparameter} (importância={top.importance:.3f})')
        top_names=[v.loc[v.importance.idxmax(),'hyperparameter'] for _,v in idf.groupby('training_fraction')]
        change='O hiperparâmetro líder permaneceu o mesmo nas duas amostras. ' if len(set(top_names))==1 and len(top_names)>1 else 'O hiperparâmetro líder mudou entre as duas amostras. ' if len(top_names)>1 else ''
        texts['optuna_importance']='Hiperparâmetro mais importante em cada busca: '+'; '.join(leaders)+'. '+change+'As importâncias são relativas às 40 avaliações e à distribuição dos candidatos, não uma propriedade universal da feature ou do otimizador. Mudar a amostra também altera o caminho adaptativo da busca; eventuais diferenças não isolam apenas o efeito do tamanho.'
    radar_methods=m.loc[[k for k in MAIN if k in m.index]]
    fastest=radar_methods.total_seconds.idxmin();rmsebest=radar_methods.test_rmse.idxmin();maebest=radar_methods.test_mae.idxmin();r2best=radar_methods.test_r2.idxmax()
    texts['radar']=f'No conjunto exibido, os líderes de qualidade são {LABELS[rmsebest]} em RMSE, {LABELS[maebest]} em MAE e {LABELS[r2best]} em R². O menor tempo total é de {LABELS[fastest]}. O radar orienta as quatro escalas para maior=melhor; as normalizações são dependentes dos métodos incluídos, e polígonos próximos não estabelecem equivalência estatística.'
    if 'residuals' in analysis:
        r=analysis['residuals'];texts['residuals']=f'Shapiro–Wilk nos {r["n"]} resíduos de teste: W={r["shapiro_W"]:.4f}, p={r["shapiro_p"]:.4g}. '+('Há evidência contra normalidade a 5%.' if r['shapiro_p']<.05 else 'Não se rejeita normalidade a 5%; isso não a comprova.')+' O diagnóstico é exploratório e normalidade dos resíduos não é requisito para minimizar RMSE com GBR.'
    if 'robustness' in analysis:
        r=analysis['robustness'];cvpercent=100*r['std_rmse_ddof1']/r['mean_rmse']
        texts['robustness']=f'Executar novamente o procedimento HPO completo com cinco seeds, mantendo holdout e folds, resultou em RMSE médio {r["mean_rmse"]:.4f} MPa e desvio padrão amostral {r["std_rmse_ddof1"]:.4f} MPa (mínimo {r["min_rmse"]:.4f}, máximo {r["max_rmse"]:.4f}). O desvio corresponde a {cvpercent:.2f}% da média: a variação é pequena em relação ao nível do erro, mas o desempenho exato depende da seed. Isso descreve estabilidade computacional no dataset fixo; sem tolerância industrial definida e validação externa, não estabelece estabilidade operacional ou populacional.'
    if 'optuna' in m.index:
        op=m.loc['optuna'];cvwin=m.loc[analysis['best_cv_method']]
        texts['recommendation']=f'Adotaria Optuna TPE como candidato operacional provisório pelo compromisso entre CV, custo e integração: CV RMSE {op.cv_rmse:.4f} MPa em {op.total_seconds:.3f} s, com 40 trials e o mesmo pipeline. A seleção formal pelo menor CV continua sendo {LABELS[analysis["best_cv_method"]]} ({cvwin.cv_rmse:.4f} MPa; {cvwin.total_seconds:.3f} s). Random Search é a alternativa mais simples para orçamento menor. Fixaria versões, seeds, split e budget e validaria em novos lotes antes de produção. Essa recomendação é uma interpretação pós-resultados; as métricas de teste são descritivas, e não o critério principal da escolha operacional.'
    return texts


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--main-only',action='store_true',help='Render primary results without unfinished robustness; writes analysis-main.json');args=parser.parse_args()
    root=args.root;base=root/'results';out=root/'figures';out.mkdir(exist_ok=True)
    metrics=pd.read_csv(base/'metrics.csv')
    if len(metrics)==0:raise RuntimeError('No real metrics available')
    metrics=metrics[metrics.method.isin(ORDER)].copy();metrics['_order']=metrics.method.map({m:i for i,m in enumerate(ORDER)});metrics=metrics.sort_values('_order').drop(columns='_order')
    if metrics.method.duplicated().any():raise ValueError('Duplicate primary metric rows; resolve seed selection first.')
    if not np.isfinite(metrics[['cv_rmse','test_rmse','test_mae','test_r2','total_seconds']]).all().all():raise ValueError('Non-finite metrics require explicit failure handling.')
    analysis={'metrics':metrics.to_dict('records'),'best_cv_method':metrics.loc[metrics.cv_rmse.idxmin(),'method'],'best_test_method':metrics.loc[metrics.test_rmse.idxmin(),'method'], 'figure_source':'real_saved_experiment_outputs','method_labels':LABELS,'limitations':['One dataset and one holdout','Unequal required budgets','Different resolution inside shared bounds','Winner selection exposes test set','CPU wall times depend on system load']}
    b=metrics.set_index('method').loc['baseline']
    efficiency=[]
    for row in metrics.to_dict('records'):
        dt=row['total_seconds']-b.total_seconds;gain=(b.test_rmse-row['test_rmse'])/b.test_rmse
        efficiency.append({'method':row['method'],'relative_rmse_improvement':float(gain),'additional_seconds':float(dt),'efficiency_per_second':float(gain/dt) if dt>0 else None,'status':'defined' if dt>0 else 'undefined_nonpositive_delta_time'})
    analysis['efficiency']=efficiency;pd.DataFrame(efficiency).to_csv(base/'efficiency.csv',index=False)
    good=[v for v in efficiency if v['efficiency_per_second'] is not None]
    if good:analysis['best_efficiency_method']=max(good,key=lambda v:v['efficiency_per_second'])['method']
    plot_eda(root,out,analysis)
    feature_overlap(root,analysis)
    predictions(base,'baseline',out,'03_baseline_predictions',analysis)
    convergence(base,['grid','random'],out,'04_grid_random_convergence','Grid × Random — mesma grade discreta')
    grid_analysis(base,out,analysis)
    convergence(base,['grid','random','gp_manual'],out,'07_gp_comparison','GP manual (2D) × Grid/Random (3D)')
    gp_figures(base,out,analysis)
    convergence(base,['bayessearch','bayesopt','optuna','hyperopt','ray'],out,'08_bayesian_convergence','Bibliotecas: melhor RMSE CV completo acumulado')
    evolutionary_figures(base,out,analysis)
    comparative_figures(metrics,out,analysis)
    predictions(base,analysis['best_test_method'],out,'15_best_predictions_residuals',analysis,diagnostic=True)
    supplemental(base,out,analysis,include_robustness=not args.main_only)
    analysis['narrative']=narrative(analysis,metrics)
    analysis['recommendation']={'method':'optuna','status':'post_result_operational_tradeoff','formal_cv_selection':analysis['best_cv_method'],'descriptive_test_winner':analysis['best_test_method'],'basis':['CV performance','search cost','bounded trials','pipeline integration'],'test_used_for_hyperparameter_selection':False}
    analysis['figures']={p.stem:str(p.relative_to(root)).replace('\\','/') for p in sorted(out.glob('*.png'))}
    analysis_path=base/('analysis-main.json' if args.main_only else 'analysis.json')
    analysis_path.write_text(json.dumps(clean_json(analysis),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'metrics':len(metrics),'figures':len(list(out.glob('*.png'))),'best_cv_method':analysis['best_cv_method'],'best_test_method':analysis['best_test_method'],'analysis':str(analysis_path)},ensure_ascii=False))


if __name__=='__main__':main()
