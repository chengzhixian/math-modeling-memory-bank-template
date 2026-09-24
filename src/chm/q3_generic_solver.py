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
class Support:
    N: tuple[float, float]
    D: tuple[float, float]
    Q: tuple[float, float]

    def __post_init__(self):
        for lo, hi in (self.N, self.D, self.Q):
            if not all(map(math.isfinite, (lo, hi))) or lo >= hi:
                raise ValueError("invalid model support")
        if self.N[0] <= 0 or self.D[0] <= 0 or not 0 <= self.Q[0] < self.Q[1] <= 1:
            raise ValueError("invalid model support units")


def resolve_support(model, support=None):
    result = support if support is not None else getattr(model, "support", None)
    if not isinstance(result, Support):
        raise ValueError("explicit model support is required; no B1 fallback")
    return result


@dataclass(frozen=True)
class SyntheticLinearQualityLoss:
    """Software-test model: B1 baseline plus gamma*(1-Q). NOT scientific evidence."""
    gamma: float = 0.2
    support = Support(N_RANGE, D_RANGE, (0., 1.))

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


def _transform(z):
    return math.exp(z[0]), math.exp(z[1]), float(z[2])


def solve_generic(model, *, budget, context_tokens, Q0, family,
                  starts=36, seed=20260924, support=None):
    support = resolve_support(model, support)
    if not math.isfinite(budget) or budget <= 0 or context_tokens <= 0 or starts < 3:
        raise ValueError("invalid budget, context or number of starts")
    if not support.Q[0] <= Q0 < support.Q[1]:
        raise ValueError("Q0 outside model support")
    nmin,nmax=support.N; dmin,dmax=support.D
    if cost_and_grad(nmin,dmin,Q0,Q0,context_tokens,family)[0] > budget*(1+1e-12):
        raise ValueError("budget below minimum supported cost")
    bounds=[tuple(map(math.log,support.N)),tuple(map(math.log,support.D)),(Q0,support.Q[1])]
    rng=np.random.default_rng(seed)
    seeds=[[b[0] for b in bounds],[b[1] for b in bounds],[sum(b)/2 for b in bounds]]
    seeds += [[rng.uniform(*b) for b in bounds] for _ in range(starts-3)]

    def objective(z):
        N,D,Q=_transform(z)
        value,grad=model.value_grad(N,D,Q)
        return value,np.array(grad)*[N,D,1.]

    def constraint(z):
        N,D,Q=_transform(z)
        value,grad=cost_and_grad(N,D,Q,Q0,context_tokens,family)
        return 1-value/budget,-np.array(grad)*[N,D,1.]/budget

    trials=[]
    for i,z in enumerate(seeds):
        res=minimize(objective,z,jac=True,method="SLSQP",bounds=bounds,
                     constraints=[{"type":"ineq","fun":lambda z:constraint(z)[0],
                                   "jac":lambda z:constraint(z)[1]}],
                     options={"ftol":1e-12,"maxiter":2000})
        N,D,Q=_transform(res.x)
        C,_=cost_and_grad(N,D,Q,Q0,context_tokens,family)
        L,_=model.value_grad(N,D,Q)
        trials.append({"start_id":i,"success":bool(res.success),
                       "feasible":bool(math.isfinite(L) and C <= budget*(1+1e-8)),
                       "loss":float(L),"N_params_B":N,"D_tokens_B":D,"Q":Q,
                       "cost_FLOPs":C,"budget_residual":C-budget,"message":str(res.message)})
    good=[r for r in trials if r["success"] and r["feasible"]]
    if not good:
        raise RuntimeError("no converged feasible solution found")
    return enrich_kkt(min(good,key=lambda r:r["loss"]),model,budget,context_tokens,Q0,family,support=support),trials


def active_set(sol,budget,q0,tol=1e-6,*,support):
    active=[]
    for name,x,bounds in (("N",sol["N_params_B"],support.N),
                          ("D",sol["D_tokens_B"],support.D),
                          ("Q",sol["Q"],(q0,support.Q[1]))):
        for tag,bound in zip(("min","max"),bounds):
            if abs(x-bound)<=tol*max(abs(bound),1e-12):
                active.append(("Q0" if tag=="min" else "Q1") if name=="Q" else name+"_"+tag)
    if abs(sol["cost_FLOPs"]/budget-1)<=1e-7:
        active.append("budget")
    return active


