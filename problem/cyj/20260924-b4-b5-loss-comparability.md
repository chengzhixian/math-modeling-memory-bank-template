# B4/B5 与 B1 Loss 可比性审查（2026-09-24）

## 同坐标所需证据

| 项目 | B1 | B4 | B5 | 是否一致 |
|---|---|---|---|---|
| tokenizer | 本附件 Loss 管线未证；官方 Pythia 模型卡只能提供背景 | 跨 12 家族，未逐行注明 | 文献来源 6 类，未逐行注明 | unknown |
| validation corpus | 未注明 | 未注明 | 未注明 | unknown |
| loss definition | `val_loss`，题面称验证交叉熵；计算细节未证 | `val_loss` 列，跨族收敛点 | `val_loss` 列，文献整理 | unknown |
| log base | ppl 与自然指数相容，原评估管线未证 | 未注明 | 未注明 | unknown |
| aggregation | 未注明 | 未注明 | 未注明 | unknown |
| N unit | 10^9 参数 | 10^9 参数 | 10^9 参数 | 表字段单位一致 |
| D unit | 10^9 tokens | 10^9 tokens | 10^9 tokens | 表字段单位一致 |
| checkpoint semantics | 8 组各 147，D 与 step 可核 | 标记 `is_converged`，与 B1 逐行 checkpoint 身份未证 | `is_converged` + 文献来源 | unknown |

B4/B5 与 B1 虽都用 `val_loss` 列名，但没有 tokenizer、验证语料、对数底、聚合定义等同一评估坐标的证据。B4 中 8 个 Pythia 标称规模终点也没有可验证的 B1 行级 checkpoint 与评估管线配对。`same_loss_coordinate=not_established`，`formal_external_RMSE_allowed=false`。

## 支持域和数据角色

B1 拟合矩形：N=[.070542,11.965825] B，D=[.134,299.893] B。按原始 B4/B5 行逐行分类，代码及哈希见 `experiments/cyj/20260924-b4-b5-comparability.md`。

| 来源 | 行数 | 范围内 | 仅 N 越界 | 仅 D 越界 | 两者越界 |
|---|---:|---:|---:|---:|---:|
| B4 | 57 | 8 | 1 | 32 | 16 |
| B5 | 44 | 8 | 4 | 17 | 15 |

范围内也不意味着 Loss 可比较；范围外还叠加支持域转移。B4 的 12 家族/57 行和 B5 的 6 个文献来源/44 行保持来源分层，现阶段只可展示分层描述，不可池化出统一 external RMSE，更不能用于调整 B1 参数后再称外测。若未来取得逐来源评估口径证明，应先固定一致子集和支持范围，才重新设计独立验证。

## 判断

`descriptive_only=true`。与 B1 的绝对 Loss 可比性 **not established**；当前 B1 声明仍仅同源经验重构，B4/B5 不提供可宣称的真实外部误差。此结论与可见说明把 B4/B5 指为跨族/文献验证候选不冲突：赛题任务需要核查可比性，不能由用途标签自动推出同一损失尺度。
