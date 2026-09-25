"""Numerical derivative and parameter recovery checks for joint optimization."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"src/cyj"))
from fit_b7_joint_nonlinear import value_jac, fit_joint, predict, CORNERS


class JointTests(unittest.TestCase):
    def test_parameter_jacobian(self):
        theta=np.array([1.7,.4,1.3,.32,.28,.4,-.05,-.02])
        x=np.array([[.07,10.,.1],[.7,100.,.5],[11.97,600.,1.]])
        _,jac=value_jac(theta,x)
        for i in range(8):
            left=theta.copy();right=theta.copy();left[i]-=1e-6;right[i]+=1e-6
            numeric=(value_jac(right,x)[0]-value_jac(left,x)[0])/(2e-6)
            np.testing.assert_allclose(jac[:,i],numeric,rtol=2e-6,atol=1e-8)

    def test_synthetic_recovery_and_support(self):
        theta=np.array([1.7,.4,1.3,.32,.28,.4,-.05,-.02])
        x=np.array([[n,d,q] for n in (.07,.3,1.,4.,11.97)
                    for d in (10.,40.,150.,600.) for q in (.1,.5,1.)])
        model=fit_joint(x,predict(theta,x),starts=3)
        self.assertLess(model["fit"]["rmse"],1e-6)
        np.testing.assert_allclose(model["theta"],theta,atol=2e-4,rtol=2e-4)
        self.assertGreater(min(CORNERS@np.array(model["theta"])),0)
        for point in ([.07,9.,.5],[.07,10.,float("nan")]):
            with self.assertRaises(ValueError):predict(theta,[point])


if __name__=="__main__":unittest.main()
