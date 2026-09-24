# cyj 接受 chm A 侧接口、定义 B 侧调用及消融前检查点

分支 `team/cyj-scaling`；本轮起点 `81ada4b0501273fab28cb5a6cb514c236387886d`。代码/输入版本 `6e3fa709dbac03c224f6ba3d42f99f56ab1322f3` 已 push/ls-remote 核对；旧两份待推送提交已包含。main `7d8081fbf50cd380904505759c116580356f102d` 于 `5ada51f9a29877dd2ee98a9b4d1b0760e1f5b818` 无冲突合入；合后重读规则、公共记忆、接口和 TASK_PLAN。公共文件变化来自 main 合并，未由 cyj 编辑。

采用 chm `7c14a0c894072048d09f04bd03653be1301f7257`、接口 `chm.q1.v1`：原生读取器验证六文件，17 维严格单纯形，Q_z 仅 A 排序，inferred Q 为 null；五 target/eta 相对效应进入显式 lambda 情景。发现 coefficients/reference/validation 的 manifest 为 CRLF 哈希而 Git 为 LF；临时恢复仅在精确命中原清单 SHA 时接受，双重 SHA/规则记录于 `outputs/cyj/interfaces/q3_bundle.json`；请 chm 后续固定跨平台换行规范。没有重建生产者 manifest 或改其文件。

命令：`python -B src/cyj/q3_interface.py --build --chm-version 7c14a0c894072048d09f04bd03653be1301f7257 --input-version 6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`；`python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q`，26/26 PASS。实际解释器为本人 environment.md 的 Python 3.12.14。真实 B1 首行预测和 chm 已公布 p 扰动例均复算通过，N/D 导数与题面三项成本差分/单位核验通过。

本版 `interfaces/cyj/CONTRACT.md` v1.8、`Q3_API.md` 与可调用 `q3_interface.py`/`q3_costs.py` 回应 chm 所需输入输出、Loss 坐标、参数、样例、成本、约束与理论边界。B1 语料/tokenizer/log-base 未识别，Q_score 性能项未拟合，Q/p 数值桥接未标定，`ready_for_Q3=false`；正式模式报错，只有显式诊断/情景可运行。定义接法不是已完成科学验证。

下一步先推送本检查点，后执行 `python -B src/cyj/ablate_b1_terms.py --input-version 6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`。仅对 B1 实际拟合的 E/N/D 分别删除并重拟合，复用冻结的 8 折留规模与 token-tail 划分，全部拟合信息留在一个结果 JSON；Q/p 尚无拟合证据不作伪消融。完成后保留代码、结果与必要日志，压缩过时当前状态说明并清理本人可再生缓存。最终提交/push/ls-remote 以实际执行为准。
