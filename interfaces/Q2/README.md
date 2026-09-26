# Q2 v8 条件接口

`NDQP_SCENARIO_V8.md` 与 `fixtures_v8/` 从 CYJ 冻结生产者 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6` 原字节收录。18 组请求/预期结果覆盖正常预测、质量与配比桥接情景、支持域和输入拒绝；`fixtures_v8/manifest.json` 逐文件记录 SHA256。

原接口文档中的 `interfaces/cyj/` 和 `outputs/cyj/` 是来源提交路径。main 将接口归入本问题目录，核心输入见 `outputs/Q1/`、`outputs/Q2/`。冻结样例的**字节身份**可在 main 直接校验；重新执行预测器需使用上述来源提交的 `src/cyj/ndqp_scenarios_v8.py` 及其依赖，再按原接口文档运行 `verify_v8_fixtures.py`。CHM 的 Q3 发布已按固定 v8 生产者消费；CYJ 又在 `53b4fb5` 独立条件签收，见 `experiments/Q3/INDEPENDENT_ACCEPTANCE.md`。

这些样例检验实现与解析边界，并不构成 A/B 质量映射或配比桥接的实证标定。
