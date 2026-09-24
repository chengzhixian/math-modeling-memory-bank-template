# chm 交接：Q1 可识别性重构（2026-09-24）

## 状态

完成 Q1 主模型、论文正文和生产者接口的严谨重构。工作分支：

```text
integration/chm-q1-rigorous-20260924
```

起点：

```text
integration/chm-q1-clean-20260923
87680947d16c9b8a486aea9b997c367e250ea0e4
```

本轮只修改 chm 归属范围，没有直接修改集成人维护的公共规则文件。

## 为什么重构

重新检查附件 A 的实际字段后确认：

- A4--A15 的配比表只有 17 域比例；
- 对应 Loss 表只有 13 个 target Loss；
- 没有与这些配方实验对应的 (D) 字段；
- 真实检验规模只有 1M、60M、1B 三个离散位置；
- 1M/60M 使用同一 256 配方，1B 使用另一组 64 配方；
- A6--A11 原本就是 A4+A5 冻结模型的 held-out 检验集。

因此旧 Q1 进一步拟合

[
L_k(N,mathbf p)=a_k(N)+b_k(N)s_k(mathbf p)
]

以及

[
log b_k(N)=c_k-etalog(N/10^6)
]

缺少充分的附件可识别性。旧 `eta=0.14503317` 及区间从 Q1 主模型和生产者接口撤出，仅保留历史审计。

## 当前正式数学链

### A1--A3：质量代理

列表字段按已核验数据卡语义压缩；A1 冻结稳健 median/MAD 标准化；8 个 model-based 指标作语义锚点，其余指标用域内 Spearman + Fisher-z 对齐方向。

综合量统一称为 A 侧质量代理 (Q_A)：

[
G_{ig}
=
operatorname{mean}_{jinmathcal J_{ig}}z^+_{ij},
qquad
S_i=rac13sum_gG_{ig},
qquad
Q_{A,i}=rac{S_i-mu_{S,A1}}{sigma_{S,A1}}.
]

家族等权是透明定义，不写成客观真值或附件唯一推导。

指标冲突主文只使用标准域内 Spearman：

[
ho_{jr,d}=ho_S(z^+_j,z^+_rmid d),
]

不再把自定义 (H_j) 或 (C_{jk,d}) 当必要主模型公式。

### A4+A5：逐 target 配比代理

[
mathbf p_{m ref}
=
rac1{512}sum_imathbf p_i,
qquad
mathbf1^	op(mathbf p-mathbf p_{m ref})=0.
]

对每个 target (k)：

[
(hatalpha_k,hateta_k)
=
argmin
sum_i
[L_{ik}-alpha-eta^	op(mathbf p_i-mathbf p_{m ref})]^2
+
lambda_k|eta|_2^2,
quad
mathbf1^	opeta=0.
]

(lambda_k) 只在 A4+A5 做 5-fold CV。

正式向下游提供：

[
m_k(mathbf p)
=
hateta_k^	op(mathbf p-mathbf p_{m ref}),
]

坐标：

```text
A4_A5_1M_target_cross_entropy_contrast
```

组成解释：从域 (r) 向域 (j) 转移 (delta) 时，

[
Delta m_k
=
delta(hateta_{k,j}-hateta_{k,r}).
]

不得解释单个 (eta_j) 为独立因果效应。

### A6--A11：只做排序验证

[
ho_{k,ell}^{m pred}
=
ho_S(
hat L_{k,1M}(mathbf p_i^{(ell)}),
L_{ik}^{(ell)}
).
]

13-target median Spearman：

```text
1M   0.8381
60M  0.8381
1B   0.7067
```

A6/A8 同一 256 配方真实 Loss 直接比较：

```text
per-target range: 0.9801--0.9980
median: 0.9944
```

这支持排序迁移，不支持连续幅度标定。

### A12--A15

10B/70B 均为 estimated/extrapolated，63 个配方均在 A4 train 中。只作压力测试。

## 绝对 Loss 诊断

完整 1M Ridge vs 无配比常数基线的 RMSE 中位数：

