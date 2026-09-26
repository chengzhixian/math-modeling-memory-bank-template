"""Redraw frozen main Q1 results; never refit or overwrite the result tables.

Run from any directory: python -B src/visualization/q1_redesign.py
Optional: --skill-dir PATH to the installed scipilot-figure-skill directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import PercentFormatter
from matplotlib.patches import Rectangle
from PIL import Image
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/Q1"
OUT = SOURCE / "redesign"
BLUE, TEAL, ORANGE = "#0072B2", "#009E73", "#E69F00"
INK, GREY, LIGHT = "#243746", "#718096", "#E8EEF2"
DIVERGE = LinearSegmentedColormap.from_list("q1_blue_white_orange", [BLUE, "#FAFCFD", ORANGE])
SEQUENTIAL = LinearSegmentedColormap.from_list("q1_white_blue", ["#F3F7FA", "#B4D4E8", BLUE, "#003E64"])
LABELS = {
    "arxiv": "arXiv", "book": "Book", "c4": "C4", "commoncrawl": "Common Crawl",
    "github": "GitHub", "stackexchange": "StackExchange", "wikipedia": "Wikipedia",
    "freelaw": "FreeLaw", "nih_exporter": "NIH", "pubmed_central": "PubMed Central",
    "wikipedia_en": "Wikipedia", "dm_mathematics": "Mathematics", "philpapers": "PhilPapers",
    "enron_emails": "Enron", "gutenberg_pg_19": "Gutenberg", "pile_cc": "Pile-CC",
    "ubuntu_irc": "Ubuntu IRC", "europarl": "EuroParl", "hackernews": "HackerNews",
    "pubmed_abstracts": "PubMed Abstracts", "uspto_backgrounds": "USPTO",
}
POLICIES = ["等权 · 无质量约束", "等权 · direct", "等权 · direct+near", "保护最差目标"]
FIGURES = []
LAYOUT = {}
INPUTS = set()


def read_csv(name):
    INPUTS.add(name)
    return pd.read_csv(SOURCE / name)


def read_json(name):
    INPUTS.add(name)
    return json.loads((SOURCE / name).read_text(encoding="utf-8-sig"))


def title(fig, text, subtitle):
    fig.suptitle(text, x=.025, y=.985, ha="left", fontsize=14, weight="bold", color=INK)
    fig.text(.025, .937, subtitle, ha="left", va="top", fontsize=8.5, color=GREY)


def base(size=(7.2, 4.7), margins=(.20, .93, .20, .81)):
    fig = plt.figure(figsize=size)
    left, right, bottom, top = margins
    fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top)
    return fig


def clean(ax, direction="x"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color("#CAD5DD")
    ax.tick_params(length=0, pad=5)
    ax.grid(axis=direction, color=LIGHT, lw=.65, zorder=0)
    ax.set_axisbelow(True)


def heatmap(ax, values, rowlabels, collabels, cmap=SEQUENTIAL, vmin=None, vmax=None,
            norm=None, formatter=None):
    im = ax.imshow(values, cmap=cmap, vmin=vmin, vmax=vmax, norm=norm, aspect="auto")
    ax.set_yticks(np.arange(len(rowlabels)), rowlabels, fontsize=8)
    ax.set_xticks(np.arange(len(collabels)), collabels, fontsize=8)
    ax.tick_params(length=0, pad=6)
    ax.set_xticks(np.arange(-.5, len(collabels), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(rowlabels), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.8)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    if formatter:
        for i in range(len(rowlabels)):
            for j in range(len(collabels)):
                v = values[i, j]
                rgba = im.cmap(im.norm(v))
                lum = .2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
                ax.text(j, i, formatter(v), ha="center", va="center", fontsize=7.5,
                        color="white" if lum < .5 else INK)
    return im


def finish(fig, stem, caption, sources, audit_layout):
    fig.text(.025, .028, caption, fontsize=7.5, color=GREY, va="bottom", linespacing=1.6)
    fig.canvas.draw()
    LAYOUT[stem] = audit_layout(fig)
    if any(level == "FAIL" for level, _ in LAYOUT[stem]):
        raise RuntimeError(f"Visual QA failed: {stem}: {LAYOUT[stem]}")
    preview = OUT / f"{stem}.png"
    fig.savefig(preview, dpi=300, facecolor="white")
    fig.savefig(OUT / f"{stem}.pdf", facecolor="white")
    fig.savefig(OUT / f"{stem}.svg", facecolor="white")
    with Image.open(preview) as im:
        im.convert("L").save(OUT / f"{stem}_gray.png", dpi=(300, 300))
    FIGURES.append({"stem": stem, "caption": caption, "sources": sources,
                    "size_inches": list(fig.get_size_inches()), "dpi": 300})
    plt.close(fig)


def quality(audit):
    d = read_csv("domain_quality.csv")
    q = d[d.dataset_scope.eq("sample")].sort_values("Q", ascending=False)
    fig = base((7.2, 4.9), (.23, .88, .24, .81))
    title(fig, "01  七个领域的质量代理差异", "同一套 A1 冻结规则；横线表示领域中位数的条件 95% bootstrap 区间")
    ax = fig.add_subplot()
    y = np.arange(len(q))
    ax.axvline(0, color=GREY, lw=.8, ls="--")
    ax.errorbar(q.Q, y, xerr=np.vstack([q.Q-q.uncertainty_low, q.uncertainty_high-q.Q]),
                fmt="o", ms=6, color=BLUE, capsize=3, lw=1.5, zorder=3)
    ax.set_yticks(y, [f"{LABELS[r.quality_domain]}   n={r.n_rows:,}" for r in q.itertuples()], fontsize=8)
    for i, r in enumerate(q.itertuples()):
        ax.text(r.Q+.12, i-.12, f"{r.Q:+.3f}", color=INK, fontsize=8.5, va="center")
    ax.set_xlim(-.75, 3.48); ax.set_ylim(len(q)-.6, -.6)
    ax.set_xlabel("相对质量代理 Q_A（A1 标准化坐标）", labelpad=10)
    clean(ax)
    fig.text(.23, .105, "Book / arXiv 较高；GitHub / C4 较低。评分依赖指标方向与权重。", fontsize=8, color=BLUE)
    finish(fig, "01_quality", "数据：A1 共 51,230 条；区间固定评分规则，不涵盖方法选择不确定性。\nQ_A 是工程评分代理；低分不等于文本无用或人工质量判定。", ["domain_quality.csv"], audit)


def conflict(audit):
    meta = read_json("conflict_validation.json")
    INPUTS.add("ANSWER.md")
    text = (SOURCE / "ANSWER.md").read_text(encoding="utf-8")
    pattern = r"分别为 ([\d,]+)、([\d,]+)、([\d,]+)、([\d,]+) 条"
    m = re.search(pattern, text)
    if not m:
        raise ValueError("Cannot find the published A1 quadrant counts")
    counts = [int(s.replace(",", "")) for s in m.groups()]
    if sum(counts) != 51230:
        raise ValueError("Published quadrant counts do not sum to A1")
    values = np.array([[counts[0], counts[2]], [counts[1], counts[3]]])
    fig = base((7.2, 4.8), (.21, .84, .29, .78))
    title(fig, "02  综合质量与指标分歧分别处理", "22 个信号形成 231 个指标对；55 条显著负相关边在扩展样本上复现")
    ax = fig.add_subplot()
    names = np.array([["保留", "低优先级"], ["保留并复核", "低优先级并复核"]])
    im = heatmap(ax, values, ["低分歧", "高分歧 · 需复核"], ["较高 Q_A", "较低 Q_A"],
            vmin=0, vmax=23000)
    cax=fig.add_axes([.88,.35,.022,.35]);cb=fig.colorbar(im,cax=cax);cb.set_label("记录条数",fontsize=8)
    for i in range(2):
        for j in range(2):
            ax.text(j, i-.12, names[i,j], ha="center", va="center", fontsize=10,
                    color="white" if values[i,j]>14000 else INK)
            ax.text(j, i+.13, f"{values[i,j]:,} 条  ·  {100*values[i,j]/51230:.1f}%", ha="center",
                    va="center", fontsize=10, color="white" if values[i,j]>14000 else INK)
    fig.text(.21, .16, f"Q_A 阈值 = {meta['q_threshold']:.4f}    |    分歧 D 阈值 = {meta['d_review_threshold']:.4f}", fontsize=8.5, color=BLUE)
    finish(fig, "02_conflict", "条数与阈值均来自 main 已发布结果；分歧高只触发复核，不机械扣减 Q_A。\n27 条文本案例用于解释规则，并非人工标签；55 条边是统计排序分歧。", ["conflict_validation.json", "ANSWER.md"], audit)


def model_validation(audit, targets):
    cv = read_csv("targetwise_oof.csv").pivot(index="target", columns="model", values="oof_rmse")
    observed = read_csv("targetwise_validation.csv")
    groups = [("嵌套 CV\n512 配方", cv.loc[targets,"ridge"].to_numpy(), cv.loc[targets,"interaction"].to_numpy())]
    for scope, label in [("test_1m", "1M 检验\n256 配方"), ("test_60m", "60M 检验\n256 配方"), ("test_1B", "1B 检验\n64 配方")]:
        d = observed[(observed.scope==scope)&(observed.support_group=="all")].set_index("target").loc[targets]
        groups.append((label, d.ridge_rmse.to_numpy(), d.interaction_rmse.to_numpy()))
    values=np.array([100*(r-i)/r for _,r,i in groups]).T
    pd.DataFrame(values,index=targets,columns=[x[0].replace("\n"," ") for x in groups]).to_csv(OUT/"rmse_improvement.csv")
    fig=base((7.2,6.0),(.23,.79,.22,.80))
    title(fig,"03  交互模型的误差改善覆盖多个目标域","以同组 Ridge 为基线；蓝色为 RMSE 下降，橙色为 RMSE 上升")
    ax=fig.add_subplot()
    limit=max(10,float(np.max(np.abs(values))))
    im=heatmap(ax,values,[LABELS[t] for t in targets],[g[0] for g in groups],DIVERGE,
               norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit),formatter=lambda v:f"{v:+.1f}%")
    # Negative values are orange, positive values blue: reverse the shared diverging map.
    im.set_cmap(DIVERGE.reversed())
    for txt in ax.texts:
        j,i=txt.get_position(); rgba=im.cmap(im.norm(values[int(i),int(j)]))
        txt.set_color("white" if sum(c*w for c,w in zip(rgba[:3],[.2126,.7152,.0722]))<.5 else INK)
    cax=fig.add_axes([.84,.30,.025,.44]);cb=fig.colorbar(im,cax=cax);cb.set_label("RMSE 下降比例（%）",fontsize=8)
    counts=(values>0).sum(axis=0)
    fig.text(.23,.145,"改善目标数："+"  /  ".join(f"{n}/13" for n in counts),fontsize=9,color=BLUE)
    finish(fig,"03_validation","改善 = (Ridge RMSE − 交互 RMSE) / Ridge RMSE。每格来自一个目标域的配方误差。\nA6–A11 曾用于模型形式判断；1B 中 47/64 配方在训练凸包外。",["targetwise_oof.csv","targetwise_validation.csv"],audit)


def rank_stress(audit):
    observed=read_csv("targetwise_validation.csv"); estimated=read_csv("estimated_targetwise.csv")
    groups=[]
    for scope,label in [("test_1m","1M"),("test_60m","60M"),("test_1B","1B")]:
        d=observed[(observed.scope==scope)&(observed.support_group=="all")]
        groups.append((label,d.interaction_spearman.to_numpy(),BLUE))
    for scope,label in [("est_10B","10B\n估算"),("est_70B","70B\n估算")]:
        groups.append((label,estimated[estimated.scope==scope].v2_spearman.to_numpy(),ORANGE))
    fig=base((7.2,4.9),(.13,.95,.25,.79))
    title(fig,"04  排序信息有保留，估算外推明显变弱","每组展示全部 13 个目标域；箱体为四分位范围，黑线为中位数")
    ax=fig.add_subplot()
    ax.axvspan(3.5,5.5,color=ORANGE,alpha=.07,zorder=0)
    for x,(label,values,color) in enumerate(groups,1):
        bp=ax.boxplot([values],positions=[x],widths=.44,patch_artist=True,showfliers=False,
                      medianprops={"color":INK,"lw":1.5},whiskerprops={"color":color},capprops={"color":color})
        bp['boxes'][0].set(facecolor=color,alpha=.18,edgecolor=color)
        jitter=np.linspace(-.14,.14,len(values))
        ax.scatter(x+jitter,values,s=22,facecolor=color,edgecolor="white",linewidth=.4,zorder=3,
                   marker="o" if x<=3 else "D")
        ax.text(x,1.04,f"{np.median(values):.3f}",ha="center",fontsize=10,color=color,weight="bold")
    ax.axvline(3.5,color=GREY,ls="--",lw=1)
    ax.set_xticks(range(1,6),[g[0] for g in groups]);ax.set_ylim(0,1.12);ax.set_xlim(.5,5.5)
    ax.set_ylabel("目标域排序相关 Spearman ρ");clean(ax,"y")
    fig.text(.18,.15,"真实检验组：n=256 / 256 / 64",fontsize=8,color=BLUE)
    fig.text(.64,.15,"估算压力表：各 n=63",fontsize=8,color=ORANGE)
    finish(fig,"04_rank_stress","标注值为 13 目标域的中位数；目标域并非 13 次独立训练实验。\n右侧 10B/70B 由附件估算得到，不能称为真实大模型训练验证。",["targetwise_validation.csv","estimated_targetwise.csv"],audit)


def recipes(audit, domains, coeff, ref):
    bounds=read_json("hull_bounds.json")
    comps=[ref]+[b["feasible_composition"] for b in bounds]
    data=np.array([[100*p[d] for p in comps] for d in domains])
    sort=np.argsort(-data.max(axis=1));data=data[sort]
    ordered=[domains[i] for i in sort]
    pd.DataFrame(data,index=ordered,columns=["reference"]+POLICIES).to_csv(OUT/"continuous_recipes_percent.csv")
    fig=base((7.2,6.9),(.23,.83,.24,.81))
    title(fig,"05  质量约束会改变配方的组成","17 个训练域 × 参考配方及四个连续凸包情景；单元格为训练份额（%）")
    ax=fig.add_subplot()
    im=heatmap(ax,data,[LABELS[d] for d in ordered],["参考\n平均配方","等权\n无约束","等权\ndirect","等权\ndirect+near","保护\n最差目标"],
               vmin=0,vmax=30,formatter=lambda v:f"{v:.1f}" if v>=.5 else "·")
    cax=fig.add_axes([.88,.34,.022,.43]);cb=fig.colorbar(im,cax=cax);cb.set_label("训练份额（%）",fontsize=8)
    fig.text(.23,.16,"加入质量约束后，arXiv 的份额明显增加；保护最差目标时，配方更分散。",fontsize=8,color=BLUE)
    finish(fig,"05_recipes","每列总和为 100%；“·”表示份额小于 0.5%，完整数值另存 CSV。\n这里展示连续凸包可行解；其位置不等于离散候选编号 136 / 301 / 172 / 477。",["hull_bounds.json","interaction_feature_definition.json"],audit)


def policy_results(audit,targets,coeff,ref):
    bounds=read_json("hull_bounds.json")
    def predict(target,p):
        c=coeff[target]
        return c['intercept']+sum(c['main'][d]*p[d] for d in c['main'])+sum(x['gamma']*p[x['domains'][0]]*p[x['domains'][1]] for x in c['pairs'])
    gains=np.array([[100*(1-predict(t,b['feasible_composition'])/coeff[t]['fitted_reference_loss']) for b in bounds] for t in targets])
    loss_values=np.array([[predict(t,b['feasible_composition']) for b in bounds] for t in targets])
    pd.DataFrame(gains,index=targets,columns=POLICIES).to_csv(OUT/"predicted_target_improvement_percent.csv")
    pd.DataFrame(loss_values,index=targets,columns=POLICIES).to_csv(OUT/"predicted_target_loss.csv")
    fig=base((7.2,6.0),(.23,.81,.22,.79))
    title(fig,"06  配方收益诊断：权衡与非物理预测","蓝色为预测下降、橙色为上升；带 * 的格子出现负预测 Loss")
    ax=fig.add_subplot()
    lim=45
    im=heatmap(ax,gains,[LABELS[t] for t in targets],["等权\n无约束","等权\ndirect","等权\ndirect+near","保护\n最差目标"],
               DIVERGE.reversed(),norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim),formatter=lambda v:f"{v:+.1f}%")
    for i,j in zip(*np.where(loss_values<0)):
        ax.add_patch(Rectangle((j-.5,i-.5),1,1,fill=False,edgecolor=ORANGE,lw=2.2,hatch='//'))
        for txt in ax.texts:
            if txt.get_position()==(j,i):txt.set_text(f"{gains[i,j]:+.1f}% *")
    cax=fig.add_axes([.86,.31,.025,.44]);cb=fig.colorbar(im,cax=cax,extend='both');cb.set_label("预测下降（%；±45% 外饱和）",fontsize=8)
    agg=-100*np.array([b['feasible_upper_bound_relative'] for b in bounds])
    fig.text(.23,.147,"* 数学目标第一列：预测 Loss = −0.0901，不能作为实际改善。",fontsize=8,color='#956000')
    finish(fig,"06_policy_results",f"第四列保护最差目标：最小预测下降 {agg[3]:.2f}%；与前三列平均目标不同。\n冻结 1M 代理的诊断；首列含非物理预测，须修正后再作收益结论。",["hull_bounds.json","interaction_coefficients_13_targets.json"],audit)


def stability(audit):
    d=read_csv("refit_replicate_choices.csv")
    policies=["unconstrained","quality_direct","quality_direct_and_near","minimax"]
    fig=base((7.2,4.8),(.24,.88,.26,.76))
    title(fig,"07  具体推荐配方的稳定性因政策而异","30 次抽取 80% 训练行后重选特征、正则并拟合；仅在 512 个已观测候选中选方")
    ax=fig.add_subplot()
    for i,p in enumerate(policies):
        s=d[d.policy==p].sort_values("repeat")
        if len(s)!=30:raise ValueError("Expected 30 refits per policy")
        same=s.same_as_frozen.astype(str).str.lower().eq('true').to_numpy()
        for repeat,yes in enumerate(same):
            ax.scatter(repeat+1,i,s=23,marker="o" if yes else "x",color=BLUE if yes else ORANGE,linewidth=.9,zorder=3)
        ax.text(31.4,i,f"{sum(same):2d}/30",color=BLUE,fontsize=10,weight="bold",va="center")
    ax.set_yticks(range(4),POLICIES);ax.set_ylim(3.6,-.6);ax.set_xlim(0,35)
    ax.set_xticks([1,5,10,15,20,25,30]);ax.set_xlabel("重拟合次数",labelpad=10);clean(ax)
    fig.text(.24,.105,"● 蓝点：仍选原候选    × 橙叉：选择改变",fontsize=9,color=INK)
    finish(fig,"07_stability","原离散候选依次为 136 / 301 / 172 / 477；无约束等权最稳定。\n重选频数不是连续凸包解的置信区间；质量约束与 minimax 需要报告情景敏感性。",["refit_replicate_choices.csv","refit_stability.json"],audit)


def gallery():
    import html
    cards=[]
    for f in FIGURES:
        stem=f['stem']
        cards.append(f'<section><img src="{stem}.png" alt="{stem}"><p>{html.escape(f["caption"]).replace(chr(10),"<br>")}</p><nav><a href="{stem}.pdf">PDF</a> · <a href="{stem}.svg">SVG</a> · <a href="{stem}.png">PNG</a></nav></section>')
    (OUT/'gallery.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Q1 结果图册</title><style>body{margin:0;background:#edf2f6;color:#243746;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1020px;margin:30px auto;padding:0 20px}section{background:white;margin:24px 0;padding:22px;border-radius:12px}img{width:100%;display:block}p{font-size:14px;color:#536674}a{color:#0072B2}</style><main><h1>Q1 结果图册</h1><p>依据 main @ a19039b 的冻结结果。蓝色表示结果主体，橙色表示估算、损失增加或选方改变。下载矢量图可直接用于后续排版。</p>'+''.join(cards)+'</main></html>',encoding='utf-8')


def pair_contributions(audit, targets, coeff, ref, pairs):
    values=np.array([[100*x['gamma']*ref[x['domains'][0]]*ref[x['domains'][1]]/coeff[t]['fitted_reference_loss']
                     for x in coeff[t]['pairs']] for t in targets])
    short={'freelaw':'Law','arxiv':'arXiv','pubmed_central':'PMC','github':'GitHub','pile_cc':'CC'}
    pair_labels=[short[a]+' ×\n'+short[b] for a,b in pairs]
    pd.DataFrame(values,index=targets,columns=['*'.join(p) for p in pairs]).to_csv(OUT/'pair_contributions_at_reference_percent.csv')
    fig=base((7.2,6.0),(.22,.86,.23,.80))
    title(fig,"08  组合项的作用方向随目标域变化","参考配方处的二元项贡献；蓝色降低预测 Loss、橙色增加预测 Loss")
    ax=fig.add_subplot()
    lim=max(abs(values.min()),abs(values.max()))
    im=heatmap(ax,values,[LABELS[t] for t in targets],pair_labels,DIVERGE,
               norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim),formatter=lambda v:f'{v:+.1f}')
    ax.tick_params(axis='x',labelsize=6.8)
    cax=fig.add_axes([.90,.33,.016,.42]);cb=fig.colorbar(im,cax=cax);cb.set_label('相对参考 Loss 的贡献（%）',fontsize=7.5)
    fig.text(.22,.15,'Law = FreeLaw；PMC = PubMed Central；CC = Pile-CC',fontsize=7.5,color=BLUE)
    finish(fig,'08_pair_contributions','每格为 γ_uv × p_ref,u × p_ref,v / 参考预测 Loss；表示模型项的局部组成。\n不等于两域因果协同，也不等于增配两域的总效应；主项及配比转移同时影响 Loss。',
           ['interaction_coefficients_13_targets.json','interaction_feature_definition.json'],audit)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-dir',type=Path,default=Path.home()/'.codex/skills/scipilot-figure-skill')
    args=parser.parse_args()
    sys.path.insert(0,str(args.skill_dir/'scripts'))
    from setup_style import setup_style
    from profile_data import profile_data
    from visual_qa import audit_layout
    setup_style(journal='general',lang='zh',use_sciplots=False)
    plt.rcParams.update({'font.family':['Microsoft YaHei'],'font.sans-serif':['Microsoft YaHei'],
        'font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
        'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
        'figure.constrained_layout.use':False,'axes.unicode_minus':False})
    OUT.mkdir(parents=True,exist_ok=True)
    profiles={}
    for name in ['domain_quality.csv','targetwise_validation.csv','targetwise_oof.csv','estimated_targetwise.csv','decision_panel.csv','refit_replicate_choices.csv']:
        profiles[name]=profile_data(read_csv(name))
    (OUT/'scipilot_profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    f=read_json('interaction_feature_definition.json');coeff=read_json('interaction_coefficients_13_targets.json')['targets']
    targets=f['target_order'];domains=f['domain_order'];ref=f['Q1_reference_p']
    quality(audit_layout);conflict(audit_layout);model_validation(audit_layout,targets)
    rank_stress(audit_layout);recipes(audit_layout,domains,coeff,ref)
    policy_results(audit_layout,targets,coeff,ref);stability(audit_layout)
    pair_contributions(audit_layout,targets,coeff,ref,f['pairs_order'])
    gallery()
    manifest={'source_main':'a19039b5d11c91cf32e301dc85b2f4d50b5a75b7','model':'chm.q1.v2.0',
        'palette':{'primary':BLUE,'positive_auxiliary':TEAL,'stress_or_adverse':ORANGE},
        'inputs':{n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in sorted(INPUTS)},
        'figures':FIGURES,'layout_audit':LAYOUT,'visual_review':'pending',
        'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'figures':len(FIGURES),'layout':LAYOUT},ensure_ascii=False))


if __name__=='__main__':main()
