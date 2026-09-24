# CYJ Handoff：诊断接口最终发布、CHM 合并检查与 PR 草案

## Task

按 `CYJ_NEXT_TASKS_FOR_CODEX.md` 完成 Task 1–10 中 CYJ 可独立执行的工作；Task 1A 的 CHM 本人实际消费、Task 11 的 GitHub PR 网页更新待外部完成。此文件取代 `20260924-2200-chm-consumable-release.md` 的旧发布 SHA。

## Input

- branch: `team/cyj-scaling`
- current main base at inspection: `b1198a1dc9bf4dc8a989811eab30f4d1c1551162`
- CYJ immutable release commit: `c71807d01b66744f3a6ca45147d9173bc2704a27`
- CHM Q1 v1.2 producer commit: `a5525935b37f873235d2f650e4810a787b9a8788`
- CHM branch head checked for merge: `cc199fe35beb50fe40d081d3a09539d3dcb3399a`
- chm Q1 manifest SHA256: `5885317d072739b02cdbb434fc730dde07510eb284dc857e35863adc877e914d`
- CYJ v2 manifest SHA256: `962c321846ebd9e80a3011924d9ad3da5911f2797194f23ba56c237e66f25e46`
- CYJ v2 expected response SHA256: `844b625f7ad9d8f4680b2e87d51432606fddc55ecb892da2b6cfd6a0322af4a1`
- consumed B files/individual SHA256: see `data/raw/F_MANIFEST.json`, machine outputs and their experiment records; seven consumed CHM producer file Git blob identities are in v2 manifest.

## Changes

`cyj.chm.v2` exposes B7-native NDQ diagnostic `value_grad`, sample and JSON APIs, three stated cost families, budget residuals and separate Q1 v1.2 A-side 13-target p sensitivity. It rejects formal mode, old eta and implicit A/B Loss addition. Old `cyj.q3.v1` is marked historical and formal use prohibited. The v2 machine response now distinguishes conditional mean interval from null total prediction/cross-source/benchmark bridge intervals. `interfaces/cyj/CONTRACT.md` points to the current release.

CYJ audited joint identifiability, B7 within-ND slopes and five nested grouped candidate forms, B1 Loss provenance, B4/B5 Loss comparability, B8 Q-direction/0.5 conflict, and B9/B10 extrapolation roles. CYJ Q2 and Q3 theory LaTeX sections are filled. Exact scripts, numeric results and limitations are in `problem/cyj/20260924-*.md`, `experiments/cyj/20260924-*.md`, and `outputs/cyj/`.

## Commands and tests actually run

```powershell
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/chm_consumer_smoke.py --release-commit c71807d01b66744f3a6ca45147d9173bc2704a27
git merge-tree --write-tree cc199fe35beb50fe40d081d3a09539d3dcb3399a c71807d01b66744f3a6ca45147d9173bc2704a27
```

- CYJ unit tests: 44 total, 44 pass, 0 fail.
- Exact release smoke: PASS, two actual sample requests plus `value_grad`, `ready_for_Q3=false`.
- XeLaTeX collaborative paper compile: exit 0, five-page PDF; only rerun/hyperref warnings.
- The dry merge returns conflicts only in `paper/latex/sections/cyj/q2.tex` and `q3_theory.tex`. CHM's commit has CYJ placeholders in these files, while CYJ's release has the completed text. Resolve both to the full version from `c71807d` and inspect the resulting paper. No CHM branch was modified, and this dry merge is not CHM acceptance.
- Temporary full worktree checkout for the merge test was interrupted because of Windows long-path and LFS checkout problems. Its Git registration was removed; its empty directory may remain until Windows releases the handle. The `merge-tree` result above is the actual conflict evidence.
- `git lfs pull` stalled and was stopped. Full `scripts/verify_raw_data.ps1` reports exactly four A archive size mismatches because they remain LFS pointers on this computer; all B inputs used in these audits were independently checked against the raw manifest.

## Results, claim and readiness

The full `L(N,D,Q,p)` is **not identified**: no observed paired A/B Q mapping, no common A-target/B Loss coordinate, and no identified p effect across scale. B1 is a within-source conditional N/D reconstruction; B7 is semi-synthetic within-source diagnostic; B8 is isolated because of conflicting quality direction and Loss at shared NDQ points. B9/B10 are estimated extrapolation stress data. The B7 nested interaction comparison is exploratory because forms were proposed after a full-source diagnostic. These are L1/L2 claims only; no validated cross-source predictor or formal Q3 optimum. `ready_for_Q3=false`; Q4 formal bridge is not ready.