| 组 | Ridge | 常数 | 改善 target |
|---|---:|---:|---:|
| 1M | 0.4478 | 0.6759 | 13/13 |
| 60M | 1.4450 | 1.4724 | 13/13 |
| 1B | 3.2079 | 3.2514 | 4/13 |

因此正文明确把“排序迁移”作为主证据，不再把 1M 绝对 Loss 幅度直接外推。

## 修改文件

- `paper/latex/sections/chm/q1.tex`
- `paper/sections/chm/q1_draft.md`
- `problem/chm/20260924_q1_rigorous_restructure.md`
- `interfaces/chm/q1_interface_v1_2.json`
- `interfaces/chm/CONTRACT.md`
- `interfaces/chm/USAGE.md`
- `interfaces/chm/Q2_BRIDGE.md`
- `interfaces/chm/CYJ_REQUIRED_INTERFACE.md`
- `src/chm/q1_interface.py`
- `src/chm/test_q1_interface.py`
- `src/chm/q3_solver.py`
- `src/chm/q1_mixture_scale_transfer.py`（加历史诊断警告，不删除）
- `experiments/chm/20260923-q1-mixture-scale-transfer.md`（标记历史诊断）
- `memory-bank/members/chm.md`
- 本交接文件

## 接口版本

新接口：

```text
chm.q1.v1.2
```

核心状态：

```text
quality_coordinate = A_composite_quality_proxy_z
mixture_effect_coordinate = A4_A5_1M_target_cross_entropy_contrast
scale_transfer_status = not_identified_from_attachment_A
```

旧 v1/v1.1 保留追溯，但新消费不能默认读取旧 `scale`/eta。

## 对 cyj 的要求

若 Q2/Q3 要将 p 纳入 B-native Loss：

- 有可验证跨 Loss 数据时，cyj 自己定义并验证桥接函数；
- 没有可识别桥接时，使用 `p_policy.mode=sensitivity_only`；
- 不再要求 chm 给 eta；
- 不允许把 (m_k) 默认单位系数加到 B1 `val_loss`。

## 请求集成人更新公共规则

`TEAM_COLLABORATION_DEPENDENCIES.md` 当前仍要求 chm 交付“p 效应的跨规模传递及不确定性”，并把 `mixture_scale_transfer*` 列为正式产物。请集成人验收本轮重构后，将公共规则改为：

> chm 交付 A4+A5 的 1M target-specific (m_k(p)) 及 A6--A11 的排序迁移证据。任何跨规模幅度或 A→B Loss 坐标桥接由 cyj 在 Q2 中根据 B/跨附件证据识别；无法识别时采用 sensitivity-only，不人为制造 eta/lambda。

## 验证状态

底层 Q、Ridge 系数、参考配比和 held-out 数值均未重算；本轮变更主要是模型语义、数学可识别性和接口收敛。

需要在完整本地仓库环境复跑：

```powershell
python src/chm/q1_interface.py
python -m unittest discover -s src/chm -p 'test_q1_interface.py'
```

以及对 LaTeX 做静态/编译检查。若本次远程环境无法完整执行，应由接收者在合并前运行上述命令，不得把“代码已修改”写成“测试已通过”。

## 远端与测试补记

- GitHub 已确认本重构分支相对起点为 ahead、behind=0，且变更范围均在 chm 归属文件。
- 尝试在当前执行容器通过 `git clone` 拉取该远端分支并运行 `py_compile` / `test_q1_interface.py`，但执行环境 DNS 无法解析 `github.com`，clone 在代码运行前失败。因此本轮**不能宣称本地单元测试已通过**。
- 已通过 GitHub 连接器重新读取当前 `q1_interface.py`、`q3_solver.py` 和 v1.2 manifest 做静态一致性复核；Q3 中 A4 原始字段名也已修正为去除 `train_the_pile_` 前缀后再调用 Q1 接口。
- 合并前仍应在团队完整仓库执行：
  ```powershell
  python -m py_compile src/chm/q1_interface.py src/chm/q3_solver.py
  python src/chm/q1_interface.py
  python -m unittest discover -s src/chm -p 'test_q1_interface.py'
  ```

