# CHM Q3 Conditional Answer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a reproducible, problem-aligned conditional Q3 numerical answer, paper section and CHM handoff from pinned CYJ v7 without claiming an identified A/B bridge.

**Architecture:** A CHM consumer pins CYJ v7 in a local read-only checkout and verifies source identities. The existing CHM B7 optimizer/certificate computes B-native N/D/Q configurations for official budget and C7 grids; the signed Q1 v2 mixture policy is attached explicitly, and CYJ v7 evaluates the separate conditional bridge scenario. A smaller direct joint N/D/Q/p run checks the algebraic reduction and quality-policy sensitivity; a publisher writes auditable tables and a manifest, then Q3 LaTeX draws only from those tables.

**Tech Stack:** Python 3.12, NumPy, SciPy, `unittest`, Git worktree for pinned CYJ source, PowerShell, LaTeX.

**Spec:** `docs/superpowers/specs/2026-09-25-chm-q3-conditional-answer-design.md`

## Global Constraints

- Work on `integration/chm-q1-clean-20260923`; keep Q1 v2 and CYJ Q2 source unchanged.
- Official Q3 budgets `1e19`, `1e22`, `1e24` FLOPs; extra `1e20` comparison; C7 contexts `2048`, `8192`, `131072` Token; quality families exponential, power, logarithmic; `Q0=0.5` is a B-native scenario.
- CYJ input is exact `895ad42de670ece04ba7e781817a2126ec34327e`; Q1 manifest `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`; Q1 hull bounds `969f810c0bf54f03492afc243091c339aaf4b27aed5c2164c186e651c7589acc`.
- Separate B-native B7 Loss from CYJ v7 conditional bridge Loss. `cross_source_empirical_calibration_complete=false` and no joint 95% interval. Do not call conditional rows `formal_validated`.
- No hidden PDF text, invalidated Gemini commit, raw-A refit, unsupported Q_A-to-Q_B mapping, or silent out-of-support prediction.

## Review Focus

1. A `1e19`/131072-token request should produce an explicit infeasible row with minimum cost, never an optimizer exception or fake optimum; Task 2 tests this.
2. A stale CYJ checkout or changed Q1 manifest should fail before any result file is written; Task 1 tests this.
3. An observed-512 or quality-constrained p outside its declared support should be rejected; Task 3 tests this.
4. A zero bridge amplitude should report p as unidentified, never a unique p optimum; Task 3 tests this.
5. Paper-facing rows should distinguish B-native and conditional Loss coordinates and contain hashes for reproduction; Task 4 tests this.

---

### Task 1: Pin and verify the CYJ v7 consumer

**Files:**
- Create: `src/chm/q3_v7_inputs.py`
- Create: `src/chm/test_q3_v7_inputs.py`
- Local ignored checkout: `.upstream/cyj-v7`

**Interfaces:**
- Produces: `verify_release(cyj_root: Path, expected_release: str = CYJ_SHA, expected_q1: str = EXPECTED_Q1_SHA) -> dict` with `release_sha`, `q1_sha`, `bounds_sha`; `load_release(cyj_root: Path) -> ConditionalV7`. `CYJ_SHA` and `EXPECTED_Q1_SHA` are the exact values in Global Constraints.
- Consumes: `src/cyj/ndqp_scenarios_v7.py::ConditionalV7`, `interfaces/cyj/NDQP_SCENARIO_V7.md`, signed CHM Q1 v2.

- [ ] **Step 1: Create a task-local runtime and exact upstream checkout.**

  Add `.upstream/` to local `.git/info/exclude`; run `git worktree add --detach .upstream/cyj-v7 895ad42de670ece04ba7e781817a2126ec34327e`. Use `uv venv .venv` and `uv pip install --python .venv/Scripts/python.exe numpy scipy`. Check the worktree HEAD and installed versions before continuing.

- [ ] **Step 2: Write failing identity and fixture tests.**

```python
class V7InputTests(unittest.TestCase):
    def test_rejects_wrong_release(self):
        with self.assertRaisesRegex(ValueError, "release SHA"):
            verify_release(Path("."), expected_release="0" * 40)

    def test_rejects_wrong_q1_manifest(self):
        with self.assertRaisesRegex(ValueError, "Q1 manifest"):
            verify_release(Path(".upstream/cyj-v7"), expected_q1="0" * 64)

    def test_official_pins_match(self):
        release = load_release(Path(".upstream/cyj-v7"))
        self.assertEqual(release.q1.manifest_sha256, EXPECTED_Q1_SHA)
```

- [ ] **Step 3: Run the tests and observe identity failure due to missing consumer.**

  Run: `.venv/Scripts/python.exe -B -m unittest src.chm.test_q3_v7_inputs -v`. Expected: import/function failure.

- [ ] **Step 4: Implement minimal pinned loader and run fixtures.**

  `verify_release` checks `git -C <cyj_root> rev-parse HEAD` and normalized Q1/bounds hashes. `load_release` imports CYJ v7 only from the verified checkout and creates `ConditionalV7(root=cyj_root)`. Run its frozen fixture verifier from the checkout: `.venv/Scripts/python.exe -B src/cyj/verify_v7_fixtures.py` with checkout as working directory; expect 21/21. Run the new tests; expect pass.

