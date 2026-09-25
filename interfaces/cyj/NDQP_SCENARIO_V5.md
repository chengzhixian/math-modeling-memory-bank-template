# CYJ NDQP conditional scenario v5

Status: `conditional_diagnostic=true`, `ready_for_Q3=false`, `formal_ready=false`.
This new interface leaves immutable `cyj.chm.v4` unchanged. CHM accepted v4
for conditional B7/NDQ numerical consumption in
`memory-bank/handoffs/chm/20260925-cyj-v4-owner-acceptance.md` on its own
branch. CHM owner acceptance of the v5 p extension has not been recorded.
Neither state establishes an A/B calibration.

## Exact inputs and provenance

- `src/cyj/joint_ndqp_scenarios.py:ConditionalNDQP` exposes `evaluate_ndq`,
  `evaluate_ndqp_scenario`, `gradient`, `transfer_derivative`, `local_substitution`,
  `equal_loss_root`, `assumptions`, `support`, and `calibration_status`.
- B7 native joint model is the already published eight-parameter fit. Inputs
  `N_params_B`, `D_tokens_B` are billions; `Q_score` is B7 native, not `Q_A`.
- A producer is pinned at CHM commit
  `cdda1ad62c5c7eb72b413c4228caeff87d2bad30`, schema `chm.q1.v1.3`,
  manifest SHA256 `925cf317c861e5f65d7f2ebdaebc693bc7f4b60d17d486488e87858bce4b5d80`.
  The loader verifies normalized SHA256 and row counts of all five published
  producer CSVs. It does not read raw A tables.
- `p` must name exactly the 17 CHM domains and lie on the nonnegative unit
  simplex. Producer validation does not provide a callable training recipe
  convex hull check, so this further support property is not certified. For
  each exact supplied `p`, the interface checks the smallest factor across
  both B7 `N` endpoints, which proves positivity over the whole B7 N interval
  at that `p`; it does not certify positivity over the entire p simplex.
- `weights` must explicitly name one or more of the 13 targets and sum to one.
  `bridge_lambda` and `eta` are required numeric arguments, with no defaults.
  Both remain **unidentified**. `N_ref=1`B is inside B7 support, while the
  A-native effects were estimated at 1M outside B7 support.

The output is `L_B(N,D,Q_B)*(1+lambda*(N/1B)^(-eta)*r_w(p))`, where
`r_w=sum_k w_k beta_k·(p-p_ref)/L^A_{k,ref}` and `L^A_{k,ref}` is the positive
fitted CHM Ridge prediction at `p_ref`. The output reports the factor,
baseline, analytic gradient, and improvement elasticities. Invalid and
nonfinite inputs, nonpositive factors, and NDQ support violations raise
`ValueError`. The quality derivative treats `Q_B` as independent of `p`.

## Consumer fixture

```python
from joint_ndqp_scenarios import ConditionalNDQP
m = ConditionalNDQP()
p = m.a["reference"].copy()
p["arxiv"] += .01
p["freelaw"] -= .01
v = m.evaluate_ndqp_scenario(1, 100, .5, p=p,
    weights={"arxiv": 1.0}, bridge_lambda=.5, eta=0)
assert abs(v["loss"] - 2.5577553937078172) < 1e-12
```

Run with `src/cyj` on `PYTHONPATH`; the import uses Python standard library
and Git, and resolves the pinned CHM producer from the local Git object store.
For process consumers, call `python -B src/cyj/joint_ndqp_scenarios.py --describe`
or `--request interfaces/cyj/fixtures/nonzero_bridge.json`. The batch schema
is `cyj.ndqp.scenario.v5` with explicit `conditional_diagnostic` mode and no
default lambda or eta. Three fixed request fixtures are published in
`interfaces/cyj/fixtures/`: reference/zero lambda, nonzero conditional bridge,
and invalid p (expected exit code 2). Duplicate JSON keys and unsupported
fields are rejected.
Run `python -B -m unittest discover -s src/cyj/tests -p
test_joint_ndqp_scenarios.py -v` for reference/zero-lambda degeneration,
finite differences, support and provenance checks. See
`outputs/cyj/q2_joint_scenarios/manifest.json` for scenario output hashes.

The v4 API and numerical values are unchanged. v5 is a scenario interface,
not a validated four-variable predictor; independent B-native observations
with varied `p` are required to identify the bridge.
