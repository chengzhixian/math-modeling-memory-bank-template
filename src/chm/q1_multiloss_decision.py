"""Default Q1 v2 decision: bounded nonlinear optimization over the A4 hull."""
import json
from q1_hull_bounds_v2 import certify as solve, release
from q1_mixture_decision_v2 import choose as choose_observed, quality_constraints, POLICIES

if __name__ == "__main__":
    print(json.dumps(release(), ensure_ascii=False, indent=2))
