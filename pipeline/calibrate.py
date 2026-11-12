"""Calibration reproductible freMTPL2 : séparation fixe, GLM et validation gelée."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import json,hashlib,platform,sys,warnings
from pathlib import Path
from datetime import datetime,timezone
import numpy as np,pandas as pd,pyreadr,sklearn,scipy
from scipy.special import gammaln
from scipy.optimize import minimize_scalar
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import PoissonRegressor,GammaRegressor
from sklearn.metrics import mean_poisson_deviance,mean_gamma_deviance,mean_tweedie_deviance
sys.path.insert(0,str(Path(__file__).parent))
from download import download
ROOT=Path(__file__).resolve().parents[1]
BINS={'DrivAge':[18,25,35,45,55,65,75,101],'VehAge':[0,2,5,10,15,101],'VehPower':[4,6,8,10,16]}
FEATURES=['DrivAgeBand','VehAgeBand','VehPowerBand','VehGas','Area','Region']
LABELS={'DrivAge':'Âge du conducteur','VehAge':'Âge du véhicule','VehPower':'Puissance fiscale','VehGas':'Carburant','Area':'Zone','Region':'Région'}
def groups(df):
 out=pd.DataFrame(index=df.index)
 for name,edges in BINS.items():
  out[name+'Band']=pd.cut(df[name],edges,right=False,labels=[f'{a}-{b-1}' for a,b in zip(edges[:-1],edges[1:])]).astype(str)
 for name in ['VehGas','Area','Region']:out[name]=df[name].astype(str)
 return out[FEATURES]
def fit_export(model,encoder,multiplier=1.):
 offset=0;factors={}
 for name,categories in zip(FEATURES,encoder.categories_):
  factors[name]={str(categories[0]):0.}
  for category in categories[1:]:factors[name][str(category)]=float(model.coef_[offset]);offset+=1
 return {'intercept':float(model.intercept_+np.log(multiplier)),'coefficients':factors}
def predict_export(model,g):
 z=np.full(len(g),model['intercept'])
 for name,levels in model['coefficients'].items():z+=g[name].map(levels).to_numpy()
 return np.exp(z)
def record(name,df,frequency,severity,baseline_freq,baseline_sev):
 e=df.Exposure.to_numpy();n=df.ClaimNb.to_numpy();y=df.cost.to_numpy()/e
 pure=frequency*severity
 return {'sample':name,'policies':len(df),'exposure':float(e.sum()),'claims':int(n.sum()),'observed_cost':float(df.cost.sum()),'predicted_cost':float(np.sum(e*pure)),
 'observed_predicted_count':float(n.sum()/np.sum(e*frequency)),'observed_predicted_cost':float(df.cost.sum()/np.sum(e*pure)),
 'frequency_poisson_deviance':float(mean_poisson_deviance(n/e,frequency,sample_weight=e)),
 'frequency_baseline_deviance':float(mean_poisson_deviance(n/e,np.full(len(e),baseline_freq),sample_weight=e)),
 'pure_tweedie_deviance_p15':float(mean_tweedie_deviance(y,pure,power=1.5,sample_weight=e)),
 'pure_baseline_deviance_p15':float(mean_tweedie_deviance(y,np.full(len(e),baseline_freq*baseline_sev),power=1.5,sample_weight=e))}
def main():
 source=download();f=pyreadr.read_r(str(ROOT/'data/raw/freMTPL2freq.rda'))['freMTPL2freq'];s=pyreadr.read_r(str(ROOT/'data/raw/freMTPL2sev.rda'))['freMTPL2sev']
 for df in [f,s]:df['IDpol']=df.IDpol.astype(str)
 assert f.IDpol.is_unique
 claims=s.groupby('IDpol',observed=True).agg(cost=('ClaimAmount','sum'),matched_claims=('ClaimAmount','size'))
 d=f.merge(claims,left_on='IDpol',right_index=True,how='left',validate='one_to_one').fillna({'cost':0,'matched_claims':0}).reset_index(drop=True)
 assert not (~s.IDpol.isin(f.IDpol)).any();assert (d.ClaimNb==d.matched_claims).all()
 assert d[FEATURES[3:]+list(BINS)+['Exposure','ClaimNb']].notna().all().all()
 valid=(d.Exposure>0)&(d.ClaimNb>=0)&(d.ClaimNb%1==0)
 for name,edges in BINS.items():valid&=(d[name]>=edges[0])&(d[name]<edges[-1])
 audit={'raw_policies':len(f),'raw_claims':len(s),'count_amount_mismatches':int((d.ClaimNb!=d.matched_claims).sum()),'orphan_claims':0,'removed_invalid_policies':int((~valid).sum()),'exposure_above_one_preserved':int((d.Exposure>1).sum()),'claims_above_four_preserved':int((d.ClaimNb>4).sum()),'maximum_claim':float(s.ClaimAmount.max()),'policy_exposure_duplicated':False}
 d=d.loc[valid].copy();assert (s.ClaimAmount>0).all()
 # Stable hash on contract ID. No dates are available: this is NOT temporal validation.
 buckets=d.IDpol.map(lambda value:int(hashlib.sha256(('clair-v1|'+value).encode()).hexdigest()[:8],16)%100)
 d['split']=np.where(buckets<60,'train',np.where(buckets<80,'validation','test'))
 train=d.loc[d.split=='train'];val=d.loc[d.split=='validation'];test=d.loc[d.split=='test']
 assert not(set(train.IDpol)&set(test.IDpol));assert not(set(train.IDpol)&set(val.IDpol))
 encoder=OneHotEncoder(drop='first',handle_unknown='error',sparse_output=True,dtype=np.float64)
 G=groups(d);encoder.fit(G.loc[train.index]);X=encoder.transform(G)
 print('Données auditées, matrice',X.shape,flush=True)
 ix={key:d.index[d.split==key].to_numpy() for key in ['train','validation','test']}
 n=d.ClaimNb.to_numpy();e=d.Exposure.to_numpy();f_candidates=[];f_models=[]
 for alpha in [0.,.0001,.01]:
  model=PoissonRegressor(alpha=alpha,max_iter=300,tol=1e-8,solver='newton-cholesky')
  model.fit(X[ix['train']],n[ix['train']]/e[ix['train']],sample_weight=e[ix['train']])
  pred=model.predict(X[ix['validation']]);score=mean_poisson_deviance(n[ix['validation']]/e[ix['validation']],pred,sample_weight=e[ix['validation']])
  f_candidates.append({'alpha':alpha,'validation_poisson_deviance':float(score),'iterations':int(model.n_iter_)})
  f_models.append(model);print('Fréquence',alpha,score,flush=True)
 best_f=int(np.argmin([r['validation_poisson_deviance'] for r in f_candidates]));freq_model=f_models[best_f]
 fp=freq_model.predict(X);base_f=float(train.ClaimNb.sum()/train.Exposure.sum())
 # Every severity claim follows its contract's split; never split joined rows independently.
 sc=s.merge(d[['IDpol','split']],on='IDpol',validate='many_to_one');policy_position=pd.Series(d.index,index=d.IDpol)
 positions=sc.IDpol.map(policy_position).to_numpy();Xs=X[positions];ys=sc.ClaimAmount.to_numpy();st=sc.split.to_numpy()=='train';sv=sc.split.to_numpy()=='validation'
 base_s=float(ys[st].mean());s_candidates=[];s_models=[]
 for cap in [None,100000.]:
  target=ys.copy() if cap is None else np.minimum(ys,cap)
  excess=0. if cap is None else float(np.maximum(ys[st]-cap,0).mean())
  for alpha in [0.,.001,.1]:
   model=GammaRegressor(alpha=alpha,max_iter=300,tol=1e-8,solver='newton-cholesky')
   model.fit(Xs[st],target[st])
   adjustment=float(target[st].sum()/model.predict(Xs[st]).sum())
   pred=model.predict(X[ix['validation']])*adjustment+excess
   score=mean_tweedie_deviance(val.cost/val.Exposure,fp[ix['validation']]*pred,power=1.5,sample_weight=val.Exposure)
   s_candidates.append({'cap':cap,'alpha':alpha,'tail_per_claim':excess,'balance_multiplier':adjustment,'validation_pure_tweedie_deviance_p15':float(score),'validation_gamma_deviance_target':float(mean_gamma_deviance(target[sv],model.predict(Xs[sv])*adjustment)),'iterations':int(model.n_iter_)})
   s_models.append(model);print('Sévérité',cap,alpha,score,flush=True)
 best_s=int(np.argmin([r['validation_pure_tweedie_deviance_p15'] for r in s_candidates]));sm=s_models[best_s];settings=s_candidates[best_s]
 sp=sm.predict(X)*settings['balance_multiplier']+settings['tail_per_claim']
 # NB2 marginal MLE for Gamma frailty U~Gamma(r,r), on TRAIN only.
 mu=e[ix['train']]*fp[ix['train']];counts=n[ix['train']]
 def nll(log_r):
  r=np.exp(log_r)
  return -float(np.sum(gammaln(counts+r)-gammaln(r)-gammaln(counts+1)+r*(np.log(r)-np.log(r+mu))+counts*(np.log(mu)-np.log(r+mu))))
 fit=minimize_scalar(nll,bounds=(-6,12),method='bounded');r=float(np.exp(fit.x));assert fit.success
 # Full raw-severity residual second moment, TRAIN only. K is STRUCTURAL, not longitudinal Bühlmann estimate.
 residual_ratio=ys[st]/sp[positions[st]]
 severity_second=float(np.mean(residual_ratio**2));severity_second=max(1.,severity_second)
 cap_sensitivity=[{'threshold':cap,'train_tail_per_claim':float(np.maximum(ys[st]-cap,0).mean()),'train_claims_above':int((ys[st]>cap).sum())} for cap in [50000,100000,250000]]
 metrics=[record(key,d.iloc[ix[key]],fp[ix[key]],sp[ix[key]],base_f,base_s) for key in ['train','validation','test']]
 test_df=d.iloc[ix['test']].copy();test_df['expected_count']=e[ix['test']]*fp[ix['test']];test_df['expected_cost']=test_df.expected_count*sp[ix['test']]
 # Bootstrap sampling interval on aggregate O/P, not individual prediction or longitudinal validation.
 rng=np.random.default_rng(20261112);ratios=[]
 for b in range(300):
  w=rng.poisson(1,len(test_df));ratios.append(np.dot(w,test_df.cost)/np.dot(w,test_df.expected_cost))
 interval=list(map(float,np.quantile(ratios,[.025,.975])))
 segments=[]
 test_df['DrivAgeBand']=groups(test_df).DrivAgeBand
 for feature in ['DrivAgeBand','Area','Region']:
  a=test_df.groupby(feature,observed=True).agg(policies=('IDpol','size'),exposure=('Exposure','sum'),claims=('ClaimNb','sum'),observed_cost=('cost','sum'),predicted_count=('expected_count','sum'),predicted_cost=('expected_cost','sum')).reset_index()
  a['count_op']=a.claims/a.predicted_count;a['cost_op']=a.observed_cost/a.predicted_cost
  for row in a.to_dict('records'):segments.append({'feature':feature,'segment':str(row.pop(feature)),**row})
 freq_export=fit_export(freq_model,encoder);sev_export=fit_export(sm,encoder,settings['balance_multiplier'])
 assert np.max(np.abs(predict_export(freq_export,G)/fp-1))<1e-10
 assert np.max(np.abs((predict_export(sev_export,G)+settings['tail_per_claim'])/sp-1))<1e-10
 version='fremtpl2-2026-11-v1'
 model={'version':version,'data_commit':source['commit'],'currency_basis':'EUR historiques, environ 2011–2013 ; aucun redressement économique appliqué','source':'CASdatasets / freMTPL2','bins':BINS,'features':FEATURES,'frequency':freq_export,'severity':sev_export,'severity_tail':settings['tail_per_claim'],'frailty_shape_r':r,'severity_second_moment_factor':severity_second,'credibility_status':'structural_compound_poisson_gamma_not_longitudinal','limits':{key:[edges[0],edges[-1]-1] for key,edges in BINS.items()},'excluded_features':['BonusMalus','IDpol'],'trained_policies':len(train),'test_policies':len(test),'selected_frequency':f_candidates[best_f],'selected_severity':settings,'release_status':'calibrated_research_not_production'}
 report={'version':version,'created_utc':datetime.now(timezone.utc).isoformat(),'source':source,'data_audit':audit,'split':{'method':'SHA256 contract ID, seed label clair-v1, 60/20/20','temporal_validation':False,'refit_on_validation':False,'test_used_for_selection':False},'frequency_candidates':f_candidates,'severity_candidates':s_candidates,'selected_frequency':f_candidates[best_f],'selected_severity':settings,'metrics':metrics,'test_aggregate_cost_op_bootstrap95':interval,'test_aggregate_cost_op_bootstrap_replicates':300,'frailty':{'r':r,'optimizer_success':bool(fit.success),'log_r_objective':float(fit.fun),'beta_definition':'r / annual frequency','longitudinal_validation':False},'credibility':{'severity_second_moment_factor':severity_second,'K_definition':'r * E[(Y / model_severity)^2] / annual frequency','status':'structural model assumption, not nonparametric longitudinal calibration'},'large_claim_sensitivity':cap_sensitivity,'segments_test':segments,'baseline':{'annual_frequency':base_f,'mean_claim':base_s},'environment':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scikit_learn':sklearn.__version__,'scipy':scipy.__version__,'pyreadr':pyreadr.__version__},'production_gaps':['Recent company portfolio, inflation and guarantee definitions','Claims maturity / ultimate amounts and reinsurance','Longitudinal history validation for Bayesian and credibility methods','Company expenses, taxes and profit/capital objectives','Independent actuarial review, monitoring and deployment controls']}
 for folder in ['artifacts','reports']: (ROOT/folder).mkdir(exist_ok=True)
 (ROOT/'artifacts/model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2,allow_nan=False))
 (ROOT/'dist/model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2,allow_nan=False))
 (ROOT/'reports/calibration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
 (ROOT/'reports/data_manifest.json').write_text(json.dumps(source,indent=2))
 pd.DataFrame(segments).to_csv(ROOT/'reports/test_segments.csv',index=False)
 (ROOT/'requirements.txt').write_text('\n'.join(f'{key}=={val}' for key,val in report['environment'].items() if key!='python').replace('scikit_learn','scikit-learn')+'\n')
 print(json.dumps({'audit':audit,'metrics':metrics,'r':r,'second_moment':severity_second,'interval':interval,'selected_severity':settings},indent=2),flush=True)
if __name__=='__main__':main()
