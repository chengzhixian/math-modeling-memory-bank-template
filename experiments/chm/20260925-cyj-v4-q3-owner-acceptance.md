# 2026-09-25 CYJ 最新协作与 CHM Q3 数值验收

## 排序及决策

1. P0：消费 CYJ v4 不可变发布 `3471530d91c8ee7eb709e5cd6c824eb9c423e0df`，解除 CHM owner acceptance 阻塞。远端审查头为 `2c237b3`。不覆盖 CYJ 文件、不合并全分支；运行时从 Git 对象临时加载发布并验哈希。
2. P0：保留已修复的发布 v2、显式支持域、归一化预算、相对 KKT；将当前候选切换为 v4 联合双交互模型。旧恒定 G 模型及其扫描只能作历史对照。
3. P1：复算 CYJ 330 个网格场景，新增 CHM 全局目标值界、连续预算加密/转移二分、嵌套支持域敏感性。复用 CYJ 的嵌套验证、模型族消融及独立 DE 证据，不重复拟合原始 B7。
4. P1：同步本人成员论文、图表与 PDF，交接验收和剩余限制；提交并推送本人分支。

## 审查发现

| 等级 | 问题、影响与处置 |
|---|---|
| MAJOR | 当前 Q3 章节仍以旧恒定 G 当主要接口。v4 已改为八参数联合拟合双交互，旧最优性推导不适用。新增独立 joint certificate 并在论文明确历史/当前模型。 |
| MAJOR | CYJ v4 等待 CHM 所有者消费验收。采用完整 commit 锁定、13 个 manifest 文件哈希及 3 个批量 fixture 原样比较；实际求解接入本人成员模块。 |
| MINOR | v4 固定 Q1 v1.2，当前 Q1 为 v1.3。实际比较两版 13 域系数及参考配方完全一致；B7 不调用 A 质量代理，因此 NDQ 和配比对比不受影响。A 质量代理有变，禁止把旧值称为当前 Q1；请 CYJ 下次版本更新元数据，不改写历史发布。 |
| MAJOR | 新模型短暂活跃集状态可能被稀预算网格遗漏。使用逐级加密，直到相邻分辨率的状态序列一致，再将转移括区细化到相对宽度 1e-5。只报告观测到的数值转移，不声称穷尽全部物理转移。 |
| BLOCKER（正式科学发布） | 半合成来源、历史全 B7 选族、区间未独立校准、A/B 和 Loss/Benchmark 桥接仍缺。维持 ready_for_Q3=false；数值签收不替代真实外测或总不确定性。 |

## 新模型数值界的独立论证

固定质量成本 q=a，允许的 D(N)=min(Dmax,C/(cN+h(a)))。设 x=ln N、y=ln D，则 y(x) 是凹函数。发布模型的 A,B,alpha,beta 均正，GN,GD 均非正，质量收益在矩形四角均正。对任意评价质量 b，N 项是 x 的凸函数，D 项是 y 的凸且递减函数，因此消去 D 后的目标关于 x 为凸；单调导数二分结合端点/折点取得全局最小值。用凸函数切线给出浮点下界，避免把近似最小值直接当下界。

对 q in [a,b]，更高质量成本只收缩可行域，更高评价质量只降低 Loss。因此 `min_N L(N,D_allowed(a),b)` 是整个质量区间的下界。按最低下界优先二分，直到可行上界减全局下界 <=1e-7。该结论仅适用代码检查过的符号/单调性前提，GN 或 GD 为正时直接拒绝，不对一般 Loss 宣称全局保证。保留浮点安全余量，未采用严格区间算术。

## 复现与证据

Python 3.12，NumPy（随运行时）、SciPy 1.18.1；本机独立依赖在仓库外 `H:/研究生数模/.q3-deps`。将其和 `src/chm` 加入 PYTHONPATH 后：

```
python src/chm/q3_b7_numerical_audit.py
python src/chm/q3_cyj_v4_acceptance.py
python -m unittest discover -s src/chm -p "test_q3_*.py"
```

当前机器结果以 `outputs/chm/q3_cyj_v4_acceptance/manifest.json` 为准；旧线性 G 对照为 `outputs/chm/q3_b7_numerical_audit_v2/manifest.json`。发布引用文件全部从 Git 精确提交取出；不读取隐藏 PDF 文字、不改写原始数据。结论等级为 **VALIDATED FOR STATED SCOPE**（条件数值验收），正式科学状态 **NOT READY**。

## 反事实与范围复核

- 简单恒定 G 与双交互存在相近 Loss、明显不同 N/D 的配置，故不把某个配置解释为稳定结构规律；CYJ 已提供四族消融，不在本轮另建复杂模型。
- 选族曾查看全 B7，嵌套留级与 bootstrap 不能回溯创造 untouched test。
- 同名 Q 不代表跨附件同量纲；A 描述性质量、B 原生 Q_score 与 13 域配比效应继续分离。
- 支持域上界造成高预算平台；不解释为真实算力无价值。参数不确定性、模型族不确定性与数值求解误差分开记录。
- CHM 可以独立完成数值验收；真实外测、跨附件映射和 Benchmark 桥接依赖数据源/团队及 ZHH。

## 审查门禁补充记录

冻结本地起点 `017c8d8`，存在本任务未提交的 Q3 代码/PDF及另一任务的换行等价 domain_mapping.csv；不覆盖另一任务成果。CYJ 与本分支 merge-base 为 `968ef7a36f1503aa222a0b09c8a8cb5d0f535ecd`，共同修改只有其 Q2/Q3 理论章节两处；不做整分支合并，避免覆盖论文所有者。本轮相对 main 的 CYJ 228 个变更文件中，重点检查新增 v4 接口、联合拟合/验证/不确定性、Q3 扫描和交接，不重复历史审计。

| 要求 / 符号 | 来源、单位、角色 | 可识别性与门禁 |
|---|---|---|
| N、D、Q、L | B7 supplementary_NQ_experiment_expanded.csv；十亿参数、十亿 token、原生 Q_score、val_loss；半合成拟合/选族 | 条件预测 identified within family；真实训练结构效应未识别 |
| E,A,B,alpha,beta,G0,GN,GD | 精确 v4 joint 模型、8 参数约束 SSE、同源 N-D 簇 bootstrap | 条件参数 weakly identified（A-alpha 强相关）；不作普适结构解释 |
| C、Q0、context | 可见题面成本及显式情景；FLOPs、0.5、Token | 情景输入，非数据估计；新增 7 个 context 不是 C7 观测 |
| p、13 target effect | A4/A5 1M Ridge；A6--A11 冻结排序检验 | A 内对比可用；跨 B Loss 换算 not identified |
| A/B、Loss/Benchmark bridge | 缺成对标定证据 | not identified，不生成默认系数 |

可信来源为当前可见题面、上述哈希锁定 B7/v4 与本地 Q1 v1.3。隐藏页边文字、隔离历史和受污染提交禁止使用。B6 与 B7 重叠不作为独立验证，B8 冲突数据保持隔离；本轮不重新划分或拟合，不引入 test 回流。文献函数形式只作候选，本次新增数值界来自显式凸性/单调性证明，不以文献名称替代适用条件。代码检查有限输入、边界、梯度、FLOPs 统一和正部成本，测试含单位缩放及解析极端情形。
