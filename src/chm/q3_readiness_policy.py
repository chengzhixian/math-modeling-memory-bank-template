"""Science-aware Q3 readiness policy.

A/B Q mapping is NOT required when Q3 explicitly uses a validated B-native
Q_score performance model. A unique p optimum is also optional when the producer
explicitly adopts a multi-target sensitivity-only policy.
"""
from __future__ import annotations


def evaluate_readiness(bundle: dict, contexts: list[int]) -> dict:
    blockers=[]
    if bundle.get("ready_for_Q3") is not True:
        blockers.append("producer ready_for_Q3 is not true")

    quality=bundle.get("quality_policy") or {}
    if quality.get("coordinate")!="B_native_Q_score":
        blockers.append("quality_policy.coordinate must be B_native_Q_score")
    if quality.get("performance_status")!="validated":
        blockers.append("B-native quality performance model is not validated")
    if quality.get("joint_NDQ_status")!="validated":
        blockers.append("N,D,Q are not validated on one B-native loss coordinate")
    if not quality.get("loss_coordinate_id"):
        blockers.append("quality_policy.loss_coordinate_id is missing")
    a_map=quality.get("A_Q_mapping_status","unidentified")
    if a_map not in ("unidentified","not_required","validated"):
        blockers.append("unknown A_Q_mapping_status")

    p=bundle.get("p_policy") or {}
    p_mode=p.get("mode")
    if p_mode=="validated_bridge":
        if not p.get("primary_anchor"):
            blockers.append("validated_bridge p policy requires primary_anchor")
        if p.get("lambda_status")!="validated":
            blockers.append("validated_bridge p policy requires validated lambda")
        scope="full_NDQP"
    elif p_mode=="sensitivity_only":
        panel=p.get("target_panel") or []
        if len(panel)<3:
            blockers.append("sensitivity_only p policy requires >=3 targets")
        if p.get("unique_p_claim_allowed") is not False:
            blockers.append("sensitivity_only p policy must forbid a unique p claim")
        scope="NDQ_with_p_sensitivity"
    else:
        blockers.append("p_policy.mode must be validated_bridge or sensitivity_only")
        scope=None

    if sorted(set(contexts))!=[2048,8192,131072]:
        blockers.append(f"unexpected C7 contexts: {contexts}")

    return {
        "schema_version":"chm.q3.readiness_policy.v2",
        "formal_ready":not blockers,
        "formal_result_scope":scope if not blockers else None,
        "blockers":blockers,
        "A_Q_mapping_required":False,
        "A_Q_mapping_status":a_map,
        "quality_policy":quality,"p_policy":p,"contexts":sorted(set(contexts)),
    }
