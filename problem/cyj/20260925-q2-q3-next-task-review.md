# CYJ Q2/Q3 下一任务清单审查（2026-09-25）

## A. 范围与状态

- 对象：`C:/Users/muyehuangyi/Downloads/CYJ_Q2_Q3_next_tasks_20260925.md`，SHA256 `21760d0f8c5ad65099fc23c50ca00007cb2ab43bc9845c642af3d1b4b817dabe`。
- 本地及远端 `team/cyj-scaling@86526a17d698e5fcc585f3099248bfa5a4ad28d8`；`main@90ac2d871c1f1bb5b2ff390c1da775a2f382a76e`，merge base 同 main，CYJ 分支 0 behind / 85 ahead。审查开始工作区干净，未见并行写入。未审查 CHM/ZHH 分支最新未合并工作。
- 可信依据：题面 DOCX SHA256 `bc99a72460fa3d947a442d502969a13212cebff3b55339da4c4`、可见数据说明 SHA256 `a681506d30ab7bf59b69916b83dda991c34e12cf60fa2b4430f1609a5bfab2b`、本分支 B/Q1 派生包、实验与输出。排除历史 PDF 隐藏文字、作废 Gemini 提交、旧 v1 eta 与未签收的正式结论。
- 只审查清单能否执行，未运行一键生成脚本或全套拟合。只读运行 v6 `--describe` 与 `test_q2_final_v6.py`：后者在授权读取本机依赖目录后 7/7 通过；常规沙箱内首次运行遇 `.venv/cyj-deps/numpy/__init__.py` PermissionError。没有据此重新声明所有结果已复现。

## B. 题面—数据—变量

| 要求 | 当前数据/字段 | 角色与限制 |
|---|---|---|
| Q2 经典 N/D | B1 `N_params_B,D_tokens_B,val_loss` | B1 同源真实记录；近确定性重构，生成/评估口径待证 |
| Q2 质量 Q | B7 `Q_score,val_loss` | 半合成 B 原生 Q；B6 与 B7 重叠，B8 冲突隔离 |
| Q2 配比 p | Q1 A4/A5 派生 512×17 配方与 13 target Loss；v6 只读派生包 | A 侧 target Loss 与 B7 `val_loss` 未配对；凸包只证 A 支持 |
| Q3 成本与上下文 | 题面三成本、C7 候选长度、显式预算 | 成本可计算；质量成本族、Q0、预算也是外生输入 |
| 大模型及外部验证 | B2/B3 形状、B4/B5 分层描述、B9/B10 估算压力 | 不能充当四变量联合模型的真实 held-out 验证 |

核心符号：`N,D` 是十亿计数，B1/B7 原生；`Q_B` 是 B7 半合成无量纲 `Q_score`，不等同 Q1 的 `Q_A`；`p` 是 Q1 派生的 17 维单纯形，Q1 观察/凸包支持不等于 B7 联合支持；`w` 是 13 target 显式情景权重；`lambda,eta` 是未识别的跨来源/规模情景参数；`L_ctx,Q0,quality_family,budget` 是外生成本情景。当前乘法桥接与四变量优化只在给定这些假设下可算，未有跨来源标定或独立实证验证。B7 的训练/嵌套留组只验证同源半合成候选；B10 estimated 不作测试。

## C/D. 发现与修订

### BLOCKER：P0-2 的脚本和验收说法不一致

`scripts/run_cyj_q2_final.ps1` 默认先执行 `src/chm/export_q1_q2_bundle.py`，读取原始 A4；`-SkipQ1Export` 才只消费派生包。该脚本只生成 Q2 V3 的 C1–C8、fixture 和 acceptance，不重建 11 项 `final_closure.json`。完整 `run_cyj_q2_closure.ps1` 又先执行两段 Q1 原始 A 导出。故按 P0-2 原样跑，既不能满足“运行时不重新读取原始 A”，也不能称 11 项刚刚独立重跑通过。修订：先校验已冻结两个 Q1 派生 manifest 和成员文件 SHA；Q2 阶段用 `-SkipQ1Export`，随后显式运行交互消费、facts、`final_q2_closure_check.py` 和单测；若需重做 Q1 导出，单独标注 CHM 上游阶段及 LFS/权限。检查所有输出 SHA、退出码与 `git diff`。重跑 C1–C8、11 closure 检查和 v6 fixture。

