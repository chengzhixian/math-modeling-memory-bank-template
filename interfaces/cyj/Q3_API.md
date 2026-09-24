# cyj.q3.v1：给 chm 的预测、成本及约束定义

状态：**可调用的诊断/情景接口；ready_for_Q3=false**。生产者 cyj；消费者 chm/zhh。采用 `chm.q1.v1`，固定 `integration/chm-q1-clean-20260923@7c14a0c894072048d09f04bd03653be1301f7257`。本文件逐项回应其 `CYJ_REQUIRED_INTERFACE.md`，字段缺证据时保留 null，不把接口可运行称作科学验证完成。

## 1. 已采用的 A 侧定义

直接调用该提交的 `src/chm/q1_interface.py::Q1Interface`，不重新拟合 A 数据。`load_chm()` 从本地 Git 对象读取生产者代码、manifest 及六个小型交付文件，在临时目录实例化原接口后立即清理，进程内复用对象；没有第二套永久系数表。队友首次使用先 `git fetch origin integration/chm-q1-clean-20260923`。

- 质量：7 域 A-native `Q_z` 和条件区间用于 A 侧描述/排序；17 域映射中 3 direct、3 near_direct、11 inferred。inferred 返回 null，`mapping_status=unidentified`，不生成完整 17 维质量向量。
- 配比：完整命名的 17 维非负 `p`，顺序以 `q1.reference`/bundle `adoption.domains` 为准，和在 `1±1e-6` 内；缺维、多维、非法和报错，不自动归一化。
- A 侧 `relative_effect(p,k,N,eta)` 已算 `m_k(p)*(N/1e6)^(-eta)`。cyj API 输入 N 为十亿参数，调用时乘 `1e9`，不再重复乘衰减因子。
- 采用敏感性面板 `pile_cc,wikipedia_en,arxiv,stackexchange,github`。B1 验证集未证同口径，`primary_anchor=null`。这表示采用生产者面板，不是宣布 pile_cc 为总体 Loss。
- chm 的 `observed/estimated/conditional_interval/scenario/unidentified` 分层继续保留。eta 点估计及条件区间可用于显式情景扫描；不替代跨 Loss 单位转换。

消费中发现：coefficients/reference/validation 三个 CSV 的清单哈希对应 CRLF，Git blob 为 LF。适配器只在 LF→CRLF 后**精确匹配原发布 SHA256**时恢复临时读取字节，否则失败；不重建或放宽生产者 manifest。bundle 同时记录 Git 字节哈希、生产者字节哈希和恢复规则。请 chm 在后续版本固定换行发布规范。

## 2. 预测入口、Loss 与 Q

```python
# 从仓库根目录运行，或将 src/cyj 加入 Python 模块搜索路径。
import sys
sys.path.insert(0, 'src/cyj')
from q3_interface import Predictor
model = Predictor()  # 校验固定上游及 B1 参数文件
book = model.q1.quality('book')  # A-native 描述性 Q
unknown = model.q1.mapped_quality('freelaw')  # inferred -> quality=None
out = model.predict(N_params_B=0.070542, D_tokens_B=0.134, mode='diagnostic')
```

参数文件：`outputs/cyj/interfaces/q3_bundle.json`。经典模型 `L0=E+A*N_B^(-alpha)+B*D_B^(-beta)` 的点估计、原拟合版本与完整 SHA 由该文件和既有 `classic_fit.json` 读取。B1 支持 N `[0.070542,11.965825]` B 参数、D `[0.134,299.893]` B token。

