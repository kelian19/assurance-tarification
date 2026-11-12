"""Challenger NB2. Le test v1 est déjà consulté : comparaison diagnostique uniquement."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
from pathlib import Path
import json,hashlib,sys
import numpy as np,pandas as pd,pyreadr
from scipy import sparse
from scipy.optimize import minimize
from scipy.special import gammaln,digamma
from scipy.stats import poisson,nbinom
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_poisson_deviance,mean_tweedie_deviance
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'pipeline'))
from calibrate import groups,predict_export

def nb2_loss_gradient(params,X,n,offset):
 beta=params[:-1];r=np.exp(params[-1]);eta=offset+X@beta;mu=np.exp(eta)
 ll=gammaln(n+r)-gammaln(r)-gammaln(n+1)+r*(np.log(r)-np.log(r+mu))+n*(eta-np.log(r+mu))
 score_b=X.T@(r*(n-mu)/(r+mu))
 score_r=r*np.sum(digamma(n+r)-digamma(r)+np.log(r)-np.log(r+mu)+1-(r+n)/(r+mu))
 return -ll.mean(),-np.r_[score_b,score_r]/len(n)

def main():
 model=json.loads((ROOT/'artifacts/model.json').read_text())
 d=pyreadr.read_r(str(ROOT/'data/raw/freMTPL2freq.rda'))['freMTPL2freq'];s=pyreadr.read_r(str(ROOT/'data/raw/freMTPL2sev.rda'))['freMTPL2sev']
 for df in [d,s]:df['IDpol']=df.IDpol.astype(str)
 cost=s.groupby('IDpol',observed=True).ClaimAmount.sum()
 d['cost']=d.IDpol.map(cost).fillna(0)
 h=d.IDpol.map(lambda value:int(hashlib.sha256(('clair-v1|'+value).encode()).hexdigest()[:8],16)%100)
 split=np.where(h<60,'train',np.where(h<80,'validation','test'))
 tr=split=='train';g=groups(d)
 encoder=OneHotEncoder(drop='first',handle_unknown='error',sparse_output=True,dtype=np.float64).fit(g.loc[tr])
 X=sparse.hstack([sparse.csr_matrix(np.ones((len(d),1))),encoder.transform(g)],format='csr');Xt=X[tr]
 n=d.ClaimNb.to_numpy();e=d.Exposure.to_numpy();nt=n[tr];offset=np.log(e[tr])
 coefficients=[model['frequency']['intercept']]
 for name,categories in zip(g.columns,encoder.categories_):coefficients.extend(model['frequency']['coefficients'][name][str(value)] for value in categories[1:])
 init=np.r_[coefficients,np.log(model['frailty_shape_r'])]
 def objective(params):return nb2_loss_gradient(params,Xt,nt,offset)
 fit=minimize(objective,init,jac=True,method='L-BFGS-B',bounds=[(None,None)]*(len(init)-1)+[(-6,12)],options={'maxiter':400,'ftol':1e-12,'gtol':1e-7,'maxls':30})
 if not fit.success:raise ValueError(fit.message)
 f_nb=np.exp(X@fit.x[:-1]);r=float(np.exp(fit.x[-1]));f_p=predict_export(model['frequency'],g);severity=predict_export(model['severity'],g)+model['severity_tail']
 rows=[]
 for sample in ['train','validation','test']:
  ix=split==sample;nn=n[ix];ee=e[ix];observed=d.cost.to_numpy()[ix]
  for name,freq,shape in [('Poisson',f_p,None),('NB2',f_nb,r)]:
   ff=freq[ix];mu=ee*ff;pure=ff*severity[ix]
   ll=poisson.logpmf(nn,mu) if shape is None else nbinom.logpmf(nn,shape,shape/(shape+mu))
   variance=mu if shape is None else mu+mu*mu/shape
   rows.append({'sample':sample,'model':name,'negative_log_likelihood_per_policy':float(-ll.mean()),'poisson_deviance_frequency':float(mean_poisson_deviance(nn/ee,ff,sample_weight=ee)),'observed_predicted_count':float(nn.sum()/mu.sum()),'observed_predicted_cost':float(observed.sum()/np.dot(ee,pure)),'predicted_cost':float(np.dot(ee,pure)),'tweedie_deviance_pure_p15':float(mean_tweedie_deviance(observed/ee,pure,power=1.5,sample_weight=ee)),'pearson_residual_variance_ratio':float(np.mean((nn-mu)**2/variance))})
 report={'status':'diagnostic_challenger_not_promoted','protocol':'Same v1 train/validation/test, identical features, exposure and fixed severity. NB2 coefficients and r jointly re-estimated on train. Test already known; no new independent validation is claimed.','optimizer':{'success':bool(fit.success),'iterations':int(fit.nit),'r':r,'gradient_max':float(np.max(np.abs(fit.jac)))},'metrics':rows,'coefficients':fit.x[:-1].tolist(),'feature_names':['intercept']+encoder.get_feature_names_out().tolist()}
 (ROOT/'reports/poisson_vs_nb.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
 print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
