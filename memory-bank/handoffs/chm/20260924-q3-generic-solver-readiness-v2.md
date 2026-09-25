# chm 交接：Q3 generic solver / KKT / readiness v2

日期：2026-09-24  
状态：第三阶段工程完成；正式科学求解仍等待 cyj 上游。

完成：
- 通用 N-D-Q callback 求解器；
- SLSQP 多起点；
- active-set 变化检测；
- 内点边际比与上下界一侧 KKT；
- Q0 右导数处理；
- readiness v2；
- 8 个单元测试 + 15 个 synthetic KKT 点全部通过。

接口原则修订：
- A Q_z ↔ B Q_score 未识别本身不阻塞 B-native Q3；
- 但正式 predictor 必须让 N/D/Q 落在同一 B-native Loss coordinate；
- p 可采用 validated_bridge 或 sensitivity_only 两种正式政策；
- sensitivity_only 不允许发布唯一 p。

下一步：等待 cyj 实际 B7/联合 Q 模型发布；收到后先做 producer API 验收和 preflight，不直接跑论文结果。若上游仍未更新，可继续写 Q3 方法章节骨架和结果表模板，但不填 formal 数值。
