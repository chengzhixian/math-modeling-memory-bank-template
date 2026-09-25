# CYJ Q1 v2 → Q2 v7 implementation checkpoint

Status: WIP, not a final Q2 release. Owner: CYJ task implementation under the user's explicit current request. Branch: `team/cyj-scaling`; clean starting merge SHA `a3b487789d8b41b2ee25d243fc56301c10843738` (remote verified before development).

## Change

Implemented a hash-pinned consumer for CHM Q1 v2, a conditional exponential baseline and linear/sensitivity variants, policy and numerical-bound consumption, derived-only output generation, request fixtures and regression tests. Updated CYJ Q2 paper to refer to Q1 v2 rather than the historical Ridge bridge. New files are under CYJ-owned src/interfaces/outputs/paper/memory paths only.

## Evidence and reproduction

Source Q1 manifest SHA256 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`; source release commit `333b1f0bbed65da43f6be2f197d9582555dc755d`, integrated in main `f9693bbf4c205aa46d3719f6f8a1d6f26561d05f`. Upstream reader verified the manifest and all nine referenced file hashes. Frozen B7 vector matched `outputs/cyj/q2_final/model_coefficients.json`. Commands so far: `python -B src/cyj/audit_q2_v7.py`, `python -B src/cyj/build_v7_fixtures.py`, and v6/v7 targeted unittest discovery. Local Python 3.12 required SciPy 1.18.1 in ignored task-local `.task_deps`; NumPy 2.3.5. Output observed: 12 policy rows; 480 sensitivity rows; v7 tests 6/6; v6 tests 7/7; original A open events 0 and Q1 derived events 15 under Python open-audit. See `outputs/cyj/q2_v7_runtime_audit.json` for exact coverage limits. Results are conditional scenarios, not A/B calibration.

## Unresolved and next steps

CYJ: rebuild fixtures after source metadata pin update, replay them, run full CYJ suite and paper compile; review output manifest and mathematical/numerical claims; complete source-by-source audit, migration comparison, final acceptance and release. CHM: independently consume exact CYJ release for Q3 before any consumer_verified status. Integrator: accept and merge only after completed handoff. Current v7 status remains WIP; single-target continuous hull bounds are not provided by signed CHM release and are marked unavailable, not fabricated.
