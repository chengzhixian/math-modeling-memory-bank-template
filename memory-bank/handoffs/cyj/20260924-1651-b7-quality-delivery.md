# cyj：B7 质量模型、导数与样本接口交付

本记录接续 `20260924-1650-quality-interface-start.md`（文件名为批次标识）。分支 team/cyj-scaling；本轮起点 `4ad0084`，main `968ef7a36f1503aa222a0b09c8a8cb5d0f535ecd` 已无冲突合入。代码/输入冻结提交 `6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b` 已 push 并 ls-remote 核验。CHM/zhh 输入保持上一检查点版本，不声称联合验收。

## 交付及证据

- 新增 B7-native N-D-Q 诊断接口 `QualityPredictor`，文档 `interfaces/cyj/QUALITY_API.md`；合同 v1.10。修正旧 Q3_API 对 B8 calibrated 的不一致建议。
- 三候选×24 个整水平留出均收敛未触边；线性 Q 的 N/D/Q 留出平均 RMSE 为 0.058231/0.057091/0.057617，均优于本轮无 Q 和对数 Q 候选。50/50 N,D 组 bootstrap 接受。
- `outputs/cyj/quality/b7_quality_fit.json` SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`，两次完整运行哈希相同。所有数据/代码身份、参数、每折测试来源行号与样本在 JSON。
- 34 项测试通过，包括数值差分、非法输入与哈希拒绝、真实 B7 样例及同编号样本对齐。命令见 `experiments/cyj/20260924-b7-quality-results.md`，不重抄参数。
- 仅修改本人范围；main 模板变化来自正常合并，无研究文件被丢弃。原始 CSV 未改写，不产生可弃过程 CSV/缓存；保留协议、关键结果和代码测试。

## 消费者与限制

chm 可读取 B7 原生 Q 性能导数及条件参数样本做情景联调；不接 p，不能直接替代 B1。zhh 可读取明确 Loss 坐标/来源及配对样本测试传播流程；不能直接转成 Benchmark。两项正式就绪均 false。既有 B1/p API 保持兼容，formal 与 Q_score 请求仍拒绝。

未知项：B7 与 B1/A 的 Loss/Q 映射、p anchor/lambda、真实生成机制和总预测误差。候选按相同留出分数选择，未做嵌套/独立测试；50 次条件 bootstrap 不含模型选择、桥接和真实训练波动。没有把此模型称作完整 validated N-D-Q-p predictor。

下一步 cyj：补独立/嵌套验证、跨来源口径和 B9/B10 讨论。chm/zhh：按文档样例验收并反馈目标 Loss 定义，不代填 null 字段。集成人：验收后汇总公共状态，个人分支已推送不等于 main 已集成。

收尾顺序：git diff --check → 明确暂存本人文件 → commit → fetch origin --prune → push origin team/cyj-scaling → rev-parse HEAD 与 ls-remote 同名分支比对。最终 SHA 以 Git/回复核验为准，不自引用。
