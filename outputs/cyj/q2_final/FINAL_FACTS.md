# Q2 FINAL FACTS (paper drafting input, not paper text)

Status: conditional engineering Q2 complete after `final_closure.json` passes; scientific A→B calibration and Q3 owner acceptance remain pending.

## Frozen model and assumptions

- Formula: `L_B(N,D,Q_B) * [1 + lambda*(N/1B)^(-eta)*sum_k w_k*(L_A,k(p)-L_A,k(p_ref))/L_A,k(p_ref)]`.
- B7 base: `E + A*N^(-alpha) + B*D^(-beta) + (1-Q_B)*(G0+GN*ln(N)+GD*ln(D/100))`; N and D are billions.
- B7 parameters: E=1.73538613554, A=0.357582948325, B=1.26537325036, alpha=0.339266809084, beta=0.320394570046, G0=0.370147257663, GN=-0.0594920641691, GD=-0.0158051978925.
- Engineering point: `N=1B, D=100B, Q_B=0.5, lambda=1, eta=0, w_k=1/13`; lambda/eta are not estimated.
- Source: `outputs/cyj/q2_final/model_coefficients.json`, `main_policy.json`; Q1 derived recipe manifest is in `q1_bundle_consumer_audit.json`.

## Supported composition policies

- Ridge main convex-hull/observed optimum: Q1 recipe `136`, conditional Loss `2.192822814440`, factor `0.854103611199`.
- All 17 proportions at the main p: arxiv=0.000000000, dm_mathematics=0.225225225, enron_emails=0.000000000, europarl=0.000000000, freelaw=0.018018018, github=0.159159159, gutenberg_pg_19=0.085085085, hackernews=0.039039039, nih_exporter=0.054054054, philpapers=0.008008008, pile_cc=0.187187187, pubmed_abstracts=0.001001001, pubmed_central=0.059059059, stackexchange=0.000000000, ubuntu_irc=0.162162162, uspto_backgrounds=0.002002002, wikipedia_en=0.000000000.
- Direct Q1 QA policy: Loss `2.263949598560`, 3 recipe weights; direct+near QA: `2.274988571899`, 3 weights.
- 13-target minimax: conditional equal-weight Loss `2.416838301146`, 10 recipe weights; its optimization objective is max target-relative effect.
- Source: `p_policy_details.json`, `p_optimization_by_scenario.csv`, `quality_mapping_sensitivity.csv`.

## Quality versus scale

- Raising Q_B from 0.5 to 0.6 at main p keeps old Loss if N becomes `0.781740379` (base 1); status `supported`.
- Raising Q_B from 0.5 to 0.6 at main p keeps old Loss if D becomes `70.171737756` (base 100); status `supported`.
- Source: `quality_vs_scale.csv`, `marginals_elasticities.csv`.

## Source-bound validation

- B1: 1,176 rows; leave-one-N-level mean RMSE `0.000146127667`; tail RMSE `0.000116004137`. B1 is a near-exact reconstruction and requires provenance caution.
- B4: within-family/source scale-dominance concordance `131/133`; B5: `113/113`. These are descriptive, not cross-source RMSE.
- B7: 24 nested held-level folds; pooled N/D/Q RMSE `0.050070/0.050039/0.049697`. B7 is semi-synthetic; B6 overlaps it and B8 is quarantined.
- B9 is metadata; B10 loss is estimated stress only. Q1 1B Ridge beat a constant-RMSE baseline for 4/13 targets.
- Source: `validation_summary.csv` and its cited frozen source files.

## Q1 fitted domain interactions

- The following are *screened fitted-basis* 1M Q1 cross partials. Negative means model-conditional complementarity under lower-is-better Loss; the descriptive sign screen is not a significance test, causal result, or B7 transfer claim:
- A4 design has full feature rank 27/27 and interaction-block rank 10/10 after linear projection; this checks numerical design support, not scientific transportability.
  - `arxiv × github`: equal-weight normalized cross partial `-0.721647`, negative in 13/13 targets, training-fold sign agreement 65/65, both domains positive in 213/512 recipes.
  - `freelaw × pubmed_central`: equal-weight normalized cross partial `-0.459340`, negative in 13/13 targets, training-fold sign agreement 62/65, both domains positive in 238/512 recipes.
  - `arxiv × pile_cc`: equal-weight normalized cross partial `-0.457230`, negative in 13/13 targets, training-fold sign agreement 65/65, both domains positive in 225/512 recipes.
  - `freelaw × pile_cc`: equal-weight normalized cross partial `-0.309587`, negative in 13/13 targets, training-fold sign agreement 64/65, both domains positive in 231/512 recipes.
- Remaining pairs have cross-target sign disagreement or weaker training-fold stability; do not call them stable complementarity/substitution.
- The published interaction candidate beats frozen Ridge RMSE on 13/13 Q1 1B targets, yet beats the constant absolute-RMSE baseline on only 11/13. The scale shift remains, and no A→B bridge is identified.
- Source: `domain_interactions.csv`, `interaction_summary.json`, Q1 `outputs/chm/q1_exports/q1_interaction_bundle_v1/`.

## Model-form and bridge sensitivity

- `equal_13` on the same 512 observed recipes: Ridge index `136`, interaction index `136`, interaction regret of Ridge choice `0.000000000`, Ridge regret of interaction choice `0.000000000` (objective-relative units).
- `arxiv_only` on the same 512 observed recipes: Ridge index `300`, interaction index `3`, interaction regret of Ridge choice `0.165061773`, Ridge regret of interaction choice `0.159403551` (objective-relative units).
- `minimax_13` on the same 512 observed recipes: Ridge index `163`, interaction index `477`, interaction regret of Ridge choice `0.027691883`, Ridge regret of interaction choice `0.043078741` (objective-relative units).
- Added bridge grid: 324 rows, valid conditional Loss range `1.241578`–`3.473967`; this is scenario spread, not a confidence interval.
- Source: `ridge_vs_interaction_policy.csv`, `new_sensitivity_grid.csv`, `sensitivity_summary.json`; four new figure hashes in `manifest.json`.

Q1 interaction export and v6 consumption await CHM owner signoff. `ready_for_Q3=false` concerns scientific calibration and stays false.
