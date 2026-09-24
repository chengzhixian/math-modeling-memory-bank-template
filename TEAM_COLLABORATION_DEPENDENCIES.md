# 三人分工、接口依赖与协作规则

更新时间：2026-09-23（北京时间）

适用项目：2026 中国研究生数学建模 F 题  
适用成员：chm、cyj、zhh  
状态：公共协作规范。用于约束三条个人分支之间的职责边界、接口交付、跨题依赖、验收与集成。

---

## 1. 总体原则

本项目采用“三条个人工作线 + 一个公共 main”的协作方式：

- `team/chm-data`：chm，负责 Q1 数据质量与配比，并负责 Q3 数值求解与 Q1/Q3 章节；
- `team/cyj-scaling`：cyj，负责 Q2 标度律、Q3 理论接口与 Q2/Q3 理论说明；
- `team/zhh-frontier`：zhh，负责 Q4 评测桥接、预测、C7 情景和论文公共章节/集成建议；
- `main`：只保存已经通过团队验收的公共规则、共享接口共识和阶段性稳定成果。

个人分支用于快速推进，`main` 用于全队共享和稳定集成。

任何成员都不得把“个人分支已 push”误写成“已进入 main”；“已备份”“已验收”“已集成”是三个不同状态。

---

## 2. 当前三条工作线

| 成员 | 主任务 | 后续任务 | 当前可独立推进部分 | 需要他人输入的部分 |
|---|---|---|---|---|
| chm | Q1 数据质量、指标冲突、17 域配比 | Q3 优化求解、预算扫描、Q1/Q3 章节 | A 数据审计、质量算法、配比模型、图表 | Q3 需要 cyj 的正式标度律；上下文情景使用 zhh 的 C7 |
| cyj | Q2 N-D-Q-p 广义标度律 | Q3 理论、目标函数、约束、边际替代关系 | B1 N-D 基线、B2–B5 验证、B 数据审计 | 最终 Q 和 p 必须接收 chm 正式接口 |
| zhh | Q4 Benchmark、桥接、能力预测 | 公共章节、集成验收建议、不确定性传播 | C 数据审计、C8 聚合、C7 情景、历史预测 | 最终能力映射需要 chm/cyj 的 Loss 与 Q3 优化结果 |

---

## 3. 已确认的三条核心依赖链

### 3.1 Q1 → Q2

Q2 不能只依赖附件 B 独立完成最终广义标度律。

chm 必须交付：

1. 质量评分 Q；
2. Q 的定义、尺度、方向和不确定性；
3. 7 质量域到 17 配方域的映射与映射置信度；
4. 17 维配比 p 的逐目标域 Loss 响应；
5. p 效应的跨规模传递及不确定性。

cyj 消费这些接口，但不得重新读取附件 A 后自行定义一套不同 Q/p。

### 3.2 Q2 → Q3

Q3 的真实优化结果必须建立在 cyj 已验收的预测接口上：

[
widehat L(N,D,Q,mathbf p).
]

在 cyj 尚未给出正式模型形式、参数、单位、有效范围和不确定性之前，chm 可以开发求解器框架，但不得使用占位参数生成论文最终结果。

### 3.3 Q1–Q3 → Q4

Q4 不能把 Loss 改善直接解释为 Benchmark 能力提升。

zhh 负责：

[
Loss ightarrow Benchmark
]

的桥接、误差量级和有效范围。

最终 Q3 的优化配置若要解释为能力变化，必须经过 zhh 的桥接和不确定性传播。

---

## 4. 当前必须联合解决的两个接口问题

### 4.1 Q 的尺度统一：chm + cyj

chm 的 Q1 主方案预计输出标准化质量指标，例如 `Q_z`；附件 B6–B8 的 `Q_score` 范围约为 0.05–1.0，属于半合成质量变量。

二者不能直接视为同一数值尺度。

因此 chm 与 cyj 必须共同冻结一个跨附件质量坐标，例如：

[
Q_A^ast=rac{Q_A-mu_A}{sigma_A},
qquad
Q_B^ast=rac{Q_B-mu_B}{sigma_B}.
]

也可以比较 quantile mapping、min-max mapping 等方案，但必须：

- 明确写出转换公式；
- 给出主方案和敏感性方案；
- 不把跨附件可迁移性假设写成观测事实；
- 记录 Q 的最终接口版本。

### 4.2 p 的 Loss 与 Q2 的 val_loss 口径统一：chm + cyj

chm 的 p 接口是：

[
widehat L_k(mathbf p),quad k=1,ldots,13,
]

