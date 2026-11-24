"""Gros sinistres : incertitude réelle du niveau de charge et charge de queue par loi de Pareto généralisée (GPD).

Étude séparée : le modèle publié (artifacts/model.json) n'est pas modifié et le test, déjà consulté, n'est utilisé qu'en lecture
descriptive. Toute sélection se fait sur la validation.

1. Bootstrap complet du ratio observé/prédit de test : on rééchantillonne les polices de train (avec leurs sinistres) ET de test.
   Le niveau prédit du modèle publié est équilibré sur train (recalage multiplicatif de la sévérité) : dans chaque réplique, le
   niveau est recalé sur le train rééchantillonné. Le bootstrap publié ne rééchantillonnait que le test.
2. Charge de queue : au-delà d'un seuil u, la sévérité est plafonnée et la charge moyenne de l'excédent par sinistre est
   estimée soit par l'excédent réalisé sur train (variante existante), soit par une GPD ajustée aux dépassements de train :
   E[(Y − u)+] = P(Y > u) · σ/(1 − ξ) si ξ < 1. Choix sur la validation (déviance Tweedie de la prime pure, ratio O/P).

python pipeline/large_loss.py        (écrit reports/large_loss.json)
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import genpareto
from sklearn.linear_model import GammaRegressor
from sklearn.metrics import mean_tweedie_deviance
sys.path.insert(0,str(Path(__file__).parent))
from calibrate import prepare_data,predict_export
ROOT=Path(__file__).resolve().parents[1]
THRESHOLDS=[50000.,100000.,250000.]
SEED=20261124;B=500

def gpd_tail(excess_claims,n_claims):
    """Ajuste une GPD (position 0) aux excédents ; renvoie ξ, σ, la charge de queue par sinistre et son intervalle (bootstrap)."""
    xi,_,sigma=genpareto.fit(excess_claims,floc=0)
    p=len(excess_claims)/n_claims
    load=p*sigma/(1-xi) if xi<1 else float('inf')
    return float(xi),float(sigma),float(load)

def bootstrap_level(cost_tr,pred_tr,cost_te,pred_te,b=B,seed=SEED):
    """Ratio O/P de test quand le niveau est recalé sur un train rééchantillonné (poids de Poisson par police)."""
    rng=np.random.default_rng(seed);out=np.empty(b);test_only=np.empty(b)
    for k in range(b):
        wt=rng.poisson(1,len(cost_tr));we=rng.poisson(1,len(cost_te))
        level=np.dot(wt,cost_tr)/np.dot(wt,pred_tr)          # facteur de recalage sur le train rééchantillonné (1 sur le train d'origine)
        out[k]=np.dot(we,cost_te)/(level*np.dot(we,pred_te));test_only[k]=np.dot(we,cost_te)/np.dot(we,pred_te)
    return out,test_only

def main():
    source,f,s,d,audit,train,val,test,G,encoder,X,ix=prepare_data()
    model=json.loads((ROOT/'artifacts/model.json').read_text(encoding='utf-8'))
    fp=predict_export(model['frequency'],G);sp=predict_export(model['severity'],G)+model['severity_tail']
    e=d.Exposure.to_numpy();cost=d.cost.to_numpy();pred=e*fp*sp
    res={'published_model':model['version'],'test_role':'lecture descriptive (déjà consulté) ; aucune sélection sur le test'}
    # --- 1. Bootstrap complet
    tr,va,te=ix['train'],ix['validation'],ix['test']
    r_full,r_test=bootstrap_level(cost[tr],pred[tr],cost[te],pred[te])
    op=float(cost[te].sum()/pred[te].sum());level_tr=float(cost[tr].sum()/pred[tr].sum())
    res['bootstrap']={'replicates':B,'seed':SEED,'test_cost_op':op,'train_balance':level_tr,
        'test_only_interval95':[float(x) for x in np.quantile(r_test,[.025,.975])],'full_interval95':[float(x) for x in np.quantile(r_full,[.025,.975])],
        'share_replicates_op_at_least_1':float(np.mean(r_full>=1)),
        'note':'Poids de Poisson par police ; la forme des GLM est figée, seul le niveau est recalé à chaque réplique.'}
    print('bootstrap',res['bootstrap'],flush=True)
    # --- 2. Charge de queue : excédent réalisé contre GPD, par seuil ; plafonnement de la sévérité, alpha choisi sur validation
    sc=s.merge(d[['IDpol','split']],on='IDpol',validate='many_to_one');pos=pd.Series(d.index,index=d.IDpol)
    positions=sc.IDpol.map(pos).to_numpy();Xs=X[positions];ys=sc.ClaimAmount.to_numpy();st=sc.split.to_numpy()=='train'
    yv=cost[va]/e[va];rows=[]
    def evaluate(label,u,load,sev_capped):
        sev=sev_capped+load;p=e*fp*sev
        return {'variant':label,'threshold':u,'tail_per_claim':load,
                'validation_cost_op':float(cost[va].sum()/p[va].sum()),'validation_tweedie_p15':float(mean_tweedie_deviance(yv,fp[va]*sev[va],power=1.5,sample_weight=e[va])),
                'test_cost_op_descriptive':float(cost[te].sum()/p[te].sum())}
    rows.append(evaluate('modèle publié (sans plafond)',None,model['severity_tail'],sp-model['severity_tail']))
    gpd={}
    for u in THRESHOLDS:
        target=np.minimum(ys,u);best=None
        for alpha in [0.,.001,.1]:
            m=GammaRegressor(alpha=alpha,max_iter=300,tol=1e-8,solver='newton-cholesky').fit(Xs[st],target[st])
            adj=float(target[st].sum()/m.predict(Xs[st]).sum());capped=m.predict(X)*adj
            score=mean_tweedie_deviance(yv,fp[va]*(capped[va]+np.maximum(ys[st]-u,0).mean()),power=1.5,sample_weight=e[va])
            if best is None or score<best[0]:best=(score,alpha,capped)
        _,alpha,capped=best;exc=ys[st][ys[st]>u]-u
        empirical=float(np.maximum(ys[st]-u,0).mean());xi,sigma,load=gpd_tail(exc,int(st.sum()))
        # Intervalle bootstrap de la charge GPD (rééchantillonnage des sinistres de train)
        rng=np.random.default_rng(SEED);loads=[]
        yt=ys[st]
        for _ in range(300):
            yb=rng.choice(yt,len(yt),replace=True);eb=yb[yb>u]-u
            if len(eb)>=5:
                xb,_,sb=genpareto.fit(eb,floc=0);loads.append(len(eb)/len(yb)*sb/(1-xb) if xb<1 else np.inf)
        loads=np.array(loads);finite=np.isfinite(loads)
        gpd[str(int(u))]={'exceedances_train':int(len(exc)),'xi':xi,'sigma':sigma,'gpd_load_per_claim':load,'empirical_load_per_claim':empirical,
                          'gpd_load_interval90':[float(x) for x in np.quantile(loads[finite],[.05,.95])] if finite.sum()>10 else None,'share_infinite_mean_replicates':float(1-finite.mean()),'alpha':alpha}
        rows.append(evaluate(f'plafond {int(u/1000)} k€ + excédent réalisé',u,empirical,capped))
        if np.isfinite(load):rows.append(evaluate(f'plafond {int(u/1000)} k€ + queue GPD',u,load,capped))
        print(u,gpd[str(int(u))],flush=True)
    res['gpd']=gpd;res['variants']=rows
    best=min(rows,key=lambda r:r['validation_tweedie_p15']);res['selected_on_validation']=best['variant']
    res['reading']=('Choix sur la validation uniquement ; les ratios de test sont descriptifs. Une variante retenue ainsi ne peut pas être déclarée validée '
                    'sur ce test déjà consulté : il faut un nouvel échantillon indépendant.')
    (ROOT/'reports/large_loss.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,default=float),encoding='utf-8')
    print(pd.DataFrame(rows).round(4).to_string(index=False));print('retenu sur validation :',best['variant'])

if __name__=='__main__':main()
