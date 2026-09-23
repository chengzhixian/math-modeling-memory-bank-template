[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》（SHA256 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`）第 2—13 页曾含近白色 5 pt 隐藏页边文字。用户明确要求：这些历史隐藏内容及其衍生的方法、参数、阈值、数值和结论绝对不能作为建模依据。

当前仓库 `problem/F/数据说明.pdf` 已在提交 `55743ca` 替换为清理版：13 页、13207231 bytes、SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；本地复核结果为可提取文本字符数 0、旧隐藏文字特征 0、近白小字号字符 0。当前 PDF 主要用于页面视觉核对；机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

Gemini 历史提交 `fd55147`、`80c7ea5`、`6086964` 的工作因无法可靠排除隐藏文字影响而作废，提交 `58f4f0a` 已明确丢弃其文件内容。不得从 Git 历史恢复、cherry-pick、复用其中的模型、参数、数值、结论或输出。若后续独立论证出同名方法适用，必须依据可见题面、真实数据或独立可核验文献重新建立证据链。

更新时间：2026-09-23 22:42（北京时间）。角色任务：Q2 标度律与推导；为 Q3 提供目标函数、约束和验证支持。
成员称呼：cyj（用户已指定）。实际电脑/环境：Windows 10.0.26200；Python 3.12.14（Codex 工作区运行时）；详见 `problem/cyj/environment.md`。
当前分支：`team/cyj-scaling`；本轮同步前个人提交 `d0a390ceb4af85eb671799696ac2f041b38100f7`；已合并 main `a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`，合并提交 `ed1613fda4a8c5a06d80d10cdcc5ee36d4690e85`。
状态：进行中。附件 B 结构审计已有已运行证据；尚无拟合或预测结果。审计脚本加固仅保存为未完成、未重新验证的 WIP，当前暂停建模。

## 当前任务

按 TASK_PLAN.md 推进 P01/P20。本轮只同步公共协作规则，不继续模型计算。恢复工作后的独立任务是完成审计加固并重新验证，再建立 B1 经典 N-D 标度律基线和预先固定的训练/验证边界；Q1 的 Q/p 未形成正式接口前只做 N-D 基线及接口准备。
公共记忆由集成人维护；本次仅修改 cyj 归属文件。

## 本次已验证与证据

- 安全上下文检查通过：清理版 PDF/派生正文一致，24 个 AI 入口规则通过。
- `src/cyj/audit_b_scaling_laws.py` 已实际运行，输入 SHA 为 `e85956f...`。
- 审计 19 个附件 B CSV、10,484 行、566,719 字节；全部文件身份匹配 `F_MANIFEST.json`。
- 审计结果为 97 pass、0 fail、3 warning。早期记录的工作区 CRLF 文件 SHA256 为 `0fa89425b2c37eb00dac1db8f8889199e895f5d8245d3e174ca30e18dded5e36`；已提交 LF 内容的 SHA256 为 `fe07d4a142f424950a63ec7689d35cb9df05d74a15a56a2316a0477bc90e4b6a`。后续接口应以明确的字节版本和哈希口径为准。
- 证据与限制见 `problem/cyj/b_data_audit.md` 和 `experiments/cyj/20260923-b-data-audit.md`。

## 依赖与阻塞

接口见 `interfaces/cyj/CONTRACT.md` v1.1 和 `interfaces/README.md`。v1.1 仍是生产者侧 draft，尚未由 chm/zhh 验收；当前没有 validated predictor，chm 不得据此生成 Q3 正式最优配置。
全库校验被附件 A 的 4 个 LFS 指针阻塞；附件 B 已单独按清单核验。最终 `L(N,D,Q,p)` 依赖 chm 的正式 Q/p 接口；zhh 的 C7 2048/8192/131072 Token 情景须作为外生敏感性输入，正式采用前仍需其更新合同并通过集成验收。官方规则仍待集成人核对。

## 2026-09-23 main 协作规则同步影响

- `Q_A` 与 B6–B8 的 `Q_score` 不视为同一数值尺度；cyj 与 chm 必须共同冻结主 mapping、敏感性 mapping、有效范围及 mapping 不确定性。
- Q1 的 13 个 domain Loss 与 B1 泛化 `val_loss` 不视为同一统计量；cyj 与 chm 必须共同冻结 Loss 定义、主 anchor、至少 3 个敏感性 target、p 的函数形式、中心化参考配方、尺度传递参数及有效范围。
- Q3 正式优化以 cyj 的 validated predictor 为启动门槛；接口必须包含数学形式、参数与单位、输入尺度、有效范围、验证误差、不确定性、可调用实现或机器可读参数文件及真实测试案例。
- Loss 不等于 Benchmark；向 zhh 交付时必须同时提供 Loss 版本、适用范围与上游不确定性，由 zhh 传播桥接误差并报告区间。
- 跨成员接口消费必须记录来源分支或 main、精确 commit SHA、接口版本、文件 SHA、单位、有效范围和 draft/validated/integrated 状态。个人分支已备份不等于团队已验收或 main 已集成。

## 下一步和交接

1. 先完成并重新验证 `d0a390c` 中尚未完成的审计加固；不得把 WIP 状态写成已修复。
2. 固定 B1 训练、B2/B3 与 B4/B5 验证边界，建立经典 N-D-Loss 基线；对 B9 的非正 D、缺失 FLOPs 和键换行制定显式清洗规则。
3. 与 chm 联合冻结 Q mapping 和 Loss/anchor/p 接法；记录实际消费的 chm SHA、接口版本和文件哈希。
4. 请 zhh 提供经合同和集成验收的 C7 外生情景，并在 Q4 传播 Loss–Benchmark 桥接误差。
5. 本轮同步交接见 `memory-bank/handoffs/cyj/20260923-2242-main-sync.md`；最终推送及远端 SHA 以 Git 实际核验为准。