### MAJOR：P2-2 混用 v4 NDQ 和 v6 NDQp 的证据

`q3_joint_sweeps.py`、`q3_independent_optimizer_check.py`、`q3_form_sensitivity.py` 的优化变量只有 `(N,D,Q_B)`，成本与 CHM 旧求解器连接；它们的数值一致性不能证明 v6 的 `p` 凸包/质量约束、联合预算 KKT 或四变量全局最优。`test_q2_final_v6.py` 已对线性 p 子问题做 512 配方枚举与凸包 LP 对照，但只是给定 N/D/Q 和场景下的 p 子问题。修订：把旧产物明确作为 NDQ 基线；另写 v6 与成本的条件联调和四变量/固定 p 情景交叉检验。若按题面允许固定 p，必须明确选择理由；若声称联立最优，需检查联合可行性、边界和独立求解。重跑对应 Q3 求解测试，不复用旧 NDQ 数字宣称 v6 验收。

### MAJOR：P3-4 不能直接手改签收 JSON

`build_q2_final.py` 与 `final_q2_closure_check.py` 把 CHM 签收写为 `pending`；后者重跑会覆盖 `final_closure.json`，前者会覆盖 `acceptance.json`。P3-4 的“更新 acceptance.json”若只是编辑结果，下一次复跑即丢失，manifest SHA 也不一致。修订：先得到 CHM 独立分支、提交与运行证据；在 CYJ 所属的版本化签收记录中引用，再修改生成逻辑/发布版本并重建 manifest。`q3_conditional_interface_accepted` 仅在实际消费签收后置 true，科学 gate 保持 false。重跑生成器与状态一致性测试。

### MINOR：当前自描述与索引存在过时信息

v6 `--describe` 仍把交互候选写为 `not_callable_without_full_Q1_coefficients`，但单独的 Q1 interaction bundle 已含 130 条完整系数；实际不可调用原因是版本/CHM 签收未完成。`--describe.support.p` 仍称凸包未认证，v6 `evaluate` 已有凸包策略。`outputs/cyj/interfaces/q3_v1_status.json` 推荐 `cyj.chm.v2`，而当前 p 情景入口是 v6；`interfaces/cyj/CONTRACT.md` 仍以 v5 增补开头。修订 P0-3/P1-3 时同步版本索引、CLI 自描述和错误文案；保持 v4 已签收的 NDQ 条件接口为有效历史基线，不把它说成当前 p 接口。重跑 `--describe`、四 fixture 与现有单测。

### MINOR：P1/P2 的交付边界需写清

P1-2 的 v6 请求本身没有预算、Q0、成本族或上下文；预算检查需独立 `q3_costs.py`/CHM 求解器包装。P2-1 外生参数清单漏写 `Q0,quality_family,budget`。P1-4 的“CHM 独立 checkout 复现”只能列为 P3 外部验收，不能作为 CYJ 独立完成 P1 的条件。P1 四 fixture 的两个非法请求预期 exit code 为 2，不是 4/4 成功退出。修订消费者示例与验收措辞即可；重跑四个 exit code/JSON 对照。

## E. 判断与从零反证

状态：**NOT READY（不能原样直接逐项执行）**。按上述修订后，P0/P1 的 CYJ 自主交付与 P2 的条件理论/数值工作可开展；P3 需 CHM/ZHH 自行验收。Q2 `Q2_MODELING_COMPLETE_EXCEPT_PAPER=true` 仅限当前条件工程范围，`formal_scientific_ready_for_Q3=false` 必须保留。

从题面、B1/B7 表头及数据角色从零出发，最多可得到 B1 同源 N/D 关系、B7 半合成域内 N/D/Q 条件曲面、Q1 的 A 侧 p→target Loss 关系和给定桥接参数时的情景优化。没有配对的同定义 A/B Loss 或 Q 坐标观测，不能唯一识别 `lambda/eta`、`Q_A→Q_B` 或四变量绝对预测；数值优化/小残差不能把情景提升为实证最优。交互候选的 fitted-basis 符号不等于因果互补或 B7 可迁移效应。既有近精确 B1 重构、B7 同源留组、B2/B3 半合成/插值、B10 estimated 与 Q1 跨规模支持变化均不能替代缺失的联合 held-out。文献或题面允许的函数形式只给候选与成本定义，不为桥接参数提供识别。论文主张应停留在条件预测/敏感性，不宣称结构因果或支持域外泛化。
