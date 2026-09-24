"""Train-only five-family selection and residual calibration within each outer fold."""
from collections import Counter
import csv
import json
import numpy as np

from fit_b7_joint_nonlinear import (AXES,FAMILIES,ROOT,SEED,fit_joint,metadata,metrics,predict,sha256,write_json)
from quality_scaling import source_data


def run():
    _,x,y,rows=source_data();folds=[];predictions=[];cache={}
    def fit_excluding(axis,levels,family):
        key=(axis,tuple(sorted(levels)),family)
        if key not in cache:
            mask=~np.isin(x[:,axis],levels)
            cache[key]=fit_joint(x[mask],y[mask],family,starts=4,seed=SEED)
        return cache[key]
    for axis,name in enumerate(AXES):
        levels=np.unique(x[:,axis])
        for outer in levels:
            inner_scores={f:[] for f in FAMILIES};inner_residuals={f:[] for f in FAMILIES}
            for inner in levels[levels!=outer]:
                held=x[:,axis]==inner
                for family in FAMILIES:
                    model=fit_excluding(axis,[float(outer),float(inner)],family)
                    p=predict(model["theta"],x[held]);inner_scores[family].append(metrics(p,y[held])["rmse"])
                    inner_residuals[family].extend((y[held]-p).tolist())
            means={f:float(np.mean(v)) for f,v in inner_scores.items()}
            selected=min(FAMILIES,key=lambda f:(means[f],FAMILIES.index(f)))
            model=fit_excluding(axis,[float(outer)],selected)
            held=x[:,axis]==outer;p=predict(model["theta"],x[held])
            train_residual=y[~held]-predict(model["theta"],x[~held])
            widths={}
            for nominal in (.8,.9,.95):
                widths[str(nominal)]={
                    "training_residual":float(np.quantile(abs(train_residual),nominal,method="higher")),
                    "inner_oof_calibrated":float(np.quantile(abs(np.array(inner_residuals[selected])),nominal,method="higher"))}
            folds.append({"axis":name,"held_level":float(outer),"selected_family":selected,
                          "inner_mean_rmse":means,"outer_metrics":metrics(p,y[held]),"interval_halfwidths":widths,
                          "outer_source_lines":[rows[i]["source_line"] for i in np.flatnonzero(held)],
                          "fit_theta":model["theta"],"outer_train_count":int((~held).sum())})
            for j,i in enumerate(np.flatnonzero(held)):
                row={"axis":name,"held_level":float(outer),"source_line":rows[i]["source_line"],
                     "selected_family":selected,"observed":float(y[i]),"prediction":float(p[j]),
                     "residual":float(y[i]-p[j])}
                for nominal,pools in widths.items():
                    for kind,width in pools.items():
                        row[f"{kind}_{nominal}_lower"]=float(p[j]-width)
                        row[f"{kind}_{nominal}_upper"]=float(p[j]+width)
                predictions.append(row)
        print(name,"nested selection complete",flush=True)
    summaries={}
    for name in AXES:
        rr=[r for r in predictions if r["axis"]==name];ff=[f for f in folds if f["axis"]==name]
        summaries[name]={**metrics(np.array([r["prediction"] for r in rr]),np.array([r["observed"] for r in rr])),
                         "mean_fold_rmse":float(np.mean([f["outer_metrics"]["rmse"] for f in ff])),
                         "worst_group_rmse":max(f["outer_metrics"]["rmse"] for f in ff),
                         "selected_family_frequency":dict(Counter(f["selected_family"] for f in ff))}
    directory=ROOT/"outputs/cyj/quality"
    with (directory/"b7_nested_cv_predictions.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(predictions[0]));w.writeheader();w.writerows(predictions)
    summary={**metadata(),"schema_version":"cyj.b7_joint_nested.v1","seed":SEED,"starts_per_fit":4,
             "families":FAMILIES,"folds":folds,"axis_summary":summaries,
             "prediction_sha256":sha256(directory/"b7_nested_cv_predictions.csv"),
             "caveat":"Outer rows are unused by this selection/calibration pipeline, but historical family design inspected all B7; not an untouched real-training test"}
    write_json(directory/"b7_nested_cv_summary.json",summary)
    coverage=[]
    for name in AXES:
        for group in [None]+sorted({r["held_level"] for r in predictions if r["axis"]==name}):
            rr=[r for r in predictions if r["axis"]==name and (group is None or r["held_level"]==group)]
            for nominal in (.8,.9,.95):
                for kind in ("training_residual","inner_oof_calibrated"):
                    low=f"{kind}_{nominal}_lower";high=f"{kind}_{nominal}_upper"
                    coverage.append({"axis":name,"held_level":group,"nominal":nominal,"method":kind,"n":len(rr),
                                     "coverage":float(np.mean([r[low]<=r["observed"]<=r[high] for r in rr])),
                                     "mean_width":float(np.mean([r[high]-r[low] for r in rr]))})
    write_json(directory/"b7_interval_calibration.json",{**metadata(),"model_hash":sha256(directory/"b7_nested_cv_summary.json"),
               "coverage":coverage,"method":"symmetric empirical abs-residual quantiles fitted only in outer training groups",
               "limitations":"Not a distribution-free conformal guarantee; groups are few, folds correlated, selected-family residuals reused internally. Undercoverage is reported without tuning on outer holdouts."})
    print(json.dumps(summaries))


if __name__=="__main__":run()
