# CYJ Q2 conditional numerical delivery

Status: engineering-conditional Q2 calculation and C1–C8 code acceptance. The A-to-B bridge parameters are **not identified by joint observations**. `ready_for_Q3=false` remains the scientific gate; CHM's consumption and signoff of the v6 p extension are pending. This directory contains data products and method checks, not paper text.

## Reproduce

From the repository root on this host:

```powershell
& 'scripts/run_cyj_q2_final.ps1'
```

The first, separately labelled Q1 production step runs `src/chm/export_q1_q2_bundle.py` and publishes `outputs/chm/q1_exports/q1_q2_bundle_v1/`. That step alone reads the original A4 table, checks its SHA, and exports the existing Q1 normalization and frozen v1.3 model. `src/cyj/build_q2_final.py` and `src/cyj/ndqp_scenarios_v6.py` read the hash-checked derived bundle, frozen B evidence, and no original A attachment. Pass `-SkipQ1Export` to rerun only the Q2 consumer. Use `-Python <path>` for another Python 3.12 interpreter with NumPy 2.3.5, SciPy 1.18.1, and Matplotlib 3.11.2. The runner executes seven numerical/API/path-audit tests and finalizes `acceptance.json` only after they pass.

## Main conditional result

The frozen B7 eight-parameter surface is multiplied by `H=1+lambda*(N/1B)^(-eta)*sum_k w_k beta_k·(p-p_ref)/L_A_ref,k`. `N` and `D` are billions of parameters/tokens; `Q_B` is the B7 native quality score. Main engineering assumptions: `lambda=1`, `eta=0`, 13 equal target weights, `N=1B`, `D=100B`, `Q_B=.5`. The 512 complete 17-domain candidate recipes are a Q1-derived export. The Q1 reference composition is in their convex hull, as verified with a coefficient certificate.

| p policy | Conditional loss | Q1 recipe representation |
|---|---:|---|
| 512 observed or unrestricted hull | 2.1928228144 | observed recipe index 136 |
| direct Q1 quality coverage and mean | 2.2639495986 | 3-recipe convex combination |
| direct plus near mapping quality coverage and mean | 2.2749885719 | 3-recipe convex combination |
| 13-target minimax | 2.4168383011 | 10-recipe convex combination |

Full 17 proportions, source indices and weights, 13 Q1 target changes, Q1 quality coverage and conditional factors are in `p_policy_details.json` and `p_optimization_by_scenario.csv`. The LP main objective agrees with independent enumeration of the 512 original vertices; the quality constrained optimum requires an LP over convex weights. At `lambda=0` all feasible p are tied. `Q_A` is a Q1 native family-balanced z-score for a quality *constraint* and is never substituted for `Q_B` in the loss formula. Eleven unmapped domains remain unknown.

At the main supported point, moving `Q_B=.5` to `.6` while preserving the previous Loss requires `N≈0.7817404B` at fixed `D=100B`, or `D≈70.171738B` at fixed `N=1B`. These are within the B7 rectangle. Three reference-to-supported-composition segments are in `p_transfer.csv`; their midpoints were checked in the Q1 recipe hull. `marginals_elasticities.csv` contains 81 main-grid rows over three p policies, and `new_sensitivity_grid.csv` adds 324 bridge/weight/p rows without rerunning the prior 540-grid output in `outputs/cyj/q2_joint_scenarios/scenario_grid.csv`.

## Evidence limits

`validation_summary.csv` separately lists B1 tail and N-level holdouts, B2/B3 trajectory shapes, B4/B5 within-family/source dominance-pair concordance, B7 nested holdouts, B8 conflicts, and B9/B10 support distance. B4: 131 of 133 dominance pairs concordant; B5: 113 of 113. These are descriptive within-source comparisons because common absolute Loss coordinates are not established. B9 is metadata only; B10 Loss is estimated, not an independent measured validation. Q1 1B Ridge absolute RMSE beats its constant baseline for only 4 of 13 targets. B7 is semi-synthetic and has separate parameter/residual uncertainty recorded in the frozen B7 interval and nested-CV files. The `lambda`, `eta`, target weights, and Q1 mapping choices are scenario sensitivity, not confidence intervals.

Q1 published only second-order candidate **metrics**, not complete 13-target interaction coefficients. `model_selection.csv` reports the published Ridge/candidate metrics; `p_optimization_ridge_vs_interaction.csv` is intentionally absent. No nonlinear optimum or cross-model regret is claimed. If CHM publishes the full versioned interaction model, that extra analysis can be added without letting Q2 read raw A data.

`manifest.json` has hashes for every result file and figure. Four new figures and their input CSV hashes are in `figures/cyj/q2_final/manifest.json`. The v6 process contract and four fixed fixtures are in `interfaces/cyj/`. The Q1 export still awaits CHM owner signoff, and the v6 API still awaits CHM Q3 consumption testing.