即 13 个具体验证域的 Loss。

而附件 B1 只有一个泛化的 `val_loss` 字段。当前可见数据说明没有证明 B1 的 `val_loss` 等于 Pile-CC、arxiv、github 或其他任一具体域 Loss。

因此禁止未经验证直接写：

[
L_{mathrm{B1}}(N,D,Q)
+
Delta L_{mathrm{pile_cc}}(N,mathbf p).
]

chm 与 cyj 必须共同决定：

1. Q2 的 Loss 精确定义；
2. 哪个 Q1 target 可以作为主 anchor；
3. 是否需要使用多个 target 做敏感性；
4. p 项采用加法修正、有效数据量修正还是其他形式；
5. 该桥接在哪个 N/D/Q 范围内有效。

当前建议敏感性面板至少考虑：

- pile_cc：跨尺度预测最稳定；
- stackexchange：direct 映射中较稳定；
- arxiv：direct 映射且有 A2 扩展质量；
- github：direct 映射且有 A3 扩展质量；
- wikipedia_en：near-direct 映射且跨尺度稳定。

不得把任一 target 自动解释为“总体 Loss”。

---

## 5. 当前已确认无冲突的规则

### 5.1 C7 上下文长度

zhh 已从 C7 生成三个观测情景：

- low：2,048 Token；
- medium：8,192 Token；
- high：131,072 Token。

Q3 中这些长度作为外生敏感性情景，不作为连续内点寻优变量。

high 情景的支持模型较少，应视为高端情景，不与 low/medium 解释成同等典型。

### 5.2 estimated / extrapolated 数据

所有成员统一遵守：

- A12–A15：estimated/extrapolated；
- B10：estimated；
- B6–B8：半合成；
- 不能把上述数据改写成真实训练观测。

### 5.3 Loss–Benchmark

zhh 已发现桥接留出性能较弱，因此：

- 禁止写“Loss 下降 x → Benchmark 必然提升 y”；
- 只能给映射区间或不确定性分布；
- 超过桥接数据覆盖范围时不得作为主结论外推。

---

## 6. 重复工作的边界

为减少重复劳动，后续按附件划分权威责任：

- 附件 A → chm；
- 附件 B → cyj；
- 附件 C → zhh。

其他成员原则上只读取生产者的 manifest、接口和结果，不重新建立第二套清洗/审计逻辑。

允许的重复只用于独立核验，例如：

- 复核关键样本数；
- 复核接口单位；
- 复核主要结论；
- 复核论文关键数字。

不建议重复：

- 全量数据清洗；
- 完整模型拟合；
- 同一附件的第二套正式审计；
- 在没有接口冲突的情况下重做他人的主模型。

---

## 7. Q1 → Q2 正式合作流程

### chm 交付

至少包括：

- `domain_quality*.csv`
- `domain_mapping*.csv`
- `mixture_effect*.csv`
- `mixture_scale_transfer*.json/csv`
- Q/p 定义；
- 输入版本；
- 训练/验证/外推边界；
- 不确定性；
- 有效范围。

### cyj 验收

cyj 必须检查：

- Q 的尺度是否与 B6–B8 兼容；
- p 的 Loss target 是否与 Q2 Loss 口径可比；
- 17 域顺序；
- N/D/Q/p 单位；
- 是否存在信息泄漏；
- A12–A15 是否被错误用作训练。

验收后 cyj 在自己的接口中记录：

- 实际消费的 chm commit SHA；
- 接口版本；
- 文件 SHA；
- 采用的 Q mapping；
- 采用的 p anchor/sensitivity panel。

---

## 8. Q2 → Q3 正式合作流程

cyj 必须给 chm 一个可调用、可复现、带边界的预测接口。

最低内容：

- 数学模型；
- 参数估计；
- 参数单位；
- N/D/Q/p 的输入尺度；
- 有效范围；
- 验证误差；
- 参数不确定性；
- 至少一个真实测试案例；
- 独立复现命令。

Q3 不能从论文文字手抄参数，必须从 cyj 输出文件或预测函数读取。

chm 负责：

- 预算扫描；
- 约束求解；
- 可行性检查；
- 约束残差；
- 结构性转移；
- 上下文敏感性；
- 不确定性传播。

---

## 9. Q3 → Q4 正式合作流程

chm 向 zhh 交付：

- 预算情景；
- C7 上下文情景；
- 最优 N/D/Q/p；
- 预测 Loss；
- Loss 的置信区间；
- 求解状态；
- 约束残差；
- 所使用的 cyj/chm/zhh 接口版本。

