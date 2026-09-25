# chm 交接：Q3 正式结果发布 schema

日期：2026-09-24
状态：发布协议与软件门禁完成；没有生成 formal 科学结果。

新增：
- `interfaces/chm/Q3_RESULTS_CONTRACT.md`
- `src/chm/q3_publish.py`
- `src/chm/test_q3_publish.py`
- `outputs/chm/q3_publish_validation_v1/manifest.json`

5/5 软件测试通过：正常 synthetic bundle 可发布；readiness=false、成本不守恒、sensitivity-only 偷塞唯一 p、缺不确定性汇总均会被拒绝。

正式输出固定为 optimization.csv、p_sensitivity.csv、uncertainty_summary.csv、manifest.json。zhh 只消费 status=formal_validated 的结果。

当前仍无 formal 数据；cyj predictor 未 ready 时发布器不会成为绕过科学门禁的捷径。
