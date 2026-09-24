# chm 可调用接口：cyj.chm.v2

入口 `src/cyj/chm_adapter_v2.py::CHMAdapter`；发布于 `team/cyj-scaling`。状态 **diagnostic_only**，支持 B7 原生 N/D/Q 求值、解析梯度、条件样本、题面成本、预算可行性以及独立 A 侧配比敏感性。已适配 chm `q1.v1.2`，不加载旧 eta 文件。正式 NDQ 验证仍未完成，`ready_for_Q3=false`；chm 正式发布 gate 应继续拒绝。

## 直接运行

在取得 cyj 发布提交和 chm 对象后运行（Python 3.12 + NumPy；本机 2.3.5）：

```powershell
git fetch origin team/cyj-scaling integration/chm-q1-clean-20260923
python -B src/cyj/chm_adapter_v2.py --describe
python -B src/cyj/chm_adapter_v2.py --request outputs/cyj/interfaces/chm_v2_request.json
python -B src/cyj/chm_consumer_smoke.py --release-commit <CYJ_RELEASE_COMMIT>
```

队友在本人分支使用独立 cyj checkout/worktree 或经集成人合并取得这些文件，不直接切换正在写入的 chm 工作区。`--describe` 给 17 域顺序、参考 p、13 target、支持域、Q/p policy 与上游 SHA。批量请求/响应样例分别为 `chm_v2_request.json`、`chm_v2_expected.json`。任一请求非法则整批退出码 2，stdout 为空，stderr 为 JSON 错误；严格拒绝重复 JSON 键、数值字符串、bool、非有限值、未知字段、formal 模式和支持域外点。

`chm_consumer_smoke.py` 要求传入发布交接中的精确 40 位 `CYJ_RELEASE_COMMIT`；它将本地代码/样例/manifest 对照该 Git 对象，核对机器清单内的逐文件 SHA，并实际调用 `value_grad` 与两条示例请求。

固定源：chm commit `a5525935b37f873235d2f650e4810a787b9a8788`、manifest 原始 Git SHA256 `5885317d072739b02cdbb434fc730dde07510eb284dc857e35863adc877e914d`；B7 fit SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`。Q1 通过其原生读取器核对 LF 规范化文件哈希及行数。所有源由固定 SHA 读取，不跟随浮动分支。

v2 加载器还逐一核对 chm 原始 Git blob 的 SHA256；七个消费文件的精确哈希写入 `chm_v2_manifest.json` 的 `chm_consumed_files_sha256`。若任一字节不符，直接拒绝加载。该 manifest 描述发布时的上游身份；本分支实际发布提交须以推送后 handoff 的 `CYJ_RELEASE_COMMIT` 为准。

## Python / 求解器入口

```python
import sys
sys.path.insert(0, "src/cyj")
from chm_adapter_v2 import CHMAdapter

