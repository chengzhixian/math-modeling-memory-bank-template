"""Q3 frozen-result figures; run previews, inspect, then rerun with --finalize.

Uses the Q2 presentation helpers to preserve styling. Does not run optimizers.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
import q2_redesign as style

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'outputs/Q3'
OUT=SOURCE/'redesign'
MAIN='b789e3fc02ba894c4787ea351f87e56fc4e7daa8'
CONTEXTS=[2048,8192,131072]
COLORS=[style.BLUE,style.TEAL,style.ORANGE]
MARKERS=['o','s','^']
BUDGETS=[1e19,1e22,1e24]
FAMILIES=['exponential','power','logarithmic']
NAMES=['指数成本','幂成本','对数成本']
csv,js,base,clean,finish=style.csv,style.js,style.base,style.clean,style.finish

def feasible(d):
    return d.status.str.endswith('_feasible')

def choose(d,context=8192,family='power'):
    return d[(d.context_tokens==context)&(d.quality_family==family)].sort_values('budget_FLOPs')

def budget_axis(ax,diagnostic=False):
    ax.set_xscale('log');ax.set_xlim(8e18,1.3e24)
    b=[1e19,1e20,1e22,1e24] if diagnostic else BUDGETS
    ax.set_xticks(b,[rf'$10^{{{int(np.log10(v))}}}$' for v in b]);clean(ax)

def configuration():
    fig=base('01  三档预算下的条件配置','幂函数质量成本；每格列出预测 Loss、规模 N、训练量 D、配方编号',size=(7.2,6.0),margins=(.15,.81,.23,.80))
    ax=fig.add_subplot();values=np.full((3,3),np.nan);rows=[]
    for i,c in enumerate(CONTEXTS):
        for j,b in enumerate(BUDGETS):
            row=GRID[(GRID.context_tokens==c)&(GRID.quality_family=='power')&(GRID.budget_FLOPs==b)].iloc[0]
            if feasible(pd.DataFrame([row])).iloc[0]:values[i,j]=row.conditional_bridge_loss
            rows.append(row)
    cmap=style.SEQ.copy();cmap.set_bad('#EDF1F4')
    im=ax.pcolormesh(np.arange(4)-.5,np.arange(4)-.5,np.ma.masked_invalid(values),cmap=cmap,norm=Normalize(1.95,3.25),edgecolors='white',linewidth=3)
    ax.set_ylim(2.5,-.5);ax.set_xlim(-.5,2.5)
    ax.set_yticks(range(3),[f'{c:,} Token' for c in CONTEXTS]);ax.set_xticks(range(3),[rf'$10^{{{int(np.log10(b))}}}$' for b in BUDGETS])
    ax.set_xlabel('预算（FLOPs）',labelpad=10);ax.tick_params(length=0,pad=8)
    for sp in ax.spines.values():sp.set_visible(False)
    for k,row in enumerate(rows):
        i,j=divmod(k,3)
        if not np.isfinite(values[i,j]):
            ax.add_patch(Rectangle((j-.5,i-.5),1,1,fill=False,hatch='///',edgecolor='#CBD5DF',linewidth=0))
            ax.text(j,i,'支持域内\n不可行',ha='center',va='center',fontsize=10,color=style.INK)
        else:
            v=values[i,j];rgb=im.cmap(im.norm(v));lum=.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
            text=f'Loss {v:.4f}\nN {row.N_params_B:.3f}B\nD {row.D_tokens_B:.1f}B\n配方 {int(row.recipe_index)}'
            ax.text(j,i,text,ha='center',va='center',fontsize=8.5,linespacing=1.65,color='white' if lum<.55 else style.INK)
    ca=fig.add_axes([.87,.30,.025,.43]);cb=fig.colorbar(im,cax=ca)
    cb.set_label('条件预测 Loss',fontsize=8)
    cb.solids.set_rasterized(False)
    finish(fig,'01_configuration','候选为 87 个符合质量与映射政策的已观测 A4 配方；不是连续凸包全局最优。\n最高预算触及 N、D 支持上界；不可行格不填零。质量随配方确定，跨源桥尚未标定。')

def trajectories():
    fig=base('02  预算增加时，资源先扩展再触及支持上限','幂成本；三种 C7 上下文分别展示同一条件优化流程',size=(7.2,7.4),margins=(.15,.93,.18,.81))
    axes=fig.subplots(3,1,sharex=True,gridspec_kw={'hspace':.23})
    for i,(col,label) in enumerate([('N_params_B','规模 N（十亿参数）'),('D_tokens_B','训练量 D（十亿 tokens）'),('conditional_bridge_loss','条件预测 Loss')]):
        ax=axes[i]
        for c,color,marker,ls in zip(CONTEXTS,COLORS,MARKERS,['-','--',':']):
            s=choose(SCAN,c);valid=feasible(s);v=s[col].where(valid)
            ax.plot(s.budget_FLOPs,v,color=color,ls=ls,lw=1.5,marker=marker,markevery=25,ms=3.5,label=f'{c:,} Token')
        ax.set_ylabel(label);budget_axis(ax)
        if i<2:ax.set_yscale('log')
        ax.text(-.13,1.02,chr(97+i),transform=ax.transAxes,fontsize=10,weight='bold')
    axes[0].axhline(11.965825,color=style.GREY,lw=.8,ls='--')
    axes[1].axhline(299.893,color=style.GREY,lw=.8,ls='--')
    axes[-1].set_xlabel('预算（FLOPs）',labelpad=8)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.54,.84),ncol=3,frameon=False,fontsize=8)
    finish(fig,'02_budget_paths','每条曲线来自 161 个对数预算点；缺失段为支持域内不可行，不跨缺口连线。\n灰虚线为 N、D 上限；平台由支持范围限制形成，不说明域外投入没有价值。')

def recipe_switch():
    joint=choose(SCAN);fixed=choose(csv('fixed_budget_scan.csv'))
    joint=joint[joint.budget_FLOPs<=1e20];fixed=fixed[fixed.budget_FLOPs<=1e20]
    t=csv('transitions.csv');t=t[(t.scenario=='observed_joint')&(t.context_tokens==8192)&(t.quality_family=='power')]
    t=t[t.state_left.str.startswith('recipe=477;')&t.state_right.str.startswith('recipe=172;')]
    if len(t)!=1:raise ValueError('Expected one 477 to 172 transition')
    lo,hi=t.iloc[0][['budget_left','budget_right']];mid=np.sqrt(lo*hi)
    fig=base('03  低预算存在配方 477 → 172 的数值切换','8192 Token、幂成本；两行分别展示条件预测 Loss 与配方质量代理',size=(7.2,6.2),margins=(.15,.93,.23,.80))
    top,bottom=fig.subplots(2,1,sharex=True,gridspec_kw={'height_ratios':[2,1],'hspace':.30})
    for s,color,ls,label in [(joint,style.BLUE,'-','87 个观测候选联立选择'),(fixed,style.GREY,'--','固定配方 172')]:
        top.plot(s.budget_FLOPs,s.conditional_bridge_loss.where(feasible(s)),color=color,ls=ls,lw=1.7,label=label)
    top.set_ylabel('条件预测 Loss');top.legend(frameon=False,fontsize=8,loc='upper right')
    for recipe in [477,172]:
        s=joint[(joint.recipe_index==recipe)&feasible(joint)]
        left,right=(1e19,lo) if recipe==477 else (hi,1e20)
        bottom.plot([left,right],[s.Q_B_proxy.iloc[0]]*2,color=style.TEAL,lw=1.6)
    bottom.set_ylabel('质量代理 q');bottom.set_ylim(.55,.73)
    for ax in [top,bottom]:
        clean(ax);ax.set_xscale('log');ax.set_xlim(1e19,1e20)
        ax.axvspan(lo,hi,color=style.ORANGE,alpha=.55)
        ax.axvline(mid,color=style.ORANGE,lw=1,ls=':')
    top.annotate('配方切换括区',xy=(mid,3.05),xytext=(2.05e19,3.18),fontsize=8,color='#956000',arrowprops={'arrowstyle':'->','color':style.ORANGE})
    bottom.text(1.08e19,.58,'配方 477',fontsize=8,color=style.INK)
    bottom.text(2e19,.689,'配方 172',fontsize=8,color=style.INK)
    bottom.set_xticks([1e19,2e19,5e19,1e20],[r'$10^{19}$',r'$2\times10^{19}$',r'$5\times10^{19}$',r'$10^{20}$'])
    bottom.set_xlabel('预算（FLOPs）',labelpad=8)
    finish(fig,'03_recipe_switch',f'切换括区：[{lo/1e19:.6f}, {hi/1e19:.6f}] × 10^19 FLOPs；橙线为括区中点，仅作定位。\nq 为配方决定的代理，不是独立干预；数值状态转移不等于真实训练的物理相变。')

def costs():
    fig=base('04  三项成本与未使用预算的分配','幂成本；所有色块均以给定预算为分母，保留支持上限造成的未使用部分',size=(7.2,6.0),margins=(.21,.84,.22,.79))
    ax=fig.add_subplot();labels=[];derived=[]
    for i,b in enumerate(BUDGETS):
        for j,c in enumerate(CONTEXTS):
            y=3*i+j;labels.append(rf'$10^{{{int(np.log10(b))}}}$'+' · '+f'{c:,}')
            row=GRID[(GRID.budget_FLOPs==b)&(GRID.context_tokens==c)&(GRID.quality_family=='power')].iloc[0]
            if not feasible(pd.DataFrame([row])).iloc[0]:
                ax.barh(y,100,color='#EDF1F4',hatch='///',edgecolor='#CBD5DF',height=.62)
                ax.text(50,y,'支持域内不可行',ha='center',va='center',fontsize=8,color=style.GREY)
                continue
            amounts=np.array([row.C_train_FLOPs,row.C_attention_FLOPs,row.C_quality_FLOPs])/b*100
            if not np.isclose(amounts.sum(),row.budget_utilization*100,rtol=1e-9):raise ValueError('Cost denominator mismatch')
            values=list(amounts)+[max(0,100-amounts.sum())];left=0
            for value,color in zip(values,[style.BLUE,style.TEAL,style.ORANGE,'#DCE4EB']):
                ax.barh(y,value,left=left,color=color,height=.62,edgecolor='white',linewidth=.4);left+=value
            ax.text(102,y,f'{amounts.sum():.2f}%',va='center',fontsize=8,color=style.INK)
            derived.append({'budget_FLOPs':b,'context_tokens':c,'train_percent':values[0],'attention_percent':values[1],'quality_percent':values[2],'unused_percent':values[3]})
    ax.set_yticks(range(9),labels,fontsize=8);ax.set(xlim=(0,100),ylim=(8.6,-.6),xlabel='占给定预算比例（%）')
    for y in [2.5,5.5]:ax.axhline(y,color=style.LIGHT,lw=1)
    clean(ax,'x')
    handles=[Rectangle((0,0),1,1,facecolor=c) for c in [style.BLUE,style.TEAL,style.ORANGE,'#DCE4EB']]
    fig.legend(handles,['基础训练','注意力','质量投入','未使用'],loc='lower center',bbox_to_anchor=(.54,.825),ncol=4,frameon=False,fontsize=8)
    fig.text(.85,.805,'使用率',fontsize=8,color=style.GREY)
    pd.DataFrame(derived).to_csv(OUT/'cost_budget_shares.csv',index=False)
    finish(fig,'04_cost_allocation','左侧：预算 FLOPs · 上下文 Token；右侧为总预算使用率，不是各项成本占比。\n最高预算的灰色部分主要来自 N、D 支持上限；不可行状态不解释为零成本。')

def family_comparison():
    fig=base('05  质量成本形式会影响条件配置','8192 Token；分开显示低预算与中预算，横轴为明确放大的 Loss 局部范围',margins=(.14,.97,.27,.79))
    axes=fig.subplots(1,2,gridspec_kw={'wspace':.42})
    for ax,b in zip(axes,[1e19,1e22]):
        rows=[GRID[(GRID.context_tokens==8192)&(GRID.quality_family==f)&(GRID.budget_FLOPs==b)].iloc[0] for f in FAMILIES]
        vals=np.array([r.conditional_bridge_loss for r in rows]);span=vals.max()-vals.min()
        for i,row in enumerate(rows):
            ax.scatter(row.conditional_bridge_loss,i,s=40,color=style.BLUE,marker=MARKERS[i])
            ax.text(row.conditional_bridge_loss,i-.22,f'{row.conditional_bridge_loss:.6f}',ha='center',fontsize=7.8,color=style.INK)
        ax.set_yticks(range(3),NAMES,fontsize=8);ax.set_ylim(2.7,-.65)
        ax.set_xlim(vals.min()-span*.35,vals.max()+span*.35)
        ax.set_xlabel('条件预测 Loss（局部放大）',fontsize=8,labelpad=10)
        ax.set_title(rf'预算 $10^{{{int(np.log10(b))}}}$ FLOPs',fontsize=10,pad=12)
        ax.ticklabel_format(axis='x',style='plain',useOffset=False)
        ax.locator_params(axis='x',nbins=3);clean(ax,'x')
    finish(fig,'05_cost_families','低预算指数成本选择 172，幂 / 对数成本选择 477；中预算三族均选择 172。\n两面板横轴范围不同；10^24 FLOPs 下三族都触及 N、D 上界，得到相同条件 Loss。')

def context_cost():
    lc=np.geomspace(1000,180000,250)
    fig=base('06  长上下文的注意力开销有明确代数临界点','由题面成本公式：注意力 / 基础训练 = 上下文长度 / 30,000')
    ax=fig.add_subplot();ax.plot(lc,lc/30000,color=style.GREY,lw=1.4)
    ax.axhline(1,color=style.GREY,ls='--',lw=1)
    ax.axvline(30000,color=style.GREY,ls=':',lw=1)
    for c,color,m in zip(CONTEXTS,COLORS,MARKERS):
        ax.scatter(c,c/30000,color=color,marker=m,s=55,zorder=3)
        ax.annotate(f'{c:,} Token\n比值 {c/30000:.4f}',(c,c/30000),xytext=(8,22) if c<30000 else (-8,-34),textcoords='offset points',ha='left' if c<30000 else 'right',fontsize=8,color=color)
    ax.annotate('30,000 Token：两项相等',(30000,1),xytext=(0,26),textcoords='offset points',ha='center',fontsize=8,color=style.INK)
    ax.set(xscale='log',yscale='log',xlim=(1000,180000),ylim=(.025,9),xlabel='上下文长度（Token）',ylabel='注意力成本 / 基础训练成本')
    ax.set_xticks([2048,8192,30000,131072],['2,048','8,192','30,000','131,072']);clean(ax)
    finish(fig,'06_context_cost','彩色标记对应 C7 提供的外生上下文情景；连续线来自成本代理的代数式。\n临界长度不是观测能力阈值；此比值不包含质量投入，131072 Token 的 C7 支持稀疏。')

def assumptions():
    meta=js('assumption_sensitivity.json');comparisons=meta['comparisons']
    d=csv('assumption_official_grid.csv')
    names=['主情景',r'$Q_0=0.45$',r'$Q_0=0.55$',r'$Q_0=0.60$',r'$Q_0=0.65$',r'$s=0.5$',r'$s=1.5$',r'$\lambda=0$',r'$\lambda=2$']
    fig=base('07  配方选择对跨源桥接假设敏感','9 个单因素情景；比较三预算 × 三上下文 × 三成本族的 27 个题面格',size=(7.2,5.8),margins=(.16,.72,.24,.80))
    ax=fig.add_subplot()
    changes=[x['changed_feasibility_or_recipe_cells'] for x in comparisons]
    ax.barh(range(9),changes,color=[style.BLUE]+[style.ORANGE]*8,height=.55)
    for i,entry in enumerate(comparisons):
        if entry['feasible_official_cells']!=24:raise ValueError('Sensitivity feasible cell count changed')
        ax.text(changes[i]+.35,i,str(changes[i]),fontsize=8.5,va='center',color=style.INK)
        for b,x in [(1e19,29.2),(1e22,34.0)]:
            r=d[(d.scenario==entry['scenario'])&(d.budget_FLOPs==b)&(d.context_tokens==8192)&(d.quality_family=='power')].iloc[0]
            ax.text(x,i,str(int(r.recipe_index)),ha='center',va='center',fontsize=8.5,color=style.INK)
    ax.set_yticks(range(9),names);ax.set(xlim=(0,26),ylim=(8.7,-1.1),xlabel='配方或可行性改变的格数（共 27 格）')
    ax.set_xticks([0,6,12,18,24]);clean(ax,'x')
    ax.text(29.2,-.8,'低预算\n配方',ha='center',fontsize=7.5,color=style.GREY)
    ax.text(34,-.8,'中预算\n配方',ha='center',fontsize=7.5,color=style.GREY)
    finish(fig,'07_assumptions','全部指定情景仍为 24 / 27 格可行；λ=0 时所有 24 个可行格的推荐配方均改变。\n右侧为 8192 Token、幂成本下的低 / 中预算配方；情景不代表置信区间或概率分布。\nQ0 为质量基线；s 为质量映射斜率倍数；λ 为配比桥强度。')

def native_quality():
    native=choose(csv('native_Q_sensitivity_grid.csv'));joint=choose(GRID)
    fig=base('08  配比决定质量与独立质量投入是两种方案','8192 Token、幂成本；并列展示两个假设机制，不把差值解释为实测干预收益',size=(7.2,6.8),margins=(.13,.94,.23,.80))
    axes=fig.subplots(2,2,gridspec_kw={'hspace':.40,'wspace':.36})
    for k,(col,label) in enumerate([('N_params_B','规模 N（B 参数）'),('D_tokens_B','训练量 D（B tokens）'),('Q_B_proxy','质量代理 q / Q_B'),('conditional_bridge_loss','条件预测 Loss')]):
        ax=axes.flat[k]
        ax.plot(joint.budget_FLOPs,joint[col],color=style.BLUE,marker='o',ms=4,lw=1.5,label='配比联立 · q(p)')
        native_col='Q_score' if col=='Q_B_proxy' else col
        ax.plot(native.budget_FLOPs,native[native_col],color=style.TEAL,marker='s',ms=4,ls='--',lw=1.5,label='固定 172 · 独立 Q_B')
        budget_axis(ax,True);ax.set_ylabel(label,fontsize=8)
        if k<2:ax.set_yscale('log')
        if k==2:ax.set_ylim(.4,1.08)
        if k>=2:ax.set_xlabel('预算（FLOPs）',fontsize=8)
        ax.text(-.13,1.02,chr(97+k),transform=ax.transAxes,fontsize=10,weight='bold')
    fig.legend(*axes.flat[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.54,.83),ncol=2,frameon=False,fontsize=8)
    finish(fig,'08_independent_quality','10^20 为额外诊断预算；其余三档为题面预算。独立 Q_B 使用 B7 半合成质量坐标。\n两方案的质量生成机制及配方限制不同；原生质量敏感性不证明 A 侧质量可被独立操控。')

def external():
    d=csv('external_nd_runs.csv');audit=js('external_nd_audit.json')
    check=csv('external_nd_budget_comparison.csv')
    restricted=check[check.training_cost_budget_FLOPs.isin([1e20,1e21])]
    if len(restricted)!=6 or sum(restricted.selection_match)!=5:raise ValueError('External budget selection mismatch')
    fig=base('09  公开实验支持 N–D 子结构的排序','42 个独立 OpenLM 模型，分语料各 14 个；用排名避免混合两种绝对 Loss 坐标',margins=(.11,.97,.28,.79))
    axes=fig.subplots(1,3,gridspec_kw={'wspace':.40})
    ranks=[]
    for ax,corpus,label,color in zip(axes,['c4_original','rpj','rw_original'],['C4','RedPajama','RefinedWeb'],COLORS):
        s=d[d.training_corpus==corpus].copy()
        s['predicted_rank']=s.B1_predicted_loss_in_Pythia_coordinates.rank()
        s['observed_rank']=s.observed_Paloma_C4_loss_in_OpenLM_coordinates.rank()
        rho=s.predicted_rank.corr(s.observed_rank)
        published=next(x['Spearman_B1_vs_external_loss'] for x in audit['correlations'] if x['training_corpus']==corpus)
        if len(s)!=14 or not np.isclose(rho,published):raise ValueError('External rank mismatch')
        ranks.append(s)
        ax.scatter(s.predicted_rank,s.observed_rank,color=color,s=26,alpha=.8)
        ax.plot([1,14],[1,14],color=style.GREY,lw=1,ls='--')
        ax.set(xlim=(0,15),ylim=(0,15),xlabel='B1 预测排名',title=label)
        ax.set_xticks([1,7,14]);ax.set_yticks([1,7,14]);clean(ax)
        ax.text(.08,.88,f'ρ = {rho:.4f}\nn = 14',transform=ax.transAxes,fontsize=8,color=color)
    axes[0].set_ylabel('OpenLM 观测排名')
    pd.concat(ranks).to_csv(OUT/'external_within_corpus_ranks.csv',index=False)
    finish(fig,'09_external_ranks','排名 1 表示最低 Loss；对角虚线为排名一致。预算筛选真正限制候选的 6 组中命中 5 组。\nRefinedWeb 的 10^21 组未命中，实测 Loss regret≈0.0705；外测不含可对齐 Q / p。\n仅复算冻结公开表的排序与选择，不是完整 N、D、Q、p 最优的真实实验验证。')

def main():
    global GRID,SCAN
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill-dir',type=Path,default=Path.home()/'.codex/skills/scipilot-figure-skill')
    p.add_argument('--finalize',action='store_true')
    args=p.parse_args();sys.path.insert(0,str(args.skill_dir/'scripts'))
    from setup_style import setup_style
    from profile_data import profile_data
    from visual_qa import audit_layout
    setup_style(journal='general',lang='zh',use_sciplots=False)
    plt.rcParams.update({'font.family':['Microsoft YaHei'],'font.sans-serif':['Microsoft YaHei'],
        'font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
        'text.color':style.INK,'axes.labelcolor':style.INK,'xtick.color':style.INK,'ytick.color':style.INK,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,
        'figure.constrained_layout.use':False})
    style.SOURCE=SOURCE;style.OUT=OUT;style.FINALIZE=args.finalize;style.AUDIT=audit_layout
    OUT.mkdir(parents=True,exist_ok=True)
    GRID=csv('observed_joint_grid.csv');SCAN=csv('observed_budget_scan.csv')
    style.INPUTS.update([SOURCE/'ANSWER.md',SOURCE/'curated_manifest.json'])
    source=js('manifest.json')
    for name,sha in source['output_files_sha256'].items():
        f=SOURCE/name
        raw=f.read_bytes();matches=[hashlib.sha256(raw).hexdigest()]
        if f.suffix in ['.csv','.json']:matches.append(hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest())
        if sha not in matches:raise ValueError(f'Frozen Q3 source hash mismatch: {name}')
    for name in ['observed_joint_grid.csv','native_Q_sensitivity_grid.csv']:
        d=csv(name);valid=feasible(d)
        if not np.isclose(d.loc[valid,['C_train_FLOPs','C_quality_FLOPs','C_attention_FLOPs']].sum(axis=1),d.loc[valid,'C_total_FLOPs'],rtol=1e-9).all():raise ValueError('Cost sum mismatch')
        if not (d.loc[valid,'C_total_FLOPs']<=d.loc[valid,'budget_FLOPs']*(1+1e-8)).all():raise ValueError('Budget exceeded')
    profiles={}
    for name in ['observed_joint_grid.csv','observed_budget_scan.csv','native_Q_sensitivity_grid.csv','assumption_official_grid.csv','external_nd_runs.csv']:
        profiles[name]=profile_data(csv(name))
    (OUT/'scipilot_profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    configuration();trajectories();recipe_switch();costs();family_comparison();context_cost();assumptions();native_quality();external()
    cards=[]
    for f in style.FIGURES:
        s=f['stem'];cards.append(f'<section><img src="{s}.png" alt="{s}"><p>{html.escape(f["caption"]).replace(chr(10),"<br>")}</p><a href="{s}.pdf">PDF</a> · <a href="{s}.svg">SVG</a></section>')
    (OUT/'gallery.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Q3 结果图册</title><style>body{margin:0;background:#edf2f6;color:#243746;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1020px;margin:30px auto;padding:0 20px}section{background:white;margin:24px 0;padding:22px;border-radius:12px}img{width:100%}p{font-size:14px;color:#536674}a{color:#0072B2}</style><main><h1>Q3 结果图册</h1><p>main @ b789e3f 的冻结条件结果；与 Q1、Q2 同一绘图分支、同一版式。未标定跨源桥，最优仅限给定模型和候选。</p>'+''.join(cards)+'</main></html>',encoding='utf-8')
    manifest={'source_main':MAIN,'model':'chm.q3.conditional_v8.release.v1','producer':'frozen CSVs; no refit or optimization',
              'inputs':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(style.INPUTS)},
              'scripts':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),ROOT/'src/visualization/q2_redesign.py']},
              'figures':style.FIGURES,'layout_audit':style.AUDITS,'visual_review':'reviewed previews before vector export' if args.finalize else 'pending',
              'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'figures':len(style.FIGURES),'layout':style.AUDITS},ensure_ascii=False))

if __name__=='__main__':main()
