"""Q4 frozen v3 scientific figures; preview, inspect, then --finalize.

No model fitting, forecast updates or changes to frozen result tables.
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
import matplotlib.dates as mdates
import q2_redesign as style

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'outputs/Q4'
OUT=SOURCE/'redesign'
MAIN='4098b8c6ca0b91b7ecd35e9251d08710dc0d6098'
TYPES=['non_pretrained','pretrained']
TYPE_NAMES=['后训练模型','基座模型']
MODELS=['constant','frontier_trend','mean_resource','quantile_resource']
MODEL_NAMES=['常数','前沿趋势','均值资源','分位资源']
COLORS=[style.GREY,style.ORANGE,style.TEAL,style.BLUE]
MARKERS=['D','^','s','o']
COORDS=['Pythia training log (Attachment B, final checkpoint D=299.9B tokens)',
        'Qwen2 Technical Report (Alibaba, 2024), validation loss',
        'Qwen2.5 Technical Report (Alibaba, 2024), validation loss']
csv,js,base,clean,finish=style.csv,style.js,style.base,style.clean,style.finish


def history():
    d=csv('prepared/leaderboard_sample.csv')
    d=d[d.model_class.isin(['pretrained','chat','domain_finetuned'])].copy()
    tasks=['IFEval','BBH','MATH Lvl 5','GPQA','MUSR','MMLU-PRO']
    if not np.allclose(d.S,d[tasks].mean(axis=1)):raise ValueError('Six-task score mismatch')
    d['date']=pd.to_datetime(d.date,utc=True).dt.tz_localize(None)
    fig=base('01  提交样本中的能力变化与类型差异','C2 六任务等权均分；每个浅点是一个模型，深色菱形为当月样本 q90',size=(7.2,6.8),margins=(.12,.96,.18,.82))
    axes=fig.subplots(2,1,sharex=True,sharey=True,gridspec_kw={'hspace':.32})
    rows=[]
    for ax,typ,name,color in zip(axes,TYPES,TYPE_NAMES,[style.BLUE,style.TEAL]):
        s=d[d.type==typ].copy()
        ax.scatter(s.date,s.S,s=7,alpha=.22,color=color,linewidths=0,rasterized=False)
        g=s.groupby('month').S.agg(n='size',q90=lambda x:x.quantile(.9),median='median').reset_index()
        g['date']=pd.to_datetime(g.month)+pd.Timedelta(days=14)
        ax.scatter(g.date,g.q90,s=35,marker='D',facecolor='white',edgecolor=color,lw=1.4,zorder=4)
        g['type']=typ;rows.append(g)
        ax.set(title=f'{name} · n = {len(s):,}',ylabel='六任务均分（分）',ylim=(0,60))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        clean(ax)
    axes[-1].set_xlabel('榜单提交日期')
    pd.concat(rows).to_csv(OUT/'monthly_score_summary.csv',index=False)
    finish(fig,'01_history','后训练 n=1,620，基座 n=204；仅使用冻结 C2 主样本，不混入 C3 异口径历史 Average。\n日期为提交时间，不能直接解释为发布时间或因果技术进步；当月 q90 不等于后续两月前沿定义。')


def contributions():
    d=csv('historical_standardized_contributions.csv')
    d=d[(d['filter']=='primary')&(d.window_months==2)&(d.bin_width_decades==.5)&(~d.developer_control)]
    fig=base('02  历史增量可拆成三个有方向的项','两个月窗口、0.5 decade 参数分箱；共同支持域标准化分解',size=(7.2,5.6),margins=(.11,.96,.25,.80))
    axes=fig.subplots(1,2,sharey=True,gridspec_kw={'wspace':.26})
    labels=['规模\n分布','规模内\n时间项','支持\n差额','全样本\n净变化']
    for ax,typ,name in zip(axes,TYPES,TYPE_NAMES):
        r=d[d.type==typ].iloc[0]
        vals=[r.scale_distribution_points,r.within_scale_temporal_points,r.composition_support_gap_points]
        if not np.isclose(sum(vals),r.full_observed_mean_change):raise ValueError('Decomposition closure failed')
        start=0
        for i,(v,c) in enumerate(zip(vals,[style.BLUE,style.TEAL,style.ORANGE])):
            end=start+v
            ax.bar(i,abs(v),bottom=min(start,end),color=c,width=.66,alpha=.9)
            ax.text(i,(start+end)/2,f'{v:+.2f}',ha='center',va='center',fontsize=9,color='white' if i<2 else style.INK)
            ax.plot([i+.33,i+.67],[end,end],color=style.GREY,lw=.8)
            start=end
        ax.bar(3,r.full_observed_mean_change,color=style.INK,width=.66)
        ax.text(3,r.full_observed_mean_change+(.35 if start>=0 else -.45),f'{start:+.2f}',ha='center',fontsize=9)
        ax.axhline(0,color=style.GREY,lw=.8);ax.set_xticks(range(4),labels)
        ax.set(title=name,ylim=(-5,8));clean(ax)
        ax.text(.02,.95,f'标准化变化 {r.standardized_change:+.2f} 分',transform=ax.transAxes,fontsize=8,va='top')
    axes[0].set_ylabel('均分变化（分）')
    finish(fig,'02_contributions','后训练：−0.758 + 6.521 = 标准化增量 5.763；再加支持差额 −1.542 得全样本增量 4.222。\n规模内时间项包含 D、后训练、选择与评测变化，不能识别为纯技术贡献。负贡献及超过 100% 的份额不画饼图。')


def sensitivity():
    d=csv('historical_standardized_contributions.csv')
    s=d[(d['filter']=='primary')&(d.window_months==2)&(~d.developer_control)]
    fig=base('03  分箱改变分解幅度，共同支持限制因果判断','主分析两个月窗口；点为确定性规格结果，无采样误差棒',size=(7.2,5.8),margins=(.12,.96,.27,.80))
    axes=fig.subplots(1,2,sharey=True,gridspec_kw={'wspace':.25})
    for ax,typ,name in zip(axes,TYPES,TYPE_NAMES):
        g=s[s.type==typ].sort_values('bin_width_decades')
        for col,label,c,m in [('scale_distribution_points','规模分布',style.BLUE,'o'),('within_scale_temporal_points','规模内时间',style.TEAL,'s'),('standardized_change','标准化总量',style.INK,'D')]:
            ax.plot(g.bin_width_decades,g[col],marker=m,color=c,lw=1.4,ms=5,label=label)
        ax.axhline(0,color=style.GREY,lw=.8,ls='--');ax.set(xticks=[.25,.5,.75],xlabel='参数分箱宽度（decade）',title=name,ylim=(-6,10));clean(ax)
    axes[0].set_ylabel('标准化分解（分）')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.54,.145),ncol=3,frameon=False,fontsize=8)
    finish(fig,'03_sensitivity','后训练三个分箱的规模项份额：−16.47%、−13.15%、−50.08%；主规格为 0.5 decade。\n主规格保留：后训练 313 / 423，基座 78 / 41（早 / 晚）；控制开发者后仅 6 / 8、3 / 2。\n这些规格诊断不能证明 D 与资源结构稳定，也不能把时间项转为因果技术贡献。')


def resources():
    d=csv('c4_annual_resource_comparison.csv');r=js('results.json')['resources']
    fig=base('04  历史资源前沿上升，估计依赖筛选口径','C4 正值完整资源记录；2021–2024 年各年的 q90，年份间连线只帮助阅读',size=(7.2,5.1),margins=(.09,.98,.26,.78))
    axes=fig.subplots(1,3,gridspec_kw={'wspace':.43})
    for ax,col,label in zip(axes,['q90_logC','q90_logN','q90_logD'],['算力 C（FLOPs）','规模 N（B 参数）','数据 D（B tokens）']):
        for gate,name,c,m,ls in [('primary','主筛选',style.BLUE,'o','-'),('wide_ratio','宽筛选',style.TEAL,'s','--')]:
            s=d[(d.resource_gate==gate)&d.year.between(2021,2024)].sort_values('year')
            if s.empty:raise ValueError('Unknown C4 resource gate')
            unit=1 if col=='q90_logC' else 1e9
            ax.plot(s.year,10**s[col]/unit,color=c,marker=m,ls=ls,lw=1.5,ms=5,label=name)
            if col=='q90_logC':
                for row in s.itertuples():ax.annotate(f'n={row.n}',(row.year,10**getattr(row,col)),xytext=(0,8 if gate=='primary' else -14),textcoords='offset points',fontsize=6.5,ha='center',color=c)
        ax.set(yscale='log',xticks=[2021,2022,2023,2024],title=label,xlabel='年份');ax.tick_params(axis='x',labelsize=7);clean(ax)
    axes[0].set_ylabel('年度 q90（对数坐标）')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.54,.13),ncol=2,frameon=False,fontsize=8)
    finish(fig,'04_resources',f'冻结主筛选 81 条、宽筛选 93 条；计算量 q90 年增倍率分别为 4.901、3.986。\n图中 n 为各年记录数；N / D / C 是各自边际 q90，不能拼成一个真实模型或用于相乘复算。\n历史资源趋势是情景输入，不是技术贡献的因果估计。')


def backtests():
    d=csv('rolling_two_month_frontier.csv');comp=csv('frontier_model_comparison.csv')
    fig=base('05  四个滚动窗口中，候选模型表现因类型而异','主资源筛选；每个点是一个两个月测试窗口的预测误差，不合并成误差棒',size=(7.2,5.8),margins=(.12,.96,.28,.80))
    axes=fig.subplots(1,2,sharey=True,gridspec_kw={'wspace':.28})
    for ax,typ,name in zip(axes,TYPES,TYPE_NAMES):
        for i,(model,color,marker) in enumerate(zip(MODELS,COLORS,MARKERS)):
            s=d[(d.type==typ)&(d.resource_gate=='primary')&(d.model==model)].sort_values('origin')
            errors=s.predicted_q90-s.actual_q90
            rmse=np.sqrt(np.mean(errors**2))
            published=comp[(comp.type==typ)&(comp.resource_gate=='primary')&(comp.model==model)].iloc[0]
            if len(s)!=4 or not np.isclose(rmse,published.rmse):raise ValueError('Backtest RMSE mismatch')
            ax.scatter(i+np.linspace(-.16,.16,4),errors,s=35,color=color,marker=marker,zorder=3)
            ax.text(i,-8.5,f'{rmse:.2f}',color=color,ha='center',fontsize=9)
        ax.axhline(0,color=style.GREY,lw=1,ls='--');ax.set_xticks(range(4),['常数','前沿\n趋势','均值\n资源','分位\n资源']);ax.set(title=name,ylim=(-10,18));clean(ax)
        ax.text(.03,.94,'下方数字：RMSE',transform=ax.transAxes,va='top',fontsize=8,color=style.GREY)
    axes[0].set_ylabel('预测 q90 − 实际 q90（分）')
    finish(fig,'05_backtests','后训练分位资源 RMSE 2.199 略优于均值资源 2.237；基座常数模型 RMSE 7.633 最低。\n全部候选测试 R² 为负；只有四个重叠窗口，模型选择与比较共用这些诊断，不构成独立盲测。\n点按起点先后轻微横向错开；不能将四个窗口当作独立重复实验。')


def forecasts():
    d=csv('frontier_candidate_forecasts.csv')
    d=d[(d.resource_gate=='primary')&(d.compute_scenario=='half')]
    fig=base('06  12 / 24 个月情景预测需要分模型类型阅读','算力增长减半；资源候选 η=0.5、漂移保留 0.5；横线为条件 bootstrap 5–95 分位',size=(7.2,6.6),margins=(.19,.95,.25,.80))
    axes=fig.subplots(1,2,sharey=True,gridspec_kw={'wspace':.25})
    labels=[]
    for ax,typ,name in zip(axes,TYPES,TYPE_NAMES):
        s=d[d.type==typ]
        for h in [12,24]:
            for i,(model,color,marker) in enumerate(zip(MODELS,COLORS,MARKERS)):
                r=s[(s.horizon_months==h)&(s.model==model)].iloc[0]
                y=(0 if h==12 else 5)+i
                ax.hlines(y,r.conditional_p05,r.conditional_p95,color=color,lw=2,alpha=.85)
                ax.scatter(r.score,y,s=45,color=color,marker=marker,zorder=3)
                if r.selected_by_diagnostic_rmse:ax.annotate(f'{r.score:.2f} *',(r.score,y),xytext=(4,7),textcoords='offset points',fontsize=8,color=color)
        ax.set(xlim=(0,100),ylim=(8.7,-1),xlabel='最近两月六任务均分 q90（分）',title=name);clean(ax,'x')
    axes[0].set_yticks([0,1,2,3,5,6,7,8],[f'12月 · {n}' for n in MODEL_NAMES]+[f'24月 · {n}' for n in MODEL_NAMES])
    finish(fig,'06_forecasts','* 为四窗口诊断所选候选。后训练：起点 2025-03-13，目标 2026-03-13 / 2027-03-13。\n基座：起点 2025-03-09，目标 2026-03-09 / 2027-03-09；此处未用今天的数据重新预测。\n区间仅为固定情景的条件变动范围，无未来覆盖率校准；预测对象不是所有未来模型的最高能力。')


def uncertainty():
    d=csv('frontier_candidate_forecasts.csv');u=csv('frontier_scenario_union.csv')
    fig=base('07  预测的不确定性从固定假设扩展到情景与偏差','后训练 · 主资源筛选 · 算力增长减半；三层范围定义不同，分别展示',size=(7.2,5.8),margins=(.24,.95,.27,.80))
    ax=fig.add_subplot()
    labels=[]
    for h,k in [(12,0),(24,4)]:
        r=d[(d.type=='non_pretrained')&(d.resource_gate=='primary')&(d.compute_scenario=='half')&(d.model=='quantile_resource')&(d.horizon_months==h)].iloc[0]
        v=u[(u.type=='non_pretrained')&(u.resource_gate=='primary')&(u.compute_scenario=='half')&(u.horizon_months==h)].iloc[0]
        ranges=[(r.conditional_p05,r.conditional_p95,style.BLUE,'固定参数'),(v.scenario_union_lower,v.scenario_union_upper,style.TEAL,'多情景并集'),(v.with_fixed_bias_stress_lower,v.with_fixed_bias_stress_upper,style.ORANGE,'叠加偏差压力')]
        for i,(lo,hi,c,label) in enumerate(ranges):
            ax.hlines(k+i,lo,hi,color=c,lw=5)
            ax.plot([lo,hi],[k+i,k+i],'|',color=c,ms=9)
            ax.text(lo-1,k+i,f'{lo:.1f}',ha='right',va='center',fontsize=8,color=c)
            ax.text(hi+1,k+i,f'{hi:.1f}',ha='left',va='center',fontsize=8,color=c)
            labels.append(f'{h}月 · {label}')
        ax.scatter(r.score,k,color=style.INK,s=32,zorder=4)
    ax.set(yticks=[0,1,2,4,5,6],yticklabels=labels,xlim=(20,105),ylim=(6.7,-.7),xlabel='情景前沿均分（分）');clean(ax,'x')
    finish(fig,'07_uncertainty','12月固定范围 50.30–56.01；情景并集 37.75–72.24；偏差压力 31.59–78.40。\n黑点为分位资源点预测；并集还纳入候选模型与资源参数变化。偏差压力沿用历史最大绝对误差。\n三层均无未来覆盖率保证，不称作 95% 预测区间；偏差的长时距保持是假设。')


def growth_scenarios():
    d=csv('frontier_candidate_forecasts.csv')
    s=d[(d.type=='non_pretrained')&(d.resource_gate=='primary')&(d.model=='quantile_resource')]
    fig=base('08  算力增长设定改变未来前沿点预测','后训练 · 分位资源候选；固定 η=0.5、漂移保留 0.5，只比较四种增长情景')
    ax=fig.add_subplot()
    scenarios=['stopped','quarter','half','historical']
    for h,color,marker,ls in [(12,style.BLUE,'o','-'),(24,style.TEAL,'s','--')]:
        g=s[s.horizon_months==h].set_index('compute_scenario').loc[scenarios]
        ax.plot(range(4),g.score,color=color,marker=marker,ls=ls,lw=1.5,ms=6,label=f'{h} 个月')
        for i,v in enumerate(g.score):ax.annotate(f'{v:.1f}',(i,v),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8,color=color)
    ax.set(xticks=range(4),xticklabels=['停止增长','历史速率 × ¼','历史速率 × ½','历史速率 × 1'],ylim=(0,100),ylabel='前沿 q90 点预测（分）',xlabel='算力对数年增长速率的情景倍率');clean(ax)
    ax.legend(frameon=False,loc='upper left',fontsize=8)
    finish(fig,'08_growth_scenarios','历史主筛选对数年增长速率为 0.6903；“减半”作用于对数速率，不是算力直接减半。\n横轴为有序增长假设，连线仅作情景比较；不是实测未来轨迹或独立验证的因果算力收益。')


def bridge():
    d=csv('prepared/bridge_sample.csv');v=csv('bridge_source_coordinate_validation.csv')
    fig=base('09  Loss—能力桥必须在各自来源坐标中验证','C6 原始 Loss_Source 分组；散点为已观测模型，右下为逐点留出 RMSE',size=(7.2,6.9),margins=(.12,.95,.22,.80))
    axes=fig.subplots(2,2,gridspec_kw={'hspace':.50,'wspace':.38})
    for ax,coord,name,color in zip(axes.flat[:3],COORDS,['Pythia · validation','Qwen2 · validation','Qwen2.5 · validation'],[style.GREY,style.BLUE,style.TEAL]):
        s=d[d.Loss_Source==coord]
        ax.scatter(s.Val_Loss,s.S,color=color,s=35,alpha=.85)
        ax.set(xlabel='该来源的验证 Loss',ylabel='六任务均分（分）',title=f'{name} · n={len(s)}',ylim=(0,60));clean(ax)
    ax=axes.flat[3]
    for i,coord in enumerate(COORDS):
        r=v[v.coordinate_id==coord].iloc[0]
        ax.plot([r.monotone_LOO_RMSE,r.constant_LOO_RMSE],[i,i],color=style.LIGHT,lw=4,zorder=1)
        ax.scatter(r.monotone_LOO_RMSE,i,color=style.BLUE,marker='o',s=35,zorder=3,label='单调桥' if i==0 else None)
        ax.scatter(r.constant_LOO_RMSE,i,color=style.ORANGE,marker='s',s=35,zorder=3,label='常数' if i==0 else None)
    ax.set(yticks=range(3),yticklabels=['Pythia','Qwen2','Qwen2.5'],xlim=(0,17),ylim=(2.6,-.6),xlabel='留出 RMSE（分）',title='同源桥与常数基线');clean(ax,'x');ax.legend(frameon=False,fontsize=7,loc='upper right')
    finish(fig,'09_bridge_validation','Qwen2 / Qwen2.5 留出 RMSE 7.048 / 2.655，优于各自常数；Pythia 0.538 劣于常数 0.426。\n样本小、Loss 来源标签未独立核验；不混合 training / validation / unspecified 坐标。\nQ3 Loss → C6 来源坐标的转换尚未经验标定，图中关系不能直接兑换为确定的未来能力。')


def bridge_stress():
    d=csv('q3_bridge_conclusion_sensitivity.csv')
    s=d[(d.context_tokens==8192)&(d.budget_FLOPs==1e22)&(d.quality_family=='power')&(d.policy_mode=='fixed_recipe')&d.diagnostic_primary_candidate]
    fig=base('10  Q3 配方的能力兑换对跨源坐标假设敏感','固定配方 172、8192 Token、预算 10^22 FLOPs；只显示两个候选来源中有支持的情景',size=(7.2,5.5),margins=(.16,.95,.30,.78))
    axes=fig.subplots(1,2,gridspec_kw={'wspace':.40})
    for i,(coord,name,c) in enumerate(zip(COORDS[1:],['Qwen2','Qwen2.5'],[style.BLUE,style.TEAL])):
        r=s[s.coordinate_id==coord].iloc[0]
        axes[0].hlines(i,r.score_min,r.score_max,color=c,lw=4)
        axes[0].scatter(r.nominal_score,i,color=c,marker='D',s=45,zorder=3)
        axes[0].text((r.score_min+r.score_max)/2,i-.16,f'{r.score_min:.2f}–{r.score_max:.2f}',ha='center',fontsize=8,color=c)
        axes[0].text(r.nominal_score,i+.22,f'名义 {r.nominal_score:.2f}',ha='center',fontsize=8,color=c)
        axes[1].hlines(i,r.gain_min,r.gain_max,color=c,lw=4)
        axes[1].plot([r.gain_min,r.gain_max],[i,i],'|',color=c,ms=10)
        axes[1].text((r.gain_min+r.gain_max)/2,i-.14,f'{r.gain_min:.2f}–{r.gain_max:.2f}',ha='center',fontsize=8,color=c)
        axes[1].text((r.gain_min+r.gain_max)/2,i+.22,f'{r.supported_gain_scenarios}/27 增益格有支持',ha='center',fontsize=7,color=style.GREY)
    for ax in axes:
        ax.set(yticks=[0,1],yticklabels=['Qwen2','Qwen2.5'],ylim=(1.6,-.7));clean(ax,'x')
    axes[0].set(xlim=(0,45),xlabel='假设兑换的六任务均分（分）',title='支持情景范围与名义点')
    axes[0].set_yticklabels(['Qwen2\n22/27 有支持','Qwen2.5\n23/27 有支持'],fontsize=7)
    axes[1].set(xlim=(0,7),xlabel='相对同 N / D 骨架的条件增益（分）',title='支持情景中的增益范围')
    finish(fig,'10_bridge_stress','27 格假设：尺度 a∈{0.9,1,1.1}，偏移 b∈{−0.1,0,0.1}，上游 Loss 扰动∈{−0.05,0,0.05}。\n菱形为 a=1、b=0、扰动=0 名义点；线段是支持格的最小–最大范围，不是置信区间。\n此图选固定配方 172；同预算联立推荐也为 172、对应分数相同，三模式完整对比见图12。\n未支持格排除，不补零；此压力影响 Q3 兑换幅度，未直接作用于 C2 / C4 前沿预测。')


def maximum_boundary():
    d=csv('frontier_maximum_scenarios.csv');b=csv('frontier_maximum_backtest.csv');comp=csv('frontier_maximum_model_comparison.csv')
    fig=base('11  最高能力边界与 q90 前沿是两个预测对象','算力增速减半：累计纪录不会因较弱提交下降；条件上尾 = max(历史纪录, q90 + 尾差)',size=(7.2,7.8),margins=(.12,.96,.22,.80))
    gs=fig.add_gridspec(2,2,hspace=.55,wspace=.32)
    for i,(typ,name) in enumerate(zip(TYPES,TYPE_NAMES)):
        ax=fig.add_subplot(gs[0,i]);s=d[(d.type==typ)&(d.compute_scenario=='half')].sort_values('horizon_months')
        ax.axhline(s.historical_record_score.iloc[0],color=style.GREY,ls=':',lw=1.2,label='纪录保持')
        ax.plot([12,24],s.q90_score,color=style.ORANGE,marker='^',ls='--',lw=1.2,label='q90 前沿')
        ax.errorbar([12,24],s.conditional_record_center,yerr=[s.conditional_record_center-s.conditional_record_lower,s.conditional_record_upper-s.conditional_record_center],color=style.BLUE,marker='o',lw=1.5,capsize=4,label='条件最高边界')
        for row in s.itertuples():ax.annotate(f'{row.conditional_record_center:.2f}',(row.horizon_months,row.conditional_record_center),xytext=(0,7),textcoords='offset points',fontsize=8,ha='center',color=style.BLUE)
        expected=np.maximum(s.historical_record_score,s.q90_score+s.tail_gap_center)
        if not np.allclose(expected,s.conditional_record_center):raise ValueError('Maximum boundary formula mismatch')
        ax.set(title=name,xticks=[12,24],xlim=(9,27),ylim=(0,85),xlabel='距 2025-03 起点（月）');clean(ax)
        if i==0:ax.set_ylabel('六任务均分（分）')
    ax=fig.add_subplot(gs[1,:])
    for typ,name,color,marker,offset in zip(TYPES,TYPE_NAMES,[style.BLUE,style.TEAL],['o','s'],[-.14,.14]):
        for k,window in enumerate([None,1,2,3]):
            s=b[b.type==typ]
            if window is None:
                s=s[s.tail_window_months==2];err=s.persistence_prediction-s.actual_cumulative_record
                row=comp[(comp.type==typ)&(comp.model=='record_persistence')].iloc[0]
            else:
                s=s[s.tail_window_months==window];err=s.tail_gap_prediction-s.actual_cumulative_record
                row=comp[(comp.type==typ)&(comp.model=='q90_plus_tail_gap')&(comp.tail_window_months==window)].iloc[0]
            if len(s)!=4 or not np.isclose(np.sqrt(np.mean(err**2)),row.rmse):raise ValueError('Maximum backtest mismatch')
            ax.scatter(k+offset+np.linspace(-.045,.045,4),err,color=color,marker=marker,s=25,label=name if k==0 else None,zorder=3)
    ax.axhline(0,color=style.GREY,ls='--',lw=.8);ax.set(xticks=range(4),xticklabels=['纪录保持','上尾 · 1月尾差','上尾 · 2月尾差','上尾 · 3月尾差'],ylabel='累计最高预测误差（分）',title='四个两月窗口的最高边界回测',ylim=(-.6,8.5));clean(ax);ax.legend(frameon=False,fontsize=7,loc='upper right')
    fig.legend(*fig.axes[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.54,.135),ncol=3,frameon=False,fontsize=7.5)
    finish(fig,'11_maximum_boundary','后训练历史纪录 51.231；12 / 24月条件最高边界 60.600 / 73.453，基座保持 38.441。\n上图误差棒为最近 1–3月尾差敏感性，不是统计置信区间。下图每点为一个重叠测试窗口。\n四个窗口均未刷新纪录，纪录保持 RMSE=0；动态上尾未优于它，不能据此保证未来不创新高。\n预测起点与图06一致；提交频率、评测口径、开放筛选或尾差结构变化时，上尾情景可能失效。')


def policy_bridge_comparison():
    d=csv('q3_bridge_conclusion_sensitivity.csv')
    s=d[(d.context_tokens==8192)&(d.quality_family=='power')&d.diagnostic_primary_candidate]
    fig=base('12  三种 Q3 投入方案的名义能力兑换与支持缺口','8192 Token、幂成本；a=1、b=0、扰动=0；每点为假设兑换，不是实测 Benchmark',size=(7.2,5.8),margins=(.12,.96,.29,.80))
    axes=fig.subplots(1,2,sharey=True,gridspec_kw={'wspace':.28})
    modes=['fixed_recipe','observed_joint_recipe','independent_native_Q']
    names=['固定配方','配方联立','独立质量']
    for ax,coord,name in zip(axes,COORDS[1:],['Qwen2 validation','Qwen2.5 validation']):
        for mode,label,c,m,off in zip(modes,names,[style.BLUE,style.TEAL,style.ORANGE],['o','s','^'],[-.15,0,.15]):
            g=s[s.coordinate_id.eq(coord)&s.policy_mode.eq(mode)].sort_values('budget_FLOPs')
            if len(g)!=4:raise ValueError('Missing bridge mode/budget')
            for i,row in enumerate(g.itertuples()):
                if np.isfinite(row.nominal_score):
                    ax.scatter(i+off,row.nominal_score,s=35,color=c,marker=m,label=label if i==1 else None,zorder=3)
                    if mode=='independent_native_Q':ax.annotate(f'{row.nominal_score:.1f}',(i+off,row.nominal_score),xytext=(3,8),textcoords='offset points',fontsize=7,color=c)
                elif row.supported_score_scenarios!=0:raise ValueError('Unexpected nonnominal support state')
        ax.text(0,.23,'固定：不可行\n联立 / 独立：\nN 超出支持',transform=ax.get_xaxis_transform(),ha='center',fontsize=7,color=style.GREY,linespacing=1.8,bbox={'facecolor':'white','edgecolor':style.LIGHT,'pad':4})
        ax.set(xticks=range(4),xticklabels=[r'$10^{19}$',r'$10^{20}$',r'$10^{22}$',r'$10^{24}$'],xlabel='预算（FLOPs）',title=name,ylim=(0,45),xlim=(-.45,3.45));clean(ax)
    axes[0].set_ylabel('假设兑换的六任务均分（分）')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.54,.18),ncol=3,frameon=False,fontsize=8)
    finish(fig,'12_policy_bridge','横向错开便于看见同预算的点；10^20 是诊断预算。支持预算中，固定与联立同为配方172、分数重合。\n10^19 联立配方477的 N=0.0873B、独立质量 N=0.1309B，均低于两条来源 N 下限；缺口不补零。\n两桥留出 RMSE 为 7.048 / 2.655 分，未作 Q3 跨坐标经验标定；名义分差不能当作实测改善。')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill-dir',type=Path,default=Path.home()/'.codex/skills/scipilot-figure-skill')
    p.add_argument('--finalize',action='store_true')
    args=p.parse_args();sys.path.insert(0,str(args.skill_dir/'scripts'))
    from setup_style import setup_style
    from profile_data import profile_data
    from visual_qa import audit_layout
    setup_style(journal='general',lang='zh',use_sciplots=False)
    plt.rcParams.update({'font.family':['Microsoft YaHei'],'font.sans-serif':['Microsoft YaHei'],'font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
        'text.color':style.INK,'axes.labelcolor':style.INK,'xtick.color':style.INK,'ytick.color':style.INK,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,'figure.constrained_layout.use':False})
    style.SOURCE=SOURCE;style.OUT=OUT;style.FINALIZE=args.finalize;style.AUDIT=audit_layout
    OUT.mkdir(parents=True,exist_ok=True)
    frozen=js('manifest.json');verified=[]
    for name,sha in frozen['output_sha256'].items():
        f=SOURCE/name;raw=f.read_bytes()
        if sha not in [hashlib.sha256(raw).hexdigest(),hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()]:raise ValueError(f'Frozen Q4 hash mismatch: {name}')
        verified.append(name)
    profiles={name:profile_data(csv(name)) for name in ['prepared/leaderboard_sample.csv','historical_standardized_contributions.csv','rolling_two_month_frontier.csv','frontier_candidate_forecasts.csv','prepared/bridge_sample.csv','q3_bridge_conclusion_sensitivity.csv','frontier_maximum_scenarios.csv','frontier_maximum_backtest.csv']}
    (OUT/'scipilot_profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    history();contributions();sensitivity();resources();backtests();forecasts();uncertainty();growth_scenarios();bridge();bridge_stress();maximum_boundary();policy_bridge_comparison()
    for f in style.INPUTS:
        key=str(f.relative_to(ROOT)).replace('\\','/')
        sha=frozen['input_sha256'].get(key)
        if sha:
            raw=f.read_bytes()
            if sha not in [hashlib.sha256(raw).hexdigest(),hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()]:raise ValueError(f'Frozen Q4 prepared input mismatch: {key}')
    cards=[]
    for f in style.FIGURES:
        s=f['stem'];cards.append(f'<section><img src="{s}.png" alt="{s}"><p>{html.escape(f["caption"]).replace(chr(10),"<br>")}</p><a href="{s}.pdf">PDF</a> · <a href="{s}.svg">SVG</a></section>')
    (OUT/'gallery.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Q4 结果图册</title><style>body{margin:0;background:#edf2f6;color:#243746;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1020px;margin:30px auto;padding:0 20px}section{background:white;margin:24px 0;padding:22px;border-radius:12px}img{width:100%}p{font-size:14px;color:#536674}a{color:#0072B2}</style><main><h1>Q4 结果图册</h1><p>main @ 4098b8c 的冻结 Q4 v3 结果，含累计最高边界及三模式桥接。历史分解是条件关联；未来预测起点为 2025 年 3 月。与 Q1–Q3 同一分支、版式和配色。</p>'+''.join(cards)+'</main></html>',encoding='utf-8')
    style.INPUTS.add(SOURCE/'ANSWER.md')
    manifest={'source_main':MAIN,'frozen_source':frozen['source_commit'],'upstream_Q3_commit':frozen['upstream_Q3_commit'],'producer':'frozen Q4 v3; no refit or forecast update','verified_frozen_outputs':verified,
        'inputs':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(style.INPUTS)},
        'scripts':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),ROOT/'src/visualization/q2_redesign.py']},
        'figures':style.FIGURES,'layout_audit':style.AUDITS,'visual_review':'reviewed previews before vector export' if args.finalize else 'pending',
        'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'figures':len(style.FIGURES),'verified_frozen_outputs':len(verified),'layout':style.AUDITS},ensure_ascii=False))


if __name__=='__main__':main()
