# cyj / P20：采用 chm 接口、定义 Q3 调用、完成消融与清理

2026-09-24；分支 `team/cyj-scaling`；本轮起点 `81ada4b0501273fab28cb5a6cb514c236387886d`。状态：接口软件验收及 B1 消融已完成，科学接口仍 draft，`ready_for_Q3=false`。详细协议/证据集中于 `interfaces/cyj/Q3_API.md` 和 `experiments/cyj/20260924-interface-adoption-ablation.md`。

## 输入、变更与实测证据

- 固定 chm 清洁分支 `7c14a0c894072048d09f04bd03653be1301f7257`，接口 `chm.q1.v1`，清单 SHA256 `c3525c2f58baa97a44bd5e4dd497b2ea9e23752c7f03e4bfad309f0af95f238d`。六文件、原生读取器与合同等的 SHA/bytes 由本人 bundle 记录；没有复制第二套永久 A 系数或重拟合 A 数据。
- 新增本人 `q3_interface.py`、`q3_costs.py`、`ablate_b1_terms.py` 和接口测试；合同 v1.8 及 `Q3_API.md` 回应 chm 的 CYJ_REQUIRED_INTERFACE。B1 模型真实样例、五 target 配比情景、显式 lambda/eta、三项题面成本及约束残差可调用；默认 formal 与未拟合的 Q_score 输入失败，未知 Loss 定义保留 null。
- 发现 chm coefficients/reference/validation 发布清单为 CRLF 哈希、Git 对象为 LF；只在临时换行恢复精确命中生产者 SHA 时读取，任何其他数据变化失败。请 chm 后续固定跨平台发布规则；本轮未改其文件/manifest。
- 代码/输入版本 `6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`。26/26 测试通过，原生 CHM p 扰动例 0.001309803924525102 和 B1 首行预测 4.738637013477364 复算通过，成本单位和 N/D 导数验证通过。
- 80 次 B1 bootstrap 是前轮结果；本轮消融另用原冻结 8 LOSO + token-tail，删除 E/N/D 后重拟合，共 27 次全部收敛且不触边。LOSO RMSE 均值 full=0.0001461277、no_E=0.0636845167、no_N=0.2126046868、no_D=0.2552874888；各删项在全部 9 划分更差。只支持保留三项进行当前 B1 重构，不作为独立真实泛化。
- `outputs/cyj/ablation/b1_terms.json` SHA256 `592c945cabd928892339b14f3008071abb5c308632e1e38367b0f333e3acfea8`；`outputs/cyj/interfaces/q3_bundle.json` SHA256 `a153cbb6a45925317dcae1727d50bd0b20e2ec6b85767981b4d8a689b5144332`。原 classic_fit 保持 SHA `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`。

## 命令与同步

Git fetch 初期因 443/reset 失败，浏览器读取也超时；Windows TLS 后端成功取得最新 chm/main。后来正常 OpenSSL push 恢复，上轮待推送结果和本轮代码 `6e3fa70` 已 push/ls-remote 一致。`git pull --ff-only` 成功后 `git merge --no-edit origin/main` 无冲突，合入 main `7d8081fbf50cd380904505759c116580356f102d`，merge `5ada51f9a29877dd2ee98a9b4d1b0760e1f5b818`；公共文件/论文入口变化来自 main，无本人公共编辑。合后重新读取协作文件和记忆。

随后生成接口并测试，再提交检查点 `9c4dcc12ece2b38d12a9d8b33e4e17c82ef943f5`，远端已核一致后才运行消融。实际运行：`python -B src/cyj/q3_interface.py --build --chm-version 7c14a0c894072048d09f04bd03653be1301f7257 --input-version 6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`；`python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q`；`python -B src/cyj/ablate_b1_terms.py --input-version 6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`。Python 指本人 environment.md 的 3.12.14 绝对路径。

清理前解析并校验本人两个 cache 绝对路径，再用 PowerShell `Remove-Item -LiteralPath <已核路径> -Recurse -Force` 删除 13 个可再生 `.pyc`、152005 bytes；没有删除原始数据或结果。合同/记忆精简后保留当前状态和历史证据入口；已有诊断代码、prepared/CV 文件因仍被 manifest/复现依赖而保留。

## 未验证与接收人

Q_score 性能项未拟合，Q0 仅显式成本情景；Q_z↔Q_score、B1↔A target/B6–B8 Loss 未定标。B1 tokenizer/语料/对数底未知，B4/B5 可比性未证实，B9/B10 讨论未完，p 训练支持凸包未自动检查；C7 合同和 Loss–Benchmark 总误差传播仍待 zhh。定义已由 cyj 承接，未声称完整 Q2 或 validated predictor 完成。

chm：按 Q3_API 的真实样例和错误边界复核，接收可调用诊断/情景及三成本/残差；修复本人的换行发布问题。cyj：优先完成 B6–B8 质量性能项与来源/同尺度审计，再形成 Q 的替代关系、B4/B5 验证和 B9/B10 外推。zhh/集成人：更新其正式合同，验收本轮后汇总公共记忆，未经验收不将条件结果写成 main 已完成。

本交接与结果明确选文件暂存、`git diff --check`、commit 后 push 本人分支；最后以 `git rev-parse HEAD` 和 `git ls-remote origin refs/heads/team/cyj-scaling` 一致及工作区干净作为交付。实际最终 SHA 由 Git 历史定位，不在自身文件写自引用。
