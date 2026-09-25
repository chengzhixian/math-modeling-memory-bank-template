# Q3 诊断基线：B1 N-D 解析优化与上游门禁

日期：2026-09-24（北京时间）  
角色：chm  
状态：diagnostic only，明确 `ready_for_Q3=false`

## 上游状态

本实验固定读取：

- cyj：`team/cyj-scaling@6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b`
- zhh：`team/zhh-frontier@d47cd2dc921333caecfcb95f09eb5a2f2714d0db`

cyj 已提供 B1 N-D predictor、三项成本、约束残差和显式 p 情景 API，但合同仍为 `ready_for_Q3=false`。主要缺口是 B-native Q 性能项尚未完成，B1↔B7 Loss 未桥接，A↔B Q mapping 未识别，p 的 primary anchor 与 `lambda_loss` 未标定。zhh 的 C7 CSV 已存在，但合同/成员记忆仍滞后。

因此本实验只验证 Q3 的 N-D 求解骨架。

## 解析基线

固定 Q=Q0、p=p_ref，则

[
L_0(N,D)=E+A N^{-alpha}+B D^{-eta}.
]

由于 `C_Q=0`，成本为

[
C(N,D;L_c)=
left(6	imes10^{18}+2	imes10^{14}L_cight)ND.
]

令

[
P=rac{C_{max}}{6	imes10^{18}+2	imes10^{14}L_c},
qquad ND=P.
]

忽略支持域边界时，一阶条件给出

[
N^star=
left(
rac{alpha A}{eta B}P^eta
ight)^{1/(alpha+eta)},
qquad
D^star=rac{P}{N^star}.
]

最终再与 cyj 声明的 B1 支持域
(N_Bin[0.070542,11.965825])、
(D_Bin[0.134,299.893])
做边界 KKT 检查。

## 诊断结果

- (10^{19}) FLOPs：2048/8192/131072 三情景均为支持域内内点，诊断 Loss 分别约 2.999、3.035、3.367。
- (10^{22}) FLOPs：2048 Token 的无约束解需要 (Dapprox311.6B)，超过支持上限，受限解落在 `D_max`；8192 和 131072 为内点。
- (10^{24}) FLOPs：三个上下文情景全部落在 `N_max,D_max`，只能使用约 2.3%、2.7%、11.6% 的预算。**这不是“高预算不需要更多算力”，而是 B1 已知支持域不足以支撑该预算的正式外推。**

这说明正式 Q3 必须把“预算可行”与“预测器支持域有效”分开报告。高预算下不能为了花完预算静默外推 B1 predictor。

## 输出

- `src/chm/q3_preflight.py`
- `src/chm/q3_nd_baseline.py`
- `outputs/chm/q3_nd_diagnostic.csv`
- `outputs/chm/q3_nd_diagnostic_manifest.json`

正式 Q3 前必须重新运行 preflight；只要 cyj `ready_for_Q3` 仍不是 true，正式求解器应拒绝生成论文最终配置。
