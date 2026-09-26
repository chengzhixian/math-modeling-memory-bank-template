"""Visualize frozen Q2 v8; no fitting or mutation of upstream result tables.

python -B src/visualization/q2_redesign.py [--finalize]
Default renders previews. After visual inspection, --finalize exports vectors.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'outputs/Q2'
OUT = SOURCE / 'redesign'
RAW = ROOT / 'data/raw/real_attachments/B_scaling_laws/pythia_training_log_existing.csv'
BLUE, TEAL, ORANGE = '#0072B2', '#009E73', '#E69F00'
INK, GREY, LIGHT = '#243746', '#718096', '#E8EEF2'
SEQ = LinearSegmentedColormap.from_list('white_blue', ['#F3F7FA', '#B4D4E8', BLUE, '#003E64'])
DIV = LinearSegmentedColormap.from_list('blue_white_orange', [BLUE, '#FAFCFD', ORANGE])
FIGURES, AUDITS, INPUTS = [], {}, set()
LABELS = {'arxiv':'arXiv', 'freelaw':'FreeLaw', 'nih_exporter':'NIH', 'pubmed_central':'PMC',
          'wikipedia_en':'Wikipedia', 'dm_mathematics':'Mathematics', 'github':'GitHub',
          'philpapers':'PhilPapers', 'stackexchange':'StackExchange', 'enron_emails':'Enron',
          'gutenberg_pg_19':'Gutenberg', 'pile_cc':'Pile-CC', 'ubuntu_irc':'Ubuntu IRC',
          'europarl':'EuroParl', 'hackernews':'HackerNews', 'pubmed_abstracts':'PubMed Abs.',
          'uspto_backgrounds':'USPTO'}

def csv(name):
    INPUTS.add(SOURCE/name)
    return pd.read_csv(SOURCE/name)

def js(name):
    INPUTS.add(SOURCE/name)
    return json.loads((SOURCE/name).read_text(encoding='utf-8-sig'))

def base(title, subtitle, size=(7.2,4.8), margins=(.14,.93,.24,.80)):
    fig=plt.figure(figsize=size)
    fig.subplots_adjust(left=margins[0],right=margins[1],bottom=margins[2],top=margins[3])
    fig.suptitle(title,x=.025,y=.985,ha='left',fontsize=14,weight='bold',color=INK)
    fig.text(.025,.936,subtitle,va='top',fontsize=8.5,color=GREY)
    return fig

def clean(ax,axis='y'):
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['bottom','left']].set_color('#CAD5DD')
    ax.tick_params(length=0,pad=5)
    ax.grid(axis=axis,color=LIGHT,lw=.7)
    ax.set_axisbelow(True)

def finish(fig,stem,caption):
    fig.text(.025,.025,caption,fontsize=7.5,color=GREY,va='bottom',linespacing=1.65)
    fig.canvas.draw()
    AUDITS[stem]=AUDIT(fig)
    if any(level=='FAIL' for level,_ in AUDITS[stem]):
        raise RuntimeError(str(AUDITS[stem]))
    fig.savefig(OUT/f'{stem}.png',dpi=300,facecolor='white')
    with Image.open(OUT/f'{stem}.png') as im:
        im.convert('L').save(OUT/f'{stem}_gray.png',dpi=(300,300))
    if FINALIZE:
        for ext in ['pdf','svg']:
            fig.savefig(OUT/f'{stem}.{ext}',facecolor='white')
        svg=OUT/f'{stem}.svg'
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    FIGURES.append({'stem':stem,'caption':caption,'size_inches':list(fig.get_size_inches()),'dpi':300})
    plt.close(fig)

def backbone(n,d):
    return COEFF['E']+COEFF['A']*n**(-COEFF['alpha'])+COEFF['B']*d**(-COEFF['beta'])

def baseline():
    INPUTS.add(RAW)
    d=pd.read_csv(RAW)
    pred=backbone(d.N_params_B.to_numpy(),d.D_tokens_B.to_numpy())
    residual=pred-d.val_loss.to_numpy()
    pd.DataFrame({'observed':d.val_loss,'predicted':pred,'residual':residual}).to_csv(OUT/'baseline_reconstruction.csv',index=False)
    fig=base('01  标度骨架重建了 B1 的 Loss 变化','B1：1,176 条同源记录、8 个模型规模；拟合误差很小，需要与独立验证区分',margins=(.12,.94,.25,.80))
    axes=fig.subplots(1,2,gridspec_kw={'wspace':.42})
    ax=axes[0]
    ax.scatter(d.val_loss,pred,s=9,color=BLUE,alpha=.45)
    lo,hi=min(d.val_loss.min(),pred.min()),max(d.val_loss.max(),pred.max())
    ax.plot([lo,hi],[lo,hi],ls='--',color=GREY,lw=1)
    ax.set(xlabel='B1 记录 Loss',ylabel='骨架拟合 Loss',title='同源重建：点接近对角线')
    clean(ax)
    ax=axes[1]
    ax.scatter(d.D_tokens_B,residual*1000,s=9,color=BLUE,alpha=.45)
    ax.axhline(0,color=GREY,lw=1,ls='--')
    ax.set(xscale='log',xlabel='训练量 D（十亿 tokens）',ylabel=r'拟合 − 记录 Loss（$\times 10^{-3}$）',title='残差的量级与分布')
    clean(ax)
    rmse=np.sqrt(np.mean(residual**2))
    if not np.isclose(rmse,0.00014657641916440922,rtol=1e-6):
        raise ValueError('B1 reconstruction differs from published fit')
    finish(fig,'01_baseline',r'冻结五参数骨架：$L_0 = E + A N^{-\alpha} + B D^{-\beta}$；'+f'同源 RMSE = {rmse:.7f}。\n此图不表示真实跨模型家族的泛化精度；残差纵轴放大 1,000 倍。')

def scale_surface():
    n=np.geomspace(.070542,11.965825,180); d=np.geomspace(10,299.893,150)
    nn,dd=np.meshgrid(n,d); z=backbone(nn,dd)
    fig=base('02  增加规模和训练量均降低骨架 Loss','连续曲面来自冻结解析模型；只显示 Q2 正式 N–D 支持范围',margins=(.13,.82,.24,.80))
    ax=fig.add_subplot()
    im=ax.pcolormesh(nn,dd,z,cmap=SEQ,shading='auto')
    c=ax.contour(nn,dd,z,levels=[2.3,2.5,2.7,2.9],colors='white',linewidths=.9)
    labels=ax.clabel(c,fontsize=8,fmt='%.1f',colors=INK)
    for label in labels:label.set_bbox({'facecolor':'white','edgecolor':'none','alpha':.85,'pad':1.5})
    ax.set(xscale='log',yscale='log',xlabel='模型规模 N（十亿参数）',ylabel='训练量 D（十亿 tokens）')
    ax.set_xticks([.1,1,10],['0.1','1','10']);ax.set_yticks([10,30,100,299.893],['10','30','100','299.9'])
    cax=fig.add_axes([.87,.30,.025,.45]);fig.colorbar(im,cax=cax).set_label(r'骨架预测 Loss $L_0$')
    finish(fig,'02_scale_surface','范围：N ∈ [0.070542, 11.965825]，D ∈ [10, 299.893]；双对数坐标。\n此图仅为 B1 骨架，不包含质量项和配比项；等值线是模型预测，不是观测分组。')

def quality_validation():
    ext=js('b7_quality_extension.json')
    folds=pd.DataFrame(ext['outer_folds'])
    folds.to_csv(OUT/'quality_outer_folds.csv',index=False)
    fig=base('03  质量扩展在半合成 B7 上的留出误差','按 N、D、质量代理分别留出一个水平；每个点是一折，保留完整离散分布',margins=(.13,.94,.25,.80))
    ax=fig.add_subplot()
    for i,(key,label,color,marker) in enumerate(zip(['N_params_B','D_tokens_B','Q_score'],['规模 N','训练量 D','质量代理 q'],[BLUE,TEAL,ORANGE],['o','s','^'])):
        s=folds[folds.axis==key].outer_rmse.to_numpy()
        if not len(s):
            raise ValueError(f'Unknown B7 outer-fold axis: {key}')
        ax.scatter(i+np.linspace(-.15,.15,len(s)),s,s=38,color=color,marker=marker,zorder=3)
        ax.hlines(s.mean(),i-.23,i+.23,color=color,lw=2)
        ax.text(i,.071,f'n={len(s)}\n均值 {s.mean():.4f}',ha='center',va='top',fontsize=8.5,color=color)
    ax.set_xticks([0,1,2],['留出规模水平','留出训练量水平','留出质量水平'])
    ax.set(xlim=(-.5,2.5),ylim=(0,.075),ylabel='外层留出 RMSE')
    clean(ax)
    finish(fig,'03_quality_validation','横线为各轴外层折的算术均值；散点不是独立实验重复，不作置信区间解释。\nB7 为 450 条半合成记录；此验证支持该条件形式，不证明真实跨数据源质量因果效应。')

def elasticity():
    d=csv('marginals_elasticities.csv')
    fig=base('04  质量、规模、训练量的局部敏感度','同一冻结配方，D = 100B tokens；弹性可在统一的相对变化尺度上比较')
    ax=fig.add_subplot()
    for col,label,c,m in [('N_elasticity','模型规模 N',BLUE,'o'),('D_elasticity','训练量 D',TEAL,'s'),('quality_proxy_elasticity','质量代理 q',ORANGE,'^')]:
        ax.plot(d.N_params_B,-d[col],marker=m,color=c,lw=1.6,ms=6,label=label)
    ax.set(xscale='log',xlabel='模型规模 N（十亿参数）',ylabel='Loss 下降弹性 −∂ln(Loss) / ∂ln(x)',ylim=(0,.14))
    ax.set_xticks([.1,1,10],['0.1','1','10']);ax.legend(frameon=False,loc='upper right',fontsize=8)
    clean(ax)
    finish(fig,'04_elasticities','曲线连接三个有序规模情景；正值表示该变量局部增加时，预测 Loss 下降。\n质量 q 为归一化工程代理；相同百分比变化不代表相同实际成本，也不表示因果优劣。')

def tradeoff():
    d=csv('quality_scale_local_tradeoff.csv')
    gains=[]
    fig=base('05  假设质量提高，可维持 Loss 并缩小模型','固定配方、D = 100B；基准 q = 0.6714，求解同 Loss 的新规模')
    ax=fig.add_subplot()
    y=np.arange(len(d))
    for delta,c,m in [('0_05',BLUE,'o'),('0_1',TEAL,'s')]:
        col='constant_L_newQ_N_delta_'+delta
        if not d[col+'_status'].eq('root_in_support').all():raise ValueError('Unsupported tradeoff root')
        values=100*(1-d[col]/d.N_params_B)
        ax.scatter(values,y,s=55,color=c,marker=m,label=f'质量代理增加 {delta.replace("_",".")}')
        for yy,v in zip(y,values):ax.text(v+.7,yy,f'{v:.1f}%',fontsize=9,color=c,va='center')
        gains.append(values.to_numpy())
    for yy,a,b in zip(y,gains[0],gains[1]):ax.plot([a,b],[yy,yy],color=LIGHT,lw=3,zorder=0)
    ax.set_yticks(y,[f'N = {n:g}B' for n in d.N_params_B]);ax.set(xlim=(0,34),ylim=(2.5,-.5),xlabel='同 Loss 下的模型规模下降（%）')
    fig.legend(*ax.get_legend_handles_labels(),frameon=False,loc='lower center',bbox_to_anchor=(.53,.815),ncol=2,fontsize=8)
    clean(ax,'x')
    pd.DataFrame({'N_params_B':d.N_params_B,'reduction_q_plus_0_05_percent':gains[0],'reduction_q_plus_0_1_percent':gains[1]}).to_csv(OUT/'same_loss_size_reductions.csv',index=False)
    finish(fig,'05_quality_tradeoff','所有新规模解均在正式支持域；比较质量代理的绝对增量，而非 5% / 10% 的相对增量。\n这是固定 p 的假想代理质量干预；不能解释为实际清洗数据即可节省相同比例算力。')

def sensitivity():
    d=csv('quality_bridge_sensitivity.csv')
    fig=base('06  质量映射假设会改变最终预测','同一配方、N = 1B、D = 100B；三个映射强度都尚未经验标定',margins=(.21,.92,.25,.80))
    ax=fig.add_subplot();y=np.arange(3)
    for i,row in enumerate(d.itertuples()):
        ax.scatter(row.Loss,i,s=60,color=BLUE if row.scale==1 else ORANGE,marker='o' if row.scale==1 else 'D')
        ax.text(row.Loss+.006,i,f'{row.Loss:.4f}  ·  q={row.Q_B_proxy:.3f}',fontsize=8.5,va='center',color=INK)
    ax.set_yticks(y,['压缩映射 ×0.5','默认映射 ×1.0','扩张映射 ×1.5'])
    ax.set(xlim=(2.28,2.45),ylim=(2.6,-.6),xlabel='条件预测 Loss（局部放大坐标）')
    clean(ax,'x')
    finish(fig,'06_bridge_sensitivity','图中范围为情景差异，不是统计置信区间；质量映射覆盖约 58.1%，未映射约 41.9%。\n质量与配比项的重复计数尚未识别；不能把默认映射当作已验证的跨数据源规律。')

def transfers():
    d=csv('domain_pair_substitution.csv');ref=js('domain_pair_reference.json')
    domains=list(ref['p']); mat=np.zeros((len(domains),len(domains)))
    if len(d)!=136 or not ref['all_pairs_hull_feasible_in_both_directions']:raise ValueError('Pair feasibility mismatch')
    for row in d.itertuples():
        i,j=domains.index(row.domain_i),domains.index(row.domain_j)
        if row.transfer_direction.replace(' ','')!=f'{row.domain_j}->{row.domain_i}':raise ValueError('Transfer sign convention changed')
        mat[i,j]=row.dLoss_depsilon;mat[j,i]=-row.dLoss_depsilon
    pd.DataFrame(mat,index=domains,columns=domains).to_csv(OUT/'transfer_derivative_matrix.csv')
    lim=np.max(np.abs(mat))
    fig=base('07  配方转移的局部方向依赖来源与去向','列是减配领域，行是增配领域；蓝色降低预测 Loss，橙色提高预测 Loss',size=(7.2,7.3),margins=(.21,.81,.29,.81))
    ax=fig.add_subplot()
    edges=np.arange(-.5,17,1)
    im=ax.pcolormesh(edges,edges,mat,cmap=DIV,norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim),shading='flat')
    ax.set_xlim(-.5,16.5);ax.set_ylim(16.5,-.5);ax.set_aspect('equal')
    names=[LABELS[k] for k in domains]
    ax.set_yticks(range(17),names,fontsize=7);ax.set_xticks(range(17),names,rotation=90,ha='center',fontsize=7)
    ax.tick_params(length=0,pad=3)
    for sp in ax.spines.values():sp.set_visible(False)
    ax.set(xlabel='减配来源领域',ylabel='增配去向领域')
    ax.set_xticks(np.arange(-.5,17,1),minor=True);ax.set_yticks(np.arange(-.5,17,1),minor=True)
    ax.grid(which='minor',color='white',lw=.5);ax.tick_params(which='minor',length=0)
    cax=fig.add_axes([.88,.36,.022,.38]);fig.colorbar(im,cax=cax).set_label('局部导数 ∂Loss / ∂ε',fontsize=8)
    finish(fig,'07_local_transfers','参考点为 512 个 A4 配方的均值，N = 1B、D = 100B、13 个目标等权；ε 为绝对份额。\n136 对均可双向局部转移；颜色不是有限转移收益，且不同方向的可行步长不同。\n这是条件模型的局部方向，不是领域因果效应，也不能沿同一颜色任意大幅调整配方。')

def main():
    global COEFF,AUDIT,FINALIZE
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill-dir',type=Path,default=Path.home()/'.codex/skills/scipilot-figure-skill')
    p.add_argument('--finalize',action='store_true')
    args=p.parse_args();FINALIZE=args.finalize
    sys.path.insert(0,str(args.skill_dir/'scripts'))
    from setup_style import setup_style
    from visual_qa import audit_layout
    from profile_data import profile_data
    AUDIT=audit_layout
    setup_style(journal='general',lang='zh',use_sciplots=False)
    plt.rcParams.update({'font.family':['Microsoft YaHei'],'font.sans-serif':['Microsoft YaHei'],
        'font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
        'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,
        'figure.constrained_layout.use':False})
    OUT.mkdir(parents=True,exist_ok=True)
    profiles={}
    for name in ['marginals_elasticities.csv','quality_scale_local_tradeoff.csv','quality_bridge_sensitivity.csv','domain_pair_substitution.csv']:
        profiles[name]=profile_data(csv(name))
    INPUTS.add(RAW);profiles['B1_raw']=profile_data(pd.read_csv(RAW),group_cols=['N_params_B'])
    (OUT/'scipilot_profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    COEFF=js('model_coefficients.json')['B1_backbone']
    js('model_definition.json')
    baseline();scale_surface();quality_validation();elasticity();tradeoff();sensitivity();transfers()
    cards=[]
    for f in FIGURES:
        s=f['stem'];cards.append(f'<section><img src="{s}.png" alt="{s}"><p>{html.escape(f["caption"]).replace(chr(10),"<br>")}</p><a href="{s}.pdf">PDF</a> · <a href="{s}.svg">SVG</a></section>')
    (OUT/'gallery.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Q2 结果图册</title><style>body{margin:0;background:#edf2f6;color:#243746;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1020px;margin:30px auto;padding:0 20px}section{background:white;margin:24px 0;padding:22px;border-radius:12px}img{width:100%}p{font-size:14px;color:#536674}a{color:#0072B2}</style><main><h1>Q2 结果图册</h1><p>依据 main @ a19039b 的冻结 v8 结果。与 Q1 使用同一配色。模型图为条件情景，不表示已验证的跨数据源因果规律。</p>'+''.join(cards)+'</main></html>',encoding='utf-8')
    manifest={'source_main':'a19039b5d11c91cf32e301dc85b2f4d50b5a75b7','model':'cyj.ndqp.scenario.v8',
              'inputs':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(INPUTS)},
              'figures':FIGURES,'layout_audit':AUDITS,'visual_review':'vectors exported after manual preview review' if FINALIZE else 'pending',
              'versions':{'python':sys.version.split()[0],'matplotlib':matplotlib.__version__,'numpy':np.__version__,'pandas':pd.__version__}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'figures':len(FIGURES),'layout':AUDITS},ensure_ascii=False))

if __name__=='__main__':main()
