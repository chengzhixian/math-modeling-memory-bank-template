import unittest
from cyj_v4_consumer import consume_release,SolverAdapter
from q3_joint_certificate import certify
from q3_generic_solver import solve_generic


class JointCertificateTests(unittest.TestCase):
    def test_linear_special_case_and_support_saturation(self):
        theta=(1.,.3,1.,.3,.3,.2,0.,0.)
        bounds=((.07,11.97),(10.,600.),(.1,1.))
        r=certify(theta,bounds,1e24,8192,'power')
        exact=1+.3*11.97**(-.3)+600**(-.3)
        self.assertLessEqual(r['global_lower_bound'],exact)
        self.assertAlmostEqual(r['feasible_upper_bound'],exact,places=12)
        self.assertLessEqual(r['global_gap'],1e-7)
    def test_invalid_convexity_rejected(self):
        with self.assertRaises(ValueError):
            certify((1.,.3,1.,.3,.3,.2,.01,0.),((.07,11.97),(10.,600.),(.1,1.)),1e22,8192,'power')
    def test_release_and_independent_solver(self):
        with consume_release() as (m,manifest,smoke):
            self.assertEqual(smoke['requests'],3)
            r=certify(m.joint_theta,m.bounds,1e19,2048,'exponential',tolerance=1e-6)
            s,_=solve_generic(SolverAdapter(m),budget=1e19,context_tokens=2048,Q0=.5,family='exponential',starts=8)
            self.assertTrue(s['kkt_check_pass'])
            self.assertLessEqual(r['global_lower_bound']-1e-10,s['loss'])
            self.assertLessEqual(s['loss'],r['feasible_upper_bound']+1e-9)
            self.assertLessEqual(r['global_gap'],1e-6)
            with self.assertRaises(ValueError):SolverAdapter(m).value_grad(.07,9.999,.5)

if __name__=='__main__':unittest.main()
