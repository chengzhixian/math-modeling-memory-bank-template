# CYJ full audit

Status: **PASS_WITH_LIMITATIONS**

| Check | Status | Detail |
|---|---|---|
| data_hashes | PASS | 6 source files match recorded bytes and SHA256 |
| model_hashes | PASS | c7426036164238d41b92ca08e9ca9087224aeb0c74554478b66093774a5b5b1a |
| B1_fit | PASS | B1 1176 rows, unknown loss generator |
| B7_joint_fit | PASS | 8 parameters, 12 starts, min G=0.194145 |
| nested_CV | PASS | 24 outer folds; 1350 held-out predictions |
| monotonicity | PASS | all 8 support corners have negative N/D/Q derivatives; max L_Q=-0.194145 |
| gradient | PASS | center-point finite differences agree with analytic N/D/Q derivatives |
| interval_coverage | PASS | 18 nominal/method/axis coverage and interval-width cells independently recomputed |
| Q3_budget_sweep | PASS | 330 grid cells; statuses {'converged_feasible': 321, 'infeasible_by_supported_domain': 9} |
| Q3_context_sweep | PASS | 10 contexts including 30000 and 32768 |
| Q3_support_KKT | PASS | 321 solutions satisfy support, budget and recorded KKT check |
| manifest_reproducibility | PASS | manifest reproduced; 12 file hashes agree |
| unit_tests | PASS | ---------------------------------------------------------------------- Ran 56 tests in 3.961s  OK |
| LaTeX_compile | PASS | XeLaTeX built 8-page team draft; no overfull boxes |

## Scientific limits

- B7 semi-synthetic with no real-training external test
- B7 function family was explored before nested evaluation
- bootstrap-plus-residual v4 interval lacks direct held-out coverage calibration
- A/B loss or quality bridge and team acceptance absent
