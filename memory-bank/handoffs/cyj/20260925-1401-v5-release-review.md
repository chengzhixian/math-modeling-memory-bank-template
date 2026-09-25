# CYJ → CHM and integrator: v5 release and review

## Task, input and immutable identities

`CYJ_RELEASE_COMMIT=2a8b03e2a26ef4eb25285cb89d14edf28d4ee316` on `team/cyj-scaling`; local and `ls-remote` SHA matched and tree was clean. `CYJ_INTERFACE_SCHEMA=cyj.ndqp.scenario.v5`. `CHM_PRODUCER_COMMIT=cdda1ad62c5c7eb72b413c4228caeff87d2bad30` (`chm.q1.v1.3`), manifest SHA256 `925cf317c861e5f65d7f2ebdaebc693bc7f4b60d17d486488e87858bce4b5d80`. B7 and 17 B raw input hashes are in `outputs/cyj/q2_joint_scenarios/requirement_coverage.json`. This follow-up documentation correction does not change the released machine code.

## Changes, commands, tests and result

V5 provides a standard-library batch JSON CLI and callable conditional NDQP model, three requests, 540 scenario cells, four hashed figures, Q2/Q3 mathematics and source-role audit. Reproduce with `python -B src/cyj/build_ndqp_v5_fixtures.py`, `python -B src/cyj/build_q2_ndqp_evidence.py`, `python -B src/cyj/plot_q2_ndqp_scenarios.py`, `python -B src/cyj/run_full_audit.py`; plotting/audit use the environment in `problem/cyj/environment.md` plus local SciPy 1.18.1 and Matplotlib 3.11.2. Full audit 19/19, CYJ unit tests 68/68, four figure hashes, XeLaTeX 11 pages without overfull. Local CHM solver diagnostic: 330 Q3 budget cells, 321 feasible; 36 independent optimizer comparisons. These are software and conditional B7 checks, not formal four-variable validation.

## CHM pull and consumer smoke

CHM owns its branch. From a clean CHM worktree:

```powershell
git fetch origin --prune
git switch integration/chm-q1-clean-20260923
git pull --ff-only
git merge --no-ff 2a8b03e2a26ef4eb25285cb89d14edf28d4ee316
python -B src/cyj/chm_consumer_smoke_v4.py --release-commit 3471530d91c8ee7eb709e5cd6c824eb9c423e0df
python -B src/cyj/joint_ndqp_scenarios.py --describe
python -B src/cyj/joint_ndqp_scenarios.py --request interfaces/cyj/fixtures/nonzero_bridge.json
python -B -m unittest discover -s src/cyj/tests -p test_joint_ndqp_scenarios.py -v
```

CHM must retain the exact CYJ commit in its experiment record, verify schema, producer SHA, N/D/Q units, p policy, support, Loss coordinate, uncertainty and false ready gate, then test that its Q3 solver consumes the response without source edits. If merging the whole branch, CHM should inspect the two CYJ LaTeX sections changed on both branches and recompile. An exact-commit read-only consumer is also valid if CHM does not merge. No parameter copying is needed.

## Identifiability, claim and unresolved owners

`ready_for_Q3=false`, `formal_ready=false`. B7 N/D/Q is a semi-synthetic conditional surface; A p is 13-target 1M sensitivity. Lambda, eta, Q_A→Q_B and A Loss→B Loss are **not_identified**. CHM v1.3 exposes no callable training-hull certificate, so v5 does not certify every p. V5 directions are model-conditional scenarios below L3, not causal or held-out B validation. Full 18-stage review: `problem/cyj/20260925-v5-release-review.md`.

CHM owner acceptance is pending: CHM should add its own consumer handoff with PASS/FAIL, actual example and solver status. CYJ owns interface fixes from that test; integrator owns public memory and main merge. The newer CHM `2450971` hull audit is useful follow-up evidence but does not change this pinned v1.3 release.
