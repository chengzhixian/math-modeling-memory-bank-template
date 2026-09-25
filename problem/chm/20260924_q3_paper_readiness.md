# Q3 数值章节阶段就绪说明

日期：2026-09-24。状态：章节结构与 diagnostic 证据可供集成人审阅；正式最优配置尚未生成。

已新增 `paper/latex/sections/chm/q3_numerical.tex`，对应 `main.tex` 已存在的 chm 数值章节入口。正文仅使用已经固定的 chm Q3 诊断证据：

- `outputs/chm/q3_regime_v1/`：连续预算相位与解析/数值交叉验证；
- `outputs/chm/q3_quality_cost_v1/`：三质量成本函数的纯成本几何；
- `outputs/chm/q3_p_validation_v1/`：held-out 配比选择验证；
- `outputs/chm/q3_solver_validation_v1/`：synthetic 软件验证，不作为科学结果。

Q3 文件自身静态检查通过：10 个 label 无重复、3 个 ref 均有定义、无嵌套 input、无 citation。当前网页环境未执行 XeLaTeX 全稿编译；集成人或 chm 本地环境合入后应运行 `paper/latex/check_draft.py` 和 XeLaTeX/BibTeX 全流程。

章节明确保留 formal TODO：只有 cyj 发布同一 B-native Loss 坐标的 validated N-D-Q predictor 且 preflight 通过后，才生成三预算×三上下文×三质量成本正式配置表。若 p policy=sensitivity_only，则只写多 target p 敏感性，不声称唯一 p。
