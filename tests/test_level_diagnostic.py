"""Diagnostic du niveau de charge : sensibilité au plus gros sinistre et incertitude du niveau appris."""
import json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pipeline.level_diagnostic import level_diagnostic

def synthetic(cost=1000.,n=10,largest=400.):
    m=lambda op:{'claims':n,'observed_cost':cost,'observed_predicted_cost':op}
    return {'metrics':[m(1.),m(0.9),m(0.8)],'data_audit':{'maximum_claim':largest},
            'dispersion_diagnostics':{'train_largest_claim_cost_share':largest/cost,'train_top10_claims_cost_share':0.9,'gamma_empirical_relative_second_moment':5.,'poisson_pearson_phi':1.},
            'test_aggregate_cost_op_bootstrap95':[0.7,0.9]}

class LevelDiagnostic(unittest.TestCase):
    def test_sensitivity_without_largest_claim(self):
        d=level_diagnostic(synthetic())['largest_claim_sensitivity']
        self.assertAlmostEqual(d['level_factor_without_largest'],(600/9)/(1000/10))
        self.assertAlmostEqual(d['test_cost_op_without_largest'],0.8/d['level_factor_without_largest'])
    def test_combined_interval_is_wider_than_test_only(self):
        u=level_diagnostic(synthetic())['level_uncertainty']
        self.assertAlmostEqual(u['relative_se_train_severity_mean'],math.sqrt(4/10))
        lo,hi=u['combined_interval95'];self.assertLess(lo,0.7);self.assertGreater(hi,0.9)
    def test_refuses_when_largest_claim_not_in_train(self):
        r=synthetic();r['dispersion_diagnostics']['train_largest_claim_cost_share']=0.1
        with self.assertRaises(ValueError):level_diagnostic(r)
    def test_published_calibration(self):
        d=level_diagnostic(json.loads((ROOT/'reports/calibration.json').read_text(encoding='utf-8')))
        self.assertAlmostEqual(d['largest_claim_sensitivity']['level_factor_without_largest'],0.8918,places=4)
        u=d['level_uncertainty'];self.assertLess(u['combined_interval95'][0],u['test_only_interval95'][0]);self.assertLess(u['combined_interval95'][1],1.)

if __name__=='__main__':unittest.main()