def enrich_kkt(sol,model,budget,context_tokens,q0,family,*,support=None):
    support=resolve_support(model,support)
    N,D,Q=sol["N_params_B"],sol["D_tokens_B"],sol["Q"]
    L,Lg=model.value_grad(N,D,Q)
    C,Cg=cost_and_grad(N,D,Q,q0,context_tokens,family)
    if not all(math.isfinite(v) for v in (L,C,*Lg,*Cg)) or min(Cg)<=0:
        raise ValueError("KKT requires finite gradients and positive cost derivatives")
    ratios=dict(zip(("N","D","Q"),(-lx/cx for lx,cx in zip(Lg,Cg))))
    active=active_set({**sol,"cost_FLOPs":C},budget,q0,support=support)
    lower=[];upper=[];free=[]
    for name,r in ratios.items():
        lo="Q0" if name=="Q" else name+"_min"
        hi="Q1" if name=="Q" else name+"_max"
        (lower if lo in active else upper if hi in active else free).append((name,r))
    vals=[r for _,r in free]
    if "budget" not in active:
        mu=0.; interval=[0.,0.]
    elif vals:
        mu=max(0.,float(np.median(vals)));interval=[mu,mu]
    else:
        lo=max([0.]+[r for _,r in lower])
        hi=min([r for _,r in upper],default=math.inf)
        mu=lo;interval=[lo,hi if math.isfinite(hi) else None]
    scale=max(abs(mu),*(abs(r) for r in ratios.values()),1e-300)
    inequalities=[{"variable":name,"bound":kind,"ratio":r,
                   "satisfied":bool((r-mu if kind=="lower" else mu-r)/scale<=1e-4)}
                  for kind,items in (("lower",lower),("upper",upper)) for name,r in items]
    violation=max([0.]+[abs(r-mu)/scale for _,r in free]
                  +[(r-mu)/scale for _,r in lower]+[(mu-r)/scale for _,r in upper])
    primal=(C<=budget*(1+1e-8) and all(lo-1e-9*max(1,abs(lo))<=x<=hi+1e-9*max(1,abs(hi))
            for x,(lo,hi) in zip((N,D,Q),(support.N,support.D,(q0,support.Q[1])))))
    complementarity=abs(mu/scale*(C/budget-1))
    return {**sol,"loss":L,"cost_FLOPs":C,"budget_utilization":C/budget,
            "active_set":active,"marginal_benefit_per_cost":ratios,
            "interior_ratio_relative_spread":(max(vals)-min(vals))/scale if len(vals)>1 else None,
            "kkt_mu_estimate":mu,"kkt_mu_interval":interval,
            "boundary_kkt_inequalities":inequalities,"primal_feasible":bool(primal),
            "kkt_relative_violation":violation,"complementarity_relative_residual":complementarity,
            "kkt_check_pass":bool(primal and violation<=1e-4 and complementarity<=1e-7),
            "kkt_note":"Relative marginal residuals; primal, dual and complementarity checked. Necessary, not sufficient, for global optimality."}


def detect_transitions(rows):
    out=[]; prev=None
    def group(r): return (r["context_tokens"],r.get("quality_family",""),r.get("Q0_scenario",0.5))
    for r in sorted(rows,key=lambda x:(group(x),x["budget_FLOPs"])):
        signature=tuple(sorted(r["active_set"])); key=group(r)
        if prev is None or group(prev)!=key:
            prev={**r,"signature":signature}; continue
        if signature!=prev["signature"]:
            out.append({"context_tokens":key[0],"quality_family":key[1],"Q0_scenario":key[2],"budget_left":prev["budget_FLOPs"],
                        "budget_right":r["budget_FLOPs"],
                        "active_left":";".join(prev["signature"]),
                        "active_right":";".join(signature)})
        prev={**r,"signature":signature}
    return out