- [ ] **Step 5: Commit CHM consumer/tests only.**

  Stage `src/chm/q3_v7_inputs.py` and `src/chm/test_q3_v7_inputs.py`; do not stage `.upstream` or `.venv`.

### Task 2: Compute the official budget and context grid

**Files:**
- Create: `src/chm/q3_conditional_grid.py`
- Create: `src/chm/test_q3_conditional_grid.py`
- Generate: `outputs/chm/q3_conditional_v1/optimization.csv`, `budget_scan.csv`, `transitions.csv`.

**Interfaces:**
- Consumes: Task 1 `load_release`, CYJ `b7`/`THETA`/`BOUNDS`, CHM `q3_generic_solver.solve_generic` and `q3_joint_certificate.certify`.
- Produces: `solve_scenario(model, budget, context, family, q0=.5) -> dict` with explicit feasible/infeasible status and `B_native_loss`; `main_grid() -> list[dict]`.

- [ ] **Step 1: Write failing tests for feasibility and accounting.**

```python
def test_long_context_low_budget_is_explicitly_infeasible():
    row = solve_scenario(B7Adapter(), 1e19, 131072, "power")
    assert row["status"] == "infeasible_within_B7_support"
    assert row["minimum_cost_FLOPs"] > 1e19

def test_three_cost_terms_sum_to_total():
    row = solve_scenario(B7Adapter(), 1e22, 8192, "power")
    parts = ("C_train_FLOPs", "C_quality_FLOPs", "C_attention_FLOPs")
    assert abs(sum(row[k] for k in parts) - row["C_total_FLOPs"]) <= 1e-8 * row["C_total_FLOPs"]
```

- [ ] **Step 2: Run and observe failure due to missing solver.**

  Run: `.venv/Scripts/python.exe -B -m unittest src.chm.test_q3_conditional_grid -v`.

- [ ] **Step 3: Implement B7 adapter, explicit minimum-cost check, certified solve and cost breakdown.**

  Define `B7Adapter.support=Support(*BOUNDS)` and `B7Adapter.value_grad(n,d,q)=b7(n,d,q)`. Use `certify(THETA, BOUNDS, budget, context, family)` and CHM `cost_and_grad`. Refuse rows without feasible support, budget tolerance or KKT. Generate 36 official-plus-extra grid rows, then a dense budget scan and transition brackets with active-set signature checks. Store actual per-scenario lower/upper objective values and numerical gaps; run tests and full CHM Q3 suite.

- [ ] **Step 4: Commit code/tests and deterministic table generation.**

  Regenerate outputs with a fixed command and seed; inspect rows/hashes before staging only Q3 files.

### Task 3: Attach Q1 p policies and check joint conditional optimization

**Files:**
- Create: `src/chm/q3_joint_v7_check.py`
- Create: `src/chm/test_q3_joint_v7_check.py`
- Generate: `outputs/chm/q3_conditional_v1/policies.csv`, `joint_checks.csv`, `bridge_sensitivity.csv`.

**Interfaces:**
- Consumes: Task 1 `ConditionalV7`; Task 2 `solve_scenario`; CHM Q1 v2 hull/observed/quality candidates.
- Produces: `evaluate_policy(model: ConditionalV7, row: dict, p: dict, weights: dict, policy: str) -> dict` with separate conditional Loss; `evaluate_bridge_sensitivity(model: ConditionalV7, row: dict, p: dict, weights: dict, policy: str, bridge_lambda: float, eta: float) -> dict`; `joint_check(row, policy, weights) -> dict` with p support, joint solver objective and independent bound gap.

- [ ] **Step 1: Write failing tests for p support, zero bridge, and factorization.**

```python
def test_zero_bridge_has_no_unique_p():
    model = load_release(Path(".upstream/cyj-v7"))
    row = solve_scenario(B7Adapter(), 1e22, 8192, "power")
    p = model.q1.p_dict(model.q1.recipes[135])
    weights = {target: 1 / 13 for target in model.q1.targets}
    result = evaluate_bridge_sensitivity(model, row, p, weights, "observed_512", bridge_lambda=0.0, eta=0.0)
    assert result["p_identifiability"] == "unidentified"

def test_v7_baseline_factorization():
    model = load_release(Path(".upstream/cyj-v7"))
    row = solve_scenario(B7Adapter(), 1e22, 8192, "power")
    p = model.q1.p_dict(model.q1.recipes[135])
    weights = {target: 1 / 13 for target in model.q1.targets}
    result = evaluate_policy(model, row, p, weights, "observed_512")
    assert math.isclose(result["conditional_bridge_loss"],
                        result["B_native_loss"] * math.exp(result["r_w"]), rel_tol=1e-10)

def test_observed_policy_rejects_unobserved_hull_point(self):
    model = load_release(Path(".upstream/cyj-v7"))
    row = solve_scenario(B7Adapter(), 1e22, 8192, "power")
    p = model.q1.p_dict((model.q1.recipes[0] + model.q1.recipes[1]) / 2)
    weights = {target: 1 / 13 for target in model.q1.targets}
    with self.assertRaisesRegex(ValueError, "observed"):
        evaluate_policy(model, row, p, weights, "observed_512")
```

