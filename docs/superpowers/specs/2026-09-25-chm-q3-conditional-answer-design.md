# CHM Q3 problem first conditional answer design

Date: 2026-09-25 (Asia/Shanghai). Owner: CHM. Target branch: `integration/chm-q1-clean-20260923`.

## Purpose and decision

Complete the numerical answer to F problem Q3 using the latest CYJ Q2 v7 conditional predictor while preserving Q1 v2 and CYJ's Q2 ownership. The user chose a **conditional Q3 answer**. After inspecting the official DOCX, the recommended main line fixes p using Q1's declared policy, which Q3 explicitly permits, and optimizes N, D and Q under the stated budget. Direct joint optimization of N, D, Q and p is a separate conditional check. Results distinguish numerical validity under stated assumptions from empirical cross-source validation.

The official DOCX asks for at least three budget magnitudes, all three cost terms, comparison of quality-cost functions, a mathematical definition and detection of structural transitions, and C7-based external context sensitivity. Its Q2 states that A and B experiments are independent and requires a testable unifying hypothesis. The desktop DOCX supplied by the user has SHA256 `bc99a72460fa3d947a442d502969a13212ce0ea092d827afdbbf3b55339da4c4`, identical to the repository file. Its AI-use clause requires contestants to understand and independently verify core modeling, derivation and arguments and disclose actual AI use.

## Trusted inputs and scientific boundary

