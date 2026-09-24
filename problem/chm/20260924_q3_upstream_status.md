# 2026-09-24 Q3 上游接口与当前可执行工作状态

角色：chm  
当前工作分支：`integration/chm-q1-clean-20260923`

## 1. 本轮读取版本

- main：`968ef7a36f1503aa222a0b09c8a8cb5d0f535ecd`
- chm clean：读取时 HEAD `b97d7a4c2e5bfbb8326e17b054518aefc22a01c6`，本轮继续追加 chm 自有提交
- cyj：`6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b`
- zhh：`d47cd2dc921333caecfcb95f09eb5a2f2714d0db`

main 公共记忆落后于最新 cyj 个人分支，且 zhh 个人合同仍滞后；正式公共状态应由集成人验收后更新，本文件只记录 chm 消费视角。

## 2. cyj 已经提供、chm 现在可以消费的内容

### 可用于工程联调

1. B1 经典 N-D predictor：
   [
   L_0=E+A N_B^{-alpha}+B D_B^{-eta}.
   ]
2. B1 支持域：
   - N=[0.070542, 11.965825] B 参数；
   - D=[0.134, 299.893] B token。
3. 题面三成本族和单位换算；
4. C7 外生上下文在成本中的位置；
5. 预算残差、p 单纯形残差、边际/KKT 定义；
6. p 的 target/lambda/eta 显式 scenario API；
7. 真实 B1 软件验收样例；
8. `outputs/cyj/interfaces/q3_bundle.json`，schema=`cyj.q3.v1`。

因此 chm 可以立即完成：
- Q3 solver 架构；
- 成本与约束单元测试；
- N-D 解析基线；
- 多预算/多上下文循环；
- 支持域边界报警；
- 显式 p 情景联调；
- readiness gate。

### 仍未达到正式 Q3 门槛

机器接口当前明确：

- `ready_for_Q3=false`；
- `Q_mapping_status=unidentified`；
- `primary_anchor=null`；
- `lambda_status=explicit_scenario_only`。

cyj 最新 `6c17cb4` 只新增 B7 原生质量候选代码和运行前协议，**尚未提交真实 `b7_quality_fit.json` 结果**。因此当前还缺：

1. B7 质量模型真实运行、候选比较、组级验证和 bootstrap 结果；
2. B7-native Q 性能模型的正式消费者版本；
3. B1 与 B7 的 Loss 坐标关系。若不能识别，应正式声明 Q3 使用独立 B-native 性能坐标/分层方案，而非假装同一 Loss；
4. p 的 primary anchor 或正式“多 target 情景”决策；
5. `lambda_loss` 的识别、范围，或正式确认只能 scenario；
6. 总预测不确定性；
7. `ready_for_Q3=true` 的生产者发布。

## 3. zhh 已经提供的内容

个人分支存在：

- `outputs/zhh/context_scenarios.csv`：
  - 2048 Token；
  - 8192 Token；
  - 131072 Token。
- Q4 基线和 Loss–Benchmark 弱桥接结果。

C7 可以作为 Q3 **候选外生情景**用于联调。

但 zhh 当前仍缺：

1. 更新后的 `interfaces/zhh/CONTRACT.md`；
2. 更新后的成员记忆/最新 main 同步；
3. versioned/manifest 化 C7 正式接口状态；
4. 若供最终 Q4 消费，机器可调用或机器可读的 Loss–Benchmark bridge 参数、输入范围和总误差协议。

因此 chm 暂时锁定精确 zhh commit 消费 C7，但不得写成 main 已联合验收。

## 4. chm 自身当前状态

### 已完成

- Q1 真实 A1–A3 全量质量分析；
- Q1 17 域配比与 13 target 跨规模验证；
- Q1 生产者接口；
- Q1 论文初稿；
- Q3 N-D 解析诊断；
- Q3 upstream readiness gate；
- 本轮新增跨平台 `chm.q1.v1.1`，修复旧 v1 CRLF/LF 哈希不稳定，不改变科学数值。

### 尚需完成

1. 本地/完整环境复跑 `chm.q1.v1.1` 新哈希协议测试并生成新的消费者验收记录；
2. Q3 数值 solver 与 scenario runner；
3. A4 支持域约束：p 不允许因线性模型直接跳到未经训练的单纯形极端点；
4. cyj 正式接口更新后重跑 preflight 并切 formal；
5. zhh 正式 C7 接口更新后替换临时锁定；
6. Q3 结果出来后交 zhh 做最终能力桥接。

Q1 尚有相关系数 bootstrap/多重比较、LightGBM 等增强项，但根据 `20260924_q1_readiness_review.md` 不阻塞 Q1 初稿和当前 Q3 主线。

## 5. 当前正式阻塞判断

**不阻塞 chm 继续工程工作：**
- Q3 solver 框架；
- N-D 诊断；
- p 显式情景；
- 成本敏感性；
- 支持域检查；
- 上游版本门禁。

**阻塞论文最终 Q3 最优配置：**
- cyj `ready_for_Q3=true`；
- B-native Q 性能项；
- p anchor/lambda 的正式科学处理；
- 生产者总不确定性；
- zhh 正式 C7 接口状态。

在这些门槛未满足前，任何数值均标 `diagnostic` 或 `scenario`，不得写作“最优资源配置结论”。
