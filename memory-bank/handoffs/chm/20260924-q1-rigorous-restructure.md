# chm 交接：Q1 严谨重构已融合至 clean 分支

日期：2026-09-24

用户要求所有后续 chm 修改继续维护在
\`\`\`text
integration/chm-q1-clean-20260923
\`\`\`
不再为同一工作流创建新的 Q1 临时分支。

本轮合并前已比较 clean 与临时 rigorous 分支：
- merge base：\`87680947d16c9b8a486aea9b997c367e250ea0e4\`；
- clean 有 7 个并发提交，主要是 Q3 预算/质量成本/p 支持域/发布器和 Q1 冲突复制性；
- rigorous 有 Q1 可识别性重构、多维 Loss、v1.2 接口和图表脚本更新；
- 两侧真正共同修改的文件只有 \`interfaces/chm/CONTRACT.md\` 与 \`memory-bank/members/chm.md\`，已人工合并；其余并发文件均保留双方版本。

科学变化：
- Q1 撤出旧 eta 跨规模幅度主张；
- 保留 13-target 1M Ridge 与 held-out 排序验证；
- 13 维 Loss 联立为 \(\mathbf m(\mathbf p)=\mathbf B(\mathbf p-\mathbf p_{\rm ref})\)；
- 新增交互矩阵、标量化、minimax、保护约束和 Pareto 决策框架；
- 决策域限制在 A4 观测配方凸包；
- clean 分支新增的冲突复制性证据一并保留。

Q1 正式机器接口为 \`chm.q1.v1.2\`。
