import unittest
import numpy as np
from scipy import sparse
from scipy.optimize import approx_fprime
from pipeline.compare_frequency import nb2_loss_gradient

class NBFitTests(unittest.TestCase):
 def test_score_matches_finite_differences(self):
  X=sparse.csr_matrix([[1.,0.],[1.,1.],[1.,2.],[1.,-1.]])
  n=np.array([0.,1.,3.,0.]);offset=np.log([.2,1.,.5,.7]);p=np.array([-1.4,.3,np.log(.7)])
  value,gradient=nb2_loss_gradient(p,X,n,offset)
  numerical=approx_fprime(p,lambda z:nb2_loss_gradient(z,X,n,offset)[0],1e-7)
  np.testing.assert_allclose(gradient,numerical,atol=1e-6,rtol=1e-5)
  self.assertTrue(np.isfinite(value))
