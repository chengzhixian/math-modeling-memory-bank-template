# cyj.b7_quality.v1：B7 原生质量诊断接口

生产者 cyj；消费者 chm/zhh。状态 draft，已完成本轮组级候选验证，但未经团队验收或真实跨来源验证；`ready_for_Q3=false`、`ready_for_Q4=false`。本接口与 `cyj.q3.v1` 的 B1/p 接口并列，**不是替换 B1 Loss 的新版本**。

## 调用及验收

```python
import sys
sys.path.insert(0, "src/cyj")
from quality_scaling import QualityPredictor
model = QualityPredictor(expected_sha256="e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025")
out = model.predict(N_params_B=0.07, D_tokens_B=10, Q_score=0.5, mode="diagnostic")
```

参数/验证/样本文件：`outputs/cyj/quality/b7_quality_fit.json`，SHA256 如上；代码/输入提交 `6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b`。消费者应固定发布 SHA，不用动态计算输入哈希替代验收。上述请求来自 B7 第 362 行（含表头），观测 Loss=3.568；预测为 **3.492870995028143**，软件验收绝对容差 `1e-8`，不是科学误差条。

| 字段 | 含义 |
|---|---|
| N_params_B / D_tokens_B | 十亿参数 / 十亿 token，支持矩形 N=[0.07,11.97]，D=[10,600] |
| Q_score | 文件原生 Q，范围 [0.1,1]，不接受 Q_z；不外推 |
| loss_coordinate | attachment_B7_native_val_loss，semi_synthetic；语料/tokenizer/log_base 未知为 null；B1_bridge 未建立、A_Q_mapping 未识别 |
| gradient | 分别对 N_B、D_B、Q 的解析偏导，单位按对应输入 |
| equal_loss_dN_dQ | −L_Q/L_N，固定 D 下局部等 Loss 替代率；不是预算最优替代率 |
| uncertainty.sample_ids / conditional_mean_samples | 50 个配对编号/预测；多个配置必须保持同一 sample_id 才能比较或传播相关性 |
| conditional_mean_percentile_95 | 固定模型族、B7 N,D 组重采样的近似 2.5%–97.5% 均值分位数；非总预测区间 |
| total_prediction_interval | null，未含模型选择、跨来源、配比和 Benchmark 误差 |

默认 formal 会拒绝；仅显式 diagnostic 可调用。非有限数、bool、支持域外值和错误文件哈希均拒绝。本版不接收 p，不能把 B1/p 输出直接加到 B7 预测上。矩形内未观测点是插值假设，不是新观测。参数文件只读取一次，批量使用应复用实例。

## 模型、验证与用途

选定 `L=E+A*N_B^-alpha+B*D_B^-beta+G*(1-Q)`。参数从文件读取；其中 G=0.36199528619528626、alpha=0.283217561405495、beta=0.29957529838453234。完整参数、每折训练/测试行号、来源哈希和环境都在 JSON。

N/D/Q 三轴留出平均 RMSE：无 Q 为 0.115812/0.118348/0.118794；线性 Q 为 0.058231/0.057091/0.057617；对数 Q 为 0.066081/0.065706/0.072320。三族各 24 折均收敛未触指数边界。候选按上述验证分数选择，**尚未进行嵌套独立测试**，不能将此当作无偏最终泛化误差。50/50 组级 bootstrap 接受，固定族条件区间不解决半合成依赖。

chm：可将 B7 原生 Q 与已有成本函数作明确标注的情景联调，读取梯度和样本；无验证桥接前不得用于正式 N-D-Q-p 联合优化。现有 B1/p API 仍拒绝 Q_score，不改变历史行为。

zhh：可消费带明确 Loss 坐标和来源的同编号样本，检查数据结构及误差传播代码；本版不输出 Benchmark，也没有证明该 Loss 可接入已有桥接。只有另行提供同坐标桥接及误差后才可组合，不能把这 50 个条件样本当作总能力区间。

B6 全部 360 行已包含在 B7，仅用 B7 的 450 行，避免重复计权；B8 两类全部排除，原因见 B8 审计。尚需：独立/嵌套验证，模型形式敏感性，跨附件 Q 与 Loss/p 标定，B1/B7 来源核实，B9/B10 外推讨论及团队验收。
