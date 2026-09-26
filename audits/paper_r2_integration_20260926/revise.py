from pathlib import Path
import json, hashlib, difflib, html

ROOT = Path(__file__).resolve().parents[1]
REV = Path(__file__).resolve().parent
changes = []
texts = {name: (ROOT / name).read_text(encoding='utf-8') for name in
         ['example.tex', 'chapter4.tex', 'chapter5.tex', 'chapter6.tex', 'chapter7.tex']}

def replace(name, old, new, location, purpose):
    assert texts[name].count(old) == 1, (name, old[:100])
    texts[name] = texts[name].replace(old, new)
    changes.append(dict(id=len(changes)+1, file=name, location=location,
                        purpose=purpose, before=old, after=new))

def paragraph(name, starts, transform, location, purpose):
    old = next(x for x in texts[name].split('\n\n') if x.startswith(starts))
    replace(name, old, transform(old), location, purpose)

replace('example.tex',
    '该模型在 13 个验证域上的交叉验证 RMSE 中位数由线性岭回归的 0.4921 降至 0.4499。',
    '该模型在 13 个验证域上的嵌套交叉验证 RMSE 中位数由线性岭回归的 0.4921 降至 0.4499，$R^2$ 中位数由 0.6056 提高至 0.6703，支持同规模下的配比预测。',
    '摘要第一段', '用同一验证口径下的 R² 与误差共同说明交互项的预测增益')
replace('example.tex',
    '并预测近期高分群。在算力对数增速减半的情景下，',
    '并预测近期高分群。后训练组短期回测的 $R^2=-0.7500$，故长期结果按条件情景解释。在算力对数增速减半的情景下，',
    '摘要第二段', '使摘要的长期预测主张与负 R² 的回测证据一致')

metrics = r'''为同时考察预测误差与相对均值预测的表现，对观测值 $y_i$ 和预测值 $\widehat y_i$ 定义决定系数与平均绝对百分比误差：
\begin{equation}
 R^2=1-\frac{\sum_{i=1}^{n}(y_i-\widehat y_i)^2}
 {\sum_{i=1}^{n}(y_i-\bar y)^2},\qquad
 \mathrm{MAPE}=\frac{100\%}{n}\sum_{i=1}^{n}
 \frac{\lvert y_i-\widehat y_i\rvert}{\lvert y_i\rvert}.
 \label{eq:prediction-metrics}
\end{equation}
其中 $\bar y$ 为对应评价集的观测均值；本文计算 MAPE 的观测值均为正。$R^2>0$ 表示平方误差小于事后用评价集均值作常数预测，$R^2<0$ 则表示未达到这一参照。该均值依赖评价集全部观测，不等同于预测时可用的历史常数基线。若观测值方差为零，$R^2$ 不定义。第一问对每个验证域分别计算指标，再报告 13 域中位数，不将不同域的 Loss 混合计算一个总体 $R^2$。后续回测与来源内留出检验沿用相同定义。'''
replace('chapter4.tex', '\\subsubsection{模型检验与外推分析}\n\n',
        '\\subsubsection{模型检验与外推分析}\n\n'+metrics+'\n\n',
        '4.3.2 模型检验与外推分析开头', '统一 R²、MAPE 的定义、均值参照和逐域汇总口径')
paragraph('chapter4.tex', '采用五折嵌套交叉验证比较模型',
    lambda old: old.replace('表明交互项有助于描述配比与 Loss 的关系。',
    '对应的折外预测 $R^2$ 中位数由 0.6056 提高至 0.6703，说明交互项在相同验证设计下提供了额外预测信息。'),
    '4.3.2 嵌套交叉验证比较段', '用同规模折外结果支持交互项增益，保留比较组参与模型选择的说明')

cross = r'''表\ref{tab:q1-r2-transfer}进一步检验冻结的 1M 模型能否直接预测不同规模组的绝对 Loss。1M 比较组的 $R^2$ 中位数为 0.6710，13 个验证域均为正，MAPE 中位数为 6.95\%，支持该模型在同规模比较组中的配比预测表现。直接用于 60M、1B 时，$R^2$ 中位数分别降至 $-8.3331$ 和 $-506.7317$，且两组的 13 个域均为负，说明绝对 Loss 的直接迁移失效。模型只以配比为输入，未校准规模变化引起的 Loss 水平和幅度变化；例如 Pile-CC 在 60M、1B 中的平均预测偏差分别为 1.0621、2.5206，而观测标准差仅为 0.3138、0.1008。系统偏差相对于组内波动很大，因而产生显著负的 $R^2$。这与下述较高的排序相关并不矛盾：排序只要求相对次序接近，不要求绝对数值吻合。因此，跨规模结果只用于考察排序迁移，后续绝对 Loss 的计算采用第二问的规模主干及明示的连接假设；本表也不能验证跨附件相对配比效应的幅度。

\begin{table}[htbp]
 \centering\small
 \caption{冻结 1M 配比模型的绝对 Loss 迁移诊断（各指标为 13 域中位数）}
 \label{tab:q1-r2-transfer}
 \begin{tabular}{lrrrr}
 \toprule
 比较规模 & 配方数 & $R^2$ & RMSE & MAPE\\
 \midrule
 1M（同规模） & 256 & 0.6710 & 0.4227 & 6.95\%\\
 60M（直接迁移） & 256 & $-8.3331$ & 1.4270 & 37.40\%\\
 1B（直接迁移） & 64 & $-506.7317$ & 2.9429 & 147.39\%\\
 \bottomrule
 \end{tabular}
\end{table}'''
replace('chapter4.tex', '进一步比较模型预测与各实验组实测 Loss 对配方的排序。',
        cross+'\n\n进一步比较模型预测与各实验组实测 Loss 对配方的排序。',
        '4.3.2 排序检验段之前，新增表 tab:q1-r2-transfer', '将绝对预测与排序迁移分开，用负 R² 解释尺度失配')
