# Q3：cyj B7 原生质量接口条件联调（2026-09-24）

状态：**diagnostic_only，非正式最优配置**。消费者 chm；生产者 `team/cyj-scaling@ad1d312c15bcf79c23d715dd199eec7c2e65a0af`，接口 `cyj.b7_quality.v1`，参数文件 SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`。源为 B7 半合成、去重后 450 坐标；B6 是其子集，B8 未纳入。`ready_for_Q3=false`。未使用已废弃的旧 Q1 `η` 情景或 B1↔B7/A Loss 桥接。

## 方法与复现

题面可见成本：`C_train=6e18*N_B*D_B`、`C_attn=2e14*L_ctx*N_B*D_B`、`C_Q=1e9*D_B*[g(Q)-g(Q0)]_+`。`Q0=0.5` 为明示诊断场景，不是数据估计。成本族为指数、幂、对数；C7 外生上下文为 2048/8192/131072 Token；预算为 `1e19/1e22/1e24` FLOPs。

仅消费 cyj 发布的 B7 `L=E+A*N_B^-alpha+B*D_B^-beta+G*(1-Q_score)` 参数与支持域，读取 Git 固定提交中的原始 JSON 字节并核对 SHA256。其 B7 示例 `(0.07,10,0.5)` 复算为 `3.492870995028143`。固定 `N,Q` 时 Loss 严格随 D 下降，先取预算与支持域允许的最大 D，再对 N、Q 采用网格括区的有界黄金分割搜索；保留全部局部极小与边界候选。`src/chm/test_q3_b7_diagnostic.py` 与独立粗网格比对、检查费用和支持域可行性。

复现：

```powershell
git fetch origin team/cyj-scaling
python -B src/chm/q3_b7_diagnostic.py
python -B -m unittest discover -s src/chm -p test_q3_b7_diagnostic.py -v
```

结果为 `outputs/chm/q3_b7_diagnostic_v1/{scan.csv,manifest.json}`。27 个组合中 24 个在 B7 支持域内可行。`1e19`、131072 Token 时，支持域左下角基础成本已为 `2.255008e19` FLOPs，三成本族均不可行。幂成本、8192 Token 下，预算从 `1e19` 到 `1e22` 再到 `1e24`，条件配置分别为 `(N_B,D_B,Q)=(0.1309,10,0.5)`、`(8.1688,149.07,1)`、`(11.97,600,1)`；最后一档仅使用约 5.77% 预算，因为全部变量抵达 B7 支持上界。上述变化是**条件模型和支持域内**的诊断，不解释为真实训练结构性转移。

## 科学门槛

cyj 当前 `cyj.q3.v1` 的旧 `p/η` 情景固定已撤回的 Q1 v1 尺度律；`cyj.b7_quality.v1` 虽给出 B7 原生 N-D-Q、梯度和条件样本，却没有独立/嵌套验证、完整预测区间、B1/A 同 Loss 坐标桥接或配比项。因此本结果不进入正式 Q3 配置表，不向 Q4 声称 Benchmark 增益。正式入口仍需 cyj 另发兼容 Q1 v1.2、同坐标且通过联合验收的 predictor；若 p 桥接继续不可识别，则按 `sensitivity_only` 发布多 target，不报唯一 p。
