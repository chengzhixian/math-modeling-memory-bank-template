# chm 不确定性传播接口 v1.0

日期：2026-09-23  
状态：Q1 生产者侧协议；供 cyj/zhh 消费时逐项传播。

## 1. 不确定性来源

Q1 当前至少有五类不确定性，不能只传播单个 bootstrap 区间：

1. **质量指标定义**：列表压缩、Qurater 聚合、指标方向和 RPS/DSIR/model 家族权重；
2. **域映射**：7 个质量域到 17 个配方域只有 3 direct、3 near-direct、11 inferred；
3. **配比代理**：Ridge 的 CV 划分、target 选择和 held-out 误差；
4. **尺度传递**：公共 `eta`、域特异 `eta_k`、1B 配方支持集变化；
5. **跨附件桥接**：Q1 target Loss 与 B1 `val_loss`、A 侧 `Q_z` 与 B 侧 `Q_score` 的不可识别映射。

## 2. 下游必须区分的状态

每个下游输入都标记：

- `observed`：真实附件直接观测；
- `estimated`：由当前数据拟合；
- `conditional_interval`：条件于固定模型/口径的区间；
- `scenario`：缺少数据识别，只能设定情景；
- `unidentified`：不得给单一数值。

Q1→Q2 当前：
- 7 域 `Q_z`：`estimated`；
- `Q_z ↔ Q_score`：`unidentified`；
- 13 域 p→Loss Ridge：`estimated`；
- 主 anchor：`scenario`，等待 cyj Loss 口径确认；
- 公共 eta 现有区间：`conditional_interval`。

## 3. 建议的情景传播顺序

当 cyj/zhh 构造联合结果时，至少按以下层级做敏感性：

1. Q 定义：primary / 稳定方向过滤 / 家族权重扫描 / Qurater 分量标准化；
2. target anchor：主 target + 至少 3 个 direct/near-direct target；
3. eta：公共主值 + 条件区间 + 域特异范围；
4. 若存在跨 Loss 桥接系数 `lambda_k`：主值与可解释上下界；
5. 最后叠加 cyj 标度律参数不确定性和 zhh Loss–Benchmark 桥接误差。

最终区间必须注明覆盖了哪些层级，不能把只覆盖一层的区间叫“总预测区间”。

## 4. 机器可读输出约定

后续 Q1 稳健性结果统一放在：

- `outputs/chm/quality_review_v1/`
- `outputs/chm/local_recheck_v1/q1_regmix_cv_split_sensitivity.csv`
- `outputs/chm/local_recheck_v1/mixture_scale_transfer_v0_manifest.json`

若某文件尚未由完整本地数据实跑生成，消费者必须把对应层级标记为 pending，不得静默回退到旧网页缓存。