paragraph('chapter4.tex', '本问建立了 A1--A3 的质量评分',
    lambda old: old.replace('且在 1M、60M、1B 检验组较好保持配方排序。',
    '嵌套交叉验证 $R^2$ 中位数为 0.6703；1M 同规模比较组为 0.6710，支持同规模预测。60M、1B 的排序相关仍较高，但直接迁移的绝对 Loss 决定系数为负，故不据此主张跨规模绝对预测有效。'),
    '4.6 本问小结', '使小结同时反映同规模有效性与跨规模限制')

paragraph('chapter5.tex', 'B1 全样本 RMSE 为',
    lambda old: old.replace('B1 全样本 RMSE 为 $1.466\\times10^{-4}$；',
        '在 B1 的 1176 条记录上，全样本 $R^2=0.999999816$、RMSE 为 $1.466\\times10^{-4}$、MAPE 为 0.00409\\%；').replace(
        '上述低误差说明', '接近 1 的 $R^2$ 与极低的相对误差共同表明记录几乎被模型重构；这一结果也可能与附件的构造或预处理规律有关。上述指标说明'),
    '5.2.1 经典标度律拟合结果段', '说明近乎精确的同源重构，保留其不证明跨系统泛化的边界')
paragraph('chapter5.tex', '为检验质量项，分别留出一个',
    lambda old: old+'\n\n'+r'''为补充解释误差相对于数据波动的大小，将每种留出方式的全部折外预测按原记录汇总，计算式\eqref{eq:prediction-metrics}的 $R^2$ 与 MAPE。留 $N$、$D$、$Q_B$ 水平的 $R^2$ 分别为 0.9793、0.9791、0.9794，MAPE 分别为 1.466\%、1.472\%、1.466\%；汇总折外 RMSE 分别为 0.049041、0.049246、0.048919，与表\ref{tab:q2-quality-models}的逐折 RMSE 平均值口径不同。作为无质量项对照，直接将固定的 B1 主干用于 B7 的 450 条记录时，$R^2=0.6296$、MAPE 为 6.233\%；加入质量项后的全样本 $R^2=0.9797$、MAPE 为 1.456\%。全样本对照表明质量项在 B7 中提供了额外拟合信息，三个留水平结果则支持这一关系在该半合成数据内部的预测稳定性。由于 B7 并非独立真实训练实验，较高的 $R^2$ 不能证明 A/B 质量映射准确，也不能验证含配比修正的四变量模型。''',
    '5.3.1 质量项留水平验证段之后', '区分折外汇总与折均误差，以基线与留出 R² 支持半合成数据内的质量项')
paragraph('chapter5.tex', '本问用 B1 同源训练轨迹估计',
    lambda old: old.replace('B1 的低 RMSE 也只表明同源轨迹的拟合一致性。',
        'B1 的 $R^2=0.999999816$ 只说明同源轨迹的近乎精确重构，B7 留水平的 $R^2=0.9791$--$0.9794$ 则支持半合成数据内部的质量项预测；二者均不构成四变量联合模型的真实外部验证。'),
    '5.9 本问小结', '防止把组件的高 R² 解释为全链条已验证')

paragraph('chapter6.tex', '对固定配方、配比联立和独立质量三种方案',
    lambda old: old+'\n\n'+r'''本问输出的是给定预算下的优化决策，现有附件没有与完整 $(N,D,Q,\boldsymbol p)$ 配置对应的同口径真实 Loss，因此不报告四变量预测 $R^2$。独立复算误差衡量的是算法数值一致性，不能代替训练预测精度；决策质量则由预算可行性、求解上下界差、假设敏感性及观测决策后悔值共同评价。第二问的高 $R^2$ 只验证相应数据内的模型组件，不能直接证明本问资源配置在真实训练中最优。''',
    '6.6.2 数值求解的复算段之后', '解释 Q3 的评价对象，避免把复算一致性或上游 R² 作为实际最优证明')
replace('chapter6.tex', '观测 Loss 差为 0.0705。',
        '观测 Loss 差为 0.0705，即相对该组最低观测 Loss 的决策后悔值约为 2.51\\%。这一结果检验的是六组有限候选中的实际选择误差，不能解释为全部配置的命中概率。',
        '6.6.3 外部实验的排序检验', '补充实际决策后悔值，以适合优化任务的指标评价质量')

