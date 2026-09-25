"""Generate paper tables, a complete Chinese answer, LaTeX section and figures.
Run after q4_complete.py. matplotlib is needed only for figures.
"""
from pathlib import Path
import json
import sys
import os
import numpy as np
import pandas as pd
from q4_complete import ROOT, OUT, sha, json_safe

# Optional repo-local installation used on this Windows machine. The published
# numerical model keeps using the bundled NumPy/Pandas loaded above.
LOCAL=ROOT/'data/processed/zhh_runtime'
if LOCAL.exists(): sys.path.append(str(LOCAL))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def table(frame, columns, names):
    out=['| '+' | '.join(names)+' |','| '+' | '.join(['---']*len(columns))+' |']
    for _,r in frame.iterrows():
        out.append('| '+' | '.join(f'{r[c]:.3f}' if isinstance(r[c],(float,np.floating)) else str(r[c]) for c in columns)+' |')
    return '\n'.join(out)


def figures(forecasts,contributions,resources):
    folder=ROOT/'paper/latex/figures/zhh'
    folder.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    scenarios=['no_growth','quarter_growth','half_growth','historical_growth']
    colors=['#62788c','#269e8e','#3973ac','#b75b46']
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    for ax,typ,title in zip(axes,['pretrained','non_pretrained'],['Pretrained base models','Chat / domain-finetuned models']):
        data=forecasts[(forecasts['filter']=='base_chat_domain_latest')&(forecasts.type==typ)&(forecasts.horizon_months==12)].set_index('scenario').loc[scenarios]
        ax.bar(np.arange(4),data.predicted_score,color=colors,width=.58)
        ax.errorbar(np.arange(4),data.predicted_score,
            yerr=[data.predicted_score-data.scenario_lower,data.scenario_upper-data.predicted_score],fmt='none',ecolor='#283746',capsize=5,lw=1.5)
        ax.axhline(data.observed_anchor_score.iloc[0],color='#666666',ls='--',lw=1,label='Observed q90 at origin')
        ax.set_xticks(np.arange(4),['Stopped','Quarter','Half','Historical'])
        ax.set_title(title); ax.set_ylim(0,100); ax.set_xlabel('Compute log-growth scenario')
        for i,v in enumerate(data.predicted_score):ax.text(i,v+1,f'{v:.1f}',ha='center',fontsize=9)
    axes[0].set_ylabel('Six-task equal-weight score (0–100)'); axes[1].legend(loc='upper left',fontsize=8)
    fig.suptitle('12-month conditional capability frontier from 2025-03-13')
    fig.text(.5,.015,'Bars: assumed eta = 0.5, drift retention = 0.5. Whiskers: sensitivity envelope, not a 95% prediction interval.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.055,1,.94]); fig.savefig(folder/'q4_frontier_12m.png',dpi=180);plt.close(fig)
    c=contributions[(contributions['filter']=='base_chat_domain_latest')&(contributions.window_months==2)]
    fig,ax=plt.subplots(figsize=(8,4.8)); x=np.arange(len(c)); width=.22
    for j,(column,label,color) in enumerate([('scale_points','Scale association','#3973ac'),('non_scale_points','Time association','#269e8e'),('unexplained_change','Unexplained / composition','#b75b46')]):
        ax.bar(x+(j-1)*width,c[column],width,label=label,color=color)
    ax.scatter(x,c.observed_change,color='black',marker='D',s=35,label='Observed q90 change',zorder=4)
    ax.axhline(0,color='#444444',lw=.7);ax.set_xticks(x,['Chat / domain-finetuned' if v=='non_pretrained' else 'Pretrained base' for v in c.type])
    ax.set_ylabel('Score change (points)');ax.set_title('Early vs late two-month windows: signed decomposition')
    ax.legend(fontsize=8,loc='upper right');fig.tight_layout();fig.savefig(folder/'q4_signed_contributions.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4.2))
    r=resources[resources.partial_year==False]
    axes[0].plot(r.year,r.q90_logC,'o-',color='#3973ac',label='Compute, FLOPs')
    axes[0].set_ylabel('log10 annual q90 compute');axes[0].set_title('Audited C4 resource history')
    axes[1].plot(r.year,r.q90_logN,'o-',label='Parameters',color='#3973ac')
    axes[1].plot(r.year,r.q90_logD,'s-',label='Tokens',color='#269e8e')
    axes[1].set_ylabel('log10 count');axes[1].set_title('Parameters and tokens have different growth');axes[1].legend()
    for ax in axes:ax.set_xlabel('Publication year');ax.set_xticks(r.year.astype(int));ax.grid(alpha=.15)
    for _,row in r.iterrows():axes[0].annotate(f"n={int(row['n'])}",(row.year,row.q90_logC),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
    fig.tight_layout();fig.savefig(folder/'q4_resource_history.png',dpi=180);plt.close(fig)
    return sorted(folder.glob('q4_*.png'))


def main():
    r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    f=pd.read_csv(OUT/'frontier_forecast.csv'); c=pd.read_csv(OUT/'historical_contributions.csv')
    coef=pd.read_csv(OUT/'dynamic_coefficients.csv'); annual=pd.read_csv(OUT/'c4_annual_resources.csv')
    primary=f[f['filter']=='base_chat_domain_latest'].copy()
    primary['类型']=primary.type.map({'pretrained':'基础预训练','non_pretrained':'chat/领域微调'})
    primary['情景']=primary.scenario.map({'no_growth':'停止','quarter_growth':'四分之一','half_growth':'减半','historical_growth':'历史对照'})
    cp=c[(c['filter']=='base_chat_domain_latest')&(c.window_months==2)].copy()
    cp['类型']=cp.type.map({'pretrained':'基础预训练','non_pretrained':'chat/领域微调'})
    cp['账面规模百分比']=100*cp.accounting_scale_share;cp['账面非规模百分比']=100*cp.accounting_non_scale_share
    pp=coef[coef['filter']=='base_chat_domain_latest'].copy()
    pp['类型']=pp.type.map({'pretrained':'基础预训练','non_pretrained':'chat/领域微调'})
    bridge=r['bridge']; resources=r['resources']; audit=r['audit']; backtest=r['backtest']['summary']
    btable=pd.DataFrame(bridge['diagnostics'])
    ms=[x for x in bridge['mappings'] if x['model']=='monotone_loss']
    q3=r['q3_consumption']; c8=r['c8']
    forecast_table=table(primary,['类型','horizon_months','情景','predicted_score','scenario_lower','scenario_upper'],['类型','月数','算力增长','点值','情景下界','情景上界'])
    contribution_table=table(cp,['类型','observed_change','scale_points','non_scale_points','unexplained_change','账面规模百分比','账面非规模百分比'],['类型','观测变化','规模关联','时间关联','未解释','账面规模%','账面非规模%'])
    coeff_table=table(pp,['类型','n','b_logN','b_month','frontier_start','N_anchor_B'],['类型','样本','bN','bt/月','当前90%前沿','高分模型N锚/B'])
    answer=rf'''# 第四问完整条件答卷：资源增长放缓下的开放模型能力前沿

发布：`zhh.q4.conditional.v2`。本答卷补齐原有空预测、C4数据量、带符号贡献、分层映射与不确定性。结论是**声明资源配置和进步持续假设下的条件答案**，不是已经识别的纯技术因果份额或已校准的未来真实最高分。所有数值由 `src/zhh/q4_complete.py` 生成；发布清单为 `outputs/zhh/q4_v2/manifest.json`。

## 1. 题面要求、指标与数据角色

综合能力 $S_i=\frac16\sum_{{j=1}}^6 S_{{ij}}$，六项为 IFEval、BBH、MATH Lvl 5、GPQA、MUSR、MMLU-PRO，分数单位为百分制点。等权是外生效用选择；不把任务准确率与任务间难度强行同质化。完整六任务才入样，空字符串为缺失，非有限、越界分数、非正N、无日期者排除。时间为榜单提交日，不等于训练完成日。

C2有{audit['raw_n']}行。Epoch明确no优先排除；yes或未标no且许可证可识别形成{audit['expanded_before_dedup']}行扩展集，保留同名最新版本后{audit['expanded_latest']}个模型。明确yes去重集{audit['strict_latest']}，Apache/MIT/BSD/CC0许可证标签白名单{audit['permissive_latest']}。白名单说明标签允许研究使用的初筛口径，没有逐仓库核验许可证版本及权重实际可得性；自定义许可证和未知者另标人工复核。

主动力学只用204个明确基础预训练模型以及477个chat、1143个领域微调模型。44个持续预训练、742个合并、6个多模态不混入主组；扩展集敏感性保留它们。chat与领域微调合并为后训练大组但原始类别始终保留。严格yes基础模型近期仅4条，因此不发布该格的高分位情景，结果明确记录缺样。

| 要求 | 数据与角色 | 当前使用与限制 |
|---|---|---|
| 多维能力、类型、时间、开放性 | C2观测 | 六任务均值、类别、提交日期；标签代理开放性 |
| 历史变化 | C3混合 | 4599行，4573来自榜单、26历史报告；分来源/年度描述，不校准拼接 |
| 算力、数据量、开放权重 | C4报告/估算 | 同行N,C,D、单位/阶段日志、年度资源轨迹、未来ND预算 |
| Loss映射 | C6混合 | high 7、medium 68分开，族/来源诊断；跨坐标只能假设情景 |
| 逐任务 | C8观测 | 1860模型×24 BBH任务，宏平均/离散度/最弱任务 |
| 上下文 | C7观测 | 2048/8192/131072 Token保持Q3外生接口 |
| 前三问输出 | Q3 v8未集成条件成果 | 固定SHA、Loss坐标假设及支持域门禁，无联合95%区间 |

C2/C6此前已经查看，以下验证均称诊断；C4只使用不晚于{audit['forecast_origin']}发布的行。C3不进入预测拟合，也不把其异构Average当六任务一致时间序列。没有仅凭模型名进行C2↔C4或C2↔C6连接。

## 2. C4数据量与资源链审计

从3523条元数据中，正有限N/C/D完整行{resources['numeric_complete']}；加入纯Language领域、生成任务、明确开放、2019以后且截至榜单终点、Token明文证据、无冲突单位、无基模型/持续训练、无稀疏专家线索、Confident/Likely条件后有{resources['candidate_n']}条候选。主比值门禁 $0.5\le C/(6ND)\le2$ 保留{resources['primary_n']}，放宽至[0.1,10]则{resources['loose_ratio_n']}条。`c4_resource_audit.csv`逐行保存源行、字段证据和多项剔除原因，`c4_usable_resources.csv`为可用表。

原始N为参数个数，D为Token数量，C为FLOPs；除以$10^9$才进入十亿单位。C4没有统一单位/架构列，因此只接受Dataset size notes明确Token且没有word/image/example/sentence单位冲突者，不作泛化词数换算；基模型缺失也不证明没有后训练，稀疏文字筛选也不保证全部为dense。数据表回溯修订及置信标签不是独立训练实验。

Epoch的计算字段可含基模型预训练，计算估计经常使用operation counting；因此接近6ND只作坐标一致性筛选，不能作为独立实验证明。参照 [Epoch估计文档](https://epoch.ai/data/ai-models-documentation/estimation)（2026-09-26查阅），不把Confident/Likely当能力预测置信区间，排除从Benchmark反推算力的估计方式。

完整年度中至少3条的2021--2024年资源90%分位拟合出 $g_C={resources['gC_log10_per_year']:.6f}$ decade/年，对应历史对照每年$10^{{g_C}}={10**resources['gC_log10_per_year']:.3f}$倍。2020只有1条不拟合，2025是未完整年。参数、数据各自年度分位不是同一个模型的配置，不能把两项分位相乘冒充观测C。C4回归 $\log C=a+c_N\log N+c_D\log D$ 的结果为 {np.round(resources['C_regression_intercept_logN_logD'],4).tolist()}，这是筛选后关联；因同源估计有循环性，不作机制识别。描述性N对C弹性为{resources['descriptive_N_on_C_elasticity']:.4f}，未来eta仍作为假设而非因果估计。

## 3. 有界能力动力学与规模/非规模贡献

定义 $z=\log[S/(100-S)]$（边界用0.001比例截断），两类分别拟合

$$z_i=a_k+b_{{N,k}}\log_{{10}}N_i+b_{{t,k}}t_i+\epsilon_i,\quad F(z)=100/(1+e^{{-z}}).$$

{coeff_table}

这是给定函数族的条件关联，不识别架构、数据工程、对齐各自独立因果效应。为得到可计算的动力学，局部前沿取每类近期两月实际综合得分的90%分位；N锚取这些高分模型的参数中位数。以实际高分位作锚，假设固定类别及评测坐标下未来曲线局部平移。它区别于平均能力，也不是世界最高分的绝对上限。

对早末两个月高分位配置，$u=b_N\Delta\log N$、$v=b_t\Delta t$，在有界分数上用对称两因素分解：

$$\Delta_N=\tfrac12\{{F(z_0+u)-F(z_0)+F(z_0+u+v)-F(z_0+v)\}},\quad \Delta_T=\Delta_{{model}}-\Delta_N.$$

相加严格等于模型的分数变化，避免分解顺序影响。再列$R=\Delta_{{observed}}-\Delta_N-\Delta_T$。题面所需两项账面分解为“规模关联项$\Delta_N$”与“非规模综合项$\Delta_T+R$”，后者包含未解释组成和选择效应，不能全部称纯技术进步。

{contribution_table}

相反方向的贡献导致带符号占比负值或大于100%，这有明确的账面含义，不截断也不伪装普通饼图。绝对值归一仅回答关联项幅度，不是因果技术占比。主chat/领域微调前沿上升但高分N缩小，时间项不能解释全部增益，未解释项较大；基础模型前沿下降也不证明真实训练技术退步。1/2/3月窗口、严格开放、许可证白名单及合并模型纳入对照见`historical_contributions.csv`。样本选择、N支持改变、任务版本和后训练都是替代解释。

## 4. 放缓情景的资源配置模型

以榜单观测终点{audit['forecast_origin']}为预测起点，未来H个月的资源情景为

$$\Delta\log_{{10}} C=s g_C H/12,\quad \Delta\log_{{10}}N=\eta s g_C H/12,\quad \Delta\log_{{10}}D=(1-\eta)s g_C H/12.$$

这三式使$C/C_0=(N/N_0)(D/D_0)$、$C_0=6N_0D_0$量纲闭合；不把算力增长直接当参数增长。主eta=0.5为N/D等比例配置假设，另取0.25/0.75压力分析；这是 [Chinchilla研究](https://arxiv.org/abs/2203.15556) 提供的候选配置思想，原研究在受控预训练、70M--16B及5--500B tokens上比较400余模型，不证明本题各种后训练模型的实际最优eta。这里用现有N锚与C4近期D中位数配对构造预算起点，该配对是资源情景，不是跨表实测模型。

前沿演化为

$$\widehat F_k(H)=F\{{\operatorname{{logit}}(F_{{k,0}}/100)+b_{{N,k}}\eta s g_C H/12+\lambda b_{{t,k}}H\}}.$$

取$s=1,0.5,0.25,0$分别为历史对照、增长减半、四分之一和停止。这里放缓的是对数增长率，不是直接把年度倍数除2。$\lambda=0.5$是主持续速度假设，0/1对应无新增时间进步/保持短窗斜率。C2缺D，故不凭空估计D独立影响能力的系数；D真实进入资源配置约束及外推支持检查。条件S随N的关联只在“未显式标定D效果”假设下使用。

{forecast_table}

12月终点2026-03-13，24月终点2027-03-13；不把当前系统日期作为观测起点。基础模型回测弱，主建议以chat/领域微调12月结果解释算力放缓影响，24月仅作进一步压力外推。主减半情景的模型内规模与非规模分数贡献可在`frontier_forecast.csv`的scale_points/non_scale_points追溯。

## 5. 时间验证、基线与不确定性

最初4个自然月份之后逐月扩展训练，测试月每类至少10条；训练去重在当时可见版本上进行，避免使用未来版本筛掉早期模型。每折资源数据重新按历史日截断。开发者及同名模型跨期重叠在CSV中报告，故不是独立新模型族检验。

| 主类别 | 月度诊断折 | 常数前沿RMSE | 月度90%分位趋势RMSE | 资源动力学RMSE |
|---|---:|---:|---:|---:|
| chat/领域微调 | {backtest['non_pretrained']['constant']['n']} | {backtest['non_pretrained']['constant']['rmse']:.3f} | {backtest['non_pretrained']['monthly_trend']['rmse']:.3f} | {backtest['non_pretrained']['resource_dynamic']['rmse']:.3f} |
| 基础预训练 | {backtest['pretrained']['constant']['n']} | {backtest['pretrained']['constant']['rmse']:.3f} | {backtest['pretrained']['monthly_trend']['rmse']:.3f} | {backtest['pretrained']['resource_dynamic']['rmse']:.3f} |

动态模型没有稳定胜过所有简单基线，更没有12/24个月真实覆盖率。基础模型不能据短窗结果宣称准确长期预测。模型优势与局限都进入正文，而不是只引用样本内拟合。

开发者为块bootstrap 200次，seed=20260926。固定情景的参数条件5--95%范围单独列；主情景范围把eta三值、lambda三值、资源增速0.5/1/1.5倍压力扰动的bootstrap分布5--95%范围扩展到包含常数/趋势、85%/95%前沿和1/3月锚窗口候选。该范围是**情景敏感性包络**，不是95%预测区间，也未完整覆盖未来随机冲击、任务版本改变及训练策略选择。每行另报告时间外推相对观测跨度及N/D超域距离。未来12/24月跨越短于9月训练窗，外推风险不能由有界sigmoid消除。

## 6. 分级Loss–Benchmark映射及误差传播

对每个可比等级建立显式候选

$$S=100\,\sigma(a+\gamma_L L+\gamma_N\log_{{10}}N),\qquad \gamma_L\le0\text{{的单调模型另作敏感性}}.$$

单变量模型与常数、Loss+N逐行留一比较，高可比7行独立于中可比68行拟合，不用任意0.35权重混合。分来源表保留原Loss_Source全文，别名与相邻版本合为report_family后整族留出，防止同一报告换名进入训练/测试两端；该分组不是验证集同坐标的证明。

{table(btable,['grade','model','n','rmse','r2'],['等级','模型','留一数','RMSE','R²'])}

高可比Loss与logN相关系数{bridge['high_loss_logN_correlation']:.4f}，解释同时控制N后Loss符号翻转的共线性；7行都是Pythia最终checkpoint，不是验证第二问的新独立数据。高可比Loss单变量斜率bootstrap5--95%为{np.round(bridge['high_loss_slope_bootstrap_p05_p95'],4).tolist()}，含接近零/正方向，常数基线误差更低。中可比Loss+N有一定样本内条件信息，但别名合并后的来源族留出RMSE={bridge['source_holdout']['rmse']:.3f}分；不能因此解除跨验证集可比性。

单调条件映射参数如下：

{table(pd.DataFrame(ms),['grade','a','bLoss','loss_min','loss_max','N_min_B','N_max_B'],['等级','a','γL','Loss下界','Loss上界','N下界/B','N上界/B'])}

只有明确声明“输入Loss与此等级C6坐标相同”的假设且在Loss/N支持内，才可计算上述换算；正式默认接口仍返回unidentified。映射局部误差按$\delta S\approx S(1-S/100)\gamma_L\delta L$，上游Loss区间不可用时不造联合CI；跨族残差分位仅作传递误差敏感性，不能伪称校准PI。模型形式可比常数/单调/Loss+N，方向与量级不稳就降低主张。

## 7. 与前三问的耦合及C8任务差异

消费CHM `integration/chm-q1-clean-20260923@{q3['commit']}` 的Q3 v8快照；该发布固定CYJ v8和Q1 v2，跨A/B映射本身也是条件假设。原始manifest和固定政策格分别保存为`upstream_q3_manifest.json`、`upstream_q3_fixed_policy_grid.csv`，逐字节核验生产者SHA256，未修改生产者文件。

36个预算×上下文×成本格经过high/medium两种映射门禁产生{q3['rows']}条记录，其中{q3['supported_assumption_rows']}条允许同坐标假设换算；越界/不可行者不给分数。输出`q3_bridge_sensitivity.csv`保留源状态、条件Loss、N、假设分数及medium来源族残差范围，实证标定分数和联合95%区间均为空。这满足前问输出进入后问的条件计算，同时避免把A侧目标Loss或半合成质量增益当真实Benchmark提升。

C8对1863目录选最新可解析JSON，1860个模型有24个BBH子任务，记录4个损坏JSON。宏平均中位数{c8['profiles']['bbhMacroMean']['median']:.3f}，任务间标准差中位数{c8['profiles']['bbhTaskSd']['median']:.3f}，最弱任务中位数{c8['profiles']['bbhTaskMin']['median']:.3f}。这说明同一模型平均分不能替代任务覆盖：宏平均最高四分位仍有{c8['low_min_high_mean_n']}个模型的最弱任务低于10分。C8 acc_norm×100是原始准确率尺度，C2可能另含榜单任务归一化，不把两者同名BBH自动相等；C8在这里用于任务差异描述，没有未经版本校准的跨表数值连接。

## 8. 适用范围与最终结论

本问已有非空、可复现的条件贡献、分级映射、算力放缓12/24月前沿及情景范围。资源增长减半降低了两类模型的条件能力前沿；这种差异依赖eta、时间进步保留比例、开放性和前沿定义。主chat/领域微调12月半增长点值约53.49，情景范围约40.41--65.96；基础模型范围宽且回测差，解释应更保守。

纯技术因果份额、跨附件Loss绝对坐标和长期未来覆盖率仍未识别。合法的最终答案是把可识别描述、声明假设的求解和未识别边界一并给出，不能宣称真实训练的无条件因果规律已被证明。最终状态：VALIDATED FOR STATED SCOPE（条件计算、数据追溯和复现；不包含因果识别、联合统计预测区间或main正式集成）。

## 9. 复现与产物

```text
node src/zhh/q4_analysis.test.js
python -B src/zhh/q4_complete.py
python -B src/zhh/test_q4_complete.py
python -B src/zhh/export_q4_answer.py
python scripts/build_safe_pdf_context.py --check
python scripts/check_ai_reading_rules.py
powershell ./scripts/verify_raw_data.ps1
```

代码依赖NumPy/Pandas；绘图另需matplotlib。当前环境和精确输入/输出哈希、种子、Q3来源SHA见manifest；论文MD、LaTeX和图的独立发布哈希见`answer_manifest.json`。原基线撤回预测保留在`outputs/zhh/legacy_baseline/`，不再覆盖当前发布。AI辅助用于审计、编码、诊断、图表和草稿组织；团队仍需核对并理解条件模型和最终提交表述。
'''
    # Replace rounded narrative examples with current generated values.
    ref=primary[(primary.type=='non_pretrained')&(primary.horizon_months==12)&(primary.scenario=='half_growth')].iloc[0]
    answer=answer.replace('约53.49，情景范围约40.41--65.96',f"约{ref.predicted_score:.2f}，情景范围约{ref.scenario_lower:.2f}--{ref.scenario_upper:.2f}")
    for target in [ROOT/'outputs/zhh/Q4_FINAL_ANSWER_V2.md',ROOT/'paper/sections/zhh/q4.md']:
        target.write_text(answer,encoding='utf-8',newline='\n')
    files=figures(f,c,annual)
    latex=latex_section(primary,cp,pp,r)
    tex=ROOT/'paper/latex/sections/zhh/q4.tex';tex.write_text(latex,encoding='utf-8',newline='\n')
    files+=[tex,ROOT/'paper/sections/zhh/q4.md',ROOT/'outputs/zhh/Q4_FINAL_ANSWER_V2.md',Path(__file__)]
    manifest={'schema':'zhh.q4.answer.v2','numerical_manifest_sha256':sha(OUT/'manifest.json'),
        'matplotlib':matplotlib.__version__,'command':'python -B src/zhh/export_q4_answer.py',
        'files_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},
        'PDF_status':'LaTeX source and figures supplied; no final competition PDF compiled by this Q4 task.'}
    (ROOT/'outputs/zhh/answer_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Generated Q4 final answer, LaTeX section, 3 figures, answer manifest.')


def latex_section(primary,cp,pp,r):
    forecast_lines=[]
    for _,row in primary[primary.horizon_months==12].iterrows():
        forecast_lines.append(f"{row['类型']} & {row['情景']} & {row.predicted_score:.2f} & [{row.scenario_lower:.2f}, {row.scenario_upper:.2f}] " + chr(92)*2)
    contribution_lines=[]
    for _,row in cp.iterrows():
        contribution_lines.append(f"{row['类型']} & {row.observed_change:.2f} & {row.scale_points:.2f} & {row.non_scale_points:.2f} & {row.unexplained_change:.2f} " + chr(92)*2)
    b=r['backtest']['summary']; bridge=r['bridge']
    shares='；'.join(f"{row['类型']}规模账面占比{100*row.accounting_scale_share:.2f}\\%、非规模综合项占比{100*row.accounting_non_scale_share:.2f}\\%" for _,row in cp.iterrows())+'。'
    section=r'''% Owner zhh; generated by src/zhh/export_q4_answer.py. Numerical source q4_v2/results.json.
\section{问题四：技术演进与算力放缓下的能力前沿}
\subsection{度量、开放性与数据角色}
综合能力为六项Benchmark百分制得分的等权平均，时间采用榜单提交日期。C2的2672条扩展开放记录按同名最新版本去重后为2616个模型，严格Epoch=yes集420个，允许性许可证标签白名单1718个。许可证与权重实际可得性尚未逐仓库核验，自定义许可者标人工复核。
主模型分别使用204个基础预训练模型和1620个chat/领域微调模型；44个持续预训练、742个合并、6个多模态条目只入扩展敏感性。C3的26条历史报告和4573条榜单数据仅做分来源/年度背景描述，不未经标定拼接异构评测曲线。

\subsection{资源字段审计}
C4的3523行中，正有限N/C/D完整案例850行。纯语言生成、明确开放、截至2025-03-13、Token明文证据、基模型/稀疏专家线索和置信条件筛选得96条候选；$0.5\le C/(6ND)\le2$门禁后81条，宽门禁93条。原始N为参数个数，D为Token数，C为FLOPs。无独立架构/单位列，故未确认单位者不换算；基模型缺失不证明没有后训练。
Epoch算力可能由同源N/D估算，6ND比值是质量筛选而非独立机制验证，文档见\url{https://epoch.ai/data/ai-models-documentation/estimation}。完整2021--2024年度资源90\%分位的对数算力年增长率为$g_C=0.690315$，2025部分年度不拟合增长。数据量实际进入年度资源分析和未来ND预算。

\subsection{有界动力学与贡献分解}
两类分别拟合$z_i=\log[S_i/(100-S_i)]=a_k+b_{N,k}\log_{10}N_i+b_{t,k}t_i+\epsilon_i$，边界比例截断为0.001。$F(z)=100/(1+e^{-z})$。局部前沿为近期两月实际S的90\%分位，以高分模型的N中位数作锚。
对于早末窗口，令$u=b_N\Delta\log_{10}N$、$v=b_t\Delta t$，对称分解为
\[
\Delta_N=\tfrac12[F(z_0+u)-F(z_0)+F(z_0+u+v)-F(z_0+v)],\quad
\Delta_T=F(z_0+u+v)-F(z_0)-\Delta_N.
\]
另列$R=\Delta_{\rm obs}-\Delta_N-\Delta_T$。规模关联与非规模综合项$\Delta_T+R$构成两项账面分解，非规模项包含选择、组成和未解释变化，不能全归于纯技术因果效应。
\begin{table}[htbp]\centering\small
\caption{早末两个月前沿的带符号分解（分）}
\begin{tabular}{lrrrr}\toprule 类型 & 观测变化 & 规模关联 & 时间关联 & 未解释 \\ \midrule
'''+'\n'.join(contribution_lines)+r'''
\bottomrule\end{tabular}\end{table}
ACCOUNTING_SHARES 贡献相反时带符号占比可负或超过100\%；绝对值份额只是幅度对照。1/2/3月窗口、严格/许可证/扩展口径均保存敏感性。数据未识别纯技术因果份额。
\begin{figure}[htbp]\centering\includegraphics[width=0.78\textwidth]{figures/zhh/q4_signed_contributions.png}\caption{规模、时间及未解释项；不是因果贡献图}\end{figure}

\subsection{算力放缓的条件预测}
起点为2025-03-13，未来H个月假设
\[
\Delta\log_{10}C=s g_C H/12,\quad
\Delta\log_{10}N=\eta s g_C H/12,\quad
\Delta\log_{10}D=(1-\eta)s g_C H/12.
\]
主$\eta=0.5$仅为N/D等比例配置假设，0.25/0.75为敏感性。Chinchilla的受控预训练实验提供候选配置思想（\url{https://arxiv.org/abs/2203.15556}），不保证本题后训练模型的最优配置。C2缺D，故不虚构D独立能力系数；D进入资源分配及支持检查。N锚与C4近期D中位数的配对是预算情景，不是实测跨表模型。
\[
\widehat F_k(H)=F\{\operatorname{logit}(F_{k,0}/100)+b_{N,k}\eta s g_C H/12+\lambda b_{t,k}H\}.
\]
$s=1,0.5,0.25,0$为历史对照、对数增长减半、四分之一、停止；主$\lambda=0.5$，敏感性0/1。以下是12个月条件计算，24个月压力结果保存在完整结果表。
\begin{table}[htbp]\centering\small\caption{2026-03-13局部90\%能力前沿的条件情景}
\begin{tabular}{llrr}\toprule 类型 & 对数算力增长 & 点值 & 情景范围 \\ \midrule
'''+'\n'.join(forecast_lines)+r'''
\bottomrule\end{tabular}\end{table}
\begin{figure}[htbp]\centering\includegraphics[width=0.95\textwidth]{figures/zhh/q4_frontier_12m.png}\caption{12月条件前沿，误差线为敏感性包络，非95\%预测区间}\end{figure}

\subsection{滚动诊断与不确定性}
最初4个自然月之后逐月扩展训练，当月测试至少10个模型；每折只采用当时可见的最新同名版本及C4历史资源。存在开发者/同名模型跨期重叠，附件已查看，故属于诊断而非最终盲测。chat/领域微调常数、分位趋势、资源动力学RMSE分别为
'''+f"{b['non_pretrained']['constant']['rmse']:.3f}、{b['non_pretrained']['monthly_trend']['rmse']:.3f}、{b['non_pretrained']['resource_dynamic']['rmse']:.3f}分；基础模型为{b['pretrained']['constant']['rmse']:.3f}、{b['pretrained']['monthly_trend']['rmse']:.3f}、{b['pretrained']['resource_dynamic']['rmse']:.3f}分。"+r'''
动力学未稳定优于简单基线，基础模型长期预测应保守。按开发者块bootstrap200次、种子20260926；固定情景参数5--95\%范围单列，主范围再传播eta/lambda/资源增速扰动并扩展到常数、趋势、85\%/95\%前沿与1/3月窗口候选。未校准未来覆盖率，不称95\%预测区间，也未覆盖任务版本改变和全部随机冲击。

\subsection{分级Loss映射及前三问耦合}
C6高可比7行与中可比68行分开，采用$S=100\sigma(a+\gamma_L L+\gamma_N\log_{10}N)$，另比较常数及$\gamma_L\le0$单调候选。高可比Pythia7行的Loss与logN相关系数为
'''+f"{bridge['high_loss_logN_correlation']:.4f}"+r'''，留一RMSE为常数0.426、Loss单变量0.538、Loss+N0.485分。高可比不是独立Q2验证。报告别名与相邻版本整族留出的桥接RMSE为
'''+f"{bridge['source_holdout']['rmse']:.3f}"+r'''分，跨验证集绝对映射仍未识别。
只有明确同Loss坐标假设且位于等级Loss/N支持内，才计算单调候选敏感性；正式默认返回unidentified。映射局部误差$\delta S\approx S(1-S/100)\gamma_L\delta L$；来源族残差分位是误差敏感性，不是校准区间。固定CHM Q3 v8精确SHA及输入哈希后，72条预算/上下文/成本×等级记录中33条可作同坐标假设换算，超域/不可行不给分数；生产者没有联合95\%区间，消费者也不补造。

\subsection{逐任务结果与边界}
C8的1863目录中1860个成功聚合24个BBH子任务，记录4个损坏JSON。宏平均中位49.401、任务间标准差中位16.934、最弱任务中位14.000分；宏平均最高四分位中仍有1个模型最弱任务低于10分。C8原始acc\_norm与C2榜单归一化尺度未直接拼接。C7的2048/8192/131072 Token保持Q3外生情景。
本问完成的是数据支持的描述与声明假设下的贡献、映射、资源放缓条件预测；不宣称纯技术因果效应、跨源绝对Loss坐标或长期预测覆盖率已经识别。完整答案、逐行审计、支持域、基线、敏感性和可复现哈希见\texttt{outputs/zhh/Q4\_FINAL\_ANSWER\_V2.md}及\texttt{outputs/zhh/q4\_v2/}。
'''
    return section.replace('ACCOUNTING_SHARES',shares)


if __name__=='__main__':main()
