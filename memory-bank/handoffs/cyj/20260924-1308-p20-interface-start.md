# cyj 接口采用与消融运行前检查点

起点 `81ada4b0501273fab28cb5a6cb514c236387886d`；分支 `team/cyj-scaling`。2026-09-24 13:08，状态 WIP：接口适配代码尚未完成测试，不能用于正式 Q3。

已读 AGENTS、TEAM_WORKFLOW、公共记忆、本人记忆，以及 chm 清洁分支 `7c14a0c894072048d09f04bd03653be1301f7257` 的 CONTRACT v1.5、USAGE、CYJ_REQUIRED_INTERFACE、OFFICIAL_DATA_REVIEW、Q2_BRIDGE、UNCERTAINTY 和 `q1_interface_v1.json`。读并检查其 `src/chm/q1_interface.py`：严格 17 维单纯形、六文件哈希、inferred Q 留空、N 参数个数、η 已先缩放。本人适配器将调用该原生读取器，避免重定义 A 侧接口。

执行 `git -c http.sslBackend=openssl fetch origin --prune` 及 HTTP/1.1 重试失败；浏览器页面读取也超时。随后 `git -c http.sslBackend=schannel fetch origin --prune` 成功，main 前进至 `7d8081f`，chm 至上述 `7c14a0c`。上轮两提交仍须 push 核验；不把 fetch 成功当成备份。当前仅新增本人 `src/cyj/q3_interface.py`、记忆与本交接。

下一步：先明确文件暂存本 WIP、commit/push/ls-remote；再安全 merge main（其新增论文入口和目录归属已只读比较，不涉及本人已有代码）。随后完成真实接口样例与边界/导数核验、三项题面成本/约束接口和 B1 分组项消融。Q_score 目前未拟合、跨 Q/Loss 仍 unidentified，lambda 为显式情景；不能因接口可调用而声称 predictor validated。清理只限 cyj 可确认过时产物及可再生缓存，保留原始数据、关键结果、复现代码与历史交接。