paragraph('chapter7.tex', '表\\ref{tab:q4-backtest}与图',
    lambda old: r'''表\ref{tab:q4-backtest}与图\ref{fig:q4-backtests}给出四个滚动窗口的结果。后训练组分位资源模型 RMSE 为 2.199 分，略低于均值资源模型的 2.237；相对预测时可用的历史常数基线 3.737 分，RMSE 降低约 41.1\%，说明其在这些窗口内提供了相对增益。但按式\eqref{eq:prediction-metrics}汇总四窗预测，$R^2=-0.7500$、MAPE 为 5.32\%，平方误差仍高于事后用四窗观测均值预测。两种参照使用的信息不同，故“优于历史常数基线”与“$R^2<0$”可以同时成立。基础预训练组以常数模型的 RMSE 7.633 分最低，但其 $R^2=-12.2321$、MAPE 为 32.97\%，仅表示它在候选中误差最小，绝对预测表现仍较弱。全部候选的测试 $R^2$ 均为负值，且四个窗口存在重叠；这些指标用于模型比较和误差诊断，尚不足以支持长期预测精度，故下文的 12、24 个月结果作为资源假设下的条件情景。''',
    '7.3.1 预测对象与模型比较结果段', '说明负 R² 与历史基线改善为何并不矛盾，并限制长期预测主张')
oldtable = next(x for x in texts['chapter7.tex'].split('\n\n') if x.startswith('\\begin{table}') and '\\label{tab:q4-backtest}' in x)
newtable = r'''\begin{table}[htbp]
 \centering\small
 \caption{最近两月能力前沿的四窗口滚动预测 RMSE（分）与 $R^2$}
 \label{tab:q4-backtest}
 \begin{tabular}{llrrrr}
 \toprule
 类型 & 指标 & 常数 & 两月趋势 & 均值资源 & 分位资源\\
 \midrule
 后训练 & RMSE & 3.737 & 3.053 & 2.237 & 2.199\\
 & $R^2$ & $-4.0520$ & $-2.3723$ & $-0.8114$ & $-0.7500$\\
 基础预训练 & RMSE & 7.633 & 9.571 & 9.763 & 10.561\\
 & $R^2$ & $-12.2321$ & $-19.8040$ & $-20.6451$ & $-24.3303$\\
 \bottomrule
 \end{tabular}
\end{table}'''
replace('chapter7.tex', oldtable, newtable, '7.3.1 表 tab:q4-backtest', '为全部候选列出负 R²，保持完整模型比较')
replace('chapter7.tex',
    'Qwen2 和 Qwen2.5\\cite{qwen22024,qwen252024} 的单调关系在各自来源内的留一误差小于常数对照，但样本分别仅有 4 和 6 条；Pythia 的 7 条记录在留一预测中反而略差。',
    'Qwen2 和 Qwen2.5\\cite{qwen22024,qwen252024} 的单调关系在各自来源内的留一误差小于常数对照，汇总留一预测的 $R^2$ 分别为 0.2071 和 0.9508，但样本分别仅有 4 和 6 条；Pythia 的 7 条记录对应 $R^2=-1.1865$，留一误差反而大于常数对照。因此，附件中的 Loss--能力预测关系具有明显的来源差异：Qwen2.5 的来源内预测较好，Qwen2 的解释能力较有限，Pythia 当前映射未显示预测优势。',
    '7.5.1 来源内单调映射及检验', '用来源内折外 R² 补充解释映射强弱，同时保留小样本和坐标限制')
paragraph('chapter7.tex', '综上，参数格标准化分解给出了',
    lambda old: old.replace('资源情景模型给出近期高分群的条件预测；',
    '后训练主模型在短期回测中优于历史常数基线，但 $R^2=-0.7500$，基础组所选常数模型为 $-12.2321$，因此资源情景模型只给出近期高分群的条件预测；'),
    '7.6 本问输出与结果讨论末段', '使最终讨论与回测证据一致')

for name, text in texts.items():
    baseline = (REV / 'original' / name).read_text(encoding='utf-8')
    assert (ROOT / name).read_text(encoding='utf-8') == baseline, f'Concurrent edit: {name}'
    # Preserve the original file newline style.
    newline = '\r\n' if b'\r\n' in (ROOT / name).read_bytes() else '\n'
    (ROOT / name).write_bytes(text.replace('\n', newline).encode('utf-8'))
    for change in changes:
        if change['file'] == name:
            change['line'] = text[:text.index(change['after'])].count('\n') + 1

(REV / 'changes.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
diff = ''.join(''.join(difflib.unified_diff((REV/'original'/name).read_text(encoding='utf-8').splitlines(True),
    texts[name].splitlines(True), fromfile='original/'+name, tofile='revised/'+name)) for name in texts)
(REV / 'paper-r2.diff').write_text(diff, encoding='utf-8')
print(f'Updated {len(texts)} source files, {len(changes)} changes; exact before/after stored.')
