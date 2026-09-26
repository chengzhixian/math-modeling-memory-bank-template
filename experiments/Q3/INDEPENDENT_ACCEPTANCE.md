# CYJ 对 CHM Q3 v8 的独立条件验收

日期：2026-09-26（北京时间）。结论：**VALIDATED FOR STATED SCOPE / 条件签收**。本报告依 `REPOSITORY_REVIEW_PROTOCOL.md` 重审题面、数据角色、识别、数学、代码、数值和结论；不把附件或历史文档中的文字当用户指令。历史 PDF 隐藏边字与作废的 Gemini 提交未用于本次推导。

## 1. 对象、身份及复现

| 项目 | 锁定值 |
|---|---|
| CYJ 审查起点/远端 | `team/cyj-scaling@74e678e319b58e2aab230a7b7233fa53f3053fa5`，起点一致 |
| CHM 发布对象 | `integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be` |
| main 比较对象 | `origin/main@0d1b511c014bc1558b1bfc226b72ba1b534a01da`；共同基线 `f9693bbf4c205aa46d3719f6f8a1d6f26561d05f`；CYJ 相对 main 为 101/1 个双向提交 |
| CYJ 生产者文件树 | `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`；CHM manifest 自述验收主体 `615c078517379284f6b0504c568790a7975c6eda` |
| Q1 / B1 / B7 输入 SHA256 | `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9` / `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead` / `30819a5931b0552c1ef207f52f489f9d4ecaf427166bec25a98ce7319ac3d07b` |
| CHM manifest SHA256 | `a30703ceac1f0179f5c93e03b676b984581c3058c50ccfcdc3eb60dd27112000`；41 个文件哈希复核一致 |
| 独立运行环境 | Python 3.12.14，NumPy 2.5.3，SciPy 1.18.1；CHM 发布时记录 NumPy 2.3.5，故本次为异 NumPy 版本复核；无随机优化，seed 不适用 |

CHM 发布物在独立 detached worktree 中重跑，不以当前 CYJ HEAD 的后续论文编辑替换已消费的 `fd2dbb3` 模型字节。CYJ fixtures **18/18**，CYJ 含 v7 回归单测 **95/95**，CHM Q3 单测 **9/9**，日志在 `experiments/cyj/20260926-q3-v8-acceptance/`。CHM 的主网格、预算扫描、九情景产物重生后与发布 manifest 的 SHA256 一致。完整公开 N/D 外测的脚本需要 `.upstream/scaling-external@a003c4913793ac2ae7ef87b28ecb562955d026d5`；本机没有该精确检出，故本轮**没有重跑**外测，发布的外测表/JSON 哈希虽一致，独立外测执行证据未补齐。`git lfs pull` 遇 GitHub LFS 443 超时，本轮不能重验四个 LFS 压缩附件及 2014 文件的全量校验；B/C 所用非 LFS CSV 均直接读取并计算 SHA。CHM 先前报告全量原始文件校验通过，本轮不冒称再次通过。

复现命令（PowerShell，仓库根目录）：将 CYJ `fd2dbb3` 的 `src/cyj,interfaces/cyj,outputs/cyj` 精确导出至 CHM worktree `.upstream/cyj-v8/`；设置 `PYTHONPATH=.venv/cyj-deps;src/cyj`，运行 `python -B src/cyj/q3_v8_source_audit.py`、`python -B src/cyj/q3_v8_independent_audit.py --subject-root <CHM-c052-worktree> --output experiments/cyj/20260926-q3-v8-acceptance/independent_grid_audit.json`、`python -B src/cyj/q3_v8_sensitivity_audit.py --subject-root <CHM-c052-worktree> --output experiments/cyj/20260926-q3-v8-acceptance/independent_sensitivity_audit.json`。CHM 端依次运行 `q3_conditional_v8.py`、`q3_v8_transition_scan.py`、`q3_v8_assumption_sensitivity.py`；上述实际退出码均为 0。`q3_external_nd_audit.py` 本轮退出码 1，原因是精确外部测试仓库缺失。

