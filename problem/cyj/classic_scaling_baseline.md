# 经典 N-D 标度律基线说明

状态：cyj 生产者侧 draft；已运行但未验证为 Q3 可消费 predictor。

## 模型与单位

模型为 `L(N,D)=E+A*N^(-alpha)+B*D^(-beta)`。N 使用十亿参数，D 使用十亿 token，L 仅指 B1 的 `val_loss`。在 B1 范围 N=0.070542–11.965825、D=0.134–299.893 内进行拟合；超出范围须显式标记外推。

复核后正式运行提交 `cf297a4ad47e235acf5a9b6e890a5df5e05b07e5` 得到 E=1.6898377713、A=0.3539687193、B=1.2402746295、alpha=0.3399854258、beta=0.2798924656。这些数值是 B1 上的点估计，不是全队已冻结参数。

## 数据与验证边界

- B1 共 8 个模型规模组，每组 147 个 checkpoint。各组在目标函数中总权重相等。
- 验证采用按规模留组与每组 token-tail 70/30；不使用随机逐行切分。
- 主拟合保留 8 个 C 恒等式 warning 行；后续显示精度诊断发现这 8 行均符合四位小数舍入，并另作剔除重拟合敏感性。原基线结果不追溯改写。
- B4/B5 的绝对 Loss 可比性为 `not_established`。其预测文件只作描述性排查，不得把 `predicted_loss-observed_loss_raw` 称为跨来源误差。
- B2/B3/B10 未被当作独立真实验证；B6–B8 的 Q_score 未用于本模型。

## 关键诊断

全样本 RMSE 0.0001465764，8 折 LOSO RMSE 均值 0.0001461277，token-tail RMSE 0.0001160041。三者均小于 0.001，已触发 near-exact reconstruction 警报。这种一致性可能表示数据共享确定性构造或强预处理；在来源机制核验前，不应解释为独立真实世界泛化能力。

机器可读结果见 `outputs/cyj/classic/classic_fit.json`，schema v2，SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`。该文件显式给出 `ready_for_Q3=false`，理由是 B4/B5 绝对 Loss 可比性、Q/p 标定和不确定性区间均未完成。

后续诊断 `outputs/cyj/diagnostics/b1_precision_sensitivity.json`（SHA256 `c7c8b346e4cdbec6034aead4f959ea7f60aa14b52ad6cd00169ea98033356fd7`）显示全部 1,176 行的显示计算量匹配 `0.006ND` 四位小数舍入；剔除 8 个相对 warning 行后，在全部行上的最大预测变化为 `7.6652e-06`。这缓解了计算量显示异常对五参数点估计的担忧，但并未解释 B1 Loss 近乎精确重构的来源；更不能把同源敏感性当作独立验证。

可见数据说明将 B1 归为 Pythia 训练轨迹；[EleutherAI Pythia 官方仓库](https://github.com/EleutherAI/pythia) 和[模型卡](https://huggingface.co/EleutherAI/pythia-70m)可供核对模型与公开 checkpoint 背景（2026-09-24 访问）。本地来源清单和目前的诊断尚无逐条 `val_loss` 评估记录、评测语料/分词器配置与 checkpoint 映射证据，不能据上述背景就确认 B1 的行级 Loss 来源。固定的低精度公式即使可贴近 B1，也是事后拟合参数的再表达，不是独立来源证明。

## 使用限制

本基线不能替代未来的 `L(N,D,Q,p)`；不能将 Q1 的 13 个 domain Loss 当作 B1 `val_loss`；不能将 B6–B8 的 Q_score 当作 Q_A；不能把 Loss 当作 Benchmark。向 chm/zhh 传递前需经接口验收并记录精确 commit、接口版本、文件哈希、单位、范围和状态。
