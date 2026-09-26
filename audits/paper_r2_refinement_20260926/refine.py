from pathlib import Path
import json, re, difflib

REV=Path(__file__).resolve().parent
ROOT=REV.parent
names=['example.tex','chapter4.tex','chapter5.tex','chapter6.tex','chapter7.tex']
texts={n:(ROOT/n).read_text(encoding='utf-8') for n in names}
changes=[]

def replace(name,old,new,location,purpose):
    assert texts[name].count(old)==1,(name,old[:60])
    texts[name]=texts[name].replace(old,new)
    changes.append(dict(id=len(changes)+1,file=name,location=location,purpose=purpose,before=old,after=new))

def paragraph(name,start,new,location,purpose):
    old=next(p for p in texts[name].splitlines() if p.startswith(start))
    replace(name,old,new,location,purpose)

replace('example.tex',
    '该模型在 13 个验证域上的嵌套交叉验证 RMSE 中位数由线性岭回归的 0.4921 降至 0.4499，$R^2$ 中位数由 0.6056 提高至 0.6703，支持同规模下的配比预测。',
    '该模型在 13 个验证域上的嵌套交叉验证 RMSE 中位数由线性岭回归的 0.4921 降至 0.4499。',
    '摘要第一段','摘要保留误差改善，具体 R² 放在验证段')
replace('example.tex','后训练组短期回测的 $R^2=-0.7500$，故长期结果按条件情景解释。','',
        '摘要第二段','删除摘要中的负 R²，保留原有条件预测措辞')

paragraph('chapter4.tex','其中 $\\bar y$ 为对应评价集的观测均值',
    r'''其中 $\bar y$ 为对应评价集的观测均值，本文用于 MAPE 的观测值均为正。$R^2$ 以评价集均值预测为参照，观测方差为零时不定义。第一问分别计算 13 个验证域的指标，再报告其中位数；后续回测与来源内留出检验沿用相同定义。''',
    '4.3.2 指标口径说明','精简定义解释，保留参照、非零方差和逐域汇总口径')

old_diagnostic=next(p for p in texts['chapter4.tex'].split('\n\n') if p.startswith('表\\ref{tab:q1-r2-transfer}进一步检验'))
old_table=next(p for p in texts['chapter4.tex'].split('\n\n') if p.startswith('\\begin{table}') and 'tab:q1-r2-transfer' in p)
replace('chapter4.tex',old_diagnostic+'\n\n'+old_table,
    r'''在 256 个配方组成的同规模 1M 比较组中，$R^2$ 中位数为 0.6710，13 个验证域均为正，MAPE 中位数为 6.95\%，支持模型在该比较组中的配比预测表现。模型未对规模变化引起的 Loss 水平与幅度变化作校准，故不用于直接跨规模预测绝对 Loss；相应诊断见附录\ref{sec:appendix-q1-transfer}。后续绝对 Loss 的计算采用第二问的规模主干及明示的连接假设。''',
    '4.3.2 同规模验证与跨规模适用范围','正文保留同规模指标和适用边界，详细失配诊断移至附录 B')

paragraph('chapter4.tex','本问建立了 A1--A3 的质量评分',
    r'''本问建立了 A1--A3 的质量评分和 A4、A5 的配比响应代理模型。后者在 13 个验证域的交叉验证误差低于线性岭回归，并在给定比较组中表现出同规模预测与跨规模排序的有效部分；跨规模应用限于排序比较，不直接预测绝对 Loss。质量映射给出的配比仅为附件和模型支持范围内的条件候选；出现负 Loss 的无质量约束连续解及配方 136 仅作边界诊断。上述结果为后续标度律与资源配置提供输入，不能视为现实训练的最优配方。''',
    '4.6 本问小结','删除重复 R² 数字，保留同规模预测与跨规模排序的区别')

paragraph('chapter5.tex','为补充解释误差相对于数据波动的大小',
    r'''将每种留出方式的全部折外预测按原记录汇总，计算式\eqref{eq:prediction-metrics}的 $R^2$ 与 MAPE。留 $N$、$D$、$Q_B$ 水平的 $R^2$ 分别为 0.9793、0.9791、0.9794，MAPE 分别为 1.466\%、1.472\%、1.466\%，支持质量扩展在 B7 内部的预测稳定性。作为无质量项对照，直接将固定的 B1 主干用于 B7 的 450 条记录时，$R^2=0.6296$、MAPE 为 6.233\%；加入质量项后的全样本 $R^2=0.9797$、MAPE 为 1.456\%，表明质量项提供了额外拟合信息。上述检验对应 B7 半合成数据内部的质量关系，不验证 A/B 质量映射或含配比修正的四变量模型。表\ref{tab:q2-quality-models}仍报告逐折 RMSE 的平均值。''',
    '5.3.1 质量项验证','保留有效 R²、相对误差和基线比较，删除重复的汇总 RMSE 数字')

old=next(p for p in texts['chapter5.tex'].split('\n\n') if p.startswith('本问用 B1 同源训练轨迹估计'))
new=old.replace('B1 的 $R^2=0.999999816$ 只说明同源轨迹的近乎精确重构，B7 留水平的 $R^2=0.9791$--$0.9794$ 则支持半合成数据内部的质量项预测；二者均不构成四变量联合模型的真实外部验证。',
    'B1 与 B7 的验证分别支持同源规模关系与半合成数据内部的质量关系，尚不能代替四变量联合模型的真实外部验证。')
replace('chapter5.tex',old,new,'5.9 本问小结','小结归纳证据范围，不重复验证段数值')

