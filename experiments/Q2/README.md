# Q2 核心实验记录

- [B1 经典 N–D 基线](B1_BASELINE.md)：原始 1,176 行、分组留出、token 尾部验证、M0 对照及复现命令。这是早期基线当时的状态；其参数随后被 v8 冻结采用。
- [v8 质量扩展与验证](QUALITY_EXTENSION.md)：固定 B1 主干、B7 半合成质量项、24 个留等级折、消融和质量桥敏感性。
- [v8 论文与数据完整审查](V8_REVIEW.md)：题面映射、变量来源、识别边界、公式与代码、数值、验证和 red-team。该审查写于 CHM 正式 Q3 消费之前，其中“Q3 待验收”是当时状态；后续 Q3 验收见 `experiments/Q3/REVIEW.md`。

两份原始 CYJ 记录来自 `team/cyj-scaling@74e678e319b58e2aab230a7b7233fa53f3053fa5`，其内 `outputs/cyj/...` 路径指向来源分支的全量发布包；main 精简文件在 [`outputs/Q2`](../../outputs/Q2/README.md)。正式 v8 数值生产者为 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`。

本次补入 B1 冻结拟合、B2/B3 和规模顺序的逐项验证、领域对参考点、B7 模型比较输入，以及 [v8 接口样例](../../interfaces/Q2/README.md)。现行主链在 main 的 `src/cyj/` 可运行；来源 `outputs/Q2/upstream_manifest.json` 是历史发布记录。由仓库根目录、Python 3.12.14 及 `scripts/requirements-integrated.txt` 中的依赖运行：

```powershell
python -B src/cyj/prepare_scaling_data.py
python -B src/cyj/fit_classic_scaling.py --output-dir data/processed/Q2/repro
python -B src/cyj/fit_b7_quality_extension_from_b1.py
python -B src/cyj/build_q2_v8.py
python -B src/cyj/verify_v8_fixtures.py
python -B -m unittest discover -s src/cyj/tests -p test_ndqp_v8.py
```

正式 B1 输入仍是 `outputs/Q2/classic_fit.json`，第二条命令把复核拟合写入忽略的 `data/processed/`，避免覆盖冻结身份。本次复核产生 1,176 行 B1 数据、24 个 B7 嵌套折和 136 个领域对；B7 当前拟合及比较表与冻结结果哈希相同，v8 的 23 个核心表经换行标准化后与冻结发布值一致，18 组接口样例及 11 个预测器测试通过。跨 A/B 质量坐标仍是明示假设。