model = CHMAdapter(mode="diagnostic")
value, (dN, dD, dQ) = model.value_grad(0.07, 10, 0.5)
N_bounds, D_bounds, Q_bounds = model.bounds
meta = model.capabilities()
out = model.evaluate(
    N_params_B=0.07, D_tokens_B=10, Q_score=0.5,
    Q0=0.5, context_tokens=2048, quality_family="exponential",
    budget_FLOPs=1e19, p=meta["reference_p"],
)
```

`value_grad` 满足 chm `LossModel` 协议，求导按输入单位；求解迭代时不重复计算 bootstrap。`evaluate` 返回完整诊断及配对条件样本。N/D 单位十亿参数/十亿 token；N=[0.07,11.97]、D=[10,600]、Q=[0.1,1]，矩形内未观测点为插值假设。Q0 显式提供、必须在 Q 支持域内，Q≥Q0；Q0=1 时应固定 Q=1，不使用要求 Q0<1 的 logistic 变换。`quality_family` 为 exponential/power/logarithmic，`context_tokens` 限 2048/8192/131072，预算单位 FLOPs。

**chm 求解器接入必须修改边界来源：**其 `q3_generic_solver.py` 当前 `solve_generic` 和 `active_set` 使用从 B1 引入的 `N_RANGE,D_RANGE`。请由 chm 同时改为接受上述 `model.bounds`（并把 Q 下界设为 Q0）；不能仅替换模型而保留 D_min=0.134。v2 会拒绝该越界点。先读取 `minimum_supported_cost_FLOPs` 判断预算是否在支持域内有解。数值边界容差由求解器处理，接口不静默截断/放宽支持域。本交付未运行 chm 的 SLSQP 优化（当前 Python 无 SciPy），未宣称已经完成预算优化联调。

## 返回字段及科学边界

| 字段 | 含义 |
|---|---|
| `prediction.loss_value` | B7 半合成原生 Loss；不等于 B1 或 A target Loss |
| `prediction.gradient` | 对 N_B、D_B、Q 的偏导 |
| `prediction.uncertainty` | 50 个同编号条件均值样本；总预测区间仍 null |
| `loss_coordinate`, `support`, `uncertainty` | 顶层机器字段，明确 B7 半合成 Loss、矩形边界与未量化的模型形式/跨源/预测不确定性 |
| `cost` | 三成本/总成本、左右 Q 导数、预算残差；题面公式 |
| `constraints` | N/D/Q 已在支持域、Q≥Q0、预算是否满足、最小支持成本及该预算下支持域是否非空 |
| `p_sensitivity.effects` | chm v1.2 的 13 维 1M centered target contrast；与 B7 Loss 分开返回 |
| `p_policy` | sensitivity_only；无唯一 p 最优结论、无 eta、无 lambda 或 B Loss 加法 |

p 可省略，此时 NDQ 求值无需 chm Git 对象。提供 p 时要求完整 17 域、非负、总和误差≤1e-6；不自动归一化。检查 simplex 不证明位于训练配方凸包，返回 `simplex_checked_training_convex_hull_not_checked`。chm 可把这些 13 维效应用于各 target/Pareto/明确权重的 A 侧敏感性，不将其追加到 B7 Loss。A_Q_mapping=unidentified **不阻塞 B-native 诊断**，p sensitivity-only 也是有效政策；当前 formal 阻塞在 NDQ 科学验证与联合验收，不在于必须人为完成 A↔B 映射。

顶层 `uncertainty` 明示 U1–U5：U1 仅固定 B7 constant-G 家族的组 bootstrap 条件均值；U2 模型形式、U3 预测残差尚未量化；U4 A/B/B1/B7 桥接不可识别；U5 zhh Benchmark 桥接未消费。`prediction_interval`、`cross_source_uncertainty`、`benchmark_bridge_uncertainty` 均为 null，调用方不得以条件均值区间代替总预测区间。完整审查见 `problem/cyj/20260924-uncertainty-scope.md`。

## 验收

```powershell
python -B src/cyj/build_chm_release_v2.py
python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
```

44 项测试通过，包含 3 维梯度差分、原生 Q1 v1.2 参考点与系数差、p 改变不影响 B7 Loss、低预算无可行支持、拒绝 B1 旧边界及旧 eta 参数、跨工作目录 CLI 及原子失败。实际调用 chm `evaluate_readiness` 验证：Q/p policy 被识别，正式 gate 仍因 producer ready=false、performance_status 和 joint_NDQ_status 非 validated 而拒绝；未绕过 gate。

验收样例 1：Loss=`3.492870995028143`，总成本≈`4.48672e18`，参考 p 的 13 项均为 0。样例 2（Q=.7 且 arxiv 增 0.01/freelaw 减 0.01）：Loss=`3.4204719377890855`，总成本≈`9.146799411773743e18`，预算 `1e19` 均可行。Loss 绝对容差 `1e-8`、成本相对容差 `1e-12` 仅用于软件复现。机器清单 `outputs/cyj/interfaces/chm_v2_manifest.json` 记录代码与样例哈希。所有优化结果须保留 diagnostic_only，直到新的验证版发布。
