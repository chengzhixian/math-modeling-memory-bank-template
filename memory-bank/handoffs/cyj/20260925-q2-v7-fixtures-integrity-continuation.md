# CYJ Q2 v7 fixtures and integrity continuation — 2026-09-25

New work: expanded production request/expected fixtures from 16 to 19 by adding duplicate-key raw JSON, nonfinite raw JSON and the real observed Q1 recipe with zero direct-Q_A coverage. The verifier now catches parser-stage errors and compares them with expected diagnostics. A temporary corrupt copy of the signed Q1 model file is rejected by the v2 consumer. Finite differences now check both exp and linear bridge gradients in N/D/Q.

Evidence: `python -B src/cyj/build_v7_fixtures.py` generated 19 cases; `python -B src/cyj/verify_v7_fixtures.py` returned 19/19 PASS; `python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q` returned 82/82 PASS. No original-A files are accessed by these Q2 routines. The existing output bundle still points to CHM Q1 v2 manifest `c621f7e4...` and frozen B7.

Remaining CYJ work: independent final acceptance/status check and any task-book evidence gaps, especially Q3 integration smoke using frozen CHM cost/C7 contracts if feasible. CHM must separately run and sign its own consumer check. Main integration belongs to the integrator. Cross-source empirical calibration remains unavailable without paired experiments.
