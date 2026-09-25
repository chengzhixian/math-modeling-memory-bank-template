# CYJ v5 Q2/Q3 release review, 2026-09-25

## A. Scope and source gate

Snapshot: local and remote `team/cyj-scaling@2a8b03e2a26ef4eb25285cb89d14edf28d4ee316`, clean tree; `origin/main@90ac2d871c1f1bb5b2ff390c1da775a2f382a76e`, merge base the same, 0 behind/76 ahead. Reviewed CYJ v4 native predictor, v5 conditional bridge, generated evidence, Q2/Q3 LaTeX and CHM release surface. Other members' implementations and official submission rules are outside scope.

Trusted: visible F statement and `problem/readable/DATA_DESCRIPTION_VISIBLE.md`; 17 B raw CSV hashes in `outputs/cyj/q2_joint_scenarios/requirement_coverage.json`; CHM Q1 v1.3 producer `cdda1ad62c5c7eb72b413c4228caeff87d2bad30`, manifest SHA256 `925cf317c861e5f65d7f2ebdaebc693bc7f4b60d17d486488e87858bce4b5d80`. Excluded: old PDF hidden text, discarded Gemini commits, legacy scale eta, old `cyj.q3.v1` formal path, B10 estimated Loss as external test.

## B. Requirement → data and variable provenance

The coverage JSON records file, field, unit, data role and source hash for each gate.

| Requirement | Fields/source | Role and sufficiency |
|---|---|---|
| N/D scaling | B1 `N_params_B,D_tokens_B,val_loss` | 1176 rows, same-source conditional reconstruction; label generation unknown |
| Trajectories | B2/B3 N,D,Loss,steps | semi-synthetic/interpolated shape only |
| Cross-family | B4/B5 N,D,Loss | descriptive; only 8 rows each inside B1 rectangle, Loss comparability unverified |
| Quality | B7 `N,D,Q_score,val_loss` | 450 semi-synthetic native rows; B6 nested, B8 conflict isolated |
| Large scale | B9/B10 N,D,Loss | B10 estimated; all 128 outside B1 N support; stress only |
| Four-variable Loss | A p/13 target Loss; B7 N,D,Q,Loss | no paired same-Loss N,D,Q,p; bridge unidentified |

| Symbol | Provenance/unit | Role/support | Status |
|---|---|---|---|
| N,D | B1/B7 observed, billions | separate source support; B7 N [.07,11.97], D [10,600] | conditionally_identified within source |
| Q_B | B7 semi-synthetic, unitless | B7 [.1,1] | conditionally_identified within B7 |
| p | CHM A observed 17-domain simplex | A 1M contrast; v5 checks simplex, not training hull | conditionally_identified in A; v5 support incomplete |
| A target Loss | CHM 13 separate fitted coordinates | A reference and 1M effects | conditionally_identified in A only |
| B7 Loss | B7 `val_loss` | same-source fit | conditionally_identified within B7 |
| weights | caller normalized policy | three target policies in grid | scenario |
| lambda, eta | caller dimensionless policy | no paired bridge or isolated scale experiment | not_identified |
| Q_A→Q_B, A Loss→B Loss | no paired observations | no empirical support | not_identified |

## C. Stages 5–18 and findings

| Stage | Finding |
|---|---|
| 5 Identifiability | **BLOCKER** for formal `L(N,D,Q,p)`: lambda/eta cannot be estimated from these tables. A smooth fitted surface cannot identify the bridge. |
| 6 Data role | B1 fit/group CV; B7 fit/nested CV; B2/B3 shape; B4/B5 descriptive; B8 isolated; B9/B10 stress. No held-out same-Loss A/B calibration. |
| 7 Overlap/support | B6 repeats 360 B7 coordinates; B8 shares 224 NDQ coordinates but Loss disagrees. B10 outside B1 N. V5 checks B7 NDQ and exact-p factor positivity, not A hull. |
| 8 Literature | No external paper justifies a bridge. B1 classic and B7 interaction forms are source-limited empirical candidates. |
| 9 Mathematics | V5 checks simplex, positive reference denominator, finite inputs and factor positivity across B7 N for supplied p. Lambda=0 exactly yields B7; gradients and equal-Loss root tested. All-p positivity is unproved. |
| 10 Formula/code | `q2.tex` v5 factor matches `joint_ndqp_scenarios.py` normalization, explicit weights/lambda/eta and B-native Q. Finite-difference and CLI fixtures cover implementation. |
| 11 Data/numeric | Source hashes/rows checked; nonfinite values, duplicate JSON keys and invalid p rejected; B8 floor and opposite Q direction kept separate. |
| 12 Baseline/sensitivity | Lambda=0 B7 baseline; B7 no-Q/constant-G/form ablation; 540 v5 cells over lambda, eta, three weights, three N and five p. Freelaw/pile_cc transfer direction changes by target weights. |
| 13 Validation | B7 24 outer grouped folds/1350 OOF are same-source; family was explored historically. 36 independent Q3 solver cases check software, not global optimum. No held-out A/B bridge test. |
| 14 Claim ladder | B1/B7 native fit: source-conditional L1/L2. V5 transfer directions: model-conditional scenario only; no L3/L4/L5. |
| 15 Cross-interface | V4 keeps p separate; v5 uses explicitly supplied unidentified bridge. Q_A/Q_B independent. CHM v1.3 pinned with file hashes. CHM owner v4/v5 acceptance pending. |
| 16 Reproducibility | `outputs/cyj/audit/full_audit.json`: 19/19 checks and 68/68 tests, four figure hashes, XeLaTeX. Manifests record code/input/output hashes; commands in interface and handoff. |
| 17 From-zero red team | From tables alone: B1 offers N/D/its Loss, B7 N/D/Q/its semi-synthetic Loss, A p/13 targets. No joint response, scale decay or quality map follows. Separate native fits plus policy sensitivity is the supported approach. |
| 18 Git/integration | CYJ vs refreshed main: 0 behind/76 ahead. CHM `origin/integration/chm-q1-clean-20260923@2450971` shares only two changed paths, both CYJ LaTeX sections. CHM new hull audit does not publish v1.4 consumer contract or CYJ acceptance. Main merge belongs to integrator. |

## D. Severity, action and gate

- **BLOCKER — formal joint bridge:** No paired same-Loss data. Affects structural v5 interpretation and any formal Q3 optimum over p. Keep `ready_for_Q3=false`; new paired observations, identification and held-out validation would require bridge/Q3 reruns.
- **MAJOR — support and calibration:** CHM v1.3 lacks a callable training-hull certificate; B7 is semi-synthetic and its family was historically explored on all B7. Keep v5 exact-p scenario only, v4 intervals conditional; re-run support and independent coverage if evidence changes.
- **MAJOR — owner acceptance:** CYJ local CHM smoke and solver diagnostics do not substitute for CHM pulling this exact release and recording its own result.
- **MINOR — stale statement:** V5 document incorrectly said CHM accepted v4. Corrected in this follow-up; PR and handoff must preserve pending status.

**Final judgment: NOT READY** for formal joint Q2/Q3 science. V4 B7 and v5 explicit sensitivity remain reproducible conditional artifacts, not a validated four-variable Loss or formal optimum.
