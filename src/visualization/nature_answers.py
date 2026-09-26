"""Independent, claim-led Q1-Q4 figures using the nature-figure Python track.

Only frozen model results and declared analytic evaluations are consumed.
No earlier figure, styling helper or image is an input.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import MaxNLocator
from PIL import Image

plt.rcParams['font.family']=['Arial','Microsoft YaHei']
plt.rcParams['font.sans-serif']=['Arial','Microsoft YaHei','DejaVu Sans']
plt.rcParams['svg.fonttype']='none'
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.size':8.5,'axes.labelsize':8.5,
    'axes.titlesize':9,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,
    'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,'legend.frameon':False,
    'axes.unicode_minus':False,'figure.constrained_layout.use':False})
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/nature'
MAIN='f3a49d4e006a70db18d8ed667ebe33a4a7ff6d9f'
BLUE,PLUM,GREY,INK,PALE,RED='#0F4D92','#9A4D8E','#767676','#272727','#D8D8D8','#B64342'
SEQ=LinearSegmentedColormap.from_list('nature_blue',['#FAFBFD','#BCCBE2',BLUE])
DIV=LinearSegmentedColormap.from_list('nature_effect',[BLUE,'#FAFAFA',PLUM])
READS=set();FIGURES=[];QA={};CURRENT=set()
DOM_NAMES={'arxiv':'arXiv','freelaw':'FreeLaw','nih_exporter':'NIH','pubmed_central':'PMC',
    'wikipedia_en':'Wikipedia','dm_mathematics':'Mathematics','github':'GitHub','philpapers':'PhilPapers',
    'stackexchange':'StackExchange','enron_emails':'Enron','gutenberg_pg_19':'Gutenberg','pile_cc':'Pile-CC',
    'ubuntu_irc':'Ubuntu IRC','europarl':'EuroParl','hackernews':'HackerNews','pubmed_abstracts':'PubMed Abs.',
    'uspto_backgrounds':'USPTO','book':'Book','commoncrawl':'CommonCrawl','c4':'C4','wikipedia':'Wikipedia'}
CONTEXTS=[2048,8192,131072]
BUDGETS=[1e19,1e22,1e24]
FAMILIES=['exponential','power','logarithmic']
FAMILY_NAMES=['指数成本','幂成本','对数成本']
COORDS=['Pythia training log (Attachment B, final checkpoint D=299.9B tokens)',
    'Qwen2 Technical Report (Alibaba, 2024), validation loss',
    'Qwen2.5 Technical Report (Alibaba, 2024), validation loss']


def read(q,name):
    p=ROOT/f'outputs/Q{q}'/name;READS.add(p);CURRENT.add(p)
    return pd.read_csv(p) if p.suffix=='.csv' else json.loads(p.read_text(encoding='utf-8-sig'))


def extra(name):
    p=ROOT/name;READS.add(p);CURRENT.add(p)
    return json.loads(p.read_text(encoding='utf-8-sig'))


def start(q,number,title,height=4.6,rows=1,cols=2,ratios=None):
    CURRENT.clear()
    fig=plt.figure(figsize=(183/25.4,height))
    fig.subplots_adjust(left=.17,right=.96,bottom=.22,top=.82,wspace=.52,hspace=.66)
    fig.text(.035,.965,f'Q{q}  |  {title}',fontsize=11,weight='bold',va='top',color=INK)
    gs=fig.add_gridspec(rows,cols,width_ratios=ratios)
    axes=np.array([fig.add_subplot(gs[i,j]) for i in range(rows) for j in range(cols)]).reshape(rows,cols)
    return fig,axes,f'Q{q}_{number:02d}'


def panel(ax,label,title):
    ax.set_title(title,loc='left',pad=15,fontweight='normal')
    ax.annotate(label,xy=(0,1),xycoords='axes fraction',xytext=(-25,14),textcoords='offset points',fontsize=9,weight='bold',ha='left',va='bottom')
    ax.tick_params(length=3,width=.6,pad=3,color=GREY)
    ax.spines[['bottom','left']].set_color(GREY)
    ax.set_axisbelow(True)


def zero(ax,vertical=False):
    (ax.axvline if vertical else ax.axhline)(0,color=PALE,ls='--',lw=.7,zorder=0)


def budget_axis(ax):
    ax.set_xscale('log');ax.set_xticks([1e19,1e20,1e22,1e24],[r'$10^{19}$',r'$10^{20}$',r'$10^{22}$',r'$10^{24}$'])
    ax.set_xlabel('预算（FLOPs）');ax.set_xlim(8e18,1.4e24)


def heat(ax,z,xlabels,ylabels,cmap=SEQ,vmin=None,vmax=None):
    z=np.asarray(z,dtype=float)
    im=ax.pcolormesh(np.arange(z.shape[1]+1)-.5,np.arange(z.shape[0]+1)-.5,np.ma.masked_invalid(z),cmap=cmap,vmin=vmin,vmax=vmax,edgecolors='white',linewidth=.5)
    ax.set(xlim=(-.5,z.shape[1]-.5),ylim=(z.shape[0]-.5,-.5),xticks=range(z.shape[1]),yticks=range(z.shape[0]),xticklabels=xlabels,yticklabels=ylabels)
    ax.tick_params(length=0);ax.spines[['left','bottom']].set_visible(False)
    return im


def colorbar(fig,im,label,ax):
    pos=ax.get_position()
    ca=fig.add_axes([pos.x0,pos.y0-.115,pos.width,.012])
    cb=fig.colorbar(im,cax=ca,orientation='horizontal')
    cb.set_label(label,fontsize=8);cb.ax.tick_params(labelsize=7.5)
    cb.solids.set_rasterized(False)
    return cb.ax


def finish(fig,stem,claim,legend,roles,excluded=()):
    from audit_panel_alignment import require_matplotlib_panel_alignment
    from audit_figure_collisions import audit_pdf,exit_code
    from audit_pdf_text import audit_pdf as text_audit
    fig.canvas.draw()
    a=require_matplotlib_panel_alignment(fig,json_out=OUT/'qa'/f'{stem}.alignment.json',exclude_axes=excluded,
        tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=True,strict=True)
    fig.savefig(OUT/f'{stem}.png',dpi=300,facecolor='white')
    fig.savefig(OUT/f'{stem}.pdf',facecolor='white')
    fig.savefig(OUT/f'{stem}.svg',facecolor='white')
    svg=OUT/f'{stem}.svg';svg.write_text('\n'.join(x.rstrip() for x in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    with Image.open(OUT/f'{stem}.png') as im:im.convert('L').save(OUT/f'{stem}_gray.png',dpi=(300,300))
    c=audit_pdf(OUT/f'{stem}.pdf');t=text_audit((OUT/f'{stem}.pdf').read_bytes(),minimum_pt=5)
    (OUT/'qa'/f'{stem}.collision.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'qa'/f'{stem}.text.json').write_text(json.dumps(t,ensure_ascii=False,indent=2),encoding='utf-8')
    QA[stem]={'alignment_verdict':a.get('verdict'),'collision_exit':exit_code(c),'collision_summary':c.get('summary'),
        'minimum_font_pt':t['minimum_found_pt'],'small_glyphs':t['below_minimum_count']}
    FIGURES.append({'stem':stem,'claim':claim,'legend':legend,'panel_roles':roles,'archetype':'quantitative grid',
        'sources':[str(p.relative_to(ROOT)).replace('\\','/') for p in sorted(CURRENT)],
        'size_inches':list(fig.get_size_inches()),'dpi':300,'visual_review':'pending'})
    plt.close(fig)
    print(stem,json.dumps(QA[stem],ensure_ascii=False),flush=True)


def q1_quality():
    fig,aa,s=start(1,1,'工程质量评分保留领域差异',height=5.1)
    d=read(1,'domain_quality.csv');a=d[d.dataset_scope=='sample'].sort_values('Q');b=d[d.dataset_scope!='sample']
    ax=aa[0,0];panel(ax,'a','A1 七域评分及固定规则区间')
    y=np.arange(len(a));ax.errorbar(a.Q,y,xerr=[a.Q-a.uncertainty_low,a.uncertainty_high-a.Q],fmt='o',color=BLUE,ms=4,capsize=2,lw=1)
    ax.set(yticks=y,yticklabels=[DOM_NAMES.get(x,x) for x in a.quality_domain],xlabel='领域质量中位数 Q_A',xlim=(-1,3.5));zero(ax,True)
    ax=aa[0,1];panel(ax,'b','评分聚合改变数值尺度')
    for i,(col,label,c,m) in enumerate([('Q','家族平衡中位数',BLUE,'o'),('Q_equal22_median','22指标等权中位数',PLUM,'s'),('Q_z_trimmed_mean','家族平衡截尾均值',GREY,'D')]):
        ax.scatter(a[col],y+i*.12-.12,color=c,marker=m,s=21,label=label)
    ax.set(yticks=y,yticklabels=[],xlabel='对应评分（规则各自尺度）',xlim=(-1,3.5));zero(ax,True)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.55,.04),ncol=1,fontsize=7.5)
    finish(fig,s,'评分在固定规则内可复现，但聚合规则和尺度不能当成人工真值。',
        'a，A1 51,230条记录的七域中位数；横线为发布表中固定评分规则的抽样区间，未覆盖方法选择不确定性。b，同一七域的三种汇总口径，只用于规则比较，不能解释为同一标尺的独立测量。A2/A3使用冻结规则，扩展全集中位数2.7253/−0.5055，去重值2.7279/−0.5063。',
        ['领域差异与固定规则范围','聚合规则敏感性'])


def q1_conflict():
    fig,aa,s=start(1,2,'冲突证据对应复核，不直接扣质量分',height=4.8)
    j=read(1,'conflict_validation.json');p=ROOT/'outputs/Q1/ANSWER.md';CURRENT.add(p);READS.add(p)
    text=p.read_text(encoding='utf-8-sig')
    numbers=re.search(r'分别为 ([\d,]+)、([\d,]+)、([\d,]+)、([\d,]+) 条',text)
    counts=[int(x.replace(',','')) for x in numbers.groups()];assert sum(counts)==51230
    ax=aa[0,0];panel(ax,'a','231 个指标对中的复制性冲突')
    ax.barh([0,1,2],[231,66,j['edge_count']],color=[PALE,GREY,BLUE],height=.5)
    ax.set(yticks=[0,1,2],yticklabels=['全部指标对','A1 显著负相关','扩展集复现'],xlabel='指标对数',xlim=(0,255),ylim=(2.6,-.6));ax.set_xticks([0,55,66,150,231])
    ax=aa[0,1];panel(ax,'b','51,230 条文本的工程处置')
    ax.barh(range(4),counts,color=[BLUE,PLUM,GREY,PALE],height=.5)
    ax.set(yticks=range(4),yticklabels=['保留','保留并复核','低优先级','低优先级并复核'],xlabel='记录数',xlim=(0,23000),ylim=(3.6,-.6));ax.xaxis.set_major_locator(MaxNLocator(3))
    finish(fig,s,'复制性指标分歧支持二维评分和人工复核，而不支持自动判定文本错误。',
        'a，22指标共231对；分范围BH-FDR=0.05，A1 66对显著负相关，55对在去重扩展集复现。b，Q_A阈值0.0273、分歧D第75百分位阈值2.0423下的处置计数；高分歧不扣Q_A。27个案例不是人工质量标签，没有准确率检验；分布四象限的D中位数不得替代复核阈值。',
        ['冲突复制证据','工程处置覆盖'])


def q1_validation():
    fig,aa,s=start(1,3,'交互代理的误差优势随验证范围展示',height=6.5,rows=2,cols=2)
    o=read(1,'targetwise_oof.csv');v=read(1,'targetwise_validation.csv');targets=o.target.unique()
    for ax,scope,label,k in zip(aa.flat,['nested','test_1m','test_60m','test_1B'],['嵌套五折 · 512 配方','A6–A7 · 1M','A8–A9 · 60M','A10–A11 · 1B'],range(4)):
        panel(ax,chr(97+k),label)
        if scope=='nested':
            x=o[o.model=='ridge'].set_index('target').loc[targets].oof_rmse;y=o[o.model=='interaction'].set_index('target').loc[targets].oof_rmse
        else:
            g=v[(v.scope==scope)&(v.support_group=='all')].set_index('target').loc[targets];x=g.ridge_rmse;y=g.interaction_rmse
        ax.scatter(x,y,color=BLUE,s=23);limit=max(x.max(),y.max())*1.08;ax.plot([0,limit],[0,limit],color=PALE,lw=.8,zorder=0)
        ax.set(xlim=(0,limit),ylim=(0,limit),xlabel='Ridge RMSE',ylabel='交互 RMSE')
        ax.set_xticks(np.linspace(0,limit,3).round(1));ax.set_yticks(np.linspace(0,limit,3).round(1))
    finish(fig,s,'逐目标配对比较支持交互代理优于线性基线，但已观察检验不能称为盲测。',
        'a–d，每点为一个目标域，n=13；对角线表示两模型RMSE相同。嵌套五折13/13更低；1M、60M、1B分别11/13、13/13更低。A6/A8共享256配方；检验组曾用于形式判断。1B 47/64配方超出A4凸包。这里只核对冻结结果，不把相关性、误差或同配方计数当作独立训练重复。',
        ['训练内嵌套配对误差','1M已观察检验','60M已观察检验','1B支持转移检验'])


def q1_decisions():
    fig,aa,s=start(1,4,'目标与质量政策共同决定配方',height=6.1,rows=1,cols=3)
    fig.subplots_adjust(left=.14,wspace=.55)
    recipes=read(1,'recipes_512.csv').set_index('index');h=read(1,'hull_bounds.json');r=read(1,'refit_replicate_choices.csv')
    policies=['unconstrained','quality_direct','quality_direct_and_near','minimax'];indices=[136,301,172,477]
    names=['等权','Direct','Direct+Near','Minimax'];domains=recipes.columns.tolist()
    z=recipes.loc[indices,domains].to_numpy().T*100
    ax=aa[0,0];panel(ax,'a','已观测配方的17域构成')
    im=heat(ax,z,[str(x) for x in indices],[DOM_NAMES[x] for x in domains],vmin=0,vmax=z.max());cb=colorbar(fig,im,'配比（%）',ax)
    ax=aa[0,1];panel(ax,'b','连续凸包的数值界')
    for i,row in enumerate(h):
        ax.hlines(i,row['lower_bound_relative']*100,row['feasible_upper_bound_relative']*100,color=BLUE,lw=4)
    ax.set(yticks=range(4),yticklabels=names,ylim=(3.6,-.6),xlabel='目标相对变化（%）',xlim=(-13,0));zero(ax,True)
    ax=aa[0,2];panel(ax,'c','离散候选重拟合稳定性')
    # Minimax is named worst_target in the frozen resampling table.
    actual=list(r.policy.unique())
    for i,idx in enumerate(indices):
        g=r[r.frozen_selected_index==idx];same=int(g.same_as_frozen.sum());assert len(g)==30
        ax.barh(i,same,color=BLUE,height=.45);ax.barh(i,30-same,left=same,color=PALE,height=.45)
    ax.set(yticks=range(4),yticklabels=names,ylim=(3.6,-.6),xlabel='30 次中原配方重选次数',xticks=[0,10,20,30],xlim=(0,30))
    finish(fig,s,'不同政策给出不同条件配方，数值精度和训练扰动稳定性必须分别报告。',
        'a，512个观测候选中的136/301/172/477，仅是有限集最优，非连续凸包解编号。配比列全部17域，无隐藏列。b，四种目标的浮点下界与可行上界，间隙均<0.001，不是统计区间或严格数学证书；Minimax与等权目标含义不同。c，30次无放回80%行重拟合，原候选重选29/10/13/7次；灰段为其他候选，无置信区间解释。',
        ['完整构成','条件优化数值界','训练扰动稳定性'],excluded=[cb])


def q1_stress():
    fig,aa,s=start(1,5,'领域响应与估算压力限定配方解释',height=6.0)
    recipes=read(1,'recipes_512.csv').set_index('index');model=read(1,'interaction_coefficients_13_targets.json')['targets'];e=read(1,'estimated_targetwise.csv')
    indices=[136,301,172,477];targets=list(model);loss=np.zeros((len(targets),4));ref=[]
    for i,k in enumerate(targets):
        coef=model[k];ref.append(coef['fitted_reference_loss'])
        for j,idx in enumerate(indices):
            p=recipes.loc[idx];p=p/p.sum()
            value=coef['intercept']+sum(v*p[d] for d,v in coef['main'].items())
            value+=sum(pair['gamma']*p[pair['domains'][0]]*p[pair['domains'][1]] for pair in coef['pairs'])
            loss[i,j]=value
    effects=(loss/np.array(ref)[:,None]-1)*100
    pd.DataFrame(loss,index=targets,columns=indices).to_csv(OUT/'source_data/Q1_recipe_target_loss.csv')
    ax=aa[0,0];panel(ax,'a','13目标的相对配方响应')
    lim=np.max(np.abs(effects));im=heat(ax,effects,[str(x) for x in indices],[DOM_NAMES[x] for x in targets],DIV,-lim,lim);cb=colorbar(fig,im,'相对参考预测 Loss（%）',ax)
    ax=aa[0,1];panel(ax,'b','估算外推的逐目标排序')
    for i,(scope,label) in enumerate([('est_10B','10B estimated'),('est_70B','70B estimated')]):
        g=e[e.scope==scope]
        ax.scatter(g.ridge_spearman,g.v2_spearman,color=[BLUE,PLUM][i],marker=['o','s'][i],s=23,label=label)
    ax.plot([-1,1],[-1,1],color=PALE,lw=.8);ax.set(xlim=(-1,1),ylim=(-1,1),xlabel='Ridge 排序 Spearman',ylabel='交互排序 Spearman');zero(ax);zero(ax,True)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.7,.08),fontsize=7.5)
    stress=read(1,'estimated_decision_stress.csv')
    finish(fig,s,'目标域响应不同，估算大模型表不能支持配方排序无条件外推。',
        'a，从冻结13目标模型复算四个已观测候选相对参考响应，非观测干预；域间绝对Loss不同，使用各自参考归一化。诊断发现Mathematics在136处预测Loss为负，表明代理的绝对物理解释有局限，未裁零或修复。b，两组各13目标、63配方的estimated排序；交互中位相关0.4915/0.3941，低于Ridge 0.5136/0.4148。两模型选16，在估算表均排61/63；这些不是10B/70B真实训练验证。',
        ['逐目标配方异质性及模型失真诊断','负向估算压力'],excluded=[cb])


def backbone(n,d):
    c=COEFF['B1_backbone'];return c['E']+c['A']*n**(-c['alpha'])+c['B']*d**(-c['beta'])


def gain(n,d):
    c=COEFF['B7_quality_extension'];return c['G0']+c['GN']*np.log(n)+c['GD']*np.log(d/100)


def q2_scaling():
    fig,aa,s=start(2,1,'规模与数据骨架之上加入条件质量项',height=4.7)
    read(2,'model_coefficients.json')
    n=np.geomspace(.070542,11.965825,45);d=np.geomspace(10,299.893,40);nn,dd=np.meshgrid(n,d)
    z=backbone(nn,dd);g=gain(nn,dd)
    bars=[]
    for ax,label,title,values in zip(aa.flat,['a','b'],['B1 标度骨架','B7 条件质量灵敏度'],[z,g]):
        panel(ax,label,title);im=ax.pcolormesh(nn,dd,values,cmap=SEQ,shading='auto')
        ax.set(xscale='log',yscale='log',xlabel='N（十亿参数）',ylabel='D（十亿 tokens）')
        ax.set_xticks([.1,1,10],['0.1','1','10']);ax.set_yticks([10,100,299.893],['10','100','299.9'])
        bars.append(colorbar(fig,im,'预测 Loss' if label=='a' else 'G = −∂Loss/∂Q_B',ax))
    finish(fig,s,'冻结解析骨架与半合成质量扩展可在共同支持域内计算条件响应。',
        'a，L0=E+AN^(−α)+BD^(−β)，B1 1176条同源Pythia记录，N/D以十亿计。b，LB=L0+(1−QB)G，G为450条半合成B7在固定B1骨架上的三参数扩展。每格为解析计算，不是重复实验或新的拟合。绘制范围为正式共同N/D支持矩形，不外推。',
        ['解析骨架的资源响应','质量扩展的空间异质性'],excluded=bars)


def q2_validation():
    fig,aa,s=start(2,2,'验证误差必须保留数据生成与划分含义',height=5.0)
    j=read(2,'b7_quality_extension.json');f=pd.DataFrame(j['outer_folds']);c=read(2,'b7_backbone_comparison.csv')
    ax=aa[0,0];panel(ax,'a','B7 24 个嵌套留等级折')
    for i,axis in enumerate(['N_params_B','D_tokens_B','Q_score']):
        values=f[f.axis==axis].outer_rmse.to_numpy()
        ax.scatter(i+np.linspace(-.15,.15,len(values)),values,color=BLUE,s=20,marker=['o','s','D'][i]);ax.hlines(np.mean(values),i-.23,i+.23,color=PLUM,lw=1.3)
    ax.set(xticks=range(3),xticklabels=['留 N 等级','留 D 等级','留 Q 等级'],ylabel='外层 RMSE',ylim=(0,.08))
    ax=aa[0,1];panel(ax,'b','固定骨架与共同拟合的检验')
    for i,row in enumerate(c.itertuples()):
        cols=[f'{x}_held_level_RMSE' if i==1 else f'{x}_nested_RMSE' for x in ['N','D','Q']]
        vals=[getattr(row,k) for k in cols]
        ax.plot(range(3),vals,color=[BLUE,GREY,PLUM][i],marker=['o','s','D'][i],lw=1,label=['固定B1：嵌套','八参数：固定形式','家族选择：嵌套'][i])
    ax.set(xticks=range(3),xticklabels=['N','D','Q'],ylabel='留等级 RMSE',xlabel='留出变量');ax.set_ylim(bottom=0)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.56,.04),ncol=3,fontsize=7)
    finish(fig,s,'半合成同源的划分检验支持条件形式，不能替代跨附件真实质量干预。',
        'a，每个点为一折，横线为相应轴折均值，平均RMSE 0.048738/0.048751/0.048639；折共享数据，不视为独立重复。b，冻结对照表的外层留等级误差；缺失项表示上游未给出对应外层结果，不补零。B1留一规模组约1.46e−4仅支持同源重构；B6/B7重叠。',
        ['24折离散误差','不同结构基线'])


def q2_tradeoff():
    fig,aa,s=start(2,3,'质量提升可兑换规模，但取决于条件模型',height=4.8)
    t=read(2,'quality_scale_local_tradeoff.csv');m=read(2,'marginals_elasticities.csv')
    ax=aa[0,0];panel(ax,'a','质量 +0.10 的等 Loss 规模')
    ax.plot(t.N_params_B,t.equivalent_oldQ_N_delta_0_1/t.N_params_B,color=BLUE,marker='o',lw=1.2,label='旧质量需扩模')
    ax.plot(t.N_params_B,t.constant_L_newQ_N_delta_0_1/t.N_params_B,color=PLUM,marker='s',lw=1.2,label='新质量可缩模')
    ax.axhline(1,color=PALE,ls='--',lw=.7);ax.set(xscale='log',xlabel='初始规模 N（B）',ylabel='等 Loss 规模 / 初始规模',ylim=(0,1.7));ax.set_xticks([.1,1,10],['0.1','1','10'])
    ax=aa[0,1];panel(ax,'b','局部弹性随规模变化')
    for col,label,c,marker in [('N_elasticity','N',BLUE,'o'),('D_elasticity','D',GREY,'s'),('quality_proxy_elasticity','质量 q',PLUM,'D')]:
        ax.plot(m.N_params_B,-m[col],color=c,marker=marker,lw=1,ms=4,label=label)
    ax.set(xscale='log',xlabel='N（B）',ylabel='Loss 下降弹性',ylim=(0,.15));ax.set_xticks([.1,1,10],['0.1','1','10'])
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower left',bbox_to_anchor=(.13,.03),fontsize=7)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower right',bbox_to_anchor=(.95,.03),ncol=3,fontsize=7)
    finish(fig,s,'固定配方的条件计算支持质量—规模替代，不证明质量可独立操控。',
        'a，D=100B，固定示例配方，对原始三档N逐行计算；N=1B时提高质量0.10，旧质量等效需1.317062B。b，冻结局部弹性示例，均无统计区间。q(p)由配方决定；额外处理可控QB是另一工程机制，不把两机制混同。',
        ['等Loss有限变化替代','局部敏感度'])


def q2_domains():
    fig,aa,s=start(2,4,'可行域转移与固定补偿的组合效应',height=6.3)
    d=read(2,'domain_pair_substitution.csv');e=extra('audits/review_followup_20260926/computed_evidence.json')
    domains=list(dict.fromkeys(d.domain_i.tolist()+d.domain_j.tolist()));z=np.zeros((17,17))
    for row in d.itertuples():
        i,j=domains.index(row.domain_i),domains.index(row.domain_j);z[i,j]=row.dLoss_depsilon;z[j,i]=-row.dLoss_depsilon
    ax=aa[0,0];panel(ax,'a','17域两两可行转移的梯度')
    lim=np.max(np.abs(z));im=heat(ax,z,[DOM_NAMES[x] for x in domains],[DOM_NAMES[x] for x in domains],DIV,-lim,lim)
    ax.tick_params(axis='x',labelrotation=90,labelsize=6);ax.tick_params(axis='y',labelsize=6);cb=colorbar(fig,im,'行域增加、列域减少：∂Loss/∂ε',ax)
    ax=aa[0,1];panel(ax,'b','固定 Pile-CC 补偿后的联合效应')
    f=pd.DataFrame(e['q2_joint_contrasts']);pairs=[('gutenberg_pg_19','europarl'),('arxiv','freelaw')]
    for k,(a,b) in enumerate(pairs):
        g=f[(f.left==a)&(f.right==b)&np.isclose(f.step,.005)&np.isclose(f.quality_scale,1)].sort_values('mixture_lambda')
        ax.plot(g.mixture_lambda,g.joint_minus_separate_loss*1e5,color=[BLUE,PLUM][k],marker=['o','s'][k],lw=1.2,label=['Gutenberg + EuroParl','arXiv + FreeLaw'][k])
    zero(ax);ax.set(xlabel='配比桥强度 λ',ylabel='联合 − 单独之和（1e−5 Loss）',xticks=[0,.5,1,2])
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.72,.04),fontsize=7)
    finish(fig,s,'领域作用依赖补偿方向与桥强度，不能从环境交叉偏导直接判因果互补。',
        'a，A4平均配比处全部136对可行局部转移；转移矩阵反对称，对角为不转移。方向限凸包可行步长，未独立标定质量桥。b，固定Pile-CC补偿、各域+0.005后的联合对比；负值是该操作下互补，正值是替代。λ=1为−1.844e−5/+1.172e−5；arXiv/FreeLaw在λ=0翻号。确定性假设诊断，无置信区间。',
        ['组成约束下的可行梯度','组合操作的桥强度敏感性'],excluded=[cb])


def q2_evidence():
    fig,aa,s=start(2,5,'跨来源证据限定统一模型的解释',height=5.0)
    d=read(2,'b2_b3_model_validation.csv');v=read(2,'scale_order_validation.csv');b=read(2,'quality_bridge_sensitivity.csv')
    ax=aa[0,0];panel(ax,'a','B2/B3 全部轨迹的形状检验')
    for source,c,m in [('B2',PLUM,'s'),('B3',BLUE,'o')]:
        g=d[d.source==source];ax.scatter(g.B1_support_fraction,g.normalized_RMSE,color=c,marker=m,s=25,label=source)
    ax.set(xlim=(-.05,1.08),xlabel='轨迹落入 B1 支持的比例',ylabel='归一化 RMSE',ylim=(0,max(d.normalized_RMSE)*1.15))
    ax=aa[0,1];panel(ax,'b','未标定质量桥改变示例 Loss')
    ax.plot(b.scale,b.Loss,color=PLUM,marker='s',lw=1.3)
    ax.set(xticks=[.5,1,1.5],xlabel='质量映射斜率倍率',ylabel='条件示例 Loss')
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower left',bbox_to_anchor=(.15,.06),ncol=2)
    finish(fig,s,'轨迹、同族方向与桥压力分别支持有限结论，不能合成为真实跨族绝对精度。',
        'a，15条曲线各一点评估；B2/B3用于轨迹形状及插值一致性，不是独立同Loss坐标外测。B4/B5支持内同族方向12/12与7/7，不能辨别多数单调模型。B10 128条estimated记录全部超过B1规模上界，不作真实验证。b，三种确定性桥假设示例2.385343/2.344348/2.303352；没有A/B成对标定或统计区间。',
        ['轨迹与支持比例','跨附件假设幅度'])


def feasible(d):
    return d[d.status.str.endswith('_feasible')].copy()


def q3_resources():
    fig,aa,s=start(3,1,'预算改变规模、数据量及可行性',height=5.1)
    d=read(3,'observed_joint_grid.csv');d=feasible(d[(d.quality_family=='power')&d.budget_FLOPs.isin(BUDGETS)])
    for k,ctx in enumerate(CONTEXTS):
        g=d[d.context_tokens==ctx].sort_values('budget_FLOPs');c=[BLUE,PLUM,GREY][k];m=['o','s','D'][k]
        aa[0,0].plot(g.N_params_B,g.D_tokens_B,color=c,marker=m,lw=1,label=f'{ctx:,} tokens')
        aa[0,1].plot(g.budget_FLOPs,g.conditional_bridge_loss,color=c,marker=m,lw=1)
    panel(aa[0,0],'a','观测候选联合配置');aa[0,0].set(xscale='log',yscale='log',xlabel='N（十亿参数）',ylabel='D（十亿 tokens）',xlim=(.06,15),ylim=(8,360))
    aa[0,0].set_xticks([.1,1,10],['0.1','1','10']);aa[0,0].set_yticks([10,100,300],['10','100','300'])
    panel(aa[0,1],'b','对应的条件目标');budget_axis(aa[0,1]);aa[0,1].set_ylabel('条件桥 Loss')
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.55,.04),ncol=3)
    finish(fig,s,'低预算受到上下文成本约束，高预算受到支持上界约束。','幂成本、Q0=0.5、87个满足质量约束的观测候选，官方预算10^19/10^22/10^24。线仅连接有序预算配置；131072上下文在低预算不可行，未补零。高预算N/D达到共同支持上界，不能解释为真实最优停止扩张。全部为条件模型优化。',['N–D资源轨迹','目标响应与不可行缺口'])


def q3_costs():
    fig,aa,s=start(3,2,'成本构成解释预算约束',height=4.9)
    d=read(3,'observed_joint_grid.csv');g=feasible(d[(d.quality_family=='power')&(d.context_tokens==8192)&d.budget_FLOPs.isin(BUDGETS)]).sort_values('budget_FLOPs')
    ax=aa[0,0];panel(ax,'a','8192上下文的实际成本占比');left=np.zeros(len(g))
    for col,label,c in [('C_train_FLOPs','训练',BLUE),('C_attention_FLOPs','注意力',GREY),('C_quality_FLOPs','质量处理',PLUM)]:
        share=g[col]/g.C_total_FLOPs*100;ax.barh(range(len(g)),share,left=left,color=c,height=.45,label=label);left+=share
    ax.set(yticks=range(len(g)),yticklabels=[r'$10^{19}$',r'$10^{22}$',r'$10^{24}$'],xlabel='实际支出占比（%）',xlim=(0,100));ax.invert_yaxis()
    ax=aa[0,1];panel(ax,'b','中预算的三种质量成本形式')
    for k,f in enumerate(FAMILIES):
        h=feasible(d[(d.quality_family==f)&(d.budget_FLOPs==1e22)]).sort_values('context_tokens')
        ax.plot(h.context_tokens,h.conditional_bridge_loss,color=[GREY,BLUE,PLUM][k],marker=['D','o','s'][k],label=FAMILY_NAMES[k])
    ax.set(xscale='log',xlabel='上下文长度（tokens）',ylabel='条件桥 Loss');ax.set_xticks(CONTEXTS,['2048','8192','131072'])
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower left',bbox_to_anchor=(.13,.04),ncol=3,fontsize=7)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower right',bbox_to_anchor=(.96,.035),ncol=1,fontsize=7)
    finish(fig,s,'长上下文提高注意力成本，成本形式改变可负担的配置。','a，分母是实际C_total，不是预算；10^24预算利用率约2.76%，不能把未花预算算成成本份额。b，固定10^22预算，各点分别优化其候选配方和N/D。成本函数属于题设工程假设，没有观测重复或误差区间。',['预算支出的机制组成','成本形式敏感性'])


def q3_states():
    fig,aa,s=start(3,3,'配方切换与质量状态阈值分开解释',height=5.1)
    d=read(3,'observed_budget_scan.csv');j=extra('audits/review_followup_round2_20260926/native_q_transitions.json')
    ax=aa[0,0];panel(ax,'a','幂成本的离散配方选择')
    for k,ctx in enumerate(CONTEXTS):
        g=feasible(d[(d.quality_family=='power')&(d.context_tokens==ctx)]).sort_values('budget_FLOPs')
        for idx,c,m in [(477,PLUM,'s'),(172,BLUE,'o')]:
            h=g[g.recipe_index==idx];ax.scatter(h.budget_FLOPs,np.full(len(h),k),color=c,marker=m,s=9,label=f'配方{idx}' if k==0 else None)
    budget_axis(ax);ax.set(yticks=range(3),yticklabels=['2048','8192','131072'],ylim=(-.5,2.5));ax.set_ylabel('上下文长度')
    ax=aa[0,1];panel(ax,'b','独立 Q_B 的数值状态区间')
    t=j['transitions'];bounds=[1e19,t[0]['budget_left_FLOPs'],t[1]['budget_left_FLOPs'],1e24]
    for k,(label,c) in enumerate([('Q0 = 0.5',GREY),('内部解',PLUM),('Qmax = 1',BLUE)]):
        ax.hlines(k,bounds[k],bounds[k+1],color=c,lw=5)
    budget_axis(ax);ax.set(yticks=range(3),yticklabels=['下界','内部','上界'],ylim=(-.5,2.5));ax.set_ylabel('质量状态')
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower left',bbox_to_anchor=(.13,.04),ncol=2)
    finish(fig,s,'配方跳变是有限候选切换，独立质量处理的转折是另一模型机制。','a，161个对数预算点，三上下文，幂成本；空白表示不可行。不连接无序配方编号。b，固定172、8192上下文，native Q_B转折位于[1.22887598,1.22896234]×10^19和[1.08599453,1.08607084]×10^20；横线为数值状态范围，不是置信区间，边界相对宽度7.03e−5。不得称为真实训练相变。',['离散配方与可行性','独立质量的数值状态'])


def q3_assumptions():
    fig,aa,s=start(3,4,'假设改变候选集及最优配方',height=5.7)
    d=read(3,'assumption_official_grid.csv');j=read(3,'assumption_sensitivity.json');sc=list(d.scenario.unique())
    g=d[(d.quality_family=='power')&(d.context_tokens==8192)&d.budget_FLOPs.isin(BUDGETS)]
    z=g.pivot(index='scenario',columns='budget_FLOPs',values='recipe_index').reindex(sc)[BUDGETS]
    ax=aa[0,0];panel(ax,'a','代表配置的候选编号')
    for i,name in enumerate(sc):
        for k,b in enumerate(BUDGETS):
            v=z.loc[name,b]
            if pd.notna(v):ax.text(k,i,str(int(v)),ha='center',va='center',fontsize=8,color=BLUE if v==172 else PLUM)
    ax.set(xticks=range(3),xticklabels=[r'$10^{19}$',r'$10^{22}$',r'$10^{24}$'],yticks=range(len(sc)),yticklabels=sc,ylim=(len(sc)-.5,-.5),xlim=(-.5,2.5),xlabel='预算（FLOPs）');ax.tick_params(axis='y',labelsize=6.5)
    ax=aa[0,1];panel(ax,'b','全部27官方配置的改变数')
    c=pd.DataFrame(j['comparisons']);ax.barh(range(len(c)),c.changed_feasibility_or_recipe_cells,color=PLUM,height=.5)
    ax.set(yticks=range(len(c)),yticklabels=[],ylim=(len(c)-.5,-.5),xlim=(0,27),xlabel='相对基准发生改变的格数',xticks=[0,9,18,27])
    finish(fig,s,'跨附件桥假设直接影响决策，不能只展示单一基准。','九种预先给定工程情景，共243=9×27官方配置；a固定幂成本、8192上下文，仅编号展示类别，空白不可行。b合并可行性与配方改变，分母27，非重复实验。桥斜率、λ及Q0没有真实成对标定；这些范围不是概率或置信区间。',['假设对具体配方的影响','全部配置覆盖'])


def q3_native():
    fig,aa,s=start(3,5,'独立处理质量与配方质量形成不同配置',height=5.0)
    d=read(3,'observed_joint_grid.csv');n=read(3,'native_Q_sensitivity_grid.csv')
    for k,(x,label,c,m) in enumerate([(d,'配方决定 q(p)',BLUE,'o'),(n,'独立处理 Q_B',PLUM,'s')]):
        g=feasible(x[(x.context_tokens==8192)&(x.quality_family=='power')]).sort_values('budget_FLOPs')
        aa[0,0].plot(g.N_params_B,g.D_tokens_B,color=c,marker=m,lw=1,label=label)
        aa[0,1].plot(g.budget_FLOPs,g.Q_B_proxy if k==0 else g.Q_score,color=c,marker=m,lw=1)
    panel(aa[0,0],'a','同预算集合的 N–D 配置');aa[0,0].set(xscale='log',yscale='log',xlabel='N（B）',ylabel='D（B tokens）');aa[0,0].set_xticks([.1,1,10],['0.1','1','10']);aa[0,0].set_yticks([10,100,300],['10','100','300'])
    panel(aa[0,1],'b','对应质量坐标');budget_axis(aa[0,1]);aa[0,1].set(ylabel='Q_B 或配方质量代理',ylim=(.45,1.05))
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.55,.04),ncol=2)
    finish(fig,s,'独立质量处理是声明机制的敏感性分支，不能替代观测配方证据。','8192上下文、幂成本，官方三预算及10^20诊断预算。线连接四个有序离散预算，不推断连续路径。独立处理固定172配方，QB可在0.5–1优化；配方代理来自未标定A→B桥。native低预算QB=0.5、中高预算接近1；两分支都为条件计算。',['两机制资源分配','两机制质量变化'])


def q3_external():
    fig,aa,s=start(3,6,'公开外部数据只验证规模与数据排序',height=5.1)
    d=read(3,'external_nd_runs.csv');b=read(3,'external_nd_budget_comparison.csv')
    ax=aa[0,0];panel(ax,'a','42次 OpenLM 的同语料排序')
    for k,(name,g) in enumerate(d.groupby('training_corpus')):
        x=g.B1_predicted_loss_in_Pythia_coordinates.rank();y=g.observed_Paloma_C4_loss_in_OpenLM_coordinates.rank()
        ax.scatter(x,y,color=[BLUE,PLUM,GREY][k],marker=['o','s','D'][k],s=23,label=name)
    ax.plot([0,15],[0,15],color=PALE,lw=.8);ax.set(xlim=(0,15),ylim=(0,15),xlabel='B1 预测 Loss 排名',ylabel='OpenLM 实测 Loss 排名')
    ax=aa[0,1];panel(ax,'b','受限预算下的离散选择遗憾')
    g=b[b.training_cost_budget_FLOPs.isin([1e20,1e21])].copy();labels=[f'{r.training_corpus}\n{int(np.log10(r.training_cost_budget_FLOPs))}' for r in g.itertuples()]
    ax.barh(range(len(g)),g.observed_loss_regret_in_OpenLM_coordinates,color=BLUE,height=.5);ax.set(yticks=range(len(g)),yticklabels=labels,xlabel='实测 Loss 遗憾',xlim=(0,.08));ax.tick_params(axis='y',labelsize=6.5)
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower left',bbox_to_anchor=(.12,.02),ncol=1,fontsize=7)
    finish(fig,s,'外部训练支持N–D排序及受限选择，尚不验证完整N–D–Q–配比机制。','a，三语料各14次真实公开训练，使用各语料内秩，不比较跨坐标绝对Loss。Spearman约0.9736/0.9868/0.9736。b，只保留10^20和10^21训练成本预算，6组中5组零遗憾；RefinedWeb另一组0.070515。仅训练成本、离散候选，不含质量、配方或注意力干预。',['全部外部训练秩一致性','受限离散决策检验'])


def q4_history():
    fig,aa,s=start(4,1,'历史变化先控制共同支持的构成',height=5.0)
    d=read(4,'historical_common_cells.csv');c=read(4,'historical_standardized_contributions.csv')
    d=d[(d['filter']=='primary')&(d.window_months==2)&(d.bin_width_decades==.5)&(~d.developer_control)]
    c=c[(c['filter']=='primary')&(c.window_months==2)&(c.bin_width_decades==.5)&(~c.developer_control)]
    ax=aa[0,0];panel(ax,'a','共同层内早期与晚期能力')
    for k,t in enumerate(['non_pretrained','pretrained']):
        g=d[d.type==t];ax.scatter(g.S_early,g.S_late,s=20+g.stratum_weight*160,color=[BLUE,PLUM][k],marker=['o','s'][k],label=['后训练','基座'][k])
    ax.plot([0,50],[0,50],color=PALE,lw=.8);ax.set(xlim=(0,50),ylim=(0,50),xlabel='早期六任务均分 S',ylabel='晚期六任务均分 S')
    ax=aa[0,1];panel(ax,'b','标准化分解与支持差额')
    cols=['scale_distribution_points','within_scale_temporal_points','composition_support_gap_points','full_observed_mean_change']
    for k,t in enumerate(['non_pretrained','pretrained']):
        row=c[c.type==t].iloc[0];ax.scatter([row[x] for x in cols],np.arange(4)+k*.15-.075,color=[BLUE,PLUM][k],marker=['o','s'][k],s=25)
    ax.set(yticks=range(4),yticklabels=['规模分布','同规模时间变化','支持与构成差额','完整样本变化'],xlabel='能力变化（分）');zero(ax,True);ax.invert_yaxis()
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.55,.04),ncol=2)
    finish(fig,s,'同规模时间变化解释部分历史上升，但没有识别纯技术因果效应。','主要过滤、首末各2个月、0.5 decade规模分箱，不控制开发者。a每点为共同层均分，面积反映层权重。b后训练规模−0.7579、时间6.5212、差额−1.5415，基座−3.7557/4.6356/−2.0716；前两项是标准化变化，第三项合为全样本变化。开发者控制仅保留极少记录；未排除数据量、选择或评估混杂，不使用因果术语。',['共同支持中的变化','变化分解及覆盖限制'])


def q4_validation():
    fig,aa,s=start(4,2,'短期回测显示类型依赖及预测局限',height=5.0)
    d=read(4,'rolling_two_month_frontier.csv');c=read(4,'frontier_model_comparison.csv');bars=[]
    models=['constant','frontier_trend','mean_resource','quantile_resource']
    for k,t in enumerate(['non_pretrained','pretrained']):
        ax=aa[0,k];panel(ax,chr(97+k),['后训练 · 四个滚动起点','基座 · 四个滚动起点'][k])
        g=d[(d.type==t)&(d.resource_gate=='primary')].copy();g['error']=g.predicted_q90-g.actual_q90
        z=g.pivot(index='origin',columns='model',values='error').reindex(columns=models)
        lim=max(abs(d.predicted_q90-d.actual_q90));im=heat(ax,z,['常数','前沿趋势','均值资源','分位资源'],z.index,DIV,-lim,lim);ax.tick_params(axis='x',labelrotation=35)
        bars.append(colorbar(fig,im,'预测 − 实际 q90（分）',ax))
    finish(fig,s,'后训练的分位资源形式短期误差较低，基座常数形式更稳，但各模型R²仍为负。','每格是一个起点的未来2个月残差，各模型同4窗口；不是独立训练重复，不给显著性或覆盖率结论。后训练RMSE2.1992，基座常数7.6331，基座分位资源10.561；形式选择和检验共享短期数据。12/24个月情景不由此获得长期准确性保证。',['后训练误差结构','基座误差结构'],excluded=bars)


def q4_forecasts():
    fig,aa,s=start(4,3,'前沿情景、最高纪录和不确定性各有含义',height=5.8,cols=3)
    fig.subplots_adjust(left=.12,wspace=.55)
    d=read(4,'frontier_candidate_forecasts.csv');m=read(4,'frontier_maximum_scenarios.csv');u=read(4,'frontier_scenario_union.csv')
    for k,t in enumerate(['non_pretrained','pretrained']):
        ax=aa[0,k];panel(ax,chr(97+k),['后训练 · 半速算力情景','基座 · 半速算力情景'][k])
        g=d[(d.type==t)&(d.resource_gate=='primary')&(d.compute_scenario=='half')&d.selected_by_diagnostic_rmse].sort_values('horizon_months')
        r=m[(m.type==t)&(m.compute_scenario=='half')].sort_values('horizon_months')
        ax.errorbar(g.horizon_months,g.score,yerr=[g.score-g.conditional_p05,g.conditional_p95-g.score],color=BLUE,marker='o',capsize=2,lw=1,label='两个月窗口 q90')
        ax.plot(r.horizon_months,r.conditional_record_center,color=PLUM,marker='s',lw=1,label='累计最高纪录情景')
        ax.axhline(r.historical_record_score.iloc[0],color=GREY,ls='--',lw=.8,label='历史最高纪录')
        ax.set(xlim=(10,26),xticks=[12,24],xlabel='相对2025年3月（个月）',ylabel='六任务均分 S',ylim=(0,100))
    ax=aa[0,2];panel(ax,'c','后训练24个月的范围解释')
    row=d[(d.type=='non_pretrained')&(d.resource_gate=='primary')&(d.compute_scenario=='half')&(d.horizon_months==24)&d.selected_by_diagnostic_rmse].iloc[0]
    ur=u[(u.type=='non_pretrained')&(u.resource_gate=='primary')&(u.compute_scenario=='half')&(u.horizon_months==24)].iloc[0]
    bounds=[(row.conditional_p05,row.conditional_p95),(ur.scenario_union_lower,ur.scenario_union_upper),(ur.with_fixed_bias_stress_lower,ur.with_fixed_bias_stress_upper)]
    for i,((lo,hi),c) in enumerate(zip(bounds,[BLUE,PLUM,GREY])):ax.hlines(i,lo,hi,color=c,lw=3)
    ax.set(yticks=range(3),yticklabels=['固定假设','假设并集','附加偏差压力'],ylim=(2.6,-.6),xlim=(0,100),xlabel='能力分数范围')
    fig.legend(*aa[0,0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.55,.04),ncol=1,fontsize=7.5)
    finish(fig,s,'最高纪录需要尾部假设；情景范围没有长期预测覆盖率保证。','预测起点固定在2025年3月，不是当前日期。半速算力下后训练12/24个月q90为53.8278/66.6810，最高纪录情景60.6000/73.4532；基座q90约21.0319而累计纪录保持38.441。q90细线为固定假设5–95%条件自助范围；紫线累计最高加入尾差，不能当同一统计目标。c仅后训练24个月，范围61.9828–69.8046、37.7548–90.6216、31.5900–96.7864；不是置信区间。四回测窗口无新纪录，纪录延续基线RMSE=0，尾差动态尚未验证优于它。',['后训练两种目标','基座两种目标','范围来源分层'])


def q4_bridge():
    fig,aa,s=start(4,4,'能力映射先校验来源，再展示条件兑换',height=6.6,rows=2,cols=2)
    models=read(4,'bridge_source_coordinate_models.csv');sample=read(4,'prepared/bridge_sample.csv');stress=read(4,'q3_bridge_conclusion_sensitivity.csv')
    primary=models[models.diagnostic_primary_candidate];ids=primary.coordinate_id.tolist()
    for k,row in enumerate(primary.itertuples()):
        ax=aa[0,k];panel(ax,chr(97+k),['Qwen2 · 来源内映射','Qwen2.5 · 来源内映射'][k])
        prefix='Qwen2.5' if '2.5' in row.coordinate_id else 'Qwen2 '
        g=sample[sample.Loss_Source.str.startswith(prefix)&sample.Loss_Source.str.contains('validation loss',case=False)]
        x=np.linspace(row.loss_min,row.loss_max,100);y=100/(1+np.exp(-(row.a+row.bLoss*x)))
        ax.scatter(g.Val_Loss,g.S,color=BLUE,s=25);ax.plot(x,y,color=PLUM,lw=1)
        ax.set(xlabel='该来源验证 Loss',ylabel='六任务均分 S',ylim=(0,100))
    ax=aa[1,0];panel(ax,'c','8192 · 幂成本的三种政策')
    for k,mode in enumerate(['fixed_recipe','observed_joint_recipe','independent_native_Q']):
        g=stress[(stress.coordinate_id==ids[1])&(stress.policy_mode==mode)&(stress.context_tokens==8192)&(stress.quality_family=='power')].sort_values('budget_FLOPs')
        ax.plot(g.budget_FLOPs,g.nominal_score,color=[GREY,BLUE,PLUM][k],marker=['D','o','s'][k],lw=1,label=['固定配方','联合配方','独立质量'][k])
    budget_axis(ax);ax.set_ylabel('Qwen2.5坐标条件能力')
    ax=aa[1,1];panel(ax,'d','中预算固定配方的桥范围')
    for k,coord in enumerate(ids):
        g=stress[(stress.coordinate_id==coord)&(stress.policy_mode=='fixed_recipe')&(stress.context_tokens==8192)&(stress.quality_family=='power')&(stress.budget_FLOPs==1e22)].iloc[0]
        ax.hlines(k,g.score_min,g.score_max,color=[BLUE,PLUM][k],lw=3);ax.scatter(g.nominal_score,k,color=INK,s=24,zorder=3)
    ax.set(yticks=[0,1],yticklabels=['Qwen2','Qwen2.5'],ylim=(1.6,-.6),xlim=(0,45),xlabel='条件能力分数')
    fig.legend(*aa[1,0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.55,.02),ncol=3,fontsize=7)
    finish(fig,s,'来源内映射可诊断，Q3 Loss到能力的跨来源坐标仍未识别。','a/b分别n=4/6，点为C6记录，曲线为冻结logistic映射，不跨Loss坐标混拟合；留一RMSE7.0475/2.6553，比常数10.7083/15.0745低。Pythia映射不优于常数，排除为主桥。c，缺失表示无支持或不可行，不补零；固定与联合在支持预算均选172而重合。d，27种确定性坐标及上游压力组合的支持内范围，22/23种支持；黑点为名义桥。不是统计区间、真实能力训练结果或未来前沿预测。',['Qwen2来源证据','Qwen2.5来源证据','三机制条件兑换','坐标和上游假设范围'])


def q4_data_scope():
    fig,aa,s=start(4,5,'附件尺度差异决定可用证据范围',height=5.2,cols=3)
    fig.subplots_adjust(left=.11,wspace=.65)
    b=read(4,'c8_bbh_task_aggregation.csv');c=read(4,'c3_row_metric_audit.csv');r=read(4,'c4_annual_resource_comparison.csv')
    ax=aa[0,0];panel(ax,'a','C8：24任务异质性')
    ax.scatter(b.bbhMacroMean,b.bbhTaskSd,color=BLUE,s=4,alpha=.18,rasterized=True);ax.set(xlabel='BBH 24任务宏平均',ylabel='任务间标准差',xlim=(0,100),ylim=(0,40))
    ax=aa[0,1];panel(ax,'b','C3：Average与六任务均分')
    for k,(source,g) in enumerate(c.groupby('Source')):
        ax.scatter(g.six_task_mean,g.Average,color=[BLUE,PLUM,GREY][k%3],marker=['o','s','D'][k%3],s=8,alpha=.3)
    ax.plot([0,100],[0,100],color=PALE,lw=.8);ax.set(xlim=(0,100),ylim=(0,100),xlabel='重算六任务均分',ylabel='附件 Average')
    ax=aa[0,2];panel(ax,'c','C4：年度算力口径敏感性')
    for k,gate in enumerate(['primary','wide_ratio']):
        g=r[(r.resource_gate==gate)&r.year.between(2021,2024)&r.complete].sort_values('year')
        ax.plot(g.year,g.q90_logC,color=[BLUE,PLUM][k],marker=['o','s'][k],lw=1,label=['严格资源门控','宽资源比例门控'][k])
    ax.set(xticks=[2021,2022,2023,2024],xlabel='完整年份',ylabel='年度 q90 log10 C');ax.tick_params(axis='x',labelrotation=45)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.75,.04),ncol=1,fontsize=7)
    finish(fig,s,'不同附件任务、年代与门控不能直接拼成统一能力曲线。','a，1860个成功解析结果各一点，24任务等权；标准差是任务差异而非模型均分置信区间，4个解析失败单列。b，4599行全列，混合来源只核对指标，不作为同口径时间轨迹；26历史行Average与六均分绝对差均值9.101。c，只画2021–24完整年份，两门控年度资源增长倍数4.901/3.986；严格样本81、宽口径93。未改写原始附件。',['BBH任务异质性','评分口径审计','资源门控敏感性'])


def main():
    global COEFF
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill-dir',type=Path,default=Path.home()/'.codex/skills/nature-figure')
    p.add_argument('--questions',default='1,2,3,4');args=p.parse_args()
    sys.path.insert(0,str(args.skill_dir/'scripts'))
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'qa').mkdir(exist_ok=True);(OUT/'source_data').mkdir(exist_ok=True)
    COEFF=read(2,'model_coefficients.json')
    selected=[int(x) for x in args.questions.split(',')]
    if 1 in selected:q1_quality();q1_conflict();q1_validation();q1_decisions();q1_stress()
    if 2 in selected:q2_scaling();q2_validation();q2_tradeoff();q2_domains();q2_evidence()
    if 3 in selected:q3_resources();q3_costs();q3_states();q3_assumptions();q3_native();q3_external()
    if 4 in selected:q4_history();q4_validation();q4_forecasts();q4_bridge();q4_data_scope()
    old=json.loads((OUT/'manifest.json').read_text(encoding='utf-8')) if (OUT/'manifest.json').exists() else {'figures':[],'inputs':{},'qa':{}}
    figures=[f for f in old['figures'] if int(f['stem'][1]) not in selected]+FIGURES
    inputs=old['inputs']|{str(f.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(READS)}
    manifest={'source_main':MAIN,'backend':'Python','skill':'nature-figure','independent_design':True,'figures':sorted(figures,key=lambda f:f['stem']),
        'inputs':inputs,'qa':old['qa']|QA,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    cards=[];legends=[]
    for f in manifest['figures']:
        stem=f['stem'];cards.append(f'<section><h2>{stem} · {html.escape(f["claim"])}</h2><img src="{stem}.png" alt="{stem}"><p>{html.escape(f["legend"])}</p><a href="{stem}.pdf">PDF</a> · <a href="{stem}.svg">SVG</a></section>')
        legends.append(f'## {stem} | {f["claim"]}\n\n{f["legend"]}\n\n面板角色：'+ '；'.join(f['panel_roles'])+'。\n')
    (OUT/'legends.md').write_text('# Q1–Q4 独立 Nature 图注\n\n'+'\n'.join(legends),encoding='utf-8')
    (OUT/'gallery.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Q1–Q4 Nature 图组</title><style>body{background:#f4f4f6;color:#272727;font:15px/1.8 Arial,"Microsoft YaHei",sans-serif}main{max-width:1100px;margin:auto}section{background:white;margin:32px 0;padding:22px}h2{font-size:18px}img{width:100%}a{color:#0F4D92}</style><main><h1>Q1–Q4 独立 Nature 图组</h1><p>按论证链组织的多面板科学图。冻结条件模型；范围、统计与局限见每张图注。</p>'+''.join(cards)+'</main></html>',encoding='utf-8')
    print('Total figures:',len(manifest['figures']))


if __name__=='__main__':main()