q3=next(p for p in texts['chapter6.tex'].split('\n\n') if p.startswith('本问输出的是给定预算下的优化决策'))
replace('chapter6.tex',q3+'\n\n','',
    '6.6.2 数值求解的复算','删除整段关于不报告 R² 的说明，保留原有可行性、复算、敏感性和决策检验')

paragraph('chapter7.tex','表\\ref{tab:q4-backtest}与图',
    r'''表\ref{tab:q4-backtest}与图\ref{fig:q4-backtests}给出四个滚动窗口的结果。后训练组分位资源模型 RMSE 为 2.199 分，略低于均值资源模型的 2.237；相对预测时可用的历史常数基线 3.737 分，RMSE 降低约 41.1\%，MAPE 为 5.32\%。基础预训练组则以常数模型的 RMSE 7.633 分最低，MAPE 为 32.97\%。所选两组模型的测试 $R^2$ 分别为 $-0.7500$ 和 $-12.2321$，说明绝对预测误差相对于目标波动仍较大。$R^2$ 使用事后的评价集均值作参照，与预测时可用的历史常数基线不同，因此后训练模型相对历史基线的误差改善与负 $R^2$ 并不矛盾。由于回测仅有四个重叠窗口，下文的 12、24 个月结果作为资源假设下的条件情景，不据此主张长期预测准确。''',
    '7.3.1 前沿回测讨论','保留两组所选模型的真实回测限制，集中解释基线区别与条件预测')

old_q4=next(p for p in texts['chapter7.tex'].split('\n\n') if p.startswith('\\begin{table}') and 'tab:q4-backtest' in p)
new_q4=(ROOT/'r2_revision_20260926/original/chapter7.tex').read_text(encoding='utf-8')
new_q4=next(p for p in new_q4.split('\n\n') if p.startswith('\\begin{table}') and 'tab:q4-backtest' in p)
replace('chapter7.tex',old_q4,new_q4,'7.3.1 回测比较表','恢复简洁的 RMSE 比较表，R² 的必要信息集中在相邻讨论段')

old=next(p for p in texts['chapter7.tex'].split('\n\n') if p.startswith('综上，参数格标准化分解给出了'))
new=old.replace('后训练主模型在短期回测中优于历史常数基线，但 $R^2=-0.7500$，基础组所选常数模型为 $-12.2321$，因此资源情景模型只给出近期高分群的条件预测；',
    '资源情景模型给出近期高分群的条件预测，短期回测显示后训练主模型相对历史常数基线有误差改善，但长期精度仍需进一步检验；')
replace('chapter7.tex',old,new,'7.6 本问输出与结果讨论','删除重复的负 R² 数字，保留回测增益与长期使用边界')

appendix=r'''\clearpage
\section{配比模型跨规模绝对 Loss 的适用边界诊断}
\label{sec:appendix-q1-transfer}
\setcounter{table}{0}
\setcounter{equation}{0}
\setcounter{figure}{0}

本附录检查未经规模校准的 1M 配比模型是否能够直接预测较大规模组的绝对 Loss，用于说明第一问的适用边界。该模型只以训练配比为输入；这一检查不评价第二问含规模项的标度模型，也不构成对最终四变量模型的验证。

表\ref{tab:q1-r2-transfer}列出冻结 1M 模型在三组比较数据上的指标。1M 同规模组的 13 个验证域均有正的 $R^2$；直接用于 60M、1B 时，两组的 13 个域均为负，表明未经校准的绝对数值不能跨规模直接使用。

'''+old_table+r'''

模型未校准规模变化引起的 Loss 水平和幅度变化。例如，Pile-CC 在 60M、1B 中的平均预测偏差分别为 1.0621、2.5206，而观测标准差仅为 0.3138、0.1008。系统偏差相对于组内波动较大，因而产生显著负的 $R^2$。较高的排序相关与此并不矛盾：排序要求相对次序接近，绝对预测还要求数值吻合。因此，第一问的跨规模比较仅检验配方排序；后续绝对 Loss 采用第二问的规模主干及明示连接假设，本表不能验证跨附件相对配比效应的幅度。
'''
changes.append(dict(id=len(changes)+1,file='appendix_q1_transfer.tex',location='附录 B（新增）',
    purpose='保留完整失配诊断及解释，明确它不是最终模型的整体预测结果',before='（新增附录；原表及详细诊断位于 4.3.2）',after=appendix))
replace('example.tex',r'\input{appendix_q3_recipes}',
        '\\input{appendix_q3_recipes}\n\\input{appendix_q1_transfer}',
        '主文件附录入口','在配方附录 A 之后装配诊断附录 B')

for n in names:
    assert (ROOT/n).read_text(encoding='utf-8')==(REV/'before'/n).read_text(encoding='utf-8'),f'Concurrent edit: {n}'
    nl='\r\n' if b'\r\n' in (ROOT/n).read_bytes() else '\n'
    (ROOT/n).write_bytes(texts[n].replace('\n',nl).encode('utf-8'))
(ROOT/'appendix_q1_transfer.tex').write_text(appendix,encoding='utf-8')
(REV/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
diff=''.join(''.join(difflib.unified_diff((REV/'before'/n).read_text(encoding='utf-8').splitlines(True),
    texts[n].splitlines(True),fromfile='before/'+n,tofile='after/'+n)) for n in names)
diff+=''.join(difflib.unified_diff([],appendix.splitlines(True),fromfile='/dev/null',tofile='after/appendix_q1_transfer.tex'))
(REV/'refinement.diff').write_text(diff,encoding='utf-8')
assert '$R^2' not in texts['chapter6.tex']
assert '-506.7317' not in texts['chapter4.tex']
assert 'R^2' not in texts['example.tex']
print(f'Refined {len(names)} source files, added appendix B; {len(changes)} recorded changes.')
