# CYJ conditional NDQP process API v6

`cyj.ndqp.scenario.v6` extends v5 with Q1-derived recipe support and quality-policy checks. It does not alter v4/v5. This interface is an **engineering conditional diagnostic**, not a cross-source calibrated predictor. `ready_for_Q3=false`; CHM owner acceptance of v6 p consumption is pending. No Q2 source file opens an original A attachment.

Run `python -B src/cyj/ndqp_scenarios_v6.py --describe` or `--request interfaces/cyj/fixtures_v6/main_supported_optimum.request.json` with `src/cyj` on `PYTHONPATH`, NumPy and SciPy installed, and the Q1 export present. The producer bundle manifest and each included file are SHA verified at initialization. The frozen CHM v1.3 Q1 model is also verified against its pinned Git commit. `--describe` reports the Q1 export manifest SHA and current support.

## Request

Top level: `schema_version`, `mode="conditional_diagnostic"`, and nonempty `requests` array. Every item requires `request_id`, `N_params_B`, `D_tokens_B`, `Q_score`, `p`, `weights`, `bridge_lambda`, `eta`; optional `p_policy` and `model_variant`. `N` and `D` are billions. `Q_score` is **B7 native** `Q_B`, not Q1 `Q_A`. All 17 Q1 domain keys must be present in `p`, nonnegative and summing to one. `weights` names Q1 targets, is nonnegative and sums to one. The explicit engineering bridge has `lambda>=0`; `eta` is finite.

`p_policy` values: `observed_512`, `convex_hull` (default), `quality_direct`, `quality_direct_and_near`, or `algebraic_reference_only`. The first four certify Q1 training recipe support. The quality policies require coverage and mapped mean Q1 quality at least as high as the Q1 reference under their respective mapping rules; unmapped domains are not assigned a score. Algebraic reference mode accepts only `p_ref` and reports its independently checked hull certificate.

`model_variant="ridge_main"` is the only callable variant. Requesting `interaction_sensitivity` fails explicitly because Q1 supplied comparison metrics but no complete 13-target second-order coefficients. No second-order prediction is fabricated.

The model checks `N∈[.07,11.97]B`, `D∈[10,600]B`, `Q_B∈[.1,1]`, and a positive factor `H=1+lambda*(N/1B)^(-eta)*r_w(p)` over the full B7 N interval for the given p. The response includes conditional Loss, frozen B7 baseline, factor, N/D/Q and 17 ambient p gradients, improvement elasticities, p hull status and certificate, Q1 quality coverage/mean, assumptions and provenance hashes. The reported p partials are ambient derivatives; physically feasible composition transfers use differences or convex-hull paths. Invalid requests exit 2 with a JSON `error` on stderr. Duplicate JSON keys and unsupported fields are rejected.

Four request/expected pairs are in `interfaces/cyj/fixtures_v6/`: zero-bridge reference, supported main optimum, invalid N, and off-hull p. Regenerate with `src/cyj/build_v6_fixtures.py`. The one-click runner generates outputs, executes the regression and finite-difference tests, and updates `outputs/cyj/q2_final/acceptance.json`. Q1 bundle owner signoff and CHM v6 Q3 integration remain separate handoffs.
