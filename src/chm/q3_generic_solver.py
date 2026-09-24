"""Generic gated Q3 optimizer and active-set/KKT diagnostics.

Scientific use requires an upstream validated loss model. Synthetic loss models in
this module exist ONLY for software tests; their numerical optima must never be
reported as problem results.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol

import numpy as np
from scipy.optimize import minimize

from q3_nd_baseline import DEFAULT_PARAMS, N_RANGE, D_RANGE
from q3_quality_cost_geometry import delta_g, g_prime


class LossModel(Protocol):
    def value_grad(self, N_B: float, D_B: float, Q: float) -> tuple[float, tuple[float,float,float]]:
        ...


@dataclass(frozen=True)
class SyntheticLinearQualityLoss:
    """Software-test model: B1 baseline plus gamma*(1-Q). NOT scientific evidence."""
    gamma: float = 0.2

    def value_grad(self, N_B, D_B, Q):
        p = DEFAULT_PARAMS
        value = (
            p["E"] + p["A"]*N_B**(-p["alpha"]) + p["B"]*D_B**(-p["beta"])
            + self.gamma*(1-Q)
        )
        grad = (
            -p["alpha"]*p["A"]*N_B**(-p["alpha"]-1),
            -p["beta"]*p["B"]*D_B**(-p["beta"]-1),
            -self.gamma,
        )
        return float(value), tuple(map(float, grad))


def cost_and_grad(N_B, D_B, Q, Q0, context_tokens, family):
    c_nd = 6e18 + 2e14*context_tokens
    dg = delta_g(Q, Q0, family)
    cost = c_nd*N_B*D_B + 1e9*D_B*dg
    dN = c_nd*D_B
    dD = c_nd*N_B + 1e9*dg
    dQ = 1e9*D_B*g_prime(Q, family) if Q >= Q0 else 0.0
    return float(cost), (float(dN),float(dD),float(dQ))


def _transform(z, q0):
    N = math.exp(z[0])
    D = math.exp(z[1])
    sig = 1/(1+math.exp(-z[2]))
    Q = q0 + (1-q0)*sig
    return N,D,Q


def solve_generic(
    model: LossModel, *,
    budget: float, context_tokens: int, Q0: float, family: str,
    starts: int = 36, seed: int = 20260924,
):
    if budget <= 0 or not math.isfinite(budget):
        raise ValueError("budget must be positive finite")
    if not 0 < Q0 < 1:
        raise ValueError("Q0 must lie in (0,1)")
    nmin,nmax=N_RANGE; dmin,dmax=D_RANGE
    rng=np.random.default_rng(seed)
    bounds=[(math.log(nmin),math.log(nmax)),(math.log(dmin),math.log(dmax)),(-16,16)]
    seeds=[
        [math.log(nmin),math.log(dmin),-12],
        [math.log(nmax),math.log(dmax),12],
        [0.5*(math.log(nmin)+math.log(nmax)),0.5*(math.log(dmin)+math.log(dmax)),0],
    ]
    while len(seeds)<starts:
        seeds.append([rng.uniform(*bounds[0]),rng.uniform(*bounds[1]),rng.uniform(-6,6)])

    def objective(z):
        N,D,Q=_transform(z,Q0)
        return model.value_grad(N,D,Q)[0]

    def budget_constraint(z):
        N,D,Q=_transform(z,Q0)
        return budget-cost_and_grad(N,D,Q,Q0,context_tokens,family)[0]

    trials=[]
    for i,z0 in enumerate(seeds):
        res=minimize(
            objective,np.array(z0,float),method="SLSQP",bounds=bounds,
            constraints=[{"type":"ineq","fun":budget_constraint}],
            options={"ftol":1e-12,"maxiter":2000,"disp":False},
        )
        N,D,Q=_transform(res.x,Q0)
        C,_=cost_and_grad(N,D,Q,Q0,context_tokens,family)
        L,_=model.value_grad(N,D,Q)
        feasible=C <= budget*(1+1e-8)
        trials.append({
            "start_id":i,"success":bool(res.success),"feasible":bool(feasible),
            "loss":float(L),"N_params_B":N,"D_tokens_B":D,"Q":Q,
            "cost_FLOPs":C,"budget_residual":C-budget,"message":str(res.message),
        })
    feasible=[r for r in trials if r["feasible"]]
    if not feasible:
        raise RuntimeError("no feasible solution found")
    best=min(feasible,key=lambda r:r["loss"])
    return enrich_kkt(best,model,budget,context_tokens,Q0,family),trials


def active_set(sol,budget,q0,tol=1e-5):
    active=[]
    N,D,Q=sol["N_params_B"],sol["D_tokens_B"],sol["Q"]
    nmin,nmax=N_RANGE; dmin,dmax=D_RANGE
    if abs(N-nmin)<=tol*max(1,nmin): active.append("N_min")
    if abs(N-nmax)<=tol*max(1,nmax): active.append("N_max")
    if abs(D-dmin)<=tol*max(1,dmin): active.append("D_min")
    if abs(D-dmax)<=tol*max(1,dmax): active.append("D_max")
    if abs(Q-q0)<=tol: active.append("Q0")
    if abs(Q-1)<=tol: active.append("Q1")
    if abs(sol["cost_FLOPs"]-budget)<=max(1,budget)*1e-7: active.append("budget")
    return active


def enrich_kkt(sol,model,budget,context_tokens,q0,family):
    N,D,Q=sol["N_params_B"],sol["D_tokens_B"],sol["Q"]
    L,Lg=model.value_grad(N,D,Q)
    C,Cg=cost_and_grad(N,D,Q,q0,context_tokens,family)
    ratios={name:(-lx/cx if cx>0 else None) for name,lx,cx in zip(("N","D","Q"),Lg,Cg)}
    active=active_set({**sol,"cost_FLOPs":C},budget,q0)

    free=[]; lower=[]; upper=[]
    for name,r in ratios.items():
        if r is None: continue
        if name=="N" and "N_min" in active: lower.append((name,r))
        elif name=="N" and "N_max" in active: upper.append((name,r))
        elif name=="D" and "D_min" in active: lower.append((name,r))
        elif name=="D" and "D_max" in active: upper.append((name,r))
        elif name=="Q" and "Q0" in active: lower.append((name,r))
        elif name=="Q" and "Q1" in active: upper.append((name,r))
        else: free.append((name,r))

    free_vals=[r for _,r in free]
    spread=(max(free_vals)-min(free_vals))/max(abs(np.mean(free_vals)),1e-30) if len(free_vals)>=2 else None
    if "budget" not in active:
        mu=0.0; mu_interval=[0.0,0.0]
    elif free_vals:
        mu=float(np.median(free_vals)); mu_interval=[mu,mu]
    else:
        lo=max([r for _,r in lower],default=0.0)
        hi=min([r for _,r in upper],default=float("inf"))
        mu=lo if math.isinf(hi) else 0.5*(lo+hi)
        mu_interval=[lo,hi]

    atol=1e-7*max(1.0,abs(mu))
    inequalities=[]
    for name,r in lower:
        inequalities.append({"variable":name,"bound":"lower","ratio":r,"satisfied":bool(r<=mu+atol)})
    for name,r in upper:
        inequalities.append({"variable":name,"bound":"upper","ratio":r,"satisfied":bool(r+atol>=mu)})
    kkt_ok=(spread is None or spread<1e-4) and all(x["satisfied"] for x in inequalities)
    return {
        **sol,"loss":L,"cost_FLOPs":C,"budget_utilization":C/budget,
        "active_set":active,"marginal_benefit_per_cost":ratios,
        "interior_ratio_relative_spread":spread,
        "kkt_mu_estimate":mu,"kkt_mu_interval":mu_interval,
        "boundary_kkt_inequalities":inequalities,"kkt_check_pass":bool(kkt_ok),
        "kkt_note":"Free variables require equal -dL/dx/dCdx. Lower bounds require ratio<=mu; upper bounds ratio>=mu. Q0 uses the right derivative.",
    }


def detect_transitions(rows):
    out=[]; prev=None
    for r in sorted(rows,key=lambda x:(x["context_tokens"],x["budget_FLOPs"])):
        signature=tuple(sorted(r["active_set"])); key=r["context_tokens"]
        if prev is None or prev["context_tokens"]!=key:
            prev={**r,"signature":signature}; continue
        if signature!=prev["signature"]:
            out.append({"context_tokens":key,"budget_left":prev["budget_FLOPs"],
                        "budget_right":r["budget_FLOPs"],
                        "active_left":";".join(prev["signature"]),
                        "active_right":";".join(signature)})
        prev={**r,"signature":signature}
    return out
