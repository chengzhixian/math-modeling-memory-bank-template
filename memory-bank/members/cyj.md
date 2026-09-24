[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》（SHA256 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`）第 2—13 页曾含近白色 5 pt 隐藏页边文字。用户明确要求：这些历史隐藏内容及其衍生的方法、参数、阈值、数值和结论绝对不能作为建模依据。

当前仓库 `problem/F/数据说明.pdf` 已在提交 `55743ca` 替换为清理版：13 页、13207231 bytes、SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；本地复核结果为可提取文本字符数 0、旧隐藏文字特征 0、近白小字号字符 0。当前 PDF 主要用于页面视觉核对；机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

Gemini 历史提交 `fd55147`、`80c7ea5`、`6086964` 的工作因无法可靠排除隐藏文字影响而作废，提交 `58f4f0a` 已明确丢弃其文件内容。不得从 Git 历史恢复、cherry-pick、复用其中的模型、参数、数值、结论或输出。若后续独立论证出同名方法适用，必须依据可见题面、真实数据或独立可核验文献重新建立证据链。

更新时间：2026-09-24 16:30（北京时间）。角色 cyj，负责 Q2 与 Q3 理论；分支 `team/cyj-scaling`。Python 3.12.14 / Windows，环境见 `problem/cyj/environment.md`。

## 当前状态

2026-09-24 接续检查点：已合并 main `968ef7a`（merge `55889bf2b942ca9643f49e420035a9f051f2bed3`），无冲突。已修正 API 的 B8 准入描述，冻结去重 B7 原生 Q 候选比较/分组验证/50 次条件 bootstrap 方案；新代码待正式实验，不能视为结果。见 `20260924-1650-quality-interface-start.md`，最终结果另交接。

本轮采用 chm `chm.q1.v1` 的原生读取器和六文件清单，定义 `cyj.q3.v1` 预测/成本/约束调用，完成 B1 E/N/D 消融及 B6–B8 质量方向/重复审计。本人合同 v1.9；软件测试 29/29 PASS，科学接口仍 draft，`ready_for_Q3=false`。完整 Q2、质量性能项和跨来源验证尚未完成。

已无冲突合并 main `7d8081fbf50cd380904505759c116580356f102d`，merge `5ada51f9a29877dd2ee98a9b4d1b0760e1f5b818`；重新读取协作规则/公共记忆/接口。论文入口迁为 `paper/latex/`，本人只负责其中 `sections/cyj/`，本轮未编辑论文及公共文件。上轮两份因网络待推送的提交已包含在成功核验的远端检查点 `6e3fa70` 中，最新运行前已核远端 `9c4dcc12ece2b38d12a9d8b33e4e17c82ef943f5`；本轮最终结果的推送 SHA 以收尾 Git 实际核验为准。

## 采用/交付接口

- 消费 `integration/chm-q1-clean-20260923@7c14a0c894072048d09f04bd03653be1301f7257` 的 `chm.q1.v1`，manifest SHA256 `c3525c2f58baa97a44bd5e4dd497b2ea9e23752c7f03e4bfad309f0af95f238d`。接受 A 侧描述性 Q、严格命名单纯形、五 target、参考 p、eta 情景和不可识别性边界，不重拟合 A 原始数据。
- 直接调用 chm `Q1Interface`；临时读取器不永久复制系数。发现 3 CSV 清单 CRLF/Git LF 差异，仅按精确发布 SHA 恢复临时字节，双重身份在本人 bundle 中。需要 chm 修正后续发布规范。
- `interfaces/cyj/Q3_API.md` 回应其 CYJ_REQUIRED_INTERFACE；`src/cyj/q3_interface.py` 实现 B1 diagnostic 和显式 p/lambda/eta scenario，默认 formal 报错、Q_score 非 null 报错。`q3_costs.py` 给题面三成本族、单位、Q0 单侧导数、C7 外生候选与约束残差。
- `outputs/cyj/interfaces/q3_bundle.json` SHA256 `a153cbb6a45925317dcae1727d50bd0b20e2ec6b85767981b4d8a689b5144332`，代码/输入 `6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`；真实 B1 首行预测 4.738637013477364，chm 发布扰动例 0.001309803924525102，均通过测试。
- zhh C7 发布候选来自 `d47cd2dc921333caecfcb95f09eb5a2f2714d0db`：2048/8192/131072 Token；其合同/成员状态滞后仍需本人修订，不能把发表分支结果称为 main 验收。Loss–Benchmark 桥接 RMSE 7.060 是该留出实验误差量级，不是 95% 区间。

## 已验证的阶段结果

| 工作 | 当前证据 |
|---|---|
| 附件 B 审计 | 19 CSV，155 pass/5 warning/0 fail；`experiments/cyj/20260924-b-data-audit-stage1.md` |
| B1 经典 N-D | 全样本/LOSO均值/tail RMSE 0.0001465764/0.0001461277/0.0001160041；原 fit SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead` |
| C 显示与八行敏感性 | 1176 行与四位小数舍入一致，删除八行最大预测变化 7.6652e-06；`20260924-b1-precision-sensitivity.md` |
| B2/B3 形状 | 半合成/插值的轨迹诊断，未作为独立验证；`20260924-b2-b3-shape-diagnostic.md` |
| B1 bootstrap | 78/80 接受，两次哈希一致，仅固定模型条件波动；`20260924-b1-group-bootstrap.md` |
| 本轮 E/N/D 消融 | 27/27 重拟合收敛未触边；LOSO RMSE full 0.0001461、no_E 0.0636845、no_N 0.2126047、no_D 0.2552875；仅支持 B1 重构保留三项 |

本轮实验集中在 `experiments/cyj/20260924-interface-adoption-ablation.md`，消融 JSON SHA256 `592c945cabd928892339b14f3008071abb5c308632e1e38367b0f333e3acfea8`。前几轮详细参数/命令/哈希以相应实验和历史 handoff 为准，不在当前记忆重复历史状态。已清除 13 个可再生 pyc（152005 bytes），复现依赖的代码、prepared/CV 和关键结果保留。

## 未验证项与下一步

1. cyj：先用去重 B7 比较原生 Q_score 候选模型并组级留出。新审计确认 B6 360 行全部重复于 B7，合并只得 450 坐标；B7/B8 224 同坐标 Loss 全异；固定 N,D 时 B8 calibrated 的 90/90 组 Q 两端 Loss 上升，B6/B7 各 45/45 下降。B8 calibrated 暂隔离，extrapolated 不拟合/独立验证；不能直接反转 Q。B8 最小 Loss=0.5 堆积 362 行，是否人为截断尚未知。详见 `experiments/cyj/20260924-b8-quality-audit.md`，JSON SHA256 `6a563849463d4c6d730d2b979b05691a4109d1b13140e7cdc076eb274653fa45`（输出与代码哈希均规范为 LF）。当前未交付完整 N-D-Q-p validated predictor。
2. cyj：继续 B1 逐行 Loss 来源和 tokenizer/评估语料/对数底，B4/B5 可比性及 B9/B10 外推。近乎精确重构、bootstrap 窄区间和本轮消融不能替代这些证据。
3. chm+cyj：按已经采用的定义联调；主 anchor 与 lambda 未识别时保留多 target 情景，不将 Q_z 等同 Q_score 或将 13 域原 Loss 平均。lambda 不默认 1，eta 不充当跨 Loss 换算。
4. chm：验收本文接口和样例并修复发布换行规范；zhh：正式确认 C7/桥接接口并传播 Loss–Benchmark 误差；集成人：验收后汇总公共记忆，cyj 不直接编辑公共状态。
5. 全库 A 附件 LFS 完整性本机仍未重新验证（B 输入已单独按清单核验）；官方规则/当年模板符合性仍需团队确认。

最新交接：`memory-bank/handoffs/cyj/20260924-1630-b8-quality-gate.md`。本次输入提交 `cebd51bd0116ef3194728cfbeed9569239e085db`，该提交此前推送因 GitHub 连接重置失败；不能称最新结果已备份，最终以收尾 SHA 核验为准。已有 Draft [PR #3](https://github.com/chengzhixian/math-modeling-memory-bank-template/pull/3) 面向 main，尚未合并；分支备份不等于验收。公共状态交集成人更新。main 优秀论文目前仅阅读参考索引，未独立读原 PDF。