| 输入/输出 | 定义与检查 |
|---|---|
| `N_params_B,D_tokens_B` | 正有限数，单位分别 1e9 参数、1e9 token；越界须显式 `allow_extrapolation=True` |
| `mode` | 默认 `formal` 会报错；仅显式 `diagnostic` 或 `scenario` 可调用 |
| `Q_score` | 本版 B1/p 接口必须 null；有值即报错。B7-native 质量模型另行发布，不自动接入 B1；B6/B7 去重，B8 calibrated 和 extrapolated 均不进入当前共同拟合，不能用 Q_z 替代 |
| `p,target,lambda_loss,eta` | 仅 scenario 使用，四项全部显式给定；target 限上述五域，lambda、eta 在此情景族中为有限非负数，无默认值 |
| `loss_value,loss_coordinate` | B1 `val_loss`（题面定义为验证交叉熵）；评估语料、tokenizer、对数底、聚合口径未证实，分别返回 null；模型族标签 attachment_B1_Pythia |
| `gradient` | N_B/D_B 的解析偏导；`p_simplex_contrasts` 是单纯形配比对比导数，不是原始未归一化权重导数 |
| `extrapolation_flags` | 分别标识 B1 N/D 越界与 chm 非 1M/60M/1B 尺度；60M/1B 即使不标尺度外推也仍是条件 eta 情景 |
| `uncertainty.total_interval` | null；已有 B1 bootstrap 仅固定模型条件层，未包含跨 Loss、Q、p 支持域与 Benchmark 桥接 |
| `ready_for_Q3` | false；正式优化及科学意义上的验证仍待后续版本 |

真实验收输入来自 B1 第 2 CSV 行、sample `B1:0.070542:64`：N=0.070542、D=0.134、观测 Loss=4.7388；接口预测应为 `4.738637013477364`（跨机绝对容差 `1e-10`），拟合残差约 `-0.0001629865`。该容差只检查实现，不是观测误差条。命令：`python -B src/cyj/q3_interface.py --request outputs/cyj/interfaces/b1_example_request.json`。

B 侧质量与来源决定：采用文件原生 `Q_score`；B6/B7 保持半合成，B8 calibrated 984 与 extrapolated 720 分开，后者不得进入独立拟合/验证。B6–B8 与 B1 的 `val_loss` 也不能未经证据统一。**本版不交付已拟合 Q 项或 Q→N 数值替代量**；成本函数可接受 B-native Q 情景，不能据成本函数反推已验证性能。Q0 由调用者显式提供且标记 scenario，不从 A 侧 Q_z 自动取得。

## 3. p→B1 Loss 的情景定义

`L_B^(k)=L0(N_B,D_B)+lambda_loss*relative_effect(p,k,N_B*1e9,eta)`。

`lambda_loss` 的单位为 B1 Loss / A target Loss，当前不可由附件内配对样本估计；在同一情景内常数，作用于生产者**已经缩放**的 A 效应。eta 只描述 A 侧规模变化。lambda 的可信区间未知，不能填写为 `[1,1]` 或默认 1。参考 p 时修正严格为零；允许 lambda=0 作为“无跨 Loss 修正”情景。任一情景产生非正/非有限 Loss 即报错。p 是否处于训练配方凸包内尚未自动核验，返回的 chm `mixture_support_status=not_checked` 必须保留。

该式仅定义可复核敏感性，不宣称已经估计了完整 `L(N,D,Q,p)`。N 导数包含修正项 `-eta*delta_L/N_B`；D 导数为 `-beta*B*D_B^(-beta-1)`；从域 i 向 j 转移一个小配比的效应为 `lambda*(N_B/0.001)^(-eta)*(beta_kj-beta_ki)`。在固定 target 的线性 p 代理下，不能凭系数声称二阶互补；若无额外配比约束，线性单纯形优化易落顶点，须报告支持域风险。

## 4. 三项成本、约束与求解边界

`src/cyj/q3_costs.py::costs` 的参数为 `N_params_B,D_tokens_B,Q_score,Q0,L_ctx,quality_family,budget_FLOPs`。公式和数值直接来自可见 F 题 DOCX 问题三/附录 B，SHA256 `bc99a72460fa3d947a442d502969a13212ce0ea092d827afdbbf3b55339da4c4`，不来自隐藏 PDF 文本。

