# chm 交接：cyj 最新接口复核与 Q3 B7 条件联调

日期：2026-09-24。chm 分支 `integration/chm-q1-clean-20260923`；消费 cyj 远端 `team/cyj-scaling@ad1d312c15bcf79c23d715dd199eec7c2e65a0af`。数据说明仅使用可见正文 `problem/readable/DATA_DESCRIPTION_VISIBLE.md` 与题面可见成本公式，未消费历史隐藏文字。

## 本次变更

- 复核 cyj 最新接口：`cyj.q3.v1` 的旧 `p/η` 情景依赖 chm 已撤回的 Q1 v1 跨规模假设，现被 cyj 自身降级；B1 diagnostic 可单独复现，B7-native N-D-Q 可单独诊断，`ready_for_Q3=false`。B1/B7/A 的 Q 与 Loss 数值桥接、正式 N-D-Q-p predictor 和总预测区间仍缺。
- 新增 `src/chm/q3_b7_diagnostic.py`，读取并核对 cyj B7 参数文件 SHA，使用题面三类质量成本与 C7 外生上下文扫描 27 个预算情景，输出 `outputs/chm/q3_b7_diagnostic_v1/`；未使用旧 eta 或将 p 接到 B7。
- 更新 chm 第三问 LaTeX 数值章节和实验记录；新增 13×17 Ridge 作用热力图，修复 Q1 论文中的条件图片遗漏与 `check_draft.py` 多 citation 解析，重新编译 19 页草稿 PDF。

## 证据与复现

`python -B src/chm/q3_b7_diagnostic.py` 得 27 行，其中 24 行在 B7 支持域内可行。`1e19` FLOPs、131072 Token 的 B7 最小基础成本为 `2.255008e19`，因此三成本族均不可行。cyj 公布样例预测 `3.492870995028143` 精确复现。三项 B7 诊断单测、八项 Q1 接口单测和 LaTeX 静态检查通过；XeLaTeX/BibTeX/XeLaTeX 两次编译成功，PDF 中已确认新表与热力图。完整条件及局限见 `experiments/chm/20260924-q3-b7-native-diagnostic.md`。

## 未解决问题与责任

- cyj：另发兼容 Q1 v1.2 的预测接口，说明 B7 模型独立/嵌套验证、B1↔B7 Loss 可比性与总不确定性；若证据不足，保持 `ready_for_Q3=false`。
- chm：在正式 predictor 通过联合门禁后重跑三预算 × 三上下文 × 三成本，执行 KKT/多起点/支持域及模型参数敏感性；配比无同坐标桥接时只给多目标敏感性，不报唯一 p。
- zhh/集成人：确认 C7 外生情景，正式 Q3 输出进入 Q4 前另行验收 Loss→Benchmark 桥接。当前 B7 诊断表不可作为最终能力提升结论。
- Q1 本问内部交付已基本就绪；剩余主要是质量代理的主观权重、11 个 inferred 映射和跨附件桥接等已声明限制，而非允许填补的缺失参数。本次未改变 Q1 数值模型。