- Official Q3 text: `problem/F/算力约束下提升大语言模型能力的资源配置建模.docx`; data description: `problem/readable/DATA_DESCRIPTION_VISIBLE.md`. Historical hidden PDF text and discarded Gemini commits are excluded.
- CHM Q1 v2 manifest: `interfaces/chm/q1_interface_v2.json`, normalized SHA256 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`. Its current hull bounds file has normalized SHA256 `969f810c0bf54f03492afc243091c339aaf4b27aed5c2164c186e651c7589acc`; both match CYJ v7 pins.
- CYJ release: `origin/team/cyj-scaling@895ad42de670ece04ba7e781817a2126ec34327e`, interface `cyj.ndqp.scenario.v7`. Its Q2 conditional acceptance is recorded, but CHM v7 consumer acceptance and main integration are pending. Consume an exact detached checkout or exact Git objects; do not silently track a moving branch or edit CYJ-owned source.
- ZHH C7 scenarios: 2,048, 8,192 and 131,072 Token. Their status is an external architectural scenario, not a continuous decision variable; the longest context has only one supporting model in ZHH's published C7 table and is a high-end scenario.
- CYJ v7 uses B7 native Q in [0.1, 1], N in [0.07, 11.97] billion parameters, D in [10, 600] billion tokens. Its default hypothesis is `L_B7(N,D,Q_B) exp(r_w(p))`, where `r_w` is the equal-weight 13-target relative Q1 v2 A-side effect, bridge amplitude 1 and size decay 0. Q1 Q_A only screens p through a declared quality policy and is never substituted for Q_B.
- No paired A/B observations identify bridge amplitude, size decay, Q_A-to-Q_B mapping or a joint predictive interval. B7 is semi-synthetic. This particularly limits the claim that any p improves B-side Loss or is a unique empirical Q3 optimum; a larger optimizer does not repair this identification gap. Report `conditional_scenario` and `cross_source_empirical_calibration_complete=false`; never call these rows `formal_validated` or use the existing formal publisher.

## Mathematical program and scenarios

For each fixed budget B, context L, quality family g and Q1-declared p policy, solve the B-native resource allocation

`min_{N,D,Q} L_B7(N,D,Q)`.

The main p is the signed Q1 v2 equal-13-target convex-hull candidate, stated as an **externally selected Q1 policy**. The B-native objective alone does not infer its effect on B Loss. CYJ v7 supplies an explicitly conditional bridge scenario

`min_{N,D,Q} L_B7(N,D,Q) exp(r_w(p_fixed))`.

Both use `C_train=6e18 N_B D_B`, `C_attention=2e14 L N_B D_B`, `C_quality=1e9 D_B max(g(Q)-g(Q0),0)`, total at most B, CYJ B7 bounds and `Q >= Q0`. N_B and D_B are in billions. The baseline Q0=0.5 is an explicitly chosen B-native scenario, not an observed A-to-B mapping. The three g families and their parameters are those in the visible official appendix and current CHM/CYJ cost implementations.

Use the official suggested budgets `{1e19, 1e22, 1e24}` FLOPs, every C7 L, and all exponential, power and logarithmic cost families as the main grid. Keep `1e20` as an extra comparison level feasible across all three contexts. At the B7 support minimum, `1e19` is infeasible for 131,072 Token because its minimum cost is `2.255008e19` FLOPs; report this infeasibility explicitly. Compare the signed Q1 equal-13 candidate with its observed-512 candidate and the `quality_direct` / `quality_direct_and_near` policies. Unmapped Q_A stays unknown. Run explicit bridge amplitude, decay and model-form sensitivity; zero bridge amplitude leaves p unidentified, so it has no unique mixture result.

For the secondary joint check, represent hull p as `p=R^T alpha` for nonnegative 512-recipe weights summing to one. This keeps all 17 p coordinates within observed support. Quality policies add the frozen reference coverage and mapped-mean linear inequalities in alpha. Joint numerical solves optimize log N, log D, Q and active alpha weights together. Use analytic gradients and multiple starts, with an active recipe set that can expand toward the full 512-recipe hull. Run the joint check across representative budgets, contexts and cost families; a failed solve is reported as such.

The v7 default has a positive p factor independent of N, D and Q. Therefore its assumed joint optimum has the same p ranking as the Q1 relative-effect objective and the same N/D/Q minimizer as the B7 objective. This is an algebraic consequence of the assumption, **not evidence that the assumption is true**. Check direct joint solutions against separate Q1 hull and B7 N/D/Q numerical bounds. For positive bridge amplitude with nonzero size decay, the best p ranking remains unchanged, while N/D/Q may change; re-solve representative sensitivity cases. Numerical bounds and KKT checks are floating-point evidence, not interval-arithmetic proofs or statistical confidence intervals.

Define a structural transition at a budget where the set of active support, quality or budget constraints changes between stable neighboring solutions. Report its bracketing interval, the states on both sides and the grid/refinement resolution; changes in cost share without an active-set change are a separate smooth response. Do not extrapolate the pattern beyond B7's supported N/D/Q box. An infeasible scenario is an explicit outcome, not a transition.

## Outputs and paper contract

Add a versioned CHM conditional Q3 result directory with machine-readable optimization rows, 17-domain p records or references, separate `B_native_loss` and `conditional_bridge_loss` fields, cost components, support/quality policy, active sets, budget and KKT residuals, numerical lower/upper gaps, structural-transition brackets, sensitivity rows and a manifest of exact input/code/output hashes, commands, seeds and environment. Include an explicit uncertainty scope: available B7 parameter bootstrap is conditional on fixed p/bridge; no cross-source or joint 95% interval exists. Do not fill missing layers with zero width or a fabricated interval.

Update `paper/latex/sections/chm/q3_numerical.tex` from its v4 diagnostic/TODO state to a conditional v7 answer with the official-budget feasibility table (including infeasible rows), a small representative configuration table, three-cost comparison, mathematically defined active-set transition, the analytic attention/training equality `L_crit=30,000` Token, C7 sensitivity, p-policy/bridge sensitivity, numerical validation and limitations. Every paper number must map to a generated row or manifest. Correct the old B1 diagnostic statement that all three `1e19` contexts are feasible when presenting the B7 v7 result. Keep Q1 frozen and avoid edits to CYJ's Q2 section, ZHH's Q4 section or shared memory.

## Verification and failure handling

1. Check raw-data and safe-reading gates, pinned Q1/CYJ SHA identities, CYJ v7 fixtures, units and support boundaries before any Q3 result generation.
2. Write failing tests for new consumer and joint solver behavior, including rejected stale hashes, out-of-support points, p hull/quality violations, infeasible budgets, gradient finite differences, cost decomposition and truthful status labels. Then implement to pass them.
3. For each main-grid solution, verify the B7 native predictor, and separately replay CYJ v7 when its conditional Loss is shown. Verify all 17 p entries, support/hull reconstruction, budget components and residual, active set and KKT. Cross-check selected joint cases with an independent optimizer and the Q1/B7 numerical bound; require a declared gap tolerance for paper inclusion.
4. Detect structural transitions from changes in the optimizer's active constraints and cost shares as budget varies. Bracket transitions with a denser budget scan; report no transition where evidence finds none. Distinguish support-bound transitions from changes caused by cost-family or bridge assumptions.
5. Re-run the CHM Q3 suite, relevant CYJ v7 fixture checks, paper static checks and available PDF build/visual inspection. Record exact commands, counts and unresolved failures. A green local test suite does not change the cross-source scientific gate.

## Ownership and delivery

CHM owns the Q3 solver, results, its paper section, `memory-bank/members/chm.md` and a new CHM handoff. CYJ v7 remains immutable input; any discovered producer defect is documented for CYJ rather than patched silently in this branch. A checkpoint is committed and pushed to the CHM branch, then the remote SHA is compared with local HEAD. The handoff names the exact CYJ and ZHH refs, evidence, limits and work left for the integrator/Q4 owner.