- `C_train=6e18*N_B*D_B`。
- `C_Q=1e9*D_B*max(g(Q)-g(Q0),0)`，Q/Q0 均在 `(0,1]`；同一个 D_B 用于全部成本。
- `C_attn=2e-4*1e18*N_B*D_B*L_ctx`；成本中的 `eta_attn=2e-4` 与 chm 的配比衰减 eta 是不同参数。
- 指数 `g=1e7*exp(6Q)`；幂函数 `g=5e9*Q^4`；对数 `g=2e9*ln(1+10Q)`。g 单位为每 token FLOPs；参数是题面给定，Q0 是显式情景。

`L_ctx` 只接受 zhh C7 发布候选 `2048,8192,131072`，来源分支 `team/zhh-frontier@d47cd2dc921333caecfcb95f09eb5a2f2714d0db`（CSV SHA `b494a8949a74133e779b683c8a46021b5e16308970150bd18e033553c6fc8608`），保持候选未联合验收标签。上下文只进入本版成本，不凭空改变 Loss；不参与内点寻优。临界长度由题面式得 `6/(2e-4)=30000` Token；该临界点不是新增可行情景。

算例 N=1B、D=100B、Q=Q0=0.5、L_ctx=2048：C_train=`6e20`、C_Q=0、C_attn=`4.096e19`、总成本=`6.4096e20` FLOPs。同 N/D 下三情景 attention/train 比为约 `0.0682667,0.2730667,4.3690667`。Q=Q0 时成本不光滑，返回左右 Q 导数；调用方不得把不存在的双侧导数当零。

条件优化目标为固定 k/lambda/eta/L_ctx 下最小化上述 Loss，约束 C_total≤budget、N/D 在声明支持范围、p≥0 且 sum(p)=1；Q 项未拟合时固定 Q=Q0，不对 Q 宣称性能寻优。预算为任意正有限 FLOPs，题面三档 `1e19,1e22,1e24` 可用于框架；高预算若最优落支持域边界只报告受限解，不能自动越界。`constraint_residuals()` 返回 `C_total-budget`（≤0 可行）、相对预算残差、`sum(p)-1`（=0）与非负性违反量。正式发布前由 chm 明确数值容差和完整可行性，不把预算一项可行等同全部可行。

边际效益采用 `-∂Loss/∂x`，弹性为 `-(x/Loss)*∂Loss/∂x`；内点预算分配比较 `(-∂Loss/∂x)/(∂C/∂x)`，边界用单侧/KKT 条件。未来可微 Q 模型的等 Loss 小扰动满足 `dN/dQ=-L_Q/L_N`，现在不代入虚构 L_Q。结构转移定义为预算连续扫描中的活跃约束/配比支持集变化或不同局部最优分支交叉；候选点须加密网格、多起点复核和参数敏感性确认，不能仅由三档成本份额不同宣布存在转移。

## 5. 验收与尚缺交付

`python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q` 覆盖真实 B1 输入、chm 发布例 `0.001309803924525102`、inferred Q null、非法配比/target/Q/范围、N/D 导数差分、三项成本和 Q0 拐点。测试覆盖软件及定义一致性，不补足科研证据。

| chm 请求 | 本版交付 | 剩余验收 |
|---|---|---|
| callable predictor、单位、实际样例、边界 | B1 diagnostic 与 p scenario、bundle、错误校验 | B1 行级来源、精确 Loss 口径、跨来源验证 |
| B-native Q 定义/基准/成本 | Q_score 坐标与分层规则、显式 Q0、三成本族 | B6–B8 质量项拟合与同尺度证据；本版调用拒绝 Q 输入 |
| p target/参考配比/接法 | 原生 chm Q1Interface、五 target、显式 lambda/eta | 主 anchor 与 lambda 配对标定；当前均情景 |
| Q3 目标/约束/边际/转移 | 上述定义及可调用成本/残差 | chm 求解器验收、zhh C7 正式验收、完整不确定性 |

定义职责已承接到 cyj；无证据的字段仍由 cyj 继续研究，不能请 chm 用默认值代填。公共状态由集成人验收汇总。
