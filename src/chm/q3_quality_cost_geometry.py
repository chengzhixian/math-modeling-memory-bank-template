"""Pure cost geometry for Q3 quality-cost families."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

N_RANGE=(0.070542,11.965825)
CONTEXTS=(2048,8192,131072)
FAMILIES=("exponential","power","logarithmic")

def g(q,family):
    q=float(q)
    if not 0<q<=1: raise ValueError("Q must be in (0,1]")
    if family=="exponential": return 1e7*math.exp(6*q)
    if family=="power": return 5e9*q**4
    if family=="logarithmic": return 2e9*math.log(1+10*q)
    raise ValueError("unknown family")

def g_prime(q,family):
    q=float(q)
    if family=="exponential": return 6e7*math.exp(6*q)
    if family=="power": return 2e10*q**3
    if family=="logarithmic": return 2e10/(1+10*q)
    raise ValueError("unknown family")

def g_second(q,family):
    q=float(q)
    if family=="exponential": return 3.6e8*math.exp(6*q)
    if family=="power": return 6e10*q**2
    if family=="logarithmic": return -2e11/(1+10*q)**2
    raise ValueError("unknown family")

def delta_g(q,q0,family):
    if not 0<q0<=1 or not 0<q<=1: raise ValueError("Q,Q0 must be in (0,1]")
    return max(g(q,family)-g(q0,family),0.0)

def base_denominator_per_N(context_tokens):
    return 6e9+2e5*int(context_tokens)

def quality_to_base_ratio(N_params_B,q,q0,context_tokens,family):
    N=float(N_params_B)
    if N<=0: raise ValueError("N must be positive")
    return delta_g(q,q0,family)/(N*base_denominator_per_N(context_tokens))

def critical_N_equal_base(q,q0,context_tokens,family):
    return delta_g(q,q0,family)/base_denominator_per_N(context_tokens)

def critical_Q_equal_base(N_params_B,q0,context_tokens,family):
    rhs=float(N_params_B)*base_denominator_per_N(context_tokens)
    if family=="exponential": q=math.log(math.exp(6*q0)+rhs/1e7)/6
    elif family=="power": q=(q0**4+rhs/5e9)**0.25
    elif family=="logarithmic": q=((1+10*q0)*math.exp(rhs/2e9)-1)/10
    else: raise ValueError("unknown family")
    return q if q<=1 else None

def cost_derivatives(N_params_B,D_tokens_B,q,q0,context_tokens,family):
    N,D=float(N_params_B),float(D_tokens_B)
    if N<=0 or D<=0: raise ValueError("N,D must be positive")
    c=6e18+2e14*context_tokens; dg=delta_g(q,q0,family)
    return {"dC_dN_B":c*D,"dC_dD_B":c*N+1e9*dg,
            "dC_dQ_left_at_Q0":0.0 if math.isclose(q,q0) else None,
            "dC_dQ_right_or_regular":1e9*D*g_prime(q,family) if q>=q0 else 0.0}

def family_rows():
    out=[]
    for fam in FAMILIES:
        for q in (.25,.5,.75,1.0):
            s=g_second(q,fam)
            out.append({"family":fam,"Q":q,"g":g(q,fam),"g_prime":g_prime(q,fam),
                        "g_second":s,"curvature":"convex" if s>0 else "concave"})
    return out

def critical_rows():
    out=[];nmin,nmax=N_RANGE
    for q0 in (.25,.5,.75):
        for ctx in CONTEXTS:
            for fam in FAMILIES:
                n=critical_N_equal_base(1,q0,ctx,fam)
                status="below_support" if n<nmin else ("above_support" if n>nmax else "crosses_within_B1_support")
                out.append({"Q0":q0,"Q":1.0,"context_tokens":ctx,"family":fam,
                            "critical_N_B_equal_quality_and_base":n,"B1_support_status":status})
    return out

def ratio_rows():
    return [{"Q0":.5,"Q":1.0,"context_tokens":ctx,"N_params_B":N,"family":fam,
             "C_Q_over_C_train_plus_attn":quality_to_base_ratio(N,1,.5,ctx,fam)}
            for ctx in CONTEXTS for N in (.1,1.0,10.0) for fam in FAMILIES]

def critical_q_rows():
    return [{"Q0":.5,"context_tokens":ctx,"N_params_B":N,"family":fam,
             "critical_Q_equal_quality_and_base":critical_Q_equal_base(N,.5,ctx,fam)}
            for ctx in CONTEXTS for N in (.1,1.0,10.0) for fam in FAMILIES]

def write_csv(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output-dir",type=Path,default=Path("outputs/chm/q3_quality_cost_v1"))
    a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
    write_csv(a.output_dir/"family_curvature.csv",family_rows())
    write_csv(a.output_dir/"critical_N_to_Q1.csv",critical_rows())
    write_csv(a.output_dir/"illustrative_ratio_Q0_0p5_to_Q1.csv",ratio_rows())
    write_csv(a.output_dir/"critical_Q_Q0_0p5.csv",critical_q_rows())
    manifest={"schema_version":"chm.q3.quality_cost_geometry.v1","status":"cost_geometry_only","ready_for_Q3":False,
              "Q0_scenarios_for_diagnostics":[.25,.5,.75],
              "identities":{"attention_train_ratio":"L_ctx/30000",
                            "quality_base_ratio":"[g(Q)-g(Q0)]/[N_B*(6e9+2e5*L_ctx)]",
                            "critical_N":"[g(Q)-g(Q0)]/[6e9+2e5*L_ctx]"},
              "limitations":["No Q-performance effect is assumed or fitted",
                             "Q0 values are illustrative scenarios, not problem defaults",
                             "C_Q has a kink at Q=Q0; use one-sided derivative/subgradient",
                             "formal Q optimization waits for cyj validated B-native quality predictor"]}
    (a.output_dir/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__": main()