- [ ] **Step 2: Run and observe failure for missing evaluation functions.**

  Run: `.venv/Scripts/python.exe -B -m unittest src.chm.test_q3_joint_v7_check -v`.

- [ ] **Step 3: Implement policy replay and a bounded direct joint check.**

  Load p candidates from signed Q1 bounds/observed tables and verify through CYJ `Q1V2Consumer.support`. For representative budget/context/family cases, optimize `(log N, log D, Q, alpha)` with alpha a simplex over an expanding active subset of the 512 A4 recipes; evaluate objective and analytic gradients through CYJ v7. Reject unsupported p and failed SLSQP/trust-constr results. Compare to Q1 relative-effect numerical bound times B7 lower bound, report only the achieved floating-point gap. Re-solve representative positive-lambda/eta sensitivity; label zero-lambda p unidentified. Run tests.

- [ ] **Step 4: Commit code/tests and sensitivity tables.**

  Inspect every policy label, support flag and Loss coordinate before staging.

### Task 4: Publish the conditional result and align the Q3 paper

**Files:**
- Create: `src/chm/q3_conditional_publish.py`
- Create: `src/chm/test_q3_conditional_publish.py`
- Modify: `paper/latex/sections/chm/q3_numerical.tex`
- Create: `experiments/chm/20260925-q3-conditional-v7.md`
- Generate: `outputs/chm/q3_conditional_v1/manifest.json` and figures needed by the paper.

**Interfaces:**
- Consumes: Tasks 1–3 outputs; emits versioned `conditional_scenario` data only, not formal v2 publisher data.
- Produces: `validate_conditional_row(row: dict) -> None`, `verify_output_manifest(out_dir: Path) -> None`, `publish_conditional(rows: list[dict], out_dir: Path) -> Path`.

- [ ] **Step 1: Write failing publication tests.**

```python
def test_conditional_rows_cannot_claim_formal_status():
    valid_row = {"status": "conditional_scenario", "B_native_loss": 2.0,
                 "conditional_bridge_loss": 1.8, "budget_FLOPs": 1e22,
                 "C_train_FLOPs": 7e21, "C_quality_FLOPs": 1e21,
                 "C_attention_FLOPs": 2e21, "C_total_FLOPs": 1e22,
                 "cross_source_empirical_calibration_complete": False}
    with self.assertRaisesRegex(ValueError, "formal"):
        validate_conditional_row({**valid_row, "status": "formal_validated"})

def test_paper_row_has_both_loss_coordinates():
    valid_row = {"status": "conditional_scenario", "B_native_loss": 2.0,
                 "conditional_bridge_loss": 1.8, "budget_FLOPs": 1e22,
                 "C_train_FLOPs": 7e21, "C_quality_FLOPs": 1e21,
                 "C_attention_FLOPs": 2e21, "C_total_FLOPs": 1e22,
                 "cross_source_empirical_calibration_complete": False}
    validate_conditional_row(valid_row)
    self.assertIn("B_native_loss", valid_row)
    self.assertIn("conditional_bridge_loss", valid_row)

def test_manifest_rejects_modified_table(self):
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        table = out / "optimization.csv"
        table.write_text("run_id\n1\n", encoding="utf-8")
        manifest = {"files": {"optimization.csv": sha256(table)}}
        (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        table.write_text("run_id\n2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash"):
            verify_output_manifest(out)
```

- [ ] **Step 2: Run and observe failure for missing validator.**

  Run: `.venv/Scripts/python.exe -B -m unittest src.chm.test_q3_conditional_publish -v`.

- [ ] **Step 3: Implement publisher, manifest and paper updates.**

  Validate every feasible/infeasible row, hashes, cost totals, support, KKT and numeric scope before writing. Manifest records exact Git refs, SHA256 files, code/environment versions and uncertainty coverage. Paper table values come from the generated CSV/JSON only. Replace stale v4 placeholder wording; explain 1e19 high-context infeasibility, `L_crit=30000`, cost-family comparison, observed active-set transitions and no calibrated A/B joint interval. Keep old diagnostic facts labeled as historical if retained.

- [ ] **Step 4: Verify science and software claims with fresh commands.**

  Run raw-data/safe-reading gates, 21 CYJ fixtures, all CHM Q3 tests, relevant Q1 freeze hash checks, paper static checks and available XeLaTeX build. Inspect paper PDF if built. Check the official Q3 requirement table line by line, and inspect Git diff for unauthorized Q1/Q2/Q4 changes.

- [ ] **Step 5: Commit, push and hand off.**

  Update `memory-bank/members/chm.md`; add `memory-bank/handoffs/chm/20260925-q3-conditional-v7.md` with exact commands/results/limits. Stage CHM-owned deliverables, commit with prior CHM identity, fetch then push the CHM branch, and compare `git ls-remote` SHA to local HEAD. Report any remote failure honestly.
