[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》（SHA256 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`）第 2—13 页曾含近白色 5 pt 隐藏页边文字。用户明确要求：这些历史隐藏内容及其衍生的方法、参数、阈值、数值和结论绝对不能作为建模依据。

当前仓库 `problem/F/数据说明.pdf` 已在提交 `55743ca` 替换为清理版：13 页、13207231 bytes、SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；本地复核结果为可提取文本字符数 0、旧隐藏文字特征 0、近白小字号字符 0。当前 PDF 主要用于页面视觉核对；机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

Gemini 历史提交 `fd55147`、`80c7ea5`、`6086964` 的工作因无法可靠排除隐藏文字影响而作废，提交 `58f4f0a` 已明确丢弃其文件内容。不得从 Git 历史恢复、cherry-pick、复用其中的模型、参数、数值、结论或输出。若后续独立论证出同名方法适用，必须依据可见题面、真实数据或独立可核验文献重新建立证据链。

更新时间：2026-09-24 09:59（北京时间）。角色任务：Q2 标度律与推导；为 Q3 提供目标函数、约束和验证支持。
成员称呼：cyj（用户已指定）。实际电脑/环境：Windows 10.0.26200；Python 3.12.14（Codex 工作区运行时）；详见 `problem/cyj/environment.md`。
当前分支：`team/cyj-scaling`；已包含 main `a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`；本轮 B1 组级 bootstrap 代码提交 `8dd672eb53571325f27342f4e545c0fa7bf06f24`，尚未生成正式结果。
状态：进行中。Stage 1 审计、B1 经典 N-D 基线、八行计算量显示精度/剔除敏感性，以及 B2/B3 轨迹形状诊断已完成；B1 Loss 近乎精确重构的来源仍未查明，接口仍是 draft，`ready_for_Q3=false`。
远端状态：上一已核检查点 `9a2d4357351afb11c59dff474cc82350a496eb7e`；本轮代码提交 `8dd672e` 尚待推送，必须以实际 Git push 与 `ls-remote` 核验，不能把本地提交视为备份。

## 本轮跨分支审查与运行前检查点

- 审查范围和精确版本见 `problem/cyj/20260924-cross-branch-interface-review.md`：chm 清洁集成分支 `7a958d7b5760bce4e7136a5c80e6b9275de60eaf`、zhh 分支 `d47cd2dc921333caecfcb95f09eb5a2f2714d0db`；两者均非已验收 main 接口。禁用受污染历史来源。
- chm 的 `Q2_BRIDGE.md` 指出 `Q_z` 与 B6–B8 `Q_score` 无配对标定，暂不能数值映射；13 域 Loss 与 B1 `val_loss` 未同口径证实，centered p 和显式 `lambda_k(N)` 只可作结构联调。需 chm+cyj 联合决定 Q 情景、Loss anchor/p，不可单方冻结。
- zhh `RESULTS.md` 提供 C7 2048/8192/131072 Token 外生情景，以及分级 Loss–Benchmark 桥接的留出误差量级；其同分支 `CONTRACT.md` 和成员记忆仍显过期，由 zhh 自行修订、集成人验收。cyj 不把 7.060 RMSE 误当 95% 区间。
- 下一步已新增 B1 按 8 个 N 轨迹整组重抽样代码与测试，21/21 测试通过；输入代码版本固定为 `8dd672eb53571325f27342f4e545c0fa7bf06f24`。长运行待本检查点推送后进行，结果只能是条件于 B1 与经典模型的诊断，不能补足 Q/p、跨 Loss 或 Q4 桥接不确定性。
- 本轮未改公共记忆、他人目录或主接口；Q3 仍 `ready_for_Q3=false`。运行前交接见 `memory-bank/handoffs/cyj/20260924-0959-p20-crossbranch-bootstrap-start.md`。

## Draft PR 交接状态

- 已创建 [PR #3](https://github.com/chengzhixian/math-modeling-memory-bank-template/pull/3)，标题 `cyj：附件 B 审计、经典基线及 B1–B3 诊断`，状态 Draft，`team/cyj-scaling` → `main`；创建时分支 HEAD 为 `3e20b3eeca2594b9311adf89442828d468fec026`，GitHub 页面显示 23 commits、40 个变更文件。40 个文件的本地比较均在 cyj 自有目录或本人成员记忆/交接范围。
- PR 描述标明 Q2 未完成、`ready_for_Q3=false`、B2/B3 非独立验证、Q/p 和 Loss anchor 未冻结，并请求集成人复现验收后再合入；创建 PR 不等于完成验收或合并 main。
- 交接详情见 `memory-bank/handoffs/cyj/20260924-0942-p20-draft-pr.md`。09:42 的首次 `git ls-remote` 临时遇到 GitHub 443 连接失败；不据此推断已发生分支变化，最终推送以再次实际核验为准。

## 本轮 B2/B3 形状诊断

- 代码/输入提交 `3cd66aeb23d9ceccc3958371bf41a212f6699658`；B2/B3 原始文件均先与提交内 `F_MANIFEST.json` 核对。命令、文件身份与性质边界见 `experiments/cyj/20260924-b2-b3-shape-diagnostic.md`。
- B2 半合成 1,029 行、7 条轨迹，每条首末 Loss 下降；1,022 对相邻 checkpoint 中有 328 对局部上升。每组末尾 5 点显示 D 同为 2050.000，形成 4 对 D 平台，保留全部行并禁止对该平台计算 `ΔLoss/ΔD`。
- B3 插值 8×500 行，每条首末 Loss 下降；3,992 对相邻点中有 566 对局部上升。每文件 `step` 标签只 117 个不同值，不能作为 500 个独立 checkpoint；按唯一递增的 D 检查形状。
- 输出 `outputs/cyj/diagnostics/b2_b3_shapes.json` schema v1，SHA256 `bea31afe812a68bb3d2af9c1ea1f0efcbe557e5dee8ad58f785c86cafe9d189e`，连续两次运行哈希稳定；完整测试 19/19 PASS。仅作同源/半合成形状诊断，未计算 B1→B2 绝对 RMSE，也不能称独立验证。
- 接口升生产者草案 v1.6，仅增加该诊断；`ready_for_Q3=false`。公共状态建议由集成人验收后汇总。B2 生成/校准与 Loss 口径、B3 行级插值方法仍待验证。

## 上轮 B1 计算量显示精度与敏感性

- 从已推送个人分支 `768cc7d9f4ad2f71ad5852b18f469feec211e4af` 开始，`git fetch origin --prune`、`git pull --ff-only` 后仍在 `team/cyj-scaling`，`origin/main=a0932fd92b3a46cef8eb0bf563df1e6abc9396ef` 为当前 HEAD 祖先；本轮未改公共或其他成员文件。
- 诊断代码/输入提交 `351ea0e0eaeab0226550311d8fcb9a855cebcc2d`。B1、两份清单、prepared 和原 fit 的身份按提交与 SHA 核对；命令与版本见 `experiments/cyj/20260924-b1-precision-sensitivity.md`。
- B1 全部 1,176 行显示 C 恰与 `round(0.006ND,4)` 一致；8 个相对偏差 warning 均符合该显示精度，最大绝对差 `4.994688e-05`（`1e21 FLOPs`）。这解释相对 warning，不能确认未舍入 C 的来源。
- 剔除 8 行后重拟合收敛；其在全部 B1 行上的 RMSE `0.0001466067`（原 `0.0001465764`），最大预测变化 `7.6652e-06`。16 项测试通过；诊断 JSON 两次重跑 SHA 稳定，为 `c7c8b346e4cdbec6034aead4f959ea7f60aa14b52ad6cd00169ea98033356fd7`。
- 原 Stage 1 审计 JSON 和 classic_fit 不改写。B1 `val_loss` 行级来源与近乎精确重构机制仍未知，不能将同源敏感性误作独立验证。
- 当时本人接口升草案 v1.5，新增诊断附件；`ready_for_Q3=false`。正式 Q/p、13 域 Loss anchor、预测区间和 Loss–Benchmark 桥接仍缺；公共记忆由集成人验收后汇总。

## 当前任务

按 TASK_PLAN.md 推进 P20。当前先审计 B1/B4/B5 的 Loss 构造与口径，并对经典基线做分组不确定性和计算恒等式离群敏感性；Q1 的 Q/p 未形成正式接口前不拟合最终广义模型。
公共记忆由集成人维护；本次仅修改 cyj 归属文件。

## 本次已验证与证据

- 安全上下文检查通过：清理版 PDF/派生正文一致，24 个 AI 入口规则通过。
- `src/cyj/audit_b_scaling_laws.py` 已在代码/输入 SHA `6880af29f2a1fc089e5fc601d0df873c0be042a3` 上实际运行；脚本 SHA256 `8fb3859344405af81664346ad80b156c6a459a30465d1a50d4e7a7d827d5880a`。
- 审计 19 个附件 B CSV、10,484 行、566,719 字节；全部文件身份匹配 `F_MANIFEST.json`。
- Stage 1 结果为 155 pass、5 warning、0 fail；9 个 `unittest` 全部通过。正式 JSON 使用 LF，SHA256 `120b97a4089c3272fd121a8d7ae4867d0c65754d4953a4ec74723d67c2b7bed7`。
- 修复后检出 B9 的 4 个非正 D；B8 calibrated 984 与 extrapolated 720 已显式隔离；B1 已验证为 8 个规模组、每组 147 checkpoint，禁止随机逐行拆分。
- B1 的计算恒等式新增逐行检查，发现 8 行偏差超过 5%；原因尚未判定，保留 warning。
- 证据与限制见 `problem/cyj/b_data_audit.md` 和 `experiments/cyj/20260924-b-data-audit-stage1.md`。

## 经典 N-D 基线（本轮）

- 已新增统一数据准备、经典拟合和共享数学工具；复核后 Python 编译通过，标准库 `unittest` 14/14 通过。
- B1 固定 8 个 N 组；token-tail 每组 102/45 行、合计 816/360 行；另做 8 折 Leave-One-Model-Size-Out，未使用随机逐行拆分。
- 模型 `L=E+A*N^-alpha+B*D^-beta` 的复核后输入/代码 SHA 为 `cf297a4ad47e235acf5a9b6e890a5df5e05b07e5`。参数为 E=1.6898377713、A=0.3539687193、B=1.2402746295、alpha=0.3399854258、beta=0.2798924656。
- 全样本 RMSE 0.0001465764；8 折 LOSO RMSE 均值 0.0001461277；token-tail RMSE 0.0001160041。三者均低于 0.001，已触发 near-exact reconstruction 警报；该现象可能来自共同确定性构造或强预处理，不能作为独立真实泛化证据。
- B4/B5 的绝对 Loss 可比性缺少本地证据，状态为 `not_established`；只输出描述性预测，不报告 external RMSE。
- B1/B4/B5 在读取前逐文件按提交内清单核对 bytes/SHA256；代码文件与输入提交逐一核对；拟合前重建并核对 prepared B1。9 个输出连续两次重跑哈希相同。
- 主结果 `outputs/cyj/classic/classic_fit.json` schema v2，SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`；数据 manifest schema v2，SHA256 `5edf56694d63b74ab715c50c8ce2bf1ebb510f40fcd184d58ae714788e8e067e`。
- 接口已升为生产者侧 draft v1.4，显式 `ready_for_Q3=false`；没有 Q/p、不确定性区间或 Loss–Benchmark 桥接。

## 依赖与阻塞

接口见 `interfaces/cyj/CONTRACT.md` v1.4 和 `interfaces/README.md`。v1.4 仍是生产者侧 draft，尚未由 chm/zhh 验收；当前没有 validated predictor，chm 不得据此生成 Q3 正式最优配置。2026-09-24 fetch 所见 chm 清洁集成分支 `7a958d7b5760bce4e7136a5c80e6b9275de60eaf` 提出 Q/p 跨附件不可识别边界，尚未由 cyj 联合验收；`team/chm-data` 明示不可直接并入 main。zhh 的当前远端合同仍为 v1 草案。
全库校验被附件 A 的 4 个 LFS 指针阻塞；附件 B 已单独按清单核验。最终 `L(N,D,Q,p)` 依赖 chm 的正式 Q/p 接口；zhh 的 C7 2048/8192/131072 Token 情景须作为外生敏感性输入，正式采用前仍需其更新合同并通过集成验收。官方规则仍待集成人核对。

## 2026-09-23 main 协作规则同步影响

- `Q_A` 与 B6–B8 的 `Q_score` 不视为同一数值尺度；cyj 与 chm 必须共同冻结主 mapping、敏感性 mapping、有效范围及 mapping 不确定性。
- Q1 的 13 个 domain Loss 与 B1 泛化 `val_loss` 不视为同一统计量；cyj 与 chm 必须共同冻结 Loss 定义、主 anchor、至少 3 个敏感性 target、p 的函数形式、中心化参考配方、尺度传递参数及有效范围。
- Q3 正式优化以 cyj 的 validated predictor 为启动门槛；接口必须包含数学形式、参数与单位、输入尺度、有效范围、验证误差、不确定性、可调用实现或机器可读参数文件及真实测试案例。
- Loss 不等于 Benchmark；向 zhh 交付时必须同时提供 Loss 版本、适用范围与上游不确定性，由 zhh 传播桥接误差并报告区间。
- 跨成员接口消费必须记录来源分支或 main、精确 commit SHA、接口版本、文件 SHA、单位、有效范围和 draft/validated/integrated 状态。个人分支已备份不等于团队已验收或 main 已集成。

## 下一步和交接

1. 审计 B1 的 Loss 生成/预处理证据，解释或限定近乎精确重构；不要先把低 RMSE 写成独立泛化结论。显示 C 的 8 行 warning 已完成舍入解释与剔除敏感性，但未证明未舍入 C 来源。
2. 补充按规模分组 bootstrap 或等价不确定性；本轮八行敏感性不是预测区间。
3. 为 B2 和 B4/B5 补齐生成/校准或 tokenizer、评估语料、Loss 定义和单位证据；证据不足时继续禁止跨来源统一 RMSE。B3 只做形状检查，不作独立验证。
4. 在广义模型前与 chm 联合冻结 Q mapping 和 Loss/anchor/p 接法；记录实际消费的 SHA、接口版本和文件哈希。
5. 最新交接见 `memory-bank/handoffs/cyj/20260924-0810-p20-b2-b3-shape-diagnostic.md`；最终推送及远端 SHA 以 Git 实际核验为准。
