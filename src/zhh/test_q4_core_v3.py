"""Mathematical counterexamples and release gate tests for Q4 v3."""
import unittest
import json
import numpy as np
import pandas as pd
import q4_core_v3 as q4


class CoreChecks(unittest.TestCase):
    def test_record_boundary_preserves_history_and_adds_tail_gap(self):
        self.assertEqual(q4.record_boundary(40, 51, 6), 51)
        self.assertEqual(q4.record_boundary(55, 51, 6), 61)
        self.assertEqual(q4.record_boundary(98, 95, 5), 100)

    def test_quantile_solver_recovers_line_despite_outliers(self):
        x=np.repeat([0.,1.,2.],6)
        y=1+2*x
        y[[5,11,17]]+=40
        b=q4.quantile_fit(x,y,.5)
        np.testing.assert_allclose(b,[1,2],atol=1e-8)
        residual=y-(b[0]+b[1]*x)
        check=lambda r:np.sum(np.maximum(.5*r,-.5*r))
        ols=q4.old.ols(x,y)
        self.assertLess(check(residual),check(y-ols[0]-ols[1]*x))

    def test_rank_deficiency_is_not_fabricated_coefficient(self):
        with self.assertRaises(ValueError):
            q4.quantile_fit(np.zeros(8),np.arange(8))

    def test_standardization_exactly_separates_mix_and_within_cell_change(self):
        def frame(low_n,high_n,shift):
            return pd.DataFrame({'model_class':['chat']*(low_n+high_n),'developer':['a']*(low_n+high_n),
                'logN':[0.1]*low_n+[1.1]*high_n,'S':[10+shift]*low_n+[30+shift]*high_n})
        result,_=q4.decompose(frame(6,2,0),frame(2,6,5),.5)
        self.assertAlmostEqual(result['scale_distribution_points'],10)
        self.assertAlmostEqual(result['within_scale_temporal_points'],5)
        self.assertAlmostEqual(result['composition_support_gap_points'],0)
        self.assertAlmostEqual(result['standardized_change'],15)

    def test_unshared_developer_cannot_be_identified_by_bin_match(self):
        a=pd.DataFrame({'model_class':['chat']*3,'developer':['a']*3,'logN':[1]*3,'S':[10]*3})
        b=a.assign(developer='b',S=20)
        result,_=q4.decompose(a,b,developer_control=True)
        self.assertEqual(result['status'],'insufficient_common_support')
        self.assertNotIn('within_scale_temporal_points',result)

    def test_support_rejection_distinguishes_infeasibility_and_coordinates(self):
        mapping={'a':2,'bLoss':-1,'loss_min':1,'loss_max':2,'N_min_B':1,'N_max_B':10}
        self.assertEqual(q4.convert(mapping,np.nan,2)[1],'infeasible_or_missing_upstream')
        self.assertEqual(q4.convert(mapping,1.5,.1)[1],'N_out_of_support')
        self.assertEqual(q4.convert(mapping,3,2)[1],'Loss_out_of_support')
        self.assertIsNone(q4.convert(mapping,3,2)[0])
        self.assertGreater(q4.convert(mapping,1.1,2)[0],q4.convert(mapping,1.9,2)[0])

    def test_no_compute_growth_has_no_parameter_scale_increment(self):
        a={'S':40}
        value=q4.predict('quantile_resource',np.array([0,2,0]),a,24,1,slowdown=0)
        self.assertAlmostEqual(value,40)
        self.assertAlmostEqual(q4.predict('quantile_resource',np.array([0,0,0]),a,24,1),40)

    def test_release_test_windows_and_parameters_match_future_target(self):
        rows=pd.read_csv(q4.OUT/'rolling_two_month_frontier.csv')
        self.assertTrue((pd.to_datetime(rows.origin)<pd.to_datetime(rows.test_start)).all())
        self.assertTrue(rows.target_window_months.eq(2).all())
        self.assertTrue(rows.forecast_window_months.eq(2).all())
        for _,r in rows.iterrows():
            self.assertEqual(r.drift_retention_assumed,q4.MAIN_RETENTION[r.model])
            self.assertEqual(pd.Timestamp(r.test_end),pd.Timestamp(r.test_start)+pd.DateOffset(months=2)-pd.Timedelta(days=1))

    def test_released_bridge_preserves_source_and_loss_kind(self):
        rows=pd.read_csv(q4.OUT/'bridge_source_coordinate_models.csv')
        primary=rows[rows.diagnostic_primary_candidate]
        self.assertTrue(primary.loss_kind.eq('validation').all())
        self.assertTrue(primary.bLoss.lt(0).all())
        self.assertTrue(rows.cross_Q3_coordinate_status.eq('unidentified').all())
        stress=pd.read_csv(q4.OUT/'q3_source_coordinate_stress.csv')
        rejected=stress.status!='conditional_affine_coordinate_assumption'
        self.assertTrue(stress.loc[rejected,'conditional_score'].isna().all())
        self.assertTrue(stress.empirically_calibrated_score.isna().all())

    def test_scenario_union_contains_every_declared_conditional_range(self):
        ranges=pd.read_csv(q4.OUT/'frontier_scenario_conditional_ranges.csv')
        union=pd.read_csv(q4.OUT/'frontier_scenario_union.csv')
        keys=['type','resource_gate','horizon_months','compute_scenario']
        merged=ranges.merge(union,on=keys,validate='many_to_one')
        self.assertTrue((merged.scenario_union_lower<=merged.conditional_p05+1e-10).all())
        self.assertTrue((merged.scenario_union_upper>=merged.conditional_p95-1e-10).all())
        self.assertTrue(union.scenario_union_lower.ge(0).all())
        self.assertTrue(union.scenario_union_upper.le(100).all())

    def test_main_and_wide_resource_gates_are_actually_reestimated(self):
        rows=pd.read_csv(q4.OUT/'c4_resource_gate_comparison.csv').set_index('resource_gate')
        self.assertGreater(rows.loc['wide_ratio','n'],rows.loc['primary','n'])
        self.assertNotAlmostEqual(rows.loc['wide_ratio','gC_log10_per_year'],rows.loc['primary','gC_log10_per_year'])

    def test_manifest_bytes_match_frozen_inputs_and_outputs(self):
        manifest=json.loads((q4.OUT/'manifest.json').read_text('utf-8'))
        for path,digest in manifest['input_sha256'].items():
            self.assertEqual(q4.old.sha(q4.ROOT/path),digest,path)
        for path,digest in manifest['output_sha256'].items():
            self.assertEqual(q4.old.sha(q4.OUT/path),digest,path)

    def test_all_released_decompositions_keep_support_gap_separate(self):
        rows=pd.read_csv(q4.OUT/'historical_standardized_contributions.csv')
        rows=rows[rows.status=='conditional_standardized_decomposition']
        np.testing.assert_allclose(rows.scale_distribution_points+rows.within_scale_temporal_points,
            rows.standardized_change,atol=1e-10)
        np.testing.assert_allclose(rows.standardized_change+rows.composition_support_gap_points,
            rows.full_observed_mean_change,atol=1e-10)

    def test_forecast_resource_units_and_support_are_explicit(self):
        rows=pd.read_csv(q4.OUT/'frontier_candidate_forecasts.csv')
        np.testing.assert_allclose(rows.C_future_FLOPs_scenario,
            6e18*rows.N_future_B_scenario*rows.D_future_B_scenario,rtol=1e-12)
        stopped=rows[rows.compute_scenario=='stopped']
        np.testing.assert_allclose(stopped.C_anchor_FLOPs_scenario,stopped.C_future_FLOPs_scenario)
        self.assertTrue(rows.time_extrapolation_observed_spans.gt(1).all())

    def test_released_maximum_frontier_keeps_record_floor_and_baseline(self):
        scenarios=pd.read_csv(q4.OUT/'frontier_maximum_scenarios.csv')
        self.assertTrue(scenarios.target_definition.eq('cumulative_best_score_by_target_date').all())
        self.assertTrue((scenarios.conditional_record_lower<=scenarios.conditional_record_center).all())
        self.assertTrue((scenarios.conditional_record_center<=scenarios.conditional_record_upper).all())
        self.assertTrue((scenarios.conditional_record_lower>=scenarios.historical_record_score).all())
        self.assertTrue(scenarios.status.eq('conditional_tail_gap_scenario_not_calibrated_prediction_interval').all())
        backtest=pd.read_csv(q4.OUT/'frontier_maximum_backtest.csv')
        self.assertTrue((backtest.persistence_prediction==backtest.prior_historical_record).all())
        self.assertTrue((backtest.actual_cumulative_record>=backtest.prior_historical_record).all())
        comparison=pd.read_csv(q4.OUT/'frontier_maximum_model_comparison.csv')
        self.assertTrue({'record_persistence','q90_plus_tail_gap'}<=set(comparison.model))

    def test_released_q3_bridge_covers_joint_and_native_quality_modes(self):
        stress=pd.read_csv(q4.OUT/'q3_source_coordinate_stress.csv')
        self.assertEqual(set(stress.policy_mode),
            {'fixed_recipe','observed_joint_recipe','independent_native_Q'})
        nominal=stress[(stress.coordinate_scale_assumed==1)&
            (stress.coordinate_offset_assumed==0)&
            (stress.upstream_loss_stress_delta_assumed==0)&
            stress.diagnostic_primary_candidate]
        low_joint=nominal[(nominal.policy_mode=='observed_joint_recipe')&
            (nominal.budget_FLOPs==1e19)&(nominal.context_tokens==8192)&
            (nominal.quality_family=='power')]
        self.assertEqual(set(low_joint.recipe_index),{477})
        self.assertTrue(low_joint.status.eq('N_out_of_support').all())
        native_mid=nominal[(nominal.policy_mode=='independent_native_Q')&
            (nominal.budget_FLOPs==1e20)&(nominal.context_tokens==8192)&
            (nominal.quality_family=='power')]
        self.assertEqual(len(native_mid),2)
        self.assertTrue(native_mid.status.eq('conditional_affine_coordinate_assumption').all())
        self.assertTrue(native_mid.conditional_score.notna().all())
        summaries=pd.read_csv(q4.OUT/'q3_bridge_conclusion_sensitivity.csv')
        self.assertTrue(summaries.mapping_LOO_RMSE.notna().all())


if __name__=='__main__':
    unittest.main()
