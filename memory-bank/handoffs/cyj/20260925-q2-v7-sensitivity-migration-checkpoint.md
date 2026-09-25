# CYJ Q2 v7 sensitivity and migration checkpoint — 2026-09-25

## Changes

- Pinned CHM Q1 v2 manifest `c621f7e4...`; retained frozen B7 and old v6 artifacts.
- Expanded two-form lambda/eta sensitivity to N=0.1, 1 and 10 B (1440 rows); 4 linear scenarios are invalid rather than silently clipped.
- Added matched v6/v7 migration decomposition at N=1 B, D=100 B, Q_B=0.5, equal 13-target weights and the same observed recipe. Historical v6 bundle remains pending CHM owner signoff, so this is an audit comparison, not a validated old release.
- Added eta=0.2 quality–scale root cases and an out-of-support case. Shortened Q2 LaTeX references to address first-pass overfull lines; a second compile/visual check remains.

## Evidence and reproduction

- `python -B src/cyj/audit_q2_v7.py`: PASS, 0 original-A Python opens, 15 derived-Q1 opens; output manifest SHA256 `f4c6b6d9ddcb716adc53a3893272e8186479e985b51648c9589f5b4b8fada3dc`.
- `python -B src/cyj/verify_v7_fixtures.py`: 16/16 PASS.
- `python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q`: 81/81 PASS.
- The local bundled Python requires project-local `.task_deps` on `PYTHONPATH` for SciPy and Matplotlib; the directory is locally excluded from Git.

## Open issues and next owner

- CYJ: complete compilation/visual QA, source/evidence red-team, independent output audit, final status and release record.
- CHM: independently consume v7 fixtures and Q3 sample after CYJ release; until then `q3_consumer_verified=false`.
- Integrator: accept and merge CYJ branch to main. Neither the engineering output nor the bridge has empirical A/B paired-data calibration.
