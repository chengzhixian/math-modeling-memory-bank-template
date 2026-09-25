"""Exact within-support equal-loss substitutions and signed/benefit elasticities."""
import csv
import json
import numpy as np
from scipy.optimize import brentq

from fit_b7_joint_nonlinear import ROOT,OUTPUT,BOUNDS,metadata,predict,sha256,write_json


def derivatives(t,n,d,q):
    E,A,B,a,b,g0,gn,gd=t
    loss=float(predict(t,[[n,d,q]])[0]);gain=g0+gn*np.log(n)+gd*np.log(d/100)
    grad=np.array([-a*A*n**(-a-1)+(1-q)*gn/n,-b*B*d**(-b-1)+(1-q)*gd/d,-gain])
    return loss,grad


def equivalent(t,base,q,axis):
    loss=float(predict(t,[base])[0]);lo,hi=BOUNDS[axis]
    def f(z):
        point=list(base);point[axis]=z;point[2]=q
        return float(predict(t,[point])[0])-loss
    if f(lo)*f(hi)>0:return None
    return float(brentq(f,lo,hi,xtol=1e-11))


def run():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t=json.loads(OUTPUT.read_text(encoding="utf-8"))["model"]["theta"]
    figure_dir=ROOT/"figures/cyj";figure_dir.mkdir(parents=True,exist_ok=True)
    rows=[];bases=[(.1,20.,.5),(.7,150.,.5),(7.,500.,.5)]
    for base in bases:
        for q in np.linspace(.1,1,91):
            n=equivalent(t,base,float(q),0);d=equivalent(t,base,float(q),1)
            rows.append({"N0":base[0],"D0":base[1],"Q0":base[2],"Q1":float(q),
                         "N1":n,"D1":d,"N_multiplier":None if n is None else n/base[0],
                         "D_multiplier":None if d is None else d/base[1],
                         "N_status":"supported" if n is not None else "no_equal_loss_root_in_support",
                         "D_status":"supported" if d is not None else "no_equal_loss_root_in_support"})
    output=ROOT/"outputs/cyj/quality/substitution_results.csv"
    with output.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    for variable,label in (("N","parameter"),("D","data")):
        fig,ax=plt.subplots(figsize=(6,4))
        for base in bases:
            rr=[r for r in rows if r["N0"]==base[0]]
            ax.plot([r["Q1"] for r in rr],[np.nan if r[variable+"_multiplier"] is None else r[variable+"_multiplier"] for r in rr],label=f"N0={base[0]}, D0={base[1]}")
        ax.axhline(1,color="gray",linestyle=":");ax.set(xlabel="B-native Q",ylabel=f"Equal-loss {variable}1/{variable}0",title="B7 conditional substitution (Q0=0.5)")
        ax.legend();fig.tight_layout();fig.savefig(figure_dir/f"q2_quality_{label}_substitution.png",dpi=180);plt.close(fig)
    ns=np.geomspace(.07,11.97,60);ds=np.geomspace(10,600,60)
    for axis,label in ((0,"N"),(1,"D")):
        z=np.array([[-derivatives(t,n,d,.5)[1][2]/derivatives(t,n,d,.5)[1][axis] for n in ns] for d in ds])
        fig,ax=plt.subplots(figsize=(6,4));mesh=ax.pcolormesh(ns,ds,z,shading="auto")
        ax.set(xscale="log",yscale="log",xlabel="N (billion parameters)",ylabel="D (billion tokens)",title=f"d{label}/dQ at fixed Loss and other scale; Q=0.5")
        fig.colorbar(mesh,ax=ax);fig.tight_layout();fig.savefig(figure_dir/f"q2_quality_{label}_substitution_heatmap.png",dpi=180);plt.close(fig)
    write_json(output.with_suffix(".metadata.json"),{**metadata(),"model_hash":sha256(OUTPUT),"result_hash":sha256(output),
               "derivative_units":"dN/dQ: billion parameters per Q; dD/dQ: billion tokens per Q",
               "elasticity_policy":"positive improvement elasticity = -x*L_x/L; signed legacy v3 elasticities retain opposite sign",
               "root_policy":"No bracket means no supported equal-loss substitute; never extrapolate"})
    print("substitution:",len(rows),"rows")


if __name__=="__main__":run()
