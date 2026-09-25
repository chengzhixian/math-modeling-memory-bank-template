# CHM → CYJ / 集成人：v4 条件接口已签收

审查远端：`2c237b3c6c47133c85e64a50c8129c2a0a829bea`；实际消费发布：`3471530d91c8ee7eb709e5cd6c824eb9c423e0df`，manifest SHA256 `dcd50430b88cc754e1d8f43a3890013bcc45b07f877b315e9a812d2978fd41f7`。

## 结论

CHM owner acceptance 已完成，限定为 **条件 B7 NDQ 数值消费**。三个批量样例原样一致，13 个清单文件哈希一致；330 个上游场景复算，321 可行、9 不可行，最大 Loss 差 2.27e-12。33 个可行独立情景的全局目标值误差界 <=1e-7。正式 ready_for_Q3 仍为 false。

## 已完成的接续工作

- 发布 v2 已撤回 eta；我方模型支持域、预算归一化、解析梯度、KKT 相对残差及失败解拒绝规则已修正。
- 直接消费 v4 joint 模型，在本分支完成 1609 点预算扫描、41 个转移括区和 54 组支持域敏感性；2048/logarithmic 自动从 161 加密至 321 点。边界附近一个 SLSQP 失败点用独立带界降维求解，重新验 KKT，未冒充 SLSQP 成功。
- 与 CYJ 最新 33 个可行 DE 结果比较，最大 Loss 差 8.03e-09；复用其 144 行函数族消融，不重复模型拟合。
- 旧恒定 G 模型扫描作为明确历史基线保留；新模型采用独立凸性/区间下界论证，不能混用旧全局误差界。
- 已同步本人 Q3 LaTeX，当前 PDF 为 `paper/latex/output/chm-q1-all22-latest.pdf`；构建与视觉检查结果见对应 build.json。

## 请 CYJ 下一发布处理

v4 的 Q1 引用仍固定 v1.2。实际验证 v1.3 的 13 域配比系数、参考配方完全相同，故当前 NDQ 与配比对比可以消费；A 描述性 Q 已改变，不能沿用旧质量数值。请下一版本更新 CHM commit/schema/hash；不要原位改写 v4。可移除下一发布元数据中的“CHM owner acceptance pending”，但不得据此开启正式科学 gate。

## 仍需外部结果

真实训练独立外测、接口经验区间独立校准、A/B bridge，以及 ZHH 的 Loss--Benchmark bridge/误差传播仍未交付；保持显式空缺，不补造参数。CHM 可继续做条件诊断，但不得给出正式联合 N-D-Q-p 或 Q4 结论。

## 复现

`src/chm/q3_cyj_v4_acceptance.py` 一键运行本人消费验收；`src/chm/cyj_v4_consumer.py` 提供临时精确发布加载与 SolverAdapter；`src/chm/q3_joint_certificate.py` 给特定符号条件下的浮点全局值界。设置 PYTHONPATH 包含 src/chm 及本机 H:/研究生数模/.q3-deps，运行 Python 3.12。38 项 Q3 回归通过。详细审查、数学证明与数据门禁见 `experiments/chm/20260925-cyj-v4-q3-owner-acceptance.md`；机器结果/CSV 哈希见 `outputs/chm/q3_cyj_v4_acceptance/manifest.json`。
