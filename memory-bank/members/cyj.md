[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》（SHA256 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`）第 2—13 页曾含近白色 5 pt 隐藏页边文字。用户明确要求：这些历史隐藏内容及其衍生的方法、参数、阈值、数值和结论绝对不能作为建模依据。

当前仓库 `problem/F/数据说明.pdf` 已在提交 `55743ca` 替换为清理版：13 页、13207231 bytes、SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；本地复核结果为可提取文本字符数 0、旧隐藏文字特征 0、近白小字号字符 0。当前 PDF 主要用于页面视觉核对；机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

Gemini 历史提交 `fd55147`、`80c7ea5`、`6086964` 的工作因无法可靠排除隐藏文字影响而作废，提交 `58f4f0a` 已明确丢弃其文件内容。不得从 Git 历史恢复、cherry-pick、复用其中的模型、参数、数值、结论或输出。若后续独立论证出同名方法适用，必须依据可见题面、真实数据或独立可核验文献重新建立证据链。

更新时间：2026-09-24 00:15（北京时间）。角色任务：Q2 标度律与推导；为 Q3 提供目标函数、约束和验证支持。
成员称呼：cyj（用户已指定）。实际电脑/环境：Windows 10.0.26200；Python 3.12.14（Codex 工作区运行时）；详见 `problem/cyj/environment.md`。
当前分支：`team/cyj-scaling`；已合并 main `a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`；本轮正式审计代码/输入提交 `6880af29f2a1fc089e5fc601d0df873c0be042a3`。
状态：进行中。Stage 1 审计加固已完成、已测试并全量重跑；尚无拟合或预测结果，当前接口仍是 audit-only draft。

## 当前任务

按 TASK_PLAN.md 推进 P01/P20。下一工作块是建立无泄漏的数据准备与经典 N-D 标度律基线：B1 按模型规模留组并按 D 做尾部外推；B4/B5 先建立 Loss 可比性表。Q1 的 Q/p 未形成正式接口前不拟合最终广义模型。
公共记忆由集成人维护；本次仅修改 cyj 归属文件。

## 本次已验证与证据

- 安全上下文检查通过：清理版 PDF/派生正文一致，24 个 AI 入口规则通过。
- `src/cyj/audit_b_scaling_laws.py` 已在代码/输入 SHA `6880af29f2a1fc089e5fc601d0df873c0be042a3` 上实际运行；脚本 SHA256 `8fb3859344405af81664346ad80b156c6a459a30465d1a50d4e7a7d827d5880a`。
- 审计 19 个附件 B CSV、10,484 行、566,719 字节；全部文件身份匹配 `F_MANIFEST.json`。
- Stage 1 结果为 155 pass、5 warning、0 fail；9 个 `unittest` 全部通过。正式 JSON 使用 LF，SHA256 `120b97a4089c3272fd121a8d7ae4867d0c65754d4953a4ec74723d67c2b7bed7`。
- 修复后检出 B9 的 4 个非正 D；B8 calibrated 984 与 extrapolated 720 已显式隔离；B1 已验证为 8 个规模组、每组 147 checkpoint，禁止随机逐行拆分。
- B1 的计算恒等式新增逐行检查，发现 8 行偏差超过 5%；原因尚未判定，保留 warning。
- 证据与限制见 `problem/cyj/b_data_audit.md` 和 `experiments/cyj/20260924-b-data-audit-stage1.md`。

## 依赖与阻塞

接口见 `interfaces/cyj/CONTRACT.md` v1.2 和 `interfaces/README.md`。v1.2 仍是生产者侧 audit-only draft，尚未由 chm/zhh 验收；当前没有 validated predictor，chm 不得据此生成 Q3 正式最优配置。
全库校验被附件 A 的 4 个 LFS 指针阻塞；附件 B 已单独按清单核验。最终 `L(N,D,Q,p)` 依赖 chm 的正式 Q/p 接口；zhh 的 C7 2048/8192/131072 Token 情景须作为外生敏感性输入，正式采用前仍需其更新合同并通过集成验收。官方规则仍待集成人核对。

## 2026-09-23 main 协作规则同步影响

- `Q_A` 与 B6–B8 的 `Q_score` 不视为同一数值尺度；cyj 与 chm 必须共同冻结主 mapping、敏感性 mapping、有效范围及 mapping 不确定性。
- Q1 的 13 个 domain Loss 与 B1 泛化 `val_loss` 不视为同一统计量；cyj 与 chm 必须共同冻结 Loss 定义、主 anchor、至少 3 个敏感性 target、p 的函数形式、中心化参考配方、尺度传递参数及有效范围。
- Q3 正式优化以 cyj 的 validated predictor 为启动门槛；接口必须包含数学形式、参数与单位、输入尺度、有效范围、验证误差、不确定性、可调用实现或机器可读参数文件及真实测试案例。
- Loss 不等于 Benchmark；向 zhh 交付时必须同时提供 Loss 版本、适用范围与上游不确定性，由 zhh 传播桥接误差并报告区间。
- 跨成员接口消费必须记录来源分支或 main、精确 commit SHA、接口版本、文件 SHA、单位、有效范围和 draft/validated/integrated 状态。个人分支已备份不等于团队已验收或 main 已集成。

## 下一步和交接

1. 建立 `prepare_scaling_data.py` 或等价数据入口，固定 B1 规模组、token-tail 划分与 ID 清单；不使用随机逐行切分。
2. 建立 B4/B5 Loss 可比性证据表；不可比来源不合并计算统一 RMSE。
3. 实现经典 N-D-Loss 基线、多起点稳健拟合、按规模留组验证和残差诊断；B2/B3/B10 不作独立真实验证。
4. 在广义模型前与 chm 联合冻结 Q mapping 和 Loss/anchor/p 接法；记录实际消费的 SHA、接口版本和文件哈希。
5. 本轮交接见 `memory-bank/handoffs/cyj/20260924-0015-p01-audit-hardening.md`；最终推送及远端 SHA 以 Git 实际核验为准。
