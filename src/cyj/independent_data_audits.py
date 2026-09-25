"""Read-only B1 structure and B7/B8 conflict audits; source-stratified plots."""
import csv
import json
from collections import Counter,defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from audit_b_scaling_laws import ROOT,DEFAULT_DATA_ROOT,DEFAULT_MANIFEST,sha256
from scaling_provenance import verify_source_files
from diagnose_b_quality import read_data,coordinate_map,FILES
from fit_b7_joint_nonlinear import metadata,write_json


def csv_rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def save_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)


def run():
    figdir=ROOT/"figures/cyj";figdir.mkdir(parents=True,exist_ok=True)
    names=("pythia_training_log_existing.csv","scaling_baseline.csv","published_scaling_data.csv",FILES["B7"],FILES["B8"])
    sources=verify_source_files(DEFAULT_DATA_ROOT,DEFAULT_MANIFEST,names)
    rows=csv_rows(DEFAULT_DATA_ROOT/names[0]);groups=defaultdict(list)
    for r in rows:groups[float(r["N_params_B"])].append(r)
    coords=[(float(r["N_params_B"]),float(r["D_tokens_B"])) for r in rows]
    grid=[{float(r["D_tokens_B"]) for r in g} for g in groups.values()]
    val=np.array([float(r["val_loss"]) for r in rows]);train=np.array([float(r["train_loss"]) for r in rows])
    report={**metadata(),"scientific_status":"B1_source_structure_descriptive",
            "candidate_result_scope":"B1_structure_only","support":None,
            "source_dataset":"official_attachment_B1","source_hash":sources[names[0]]["sha256"],
            "rows":len(rows),"N_groups":len(groups),"rows_per_N":{str(n):len(g) for n,g in groups.items()},
            "duplicate_ND_count":len(coords)-len(set(coords)),"unique_run_ids":len({r["run_id"] for r in rows}),
            "common_D_grid_across_N":all(g==grid[0] for g in grid),"unique_D":len(set.union(*grid)),
            "D_step_formula_max_abs_error":float(max(abs(float(r["D_tokens_B"])-int(r["steps"])*2097152/1e9) for r in rows)),
            "train_validation_difference_percentiles":np.quantile(val-train,[0,.25,.5,.75,1]).tolist(),
            "train_validation_correlation":float(np.corrcoef(train,val)[0,1]),
            "provenance_audit_sha256":sha256(ROOT/"outputs/cyj/diagnostics/b1_loss_provenance.json"),
            "conclusion":"Regular shared checkpoint grid and near-formula reconstruction are warning signs, not proof of synthetic generation. val_loss generation and evaluation pipeline remain unknown.",
            "train_validation_generation_same_process":"not_identified","explicit_loss_generator_found":False,
            "near_duplicate_trajectory_definition":"same D grid with group-specific Loss offset; does not imply independent replicas"}
    aligned=np.array([[float(r["val_loss"]) for r in sorted(g,key=lambda r:float(r["D_tokens_B"]))] for g in groups.values()])
    centered=aligned-aligned.mean(axis=1,keepdims=True)
    report["centered_trajectory_cross_N_std_rms"]=float(np.sqrt(np.mean(np.std(centered,axis=0)**2)))
    write_json(ROOT/"outputs/cyj/classic/b1_structure_audit.json",report)
    seven=coordinate_map(read_data(DEFAULT_DATA_ROOT/FILES["B7"]));eight=coordinate_map(read_data(DEFAULT_DATA_ROOT/FILES["B8"]))
    shared=sorted(seven.keys()&eight.keys())
    differences=[{"N_params_B":k[0],"D_tokens_B":k[1],"Q_score":k[2],"B7_loss":seven[k]["val_loss"],
                  "B8_loss":eight[k]["val_loss"],"B8_minus_B7":eight[k]["val_loss"]-seven[k]["val_loss"]} for k in shared]
    save_csv(ROOT/"outputs/cyj/quality/b7_b8_conflict_audit.csv",differences)
    slopes=[]
    for label,data in (("B7",seven),("B8",eight)):
        nd=defaultdict(list)
        for k,r in data.items():nd[k[:2]].append(r)
        for key,rr in nd.items():
            slope=float(np.polyfit([r["Q_score"] for r in rr],[r["val_loss"] for r in rr],1)[0])
            slopes.append({"source":label,"N":key[0],"D":key[1],"Q_slope":slope,"points":len(rr)})
    save_csv(ROOT/"outputs/cyj/quality/b7_b8_q_slopes.csv",slopes)
    conflict={**metadata(),"scientific_status":"B7_B8_source_conflict_descriptive",
              "candidate_result_scope":"B7_B8_noncomparability","source_dataset":"official_attachments_B7_and_B8",
              "source_hash":{"B7":sources[FILES["B7"]]["sha256"],"B8":sources[FILES["B8"]]["sha256"]},
              "source_files":sources,"shared_coordinates":len(shared),
              "nonzero_loss_difference_count":sum(r["B8_minus_B7"]!=0 for r in differences),
              "B8_minus_B7_quantiles":np.quantile([r["B8_minus_B7"] for r in differences],[0,.25,.5,.75,1]).tolist(),
              "slope_sign_counts":{s:dict(Counter("positive" if r["Q_slope"]>0 else "negative" if r["Q_slope"]<0 else "zero" for r in slopes if r["source"]==s)) for s in ("B7","B8")},
              "B8_policy":"isolated_evidence_no_pooling_no_Q_reversal"}
    write_json(ROOT/"outputs/cyj/quality/b7_b8_conflict_summary.json",conflict)
    fig,ax=plt.subplots(figsize=(6,4))
    for label in ("B7","B8"):
        v=sorted(r["Q_slope"] for r in slopes if r["source"]==label)
        ax.plot(np.linspace(0,1,len(v)),v,label=label)
    ax.axhline(0,color="gray",linestyle=":");ax.set(xlabel="Within-source group quantile",ylabel="OLS Q slope at fixed N,D",title="Conflict audit: B7 and B8 remain separate");ax.legend()
    fig.tight_layout();fig.savefig(figdir/"b7_b8_q_slope_comparison.png",dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,name,label in zip(axes,names[1:3],("B4","B5")):
        data=csv_rows(DEFAULT_DATA_ROOT/name)
        for family in sorted({r["family"] for r in data}):
            rr=[r for r in data if r["family"]==family]
            ax.scatter([float(r["N_params_B"]) for r in rr],[float(r["val_loss"]) for r in rr],s=20,label=family)
        ax.set(xscale="log",xlabel="N (billion parameters)",ylabel="Source-native reported Loss",title=label+": descriptive only")
    axes[-1].legend(fontsize=6,bbox_to_anchor=(1.02,1));fig.tight_layout();fig.savefig(figdir/"b4_b5_descriptive_trends.png",dpi=180);plt.close(fig)
    identification=json.loads((ROOT/"outputs/cyj/quality/b7_identifiability.json").read_text())
    labels=identification["parameter_names"]
    fig,ax=plt.subplots(figsize=(6,5));im=ax.imshow(identification["local_working_correlation"],vmin=-1,vmax=1,cmap="coolwarm")
    ax.set_xticks(range(8),labels);ax.set_yticks(range(8),labels);ax.set_title("B7 joint: local working correlation")
    fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(figdir/"b7_parameter_correlation.png",dpi=180);plt.close(fig)
    fig,axes=plt.subplots(2,4,figsize=(11,5));samples=np.array(identification["bootstrap_parameter_samples"])
    for i,ax in enumerate(axes.flat):ax.hist(samples[:,i],bins=20);ax.set_title(labels[i])
    fig.suptitle("B7 joint: ND-cluster bootstrap (conditional)");fig.tight_layout();fig.savefig(figdir/"b7_parameter_bootstrap.png",dpi=180);plt.close(fig)
    calibration=json.loads((ROOT/"outputs/cyj/quality/b7_interval_calibration.json").read_text())
    fig,ax=plt.subplots(figsize=(6,4))
    for axis in ("N_params_B","D_tokens_B","Q_score"):
        rr=[r for r in calibration["coverage"] if r["axis"]==axis and r["held_level"] is None and r["method"]=="inner_oof_calibrated"]
        ax.plot([r["nominal"] for r in rr],[r["coverage"] for r in rr],"o-",label=axis)
    ax.plot([.8,.95],[.8,.95],"k:");ax.set(xlabel="Nominal",ylabel="Outer held-out empirical coverage",title="B7 nested residual intervals");ax.legend()
    fig.tight_layout();fig.savefig(figdir/"b7_interval_coverage.png",dpi=180);plt.close(fig)
    print(json.dumps({"B1":report["centered_trajectory_cross_N_std_rms"],"conflict":conflict["slope_sign_counts"],"shared":len(shared)}))


if __name__=="__main__":run()
