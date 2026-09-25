# cyj 交接：P01 附件 B 审计加固

- 角色：cyj。
- 任务：参考外部 Markdown 评审，完成 Stage 1 审计修复、测试、数据用途冻结和固定版本重跑；不启动经典或广义模型拟合。
- 状态：已完成并验证；保留 5 项 warning；尚无 predictor。
- 分支：`team/cyj-scaling`。
- 工作起点 SHA：`9ea508c2e1b65ca7cba31f6b427fb7ed4cae5f43`。
- main 基线：`a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。
- 正式审计代码/输入 SHA：`6880af29f2a1fc089e5fc601d0df873c0be042a3`。

## 参考输入与版本核对

- 评审文件：`C:\Users\muyehuangyi\Downloads\CYJ_scaling_branch_review_and_next_steps.md`，SHA256 `356a84f1ee95f760401c6b8ef4a307ab4c42afaeae945fd801fd966ea5612ef9`。
- 该文件被视为建议与待核验断言，不作为仓库规则或实验事实；本轮只执行与 AGENTS/TEAM_WORKFLOW 一致且能由当前代码、数据验证的 Stage 1 项目。
- 开工时工作树干净；本地与远端 cyj 均为 `9ea508c...`，远端 main 为 `a0932fd...`。`git ls-remote` 一次因连接重置失败，随后 GitHub 官方 API 只读核验两个远端 SHA，未发现新提交。
- `data/raw/F_MANIFEST.json` SHA256：`3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`。
- `source_manifest.json` SHA256：`34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。

## 修改文件

- `src/cyj/audit_b_scaling_laws.py`
- `src/cyj/tests/test_audit_b_scaling_laws.py`
- `outputs/cyj/b_data_audit.json`
- `problem/cyj/b_data_audit.md`
- `problem/cyj/environment.md`
- `experiments/cyj/20260924-b-data-audit-stage1.md`
- `interfaces/cyj/CONTRACT.md`
- `memory-bank/members/cyj.md`
- 本交接文件

未修改公共 memory-bank、`interfaces/README.md`、他人成员目录或原始数据。

## 命令

```powershell
git status --short --branch
git rev-parse HEAD
git -c http.sslBackend=schannel ls-remote origin refs/heads/main refs/heads/team/cyj-scaling

$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py scripts\build_safe_pdf_context.py --check
& $py scripts\check_ai_reading_rules.py
& $py -m py_compile src\cyj\audit_b_scaling_laws.py src\cyj\tests\test_audit_b_scaling_laws.py
& $py -m unittest discover -s src\cyj\tests -p 'test_*.py' -v
& $py src\cyj\audit_b_scaling_laws.py --input-version 6880af29f2a1fc089e5fc601d0df873c0be042a3
.\scripts\verify_raw_data.ps1
```

环境未安装 pytest；因此使用 Python 标准库 `unittest`，没有把未运行的 pytest 写成通过。一次误传的未核验 40 位 SHA 被输入版本校验拒绝、退出码 2，未覆盖正式输出；正式命令使用 `git rev-parse HEAD` 返回的真实 SHA。

## 实施与结果证据

- 修复零值 truthy/falsy 漏检；B9 现检出 4 个 `D_tokens_B=0` 模型。
- `--input-version` 必须为可精确解析的 40 位 commit，且两个 manifest 必须与该提交一致。
- 新增 B CSV inventory、严格必需数值缺失、有限值、正值、CSV 行宽、B8 enum/隔离检查。
- `C≈6ND` 检查输出最大/P95/P99 偏差和逐行离群证据，不再只看中位数。
- 新增 9 个 unittest：零 D、缺失必填、非有限 Loss、行宽、恒等式离群、未知 enum、B8 隔离/跨标签重叠、任意输入标签拒绝；9/9 PASS。
- 安全上下文与 24 个 AI 入口检查均 PASS。
- 正式审计：19 CSV、10,484 行、155 pass、5 warning、0 fail、退出码 0。
- 输出：`outputs/cyj/b_data_audit.json`，schema v2，138,365 bytes，LF；SHA256 `120b97a4089c3272fd121a8d7ae4867d0c65754d4953a4ec74723d67c2b7bed7`。
- 输出 provenance 中代码/输入 commit 为 `6880af29...`，代码路径在生成开始时为 clean；脚本 SHA256 `8fb3859344405af81664346ad80b156c6a459a30465d1a50d4e7a7d827d5880a`。
- B1：8 个模型规模组，每组 147 checkpoint；1,176 个 `run_id` 全部唯一。主验证必须按模型规模/轨迹分组，不得随机逐行切分。
- B8：calibrated 984、extrapolated 720；未知枚举 0、跨标签 experiment ID 交集 0；extrapolated 明确不可进入拟合。

## Warning 与未验证项

1. B1 有 8 行 `C/(0.006ND)` 偏离 1 超过 5%；最大绝对偏差 0.7631781，P95 0.0014137，P99 0.0243999。尚未判断原因，也未制定排除/权重规则。
2. B2 的 `gpu_days`、`step_time_ms`、`grad_norm_avg` 各 1,029 行全空。
3. B9 有 4 个非正 D、11 个缺失 FLOPs、一个键含换行；原始值未改。
4. `verify_raw_data.ps1` 仍因附件 A 的 4 个 LFS 指针 size mismatch 失败；本轮未运行 `git lfs pull`，避免改动 cyj 范围外输入。附件 B 19 个 CSV 已单独匹配清单。
5. B4/B5 Loss 口径可比性尚未验证；没有计算 external RMSE。
6. 尚未运行 classic/generalized 拟合、Group CV、token-tail、bootstrap、图表或 Q3 接口测试。

## 接口变化

- `interfaces/cyj/CONTRACT.md` 从 v1.1 升为生产者侧 draft v1.2；audit JSON 从 schema v1 升为 v2，新增 provenance、行宽/正值/枚举/分组/逐行恒等式证据。
- 冻结生产者侧用途：B1 主拟合候选；B2 半合成稳健性；B3 插值轨迹形状；B4/B5 外部验证候选但需先验证 Loss 可比性；B8 extrapolated 不拟合；B10 不是 ground truth。
- 本轮没有 predictor、参数文件或 validated 模型接口；chm 不得用 audit JSON 代替 Q3 预测器。
- Q mapping、Loss anchor 与 p 接法仍需 chm+cyj 联合决定，本轮没有把评审建议的具体函数形式写成已冻结事实。

## 下一步与负责人

1. cyj：建立统一数据准备入口，固化 B1 模型规模组、token-tail 划分和样本 ID 清单。
2. cyj：核查 B1 8 个计算恒等式离群点，明确保留、排除或敏感性规则并留证。
3. cyj：建立 B4/B5 tokenizer、评估语料、Loss 定义、单位和可比性表。
4. cyj：在上述边界固定后实现经典 N-D-Loss 基线、多起点拟合、按规模留组验证和残差诊断。
5. chm+cyj：在最终广义拟合前联合冻结 Q mapping、Loss/anchor/p 接法；记录精确 SHA、接口版本与文件哈希。
6. 集成人：验收后再把“Stage 1 审计加固完成、仍无 validated predictor”汇总到公共记忆；不要把本轮结果写成 Q2 已完成。