## Interface impact and CHM action

CHM can merge the exact `CYJ_RELEASE_COMMIT`, resolve the two CYJ paper files to the release version, and run:

```powershell
python -B src/cyj/chm_consumer_smoke.py --release-commit c71807d01b66744f3a6ca45147d9173bc2704a27
python -B src/cyj/chm_adapter_v2.py --request outputs/cyj/interfaces/chm_v2_request.json
```

The consumer must use `model.bounds` (B7 D minimum is 10) and record actual solver consumption, returned schema and any adaptation in `memory-bank/handoffs/chm/`. CYJ's local smoke does not establish CHM's own acceptance. ZHH should inspect the null total/cross-source/benchmark uncertainty fields before any Q4 capability claim. The integrator should update public memory only after branch merge and acceptance.

## Draft PR #3 update (not applied to GitHub)

Suggested title: `cyj: Q2 evidence audit and CHM-consumable Q3 diagnostic interface (Draft)`

Suggested body:

> **Branch/release:** `team/cyj-scaling`; immutable code release `c71807d01b66744f3a6ca45147d9173bc2704a27`; main base checked `b1198a1dc9bf4dc8a989811eab30f4d1c1551162`; producer `chm.q1.v1.2@a5525935b37f873235d2f650e4810a787b9a8788`. The PR head should be refreshed from remote when editing, because documentation commits may follow this release.
>
> **Work:** B1 provenance and baseline/ablation; B7 native NDQ fit, within-ND Q-slope and nested interaction comparison; B8 conflict audit and isolation; B9/B10 estimated extrapolation audit; B4/B5 same-coordinate check; Q2/Q3 theory draft; `cyj.chm.v2` machine API and explicit uncertainty/usage gates.
>
> **Verification:** 44/44 CYJ unit tests, exact release smoke PASS with two requests and `value_grad`; XeLaTeX draft compiles. CHM real-branch consumption remains pending. A-side four LFS archives on this computer remain pointers, so full 2014-file raw verification does not pass; B audit inputs were independently verified.
>
> **Scientific status:** complete `L(N,D,Q,p)` not identified. B1/B7 results are conditional diagnostics; B7 interaction comparison is semi-synthetic exploratory; B8 kept isolated; B10 estimated, not external test. Prediction, cross-source and benchmark bridge intervals are null. `ready_for_Q3=false`; formal Q3 and Q4 claims blocked.
>
> **Cross-branch merge:** dry merge with CHM `cc199fe35beb50fe40d081d3a09539d3dcb3399a` conflicts only in CYJ-owned `q2.tex` and `q3_theory.tex`: take full CYJ release content in both, replacing CHM placeholders. CHM must run its solver with `model.bounds`, record actual consumer acceptance and any fixes. ZHH reviews uncertainty/bridge fields; integrator accepts and updates public memory. Keep this PR Draft.

GitHub PR #3 was **not** edited: no `gh` CLI or GitHub connector was available, and the in-app browser operation timed out twice. The body above is a concrete proposed update, not a claim that PR metadata changed.

## Remote checkpoint status

The earlier code release `c71807d01b66744f3a6ca45147d9173bc2704a27` was pushed and its remote SHA verified. The subsequent documentation-only checkpoint is local. A new `fetch`, `ls-remote`, and three non-forced `push` attempts failed on GitHub HTTPS connection, slow-transfer, or connection-reset errors. Therefore this handoff and `CONTRACT.md` revision are **not yet backed up remotely**; the next CYJ session should retry the push and verify `ls-remote` SHA before describing the final handoff as published. No force push is authorized or needed.

## Next and owner

- CHM: merge exact release, resolve two placeholder conflicts, run smoke plus real solver consumer, write CHM handoff.
- ZHH: review diagnostic/uncertainty contract before Q4 use.
- Integrator: review code/data/claims, update public memory and PR metadata while retaining Draft, and gate formal status.
- CYJ: respond to genuine consumer defects; obtain B1/B4/B5 source provenance and paired A/B calibration before revisiting joint identification.
