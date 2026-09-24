# zhh Q4 审查整改交接（2026-09-24）

分支：`team/zhh-frontier`。数据说明使用清理版 PDF 与 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`；未使用历史隐藏页边文字或作废建模结果。附件审查文档只作为待核实的问题清单。

## 变更

- 撤回 `paper/sections/zhh/q4.md` 的旧算力放缓点值和 Bootstrap 区间；统一 Markdown、LaTeX、接口为 `not_identified_for_compute_slowdown`。旧运行日志改名并加醒目撤回标记。
- `interfaces/zhh/RESULTS.md` 不再把 Loss 留出 RMSE 写成可加减的能力误差界。跨来源桥接维持 `unidentified`。
- Epoch 明确 `no` 优先于许可证，排除 6 条冲突行；扩展集 2,672 条与严格 Epoch-yes 集 424 条分别输出关联回归、早末窗口分解及时间留出。
- 补充 pretrained/non-pretrained 分组及交互回归、按模型名只保留最新记录的敏感性。扩展集分组时间斜率 0.431/1.115 分/月，表明共同斜率不宜外推。

## 复现与限制

运行 `node src/zhh/q4_analysis.test.js`，它重跑 `q4_analysis.js` 并检查筛选、分组敏感性和预测为空。结果在 `outputs/zhh/q4_results.json`；代码与论文数字据此同步。清理版 PDF 检查和 AI 入口规则检查通过。原始数据全量校验仍有四个 A 附件 LFS 指针尺寸不符，需获取 LFS 对象后复核；本轮 Q4 使用的 C 附件可读且代码实际运行成功。

本机 OCR 代码审查工具因未配置 LLM endpoint 未运行。GitHub 网络连接失败时不得把本地提交称为远程备份；需联网后先 fetch 核查 `team/zhh-frontier` 是否有新提交，再仅推送该分支并以 `ls-remote` 核验 SHA。

## 待处理

- zhh：如需正式满足算力放缓能力预测，寻找独立且同坐标的算力—参数—能力数据链与外推误差校准；否则在终稿明确报告未识别。
- 集成人：仅在验收后引用本分支 Q4 结果；不要将 C3 历史 `Average` 与 C1/C2 直接拼接，也不要只按模型名将 C6 接到 C1。
