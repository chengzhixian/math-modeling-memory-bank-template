# Q2 conditional NDQP and requirement coverage

Start snapshot: `team/cyj-scaling@2c237b3c6c47133c85e64a50c8129c2a0a829bea`,
clean and equal to remote before work. Latest `origin/main@90ac2d8` was merged.
CHM producer: `cdda1ad62c5c7eb72b413c4228caeff87d2bad30`, Q1 v1.3;
CHM v4 owner acceptance: `memory-bank/handoffs/chm/20260925-cyj-v4-owner-acceptance.md`.
No historical hidden PDF text, discarded Gemini output, or new A cleaning was used.

| Requirement | Input / role | Machine evidence | Conclusion |
|---|---|---|---|
| B1 N,D | 1176 real records; fit and grouped check; billions | `outputs/cyj/classic/classic_fit.json` | same-source reconstruction only |
| B2/B3 | 1029 semi-synthetic Cerebras / Pythia interpolation; shape check | `outputs/cyj/diagnostics/b2_b3_shapes.json` | no shared absolute Loss RMSE |
| B4/B5 | 57 real cross-family points / 44 literature points; descriptive | `outputs/cyj/diagnostics/b4_b5_comparability.json` | 8 rows each inside B1 ND rectangle; tokenizer, corpus, log base, aggregation unverified |
| B6/B7/B8 | 360 nested in B7 450 / B8 1704 conflicting semi-synthetic rows | `outputs/cyj/quality/b7_b8_conflict_summary.json` | B6 no independent test; B8 isolated |
| B9/B10 | 132 metadata / 128 estimated Loss; stress | `outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json` | all B10 N beyond B1; no external error estimate |
| A mixture | CHM 13 target 1M Ridge contrast; 1M/60M/1B held-out ranking | pinned Q1 v1.3 producer, `validation_by_source.csv` | target-specific A coordinate only |

The executable source gate and per-source SHA256 are in
`outputs/cyj/q2_joint_scenarios/requirement_coverage.json`. This updates
question coverage explicitly instead of equating old software tests with all
question requirements. The frozen B7 fit and its 24-fold nested evaluation
remain conditional semi-synthetic evidence; the family was proposed after
inspecting all B7, so the folds are not an untouched test.

The four-variable formula and provenance table are in the CYJ Q2 LaTeX and
`interfaces/cyj/NDQP_SCENARIO_V5.md`. The A Ridge intercept plus beta dot
`p_ref` supplies each positive **fitted** reference denominator; it is never
called an observed B Loss. Nonidentification has a constructive counterexample:
lambda 0 and 1 fit all available source observations identically when B's
unrecorded p is assigned p_ref, but produce different conditional predictions
for a nonzero A contrast. The A scale groups do not isolate pure N because D
and other conditions are incompletely controlled. Q_A-to-Q_B remains unknown.

Grid: lambda `{0,.25,.5,1}`, eta `{-.5,0,.5}`, weights arxiv/pile_cc/equal
13, N `{.1,1,10}`B, D `100`B, Q_B `.5`, and p_ref or two 1% transfers.
`scenario_grid.csv` contains 324 conditional rows; `support_failures.csv`
reports none on this grid. These are analysis ranges, not probability intervals.
The code checks only each point's positivity and simplex, so global positivity
over the entire p simplex and membership in the A training convex hull are
not certified. CHM Q1's held-out rank metrics are consumed without refit.

Reproduction on this machine uses the bundled Python 3.12 runtime:

```text
python -B src/cyj/build_q2_ndqp_evidence.py
python -B src/cyj/run_full_audit.py --coverage-only
python -B -m unittest discover -s src/cyj/tests -p test_joint_ndqp_scenarios.py -q
```

Observed this work block: 324 scenario rows, 0 failed grid points, 5/5 new
tests passed, and both Q2 coverage audit checks passed. Full legacy audit
has not been rerun here because its fitting imports require SciPy, absent
from the bundled runtime. XeLaTeX is likewise not verified in this block.
No four-variable formal accuracy or global optimum claim follows.
