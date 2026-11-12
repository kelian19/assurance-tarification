import unittest
from python.model import predict,load_model
from python.pricing import calculate,Period
PROFILE=dict(DrivAge=45,VehAge=7,VehPower=6,VehGas='Diesel',Area='C',Region='Centre')
class ModelTests(unittest.TestCase):
 def test_calibrated_gamma_consistency(self):
  m=load_model();p=predict(PROFILE,m)
  self.assertAlmostEqual(p['beta']*p['frequency'],m['frailty_shape_r'])
  self.assertGreaterEqual(p['k'],p['beta'])
 def test_inflation_affects_cost_not_frequency(self):
  a=predict(PROFILE);b=predict(PROFILE,cost_index=1.5)
  self.assertEqual(a['frequency'],b['frequency']);self.assertAlmostEqual(b['severity'],a['severity']*1.5)
 def test_out_of_scope_rejected(self):
  for key,value in [('DrivAge',17),('VehPower',16),('Region','inconnue'),('DrivAge',45.5)]:
   with self.assertRaises(ValueError):predict({**PROFILE,key:value})
  with self.assertRaises(ValueError):predict(PROFILE,cost_index=0)
 def test_posterior_uses_calibrated_r(self):
  p=predict(PROFILE);r=calculate(p['frequency'],p['severity'],[Period(1,0)]*3,beta=p['beta'],k=p['k'])
  self.assertLess(r['bayes'],r['prior']);self.assertGreater(r['bayes'],0)
 def test_split_provenance(self):
  import json
  from pathlib import Path
  report=json.loads((Path(__file__).resolve().parents[1]/'reports/calibration.json').read_text())
  self.assertFalse(report['split']['test_used_for_selection'])
  self.assertEqual(sum(row['policies'] for row in report['metrics']),report['data_audit']['raw_policies'])
