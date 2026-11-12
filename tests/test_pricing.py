import unittest
from python.pricing import calculate,Period

class PricingTests(unittest.TestCase):
    def test_no_history_equals_prior(self):
        for method in ['prior','bayes','credibility']:
            r=calculate(.08,2500,method=method)
            self.assertAlmostEqual(r['annual_pure'],200)
    def test_course_posterior_identity(self):
        r=calculate(.08,2500,[Period(1,0)]*3)
        self.assertAlmostEqual(r['bayes'],800/7)
        self.assertAlmostEqual(r['z_bayes'],3/7)
        self.assertAlmostEqual(r['posterior_alpha'],.32)
        self.assertAlmostEqual(r['posterior_beta'],7)
    def test_claim_increases_estimate(self):
        a=calculate(.08,2500,[Period(1,0)])
        b=calculate(.08,2500,[Period(1,1,2000)])
        self.assertGreater(b['bayes'],a['bayes'])
    def test_bayes_ignores_cost_credibility_uses_cost(self):
        a=calculate(.08,2500,[Period(1,1,1000)])
        b=calculate(.08,2500,[Period(1,1,5000)])
        self.assertEqual(a['bayes'],b['bayes'])
        self.assertGreater(b['credibility'],a['credibility'])
    def test_partial_periods_and_commercial_loading(self):
        r=calculate(.1,2000,[Period(.5,1,1000)],coverage=.5,fixed_fee=10,expense_rate=.2,margin_rate=.1)
        self.assertAlmostEqual(r['posterior_frequency'],1.4/4.5)
        self.assertAlmostEqual(r['premium'],(r['annual_pure']*.5+10)/.7)
    def test_split_exposure_invariance(self):
        self.assertEqual(calculate(.08,2500,[Period(1,1,1000)]),calculate(.08,2500,[Period(.5,0),Period(.5,1,1000)]))
    def test_invalid_inputs(self):
        for kw in [dict(beta=0),dict(k=-1),dict(coverage=0),dict(expense_rate=.8,margin_rate=.3),dict(method='unknown')]:
            with self.assertRaises(ValueError):calculate(.08,2500,**kw)
        for p in [Period(0,1),Period(1,1.5),Period(1,0,200),Period(1,-1),Period(2,1)]:
            with self.assertRaises(ValueError):calculate(.08,2500,[p])
    def test_long_zero_claim_history_approaches_zero(self):
        r=calculate(.08,2500,[Period(1,0)]*100)
        self.assertGreater(r['bayes'],0);self.assertLess(r['bayes'],10)

if __name__=='__main__':unittest.main()
