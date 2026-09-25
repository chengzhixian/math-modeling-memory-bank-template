"""Deterministically publish the three CHM consumer fixtures for NDQP v5."""
import json
from pathlib import Path

from joint_ndqp_scenarios import ConditionalNDQP, ROOT, VERSION

OUT = ROOT / "interfaces/cyj/fixtures"


def fixture(name, p, bridge_lambda, eta):
    request = {"schema_version": VERSION, "mode": "conditional_diagnostic",
               "requests": [{"request_id": name, "N_params_B": 1, "D_tokens_B": 100,
                             "Q_score": .5, "p": p, "weights": {"arxiv": 1.0},
                             "bridge_lambda": bridge_lambda, "eta": eta}]}
    (OUT / f"{name}.json").write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8", newline="\n")


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = ConditionalNDQP().a["reference"]
    fixture("p_ref_lambda_zero", ref, 0, 0)
    shifted = ref.copy()
    shifted["arxiv"] += .01
    shifted["freelaw"] -= .01
    fixture("nonzero_bridge", shifted, .5, 0)
    invalid = ref.copy()
    invalid["arxiv"] += .2
    fixture("invalid_p", invalid, .5, 0)


if __name__ == "__main__":
    run()