zhh 再执行：

[
Loss
ightarrow
Benchmark
]

映射并传播桥接误差。

最终能力结果必须报告：

- 点估计；
- 置信区间；
- 上游参数不确定性；
- Loss–Benchmark 桥接不确定性；
- 是否超出桥接有效范围。

---

## 10. 三层不确定性传播

最终 Q3/Q4 至少包含三类不确定性：

### chm

- Q 评分；
- 域映射；
- p 系数；
- p 效应随规模衰减。

### cyj

- N/D/Q 标度律参数；
- 模型形式；
- 跨来源传递；
- 外推误差。

### zhh

- Loss–Benchmark 桥接；
- Benchmark 聚合；
- 时间预测；
- 场景不确定性。

推荐最终使用统一采样方式：

[
	heta^{(s)}sim P(	heta),
]

对每一组样本重新求解：

[
(N^ast,D^ast,Q^ast,mathbf p^ast)^{(s)}.
]

最终报告：

- 最优配置中位数；
- 95% 区间；
- 预算约束满足率；
- 结构性转移发生频率；
- Benchmark 区间。

---

## 11. 当前立即执行顺序

### chm

1. 在完整 Git LFS 环境运行 A1–A3；
2. 冻结 Q；
3. 更新 `interfaces/chm/CONTRACT.md`；
4. 与 cyj 联合确认 Q mapping 和 p→Loss 口径；
5. 等 cyj 预测接口后做 Q3。

### cyj

1. 不等待 Q1 全部完成，立即拟合 B1 的 N-D 基线；
2. 用 B2–B5 做验证；
3. 明确 B1 `val_loss` 的定义和有效范围；
4. 与 chm 冻结 Q mapping 和 p 接法；
5. 输出可调用的 `L(N,D,Q,p)` 接口。

### zhh

1. 更新自己过时的 `interfaces/zhh/CONTRACT.md` 和成员记忆；
2. 保持 C7 三情景为正式外生接口；
3. 保持 Loss–Benchmark 弱识别结论；
4. 等 chm/cyj 的正式 Loss 与 Q3 结果后传播不确定性。

---

## 12. main 与个人分支的同步规则

本文件属于公共团队规则，因此应放在 `main`。

其他成员无需放弃自己的个人分支。同步 main 的标准流程：

```powershell
git status
git fetch origin --prune
git switch team/cyj-scaling   # 或 team/chm-data / team/zhh-frontier
git pull --ff-only
git merge origin/main
```

如果产生冲突，立即停止自动操作，人工核对后解决；禁止使用 `reset --hard` 或整文件 ours/theirs 覆盖。

如果成员只想查看 main 的最新规则，而暂时不想合并：

```powershell
git fetch origin --prune
git show origin/main:TEAM_COLLABORATION_DEPENDENCIES.md
```

也可以比较个人分支与 main：

```powershell
git diff HEAD..origin/main -- TEAM_COLLABORATION_DEPENDENCIES.md
```

推荐规则：

- 每天开工前合并一次最新 `origin/main`；
- 公共接口规则发生变化后立即合并；
- 接收跨成员接口前先合并最新 main；
- 个人分支禁止长期脱离 main 多天工作；
- 不通过 rebase/force push 改写固定个人分支历史。

---

## 13. 最关键的团队共识

当前真正的跨团队瓶颈不是“谁做得慢”，而是以下三个接口必须统一：

[
Q_A 
otequiv Q_B,
]

[
L_{mathrm{Q1,domain}} 
otequiv L_{mathrm{B1}},
]

[
Loss 
otequiv Benchmark.
]

对应责任：

- 第一个：chm + cyj；
- 第二个：chm + cyj，优先级最高；
- 第三个：chm + cyj + zhh。

这三个接口一旦冻结，完整链路才成立：

[
oxed{
Q1
ightarrow
Q2
ightarrow
Q3
ightarrow
Q4
}
]

任何成员不得绕过接口，直接用另一附件的变量“看起来相似”就当成同一量。

## 2026-09-24 完整审查协议

根目录 `REPOSITORY_REVIEW_PROTOCOL.md` 已由用户授权为全团队公共强制规则。任何跨成员接口验收、分支审查、模型复核或“检查能否写入论文”的任务，都必须执行该协议，尤其不能跳过 variable provenance、identifiability、数据角色冻结、support/leakage、claim ladder 和从零 red-team。

跨成员依赖如果需要一个上游并未被数据识别的参数，必须把接口状态标成 unidentified / sensitivity-only，而不是要求上游为了下游方便补造参数。

