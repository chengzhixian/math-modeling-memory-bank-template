# CYJ Q2/Q3 checklist review handoff, 2026-09-25

## Change

Reviewed the user-supplied next-task checklist only. Detailed finding and corrected execution conditions: `problem/cyj/20260925-q2-q3-next-task-review.md`. No model, source, interface, fixture or result was changed. The checklist is NOT READY to follow literally; its conditional Q2/Q3 direction remains useful after corrections.

## Evidence/reproduction

Reviewed `team/cyj-scaling@86526a17d698e5fcc585f3099248bfa5a4ad28d8` against official F DOCX, visible data description, Q1 derived manifests, v6 code, Q2 closure outputs and Q3 optimizer code. Remote SHA matched local before this documentation change. Read-only command `src/cyj/ndqp_scenarios_v6.py --describe` exposed stale interaction and hull wording. `python -B -m unittest discover -s src/cyj/tests -p test_q2_final_v6.py -q` passed 7/7 with local dependency access; regular sandbox test initially hit a dependency-directory PermissionError. Did not rerun Q2 full generation, all B fits, or Q3 optimization.

## Open items and owners

- CYJ, if user later requests execution: revise P0-2 to use `-SkipQ1Export` and explicitly regenerate 11 closure checks; keep any Q1 raw-A export as separate CHM upstream work.
- CYJ: refresh v6 self-description/version index, add v6-plus-cost conditional Q3 smoke and independent joint or fixed-p optimization checks; retain old NDQ checks as baseline.
- CHM: independently sign off Q1 interaction export and v6 Q3 consumption in their own branch. ZHH: confirm context/bridge inputs. CYJ may record signed evidence in a versioned release; no one may infer scientific calibration from software signoff.
- Integrator: review before main merge. `formal_scientific_ready_for_Q3=false` remains until paired cross-source calibration and independent validation exist.