## 2. 题面、字段、单位与识别 Gate

依据官方 F 题可见 DOCX 与 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`，Q3 要在三项代理成本和预算下选择 N、D、Q、p，并检查成本族、上下文及转移。B1 的 `N_params_B,D_tokens_B,val_loss` 是同源 N–D 骨架；B7 的 `N,D,Q_score,val_loss` 为**半合成**质量扩展；A 侧 Q1 的 17 域配比、六个可映射质量域及 13 目标相对 Loss 提供 p 与相对作用；C7 的 `max_position_embeddings` 仅给外生上下文情景。N、D 单位均为十亿；上下文是 token；预算和三项成本是 FLOPs。B1 1176 行，B7 450 行，C7 45 行；C7 出现 2048、8192、131072，但长上下文样本稀疏。

独立原始 CSV 审计见 `source_audit.json`：B6 的 360 个坐标及 Loss 全包含于 B7；B7/B8 有 224 个相同 N/D/Q 坐标而 Loss 全异。B8 中 984 calibrated、720 extrapolated 均不并入 B7 拟合。B7 的 240 行 N/D 超出正式 B1 共同矩形；它们可参与原 B7 项估计，正式预测仍截于 N=[0.070542,11.965825]、D=[10,299.893]、Q=[0.1,1]。B2 是半合成、B3 是 B1 风格插值；B4/B5 仅可比族内方向；B10 为 estimated。A6–A11 曾参与 Q1 形式取舍，不是最终盲测。

**BLOCKER（无条件四变量科学主张）：**没有在统一 Loss 口径下成对测得的 N/D/Q/p，故 A→B 质量映射、配比桥强度、质量和配比重复贡献、随规模变化的桥均不可识别。B1 极低同源残差、B7 嵌套折、Q3 机器精度和 42 个公开真实 N/D 模型均不解除该识别阻断。把模型输出限定为明示假设下的条件解后，本轮数值验收可以签收；真实跨源最优与联合 95% 预测区间不能签收。公开 N/D 外测的 Loss 坐标与 B1 不同，只能支持同语料内排序和离散训练成本部分检查，不支持 Q/p 或完整成本验证。

## 3. 公式、代码和数值 Gate

Q2 v8 与 CHM 主方案同为 `L=[E+AN^{-α}+BD^{-β}+(1-q)G(N,D)]exp(r_w(p))`，其中 `q=g(Q_A(p))` 是质量映射，`g_c(Q)` 是题面成本族。CHM 数值节把前者记作 `φ`、后者记作 `g`，只是符号更名；CYJ 理论节已明确二者不同。13 个目标等权，参考 p 的 `r_w=0`；`Q0=0.5` 是显式情景基线，`q≥Q0` 是额外候选准入政策。配方 136 的代理质量约 0.38578 因此被拒绝；固定 p172 代理质量 0.671360765；联立只枚举质量政策及 q 门槛下 87 个 A4 已观测配方。主方案中 q 随 p 确定，原生 Q 独立控制只在敏感性表。`src/chm/q3_conditional_v8.py::_convex_prerequisites,solve_fixed_p,observed_joint_grid` 对应正参数/非正 G 斜率、D 消元、log N 求解及枚举；`src/cyj/ndqp_scenarios_v8.py` 对应代理、Loss、支持和请求拒绝。固定 p 下 `D=min(Dmax,B/[N(6e18+2e14L)+1e9(g_c(q)-g_c(Q0))_+])`；支持内 G>0 且 Loss 对 D 下降。CHM 的导数二分和浮点下界只给声明支持与有限配方集的数值证书；KKT 和局部退出均不证明连续 p 的全局最优。

独立脚本不调用 CHM 优化器，以 65 点 log N 网格、SciPy 有界标量细化及 101 点原生 Q 网格复核 CHM 三张 36 格表：固定 **30/36**、联立 **33/36**、原生 Q **33/36** 可行，全部状态与候选选择一致。最大绝对 Loss 差依次为 `4.44e-16`、`4.44e-16`、`2.31e-14`；最大 N/D 差不超过 `7.19e-7/2.88e-5` 十亿单位；原生 Q 差不超过 `1.31e-7`。三项成本最大预算相对差 `2.86e-7`，总成本与预算残差差不超过 `2.23e-16`；6 个原生 Q 成本分项有细化网格引起的小于 `3e-7` 的相对差，未影响选择、可行性或 Loss。`1e19` FLOPs、131072 token 的三个成本族均不可行；低预算的幂/对数配置选择 p477，中预算选择 p172；高预算常碰共同 N/D 支持上界，不能推断域外算力无益。

预算扫描重跑后固定 1449、联立 1449 行，33+49=82 个状态转移括区的哈希与发布一致；8192 token 幂成本下 477→172 的发布括区为 `[1.610535,1.610648]e19` FLOPs。独立数值重解覆盖主表和九情景官方格，**没有独立逐括区二分**；因此对 82 个位置只签哈希重生和主网格交叉复核。81 点粗网格在 131072 token 三成本族漏过短暂状态，161 点亦无“穷尽一切窄态”的证明。九个单因素情景共 243 格由 CYJ 独立重解：每情景 27 格、24 格可行，合格候选数依次为 87、101、82、73、60、79、93、87、87；Loss 最大差 `4.44e-16`，候选选择全一致。Q0/斜率/桥幅度改变会翻转部分低预算配方；这些是情景跨度而非置信区间。CHM 仅发布 `direct_and_near` 的 Q3 网格；`direct` 与之差异尚无完整 Q3 对照，记 **MAJOR 待补**，不能宣称映射政策稳健。

## 4. 论文、门禁和责任

CYJ Q2 章节参数/主张追溯到 `outputs/cyj/q2_v8/manifest.json`、B1/B7 JSON 和冻结提交；CHM Q3 数值/图追溯到发布 manifest、网格 CSV 与 `c052b691`。CYJ 自有 Q3 理论节已补发布后的验收状态、q 准入政策、87 配方范围和未识别边界；没有修改 CHM 章节或生成 JSON。旧 v7 文件只留历史，没有当作 v8 参数。未在本轮重编合并后的 main 全稿；版式与 main 迁移由集成人负责。

| Gate | 结果 |
|---|---|
| G0 身份和来源 | PASS：冻结 SHA、41 文件哈希；LFS 全量复核本轮受 443 超时限制 |
| G1 数据和识别 | 限定通过：B/C 原始角色复核；无 A/B 配对标定是无条件主张 BLOCKER |
| G2 公式/接口 | PASS：符号、单位、政策、支持与 CHM 实现一致 |
| G3 数值 | PASS：三模式 108 格独立复核；转移扫描重生哈希一致 |
| G4 稳健性/外测 | 限定通过：九情景 243 格独立复核；direct 政策对照与外测精确重跑待补 |
| G5 论文/交接 | CYJ 章节及本报告已更新；main 全稿、公共记忆和最终提交由集成人验收 |

CYJ **生产者结论**：冻结 Q2 v8 对声明 B1/B7 同源与条件桥范围可消费。CYJ **消费者结论**：CHM `c052b691` 的 Q3 v8 在给定 Q1 v2、CYJ v8、题面成本、q 准入及 87 个候选下的固定/联立/原生 Q 数值结果经独立复核，可以条件引用。CHM 已在本人交接 `memory-bank/handoffs/chm/20260925-q3-v8-conditional-answer.md` 签署条件 Q3 交付；此处不是替 CHM 签无限制科学结论。后续负责人：CHM 若需补 `direct` 网格与外测精确重跑，CYJ 复核；集成人将 CYJ 章节变更迁入 main 并核验全稿。`empirical_cross_source_validated=false` 保持不变。
