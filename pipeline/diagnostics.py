"""Diagnostics de dispersion sur apprentissage ; aucun nouveau choix de modèle."""
from pathlib import Path
import sys,json,numpy as np,pyreadr
from scipy.optimize import brentq
from scipy.special import digamma
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'pipeline'))
from calibrate import groups,predict_export

def main():
 import hashlib
 model=json.loads((ROOT/'artifacts/model.json').read_text());report=json.loads((ROOT/'reports/calibration.json').read_text())
 f=pyreadr.read_r(str(ROOT/'data/raw/freMTPL2freq.rda'))['freMTPL2freq'];s=pyreadr.read_r(str(ROOT/'data/raw/freMTPL2sev.rda'))['freMTPL2sev']
 for df in [f,s]:df['IDpol']=df.IDpol.astype(str)
 f=f.loc[f.IDpol.map(lambda value:int(hashlib.sha256(('clair-v1|'+value).encode()).hexdigest()[:8],16)%100<60)].copy()
 g=groups(f);mu=f.Exposure.to_numpy()*predict_export(model['frequency'],g);n=f.ClaimNb.to_numpy();r=model['frailty_shape_r'];p=41
 phi=float(np.sum((n-mu)**2/mu)/(len(f)-p));nb_phi=float(np.sum((n-mu)**2/(mu+mu**2/r))/(len(f)-p))
 means=predict_export(model['severity'],g)+model['severity_tail']
 sc=s.merge(f[['IDpol']].assign(predicted=means),on='IDpol',validate='many_to_one');ratio=sc.ClaimAmount.to_numpy()/sc.predicted.to_numpy()
 target=float(np.mean(ratio-np.log(ratio)-1))
 shape=float(brentq(lambda k:np.log(k)-digamma(k)-target,1e-5,1e6))
 largest=float(sc.ClaimAmount.max()/sc.ClaimAmount.sum());top10=float(sc.ClaimAmount.nlargest(10).sum()/sc.ClaimAmount.sum())
 report['dispersion_diagnostics']={'sample':'train','poisson_pearson_phi':phi,'nb2_pearson_residual_ratio':nb_phi,'gamma_shape_mle':shape,'gamma_phi_mle':1/shape,'gamma_empirical_relative_second_moment':float(np.mean(ratio**2)),'train_largest_claim_cost_share':largest,'train_top10_claims_cost_share':top10,'interpretation':'Gamma likelihood shape and empirical second moment are distinct diagnostics; large discrepancy exposes heavy-tail risk. NB2 is a frailty approximation, not validated persistence.'}
 (ROOT/'reports/calibration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
 print(json.dumps(report['dispersion_diagnostics'],indent=2))
if __name__=='__main__':main()
