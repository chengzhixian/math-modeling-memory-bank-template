# CYJ full audit

Status: **PASS_WITH_LIMITATIONS**

| Check | Status | Detail |
|---|---|---|
| data_hashes | PASS | 6 source files match recorded bytes and SHA256 |
| model_hashes | PASS | c7426036164238d41b92ca08e9ca9087224aeb0c74554478b66093774a5b5b1a |
| B1_fit | PASS | B1 1176 raw rows; RMSE 0.000146576419; loss generator unknown |
| B7_joint_fit | PASS | 8 parameters, 12 starts, raw B7 RMSE 0.0484101276, min G=0.194145 |
| nested_CV | PASS | 24 outer folds; 1350 held-out predictions |
| monotonicity | PASS | all 8 support corners have negative N/D/Q derivatives; max L_Q=-0.194145 |
| gradient | PASS | center-point finite differences agree with analytic N/D/Q derivatives |
| interval_coverage | PASS | 18 nominal/method/axis coverage and interval-width cells independently recomputed |
| Q3_budget_sweep | PASS | 330 grid cells; statuses {'converged_feasible': 321, 'infeasible_by_supported_domain': 9} |
| Q3_context_sweep | PASS | 10 contexts including 30000 and 32768 |
| Q3_support_KKT | PASS | 321 solutions satisfy support, budget and recorded KKT check |
| Q3_model_form | PASS | 144 model-form cases, 132 feasible; all cross-model regrets nonnegative within 1e-5 |
| Q3_independent_optimizer | PASS | 33 feasible independent solutions agree with CHM within 1e-4 Loss; 3 support-infeasible |
| manifest_reproducibility | PASS | manifest reproduced; 13 file hashes agree |
| Q2_requirement_coverage | PASS | six Q2 gates, seven audit hashes, 17 raw B source hashes; limitations explicit |
| Q2_conditional_scenarios | PASS | 540 reproducible conditional cells; no fitted bridge claim |
| Q2_scenario_figures | PASS | four conditional figures match input, plot code and output hashes |
| unit_tests | PASS | ---------------------------------------------------------------------- Ran 68 tests in 4.764s  OK |
| LaTeX_compile | PASS | XeLaTeX built team draft; no overfull boxes |

## Scientific limits

- B7 semi-synthetic with no real-training external test
- B7 function family was explored before nested evaluation
- Q3 N/D allocation changes across plausible B7 quality terms even when modeled loss regret is small
- Derivative-free Q3 agreement on 36 scenarios does not prove global optimality
- bootstrap-plus-residual v4 interval lacks direct held-out coverage calibration
- A/B loss or quality bridge unidentified; CHM v4 conditional owner acceptance completed
