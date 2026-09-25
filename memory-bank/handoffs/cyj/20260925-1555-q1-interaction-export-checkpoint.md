# CYJ Q1 upstream interaction export checkpoint, 2026-09-25 15:55 CST

## Change and evidence

The remote CHM Q1 branch `integration/chm-q1-clean-20260923@2450971` has the complete definition and published metrics for its 13-target second-order candidate, but no callable coefficient package. Following the user-supplied closure task, CYJ wrote and ran **an explicitly upstream Q1 stage**: `src/chm/export_q1_interaction_bundle.py`. It reads/hash-checks original A4/A5 only in `src/chm`, consumes the existing normalized 512×17 Q1 recipe export, and reproduces CHM's fixed five high-variance domains, ten pair products, unshuffled five-fold CV, and seven Ridge alphas. It does not read A6–A11 for tuning, change v1.3, or use the discarded historical models/PDF hidden text.

`outputs/chm/q1_exports/q1_interaction_bundle_v1/` contains full 13-target intercepts/main coefficients/ten interactions/positive fitted reference losses, feature order, training-only fold sign stability, CV summary and all input/output SHA256 values. `interaction_manifest.json` SHA256 is `608595491268cf859331f3f8b9d7618a9e86fef94928120dbfa6ded3082f600c`. The maximum difference from CHM's previously published 13 CV RMSEs is `3.33e-16`; all selected alpha and feature orders match. The Q1 bundle is a **reproduction pending CHM owner signoff**, not an alteration of `chm.q1.v1.3`.

## Remaining

CYJ will add a Q2-only derived-bundle consumer for pair effects and 512-observed policy comparison, then independent closure assertions and facts package. CHM should later inspect/sign off Q1 production identity and normalization. A-to-B bridge parameters remain unidentifiable, so `ready_for_Q3=false` retains its scientific meaning. This checkpoint is not yet a Q2 closure claim.
