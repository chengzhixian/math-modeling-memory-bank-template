# Q2 核心实验记录

- [B1 经典 N–D 基线](B1_BASELINE.md)：原始 1,176 行、分组留出、token 尾部验证、M0 对照及复现命令。这是早期基线当时的状态；其参数随后被 v8 冻结采用。
- [v8 质量扩展与验证](QUALITY_EXTENSION.md)：固定 B1 主干、B7 半合成质量项、24 个留等级折、消融和质量桥敏感性。
- [v8 论文与数据完整审查](V8_REVIEW.md)：题面映射、变量来源、识别边界、公式与代码、数值、验证和 red-team。该审查写于 CHM 正式 Q3 消费之前，其中“Q3 待验收”是当时状态；后续 Q3 验收见 `experiments/Q3/REVIEW.md`。

两份原始 CYJ 记录来自 `team/cyj-scaling@74e678e319b58e2aab230a7b7233fa53f3053fa5`，其内 `outputs/cyj/...` 路径指向来源分支的全量发布包；main 精简文件在 [`outputs/Q2`](../../outputs/Q2/README.md)。正式 v8 数值生产者为 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`。
