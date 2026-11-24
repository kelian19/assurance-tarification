"""Étude des gros sinistres : ajustement GPD et bootstrap du niveau, sur données synthétiques."""
import sys,unittest
from pathlib import Path
import numpy as np
from scipy.stats import genpareto
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pipeline.large_loss import gpd_tail,bootstrap_level

class LargeLoss(unittest.TestCase):
    def test_gpd_recovers_tail_and_load(self):
        x=genpareto.rvs(0.3,scale=1000.,size=20000,random_state=1)
        xi,sigma,load=gpd_tail(x,n_claims=100000)
        self.assertAlmostEqual(xi,0.3,delta=0.05);self.assertAlmostEqual(sigma,1000.,delta=60.)
        self.assertAlmostEqual(load,0.2*sigma/(1-xi),places=6)
    def test_infinite_mean_is_reported(self):
        x=genpareto.rvs(1.3,scale=1000.,size=5000,random_state=2)
        self.assertEqual(gpd_tail(x,10000)[2],float('inf'))
    def test_full_bootstrap_is_wider_than_test_only(self):
        rng=np.random.default_rng(0);pred_tr=np.full(5000,10.);pred_te=np.full(2000,10.)
        cost_tr=rng.pareto(1.5,5000)*10/2;cost_te=rng.pareto(1.5,2000)*10/2   # queue lourde, moyenne 10
        full,test_only=bootstrap_level(cost_tr,pred_tr*cost_tr.sum()/pred_tr.sum(),cost_te,pred_te*cost_tr.sum()/pred_tr.sum(),b=300,seed=1)
        self.assertGreater(np.diff(np.quantile(full,[.025,.975]))[0],np.diff(np.quantile(test_only,[.025,.975]))[0])

if __name__=='__main__':unittest.main()
