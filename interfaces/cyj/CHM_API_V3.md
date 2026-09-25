# CYJ → CHM v3 条件接口（科学 gate 未开启）

`src/cyj/chm_adapter_v3.py::CHMAdapterV3` 固定 B7 双交互候选，提供 `bounds`、`value_grad(N_B,D_B,Q)`、`capabilities()`、`evaluate(...)`、`p_sensitivity(p)`、`elasticities(...)`、`substitution_rates(...)` 与 `prediction_interval(...)`。构造时必须显式使用 `mode="conditional_diagnostic"`。`schema_version=cyj.chm.v3`，`status=conditional_within_B7_pending_independent_test`，`ready_for_Q3=false`；`formal` 模式被拒绝。旧 v2 只供其原版诊断复现。

模型为 $E+AN^{-\alpha}+BD^{-\beta}+(1-Q)[G_0+G_N\ln N+G_D\ln(D/100)]$，N、D 单位分别为十亿参数、十亿 token，Q 为 B 原生无量纲分数，Loss 是 B7 原生 `val_loss`。范围 N=[0.07,11.97]、D=[10,600]、Q=[0.1,1]。`value_grad` 的梯度分别以 B Loss／十亿参数、B Loss／十亿 token、B Loss／Q 单位计。矩形内非观测点仍是插值假设；范围外一律拒绝。

`evaluate` 返回 B Loss、梯度、弹性、替代率、成本及预算约束；`prediction.uncertainty` 中区分条件均值分位区间、叠加 OOF 残差的经验预测分位区间与恒定 G 的点预测差。500 个 N-D 簇 bootstrap 与留 N 级 OOF 残差均来自同一半合成 B7，`calibrated_coverage_claim=false`。U4 跨来源和 U5 Benchmark 仍为 null。A 侧 p 只返回固定 CHM Q1 v1.2 的 13 target 敏感性，改变 p 不改变 B Loss；不使用 eta、默认 lambda、唯一 p 结论或 A/B Loss 数值相加。

## 可复现调用

```powershell
python -B src/cyj/build_chm_release_v3.py
python -B src/cyj/chm_adapter_v3.py --describe
python -B src/cyj/chm_adapter_v3.py --request outputs/cyj/interfaces/chm_v3_request.json
python -B src/cyj/chm_consumer_smoke_v3.py --release-commit <交接记录中的40位CYJ_SHA>
```

批量请求必须是 `schema_version`、`mode`、非空 `requests` 三字段；每条请求有唯一 `request_id` 与 `N_params_B,D_tokens_B,Q_score,Q0,context_tokens,quality_family,budget_FLOPs`，可另给完整 17 域 `p`。重复 JSON 键、未知字段、字符串数字、布尔值、NaN/Inf、越界点、负预算均拒绝。最低可行成本由 N、D 下界和 Q=Q0 给出；低于该成本是 `infeasible_by_supported_domain`。

## CHM 求解器 `Support` 包装

CHM `92e0592` 的 `solve_generic` 读取 `model.support`，且类型必须是 CHM 本人模块中的 `Support`；CYJ 的公开接口保持 `bounds`，避免导入 CHM 私有类型。消费者可在自己的分支写：

```python
from q3_generic_solver import Support, solve_generic
from chm_adapter_v3 import CHMAdapterV3

class CYJV3ForCHM:
    def __init__(self):
        self.upstream = CHMAdapterV3(mode="conditional_diagnostic")
        n, d, q = self.upstream.bounds
        self.support = Support(N=tuple(n), D=tuple(d), Q=tuple(q))

    def value_grad(self, N_B, D_B, Q):
        return self.upstream.value_grad(N_B, D_B, Q)

model = CYJV3ForCHM()
solution, trials = solve_generic(model, budget=1e22, context_tokens=2048,
                                 Q0=.5, family="exponential")
```

SLSQP 计算 `exp(log(bound))` 时可能产生机器精度级越界；CYJ 本地 27 场景测试仅在 `1e-12 × 上界` 内裁回边界，超出则报错。此数值容差应由 CHM 本人最终消费包装明确实现，不可放宽科学支持域。完整本地证据在 `outputs/cyj/interfaces/chm_solver_consumption_b7_candidate.json`：24 个可行收敛、3 个支持域不可行，24 个 KKT 必要条件检查通过。这个结果只证明软件调用成功；CHM 所有者尚须拉取精确 release 并提交 consumer acceptance。

冻结模型、验证、区间及接口文件的 SHA 由 `outputs/cyj/interfaces/chm_v3_manifest.json` 列出。发布提交的 SHA 在本交接及远端核对后提供。由于候选族在查看完整 B7 后提出，固定族重跑同源 CV 不构成未触碰最终测试，正式科学 gate 保持关闭。
