import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import q4_complete as q4


class MathematicalChecks(unittest.TestCase):
    def test_missing_is_not_zero(self):
        values=q4.numeric(pd.Series(['','  ','0','NaN','inf','3.5']))
        self.assertTrue(pd.isna(values[0]) and pd.isna(values[1]))
        self.assertEqual(values[2],0)
        self.assertEqual(values[5],3.5)

    def test_shapley_conservation_negative_and_cancelling_changes(self):
        for z,dn,dt in [(0,0,0),(-1,-2,3),(3,2,-2),(-5,.2,-.3)]:
            result=q4.shapley(z,dn,dt)
            self.assertAlmostEqual(result['scale_points']+result['non_scale_points'],
                q4.sigmoid(z+dn+dt)-q4.sigmoid(z),places=12)
        self.assertIsNone(q4.shapley(3,2,-2)['signed_scale_share'])

    def test_bounds_and_units(self):
        self.assertAlmostEqual(q4.sigmoid(0),50)
        self.assertTrue(np.all((q4.sigmoid(np.arange(-100,101))>=0)&(q4.sigmoid(np.arange(-100,101))<=100)))
        # N,D each in billions; toy case 2B parameters, 3B tokens.
        self.assertEqual(6e18*2*3,6*(2e9)*(3e9))

    def test_rank_failure_is_explicit(self):
        with self.assertRaises(ValueError): q4.ols(np.ones((5,2)),np.arange(5))

    def test_past_snapshot_keeps_version_before_future_revision(self):
        rows=[]
        for month in range(6,12):
            for i in range(12):
                rows.append({'Model':f'org/m{month}_{i}','source_row':len(rows)+2,
                    'date':pd.Timestamp(f'2024-{month:02}-15',tz='UTC'), 'N':1+i, 'S':20+i+month,
                    'type':'pretrained'})
        # Same name reappears in October. A final global dedup would remove
        # June's row before the first October forecast, contaminating train_n.
        rows[48]['Model']=rows[0]['Model']
        original=q4.OUT
        try:
            with tempfile.TemporaryDirectory() as tmp:
                q4.OUT=Path(tmp)
                resources=pd.DataFrame({'date':pd.to_datetime([],utc=True),'C':pd.Series([],dtype=float)})
                q4.rolling(pd.DataFrame(rows),resources)
                result=pd.read_csv(q4.OUT/'rolling_frontier_backtest_primary.csv')
                self.assertEqual(result.iloc[0].train_n,48)
                self.assertAlmostEqual(result.iloc[0].model_overlap_test_fraction,1/12)
        finally: q4.OUT=original


class PublishedIntegrationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads((q4.OUT/'results.json').read_text(encoding='utf-8'))
        cls.forecast=pd.read_csv(q4.OUT/'frontier_forecast.csv')

    def test_forecasts_are_finite_conditional_and_resource_closed(self):
        f=self.forecast
        primary=f[f['filter']=='base_chat_domain_latest']
        self.assertEqual(len(primary),16)
        self.assertTrue(np.isfinite(primary.predicted_score).all())
        self.assertTrue(primary.predicted_score.between(0,100).all())
        self.assertTrue((primary.scenario_lower<=primary.predicted_score).all())
        self.assertTrue((primary.scenario_upper>=primary.predicted_score).all())
        np.testing.assert_allclose(f.C_future_FLOPs_scenario,6e18*f.N_future_B*f.D_future_B_scenario,rtol=1e-12)
        self.assertEqual(set(f.origin),{'2025-03-13'})
        self.assertTrue(f.status.str.startswith('conditional').all())

    def test_resource_and_bridge_gates(self):
        r=pd.read_csv(q4.OUT/'c4_usable_resources.csv')
        self.assertTrue((pd.to_datetime(r['Publication date'])<=pd.Timestamp('2025-03-13')).all())
        self.assertTrue(r.C_over_6ND.between(.5,2).all())
        self.assertTrue((r['Open model weights?'].str.lower()=='yes').all())
        self.assertEqual(self.result['bridge']['formal_cross_coordinate_status'],'unidentified')
        p=pd.read_csv(q4.OUT/'q3_bridge_sensitivity.csv')
        self.assertTrue(p.empirically_calibrated_score.isna().all())
        self.assertTrue(p.joint_95_prediction_interval.isna().all())
        self.assertTrue(p[p.status=='out_of_support_or_infeasible'].assumption_score.isna().all())

    def test_manifest_inputs_and_outputs(self):
        manifest=json.loads((q4.OUT/'manifest.json').read_text(encoding='utf-8'))
        for path,digest in manifest['input_sha256'].items():
            self.assertEqual(q4.sha(q4.ROOT/path),digest,path)
        for path,digest in manifest['output_sha256'].items():
            self.assertEqual(q4.sha(q4.OUT/path),digest,path)


if __name__=='__main__': unittest.main()
