# cyj 交接：P20 审查问题修复与进度核验

- 角色/分支：cyj / `team/cyj-scaling`。
- 任务起点：`260e989e403100a561e478ff51cc80964fafbf86`；开工工作区干净。
- 同步：`git fetch origin --prune`、`git pull --ff-only` 均成功；个人分支已是远端最新。`origin/main=a0932fd92b3a46cef8eb0bf563df1e6abc9396ef` 已是本分支祖先，无新增 main 冲突。
- 修复代码/输入版本：`cf297a4ad47e235acf5a9b6e890a5df5e05b07e5`。最终交付提交与远端 SHA 以 Git 核验为准，本文件不预写未来提交成功。
- 状态：审查所列溯源、文件名、阈值表述、输出时间戳问题已修复并重跑；Q2 仍是 B1 经典基线草案，不是 Q3 validated predictor。

## 修改范围

- `src/cyj/scaling_provenance.py`（新增）、`src/cyj/prepare_scaling_data.py`、`src/cyj/fit_classic_scaling.py`、`src/cyj/tests/test_classic_scaling.py`。
- `outputs/cyj/classic/classic_data_manifest.json`、`outputs/cyj/classic/classic_fit.json`；其他 7 个输出重跑后哈希不变。
- `experiments/cyj/20260924-classic-baseline.md`、`problem/cyj/classic_scaling_baseline.md`、`problem/cyj/environment.md`、`interfaces/cyj/CONTRACT.md`、`memory-bank/members/cyj.md`。
- 旧交接 `20260924-0150-p20-classic-baseline.md` 仅纠正不存在的 B1 文件名并补记同一轮最终 push 成功；本文件是新交接。

公共记忆、公共接口、原始数据、chm/zhh 目录均未修改。公共状态更新由集成人验收汇总。

## 输入版本与实际命令

- B1：`data/raw/real_attachments/B_scaling_laws/pythia_training_log_existing.csv`，111,459 bytes，SHA256 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`。
- B4：`scaling_baseline.csv`，1,421 bytes，SHA256 `2272983ded93de35e05f9acbf95ebceedf43f283345e4be72b54fee94080391e`。
- B5：`published_scaling_data.csv`，1,967 bytes，SHA256 `dd858c5e48610e28589340d5db023d6abfb31df597506789ccdfc6a546731bbd`。
- 清单：`data/raw/F_MANIFEST.json` SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`；`data/raw/real_attachments/source_manifest.json` SHA256 `34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。

```powershell
git status --short --branch
git fetch origin --prune
git pull --ff-only
git rev-parse HEAD
git rev-parse origin/main

$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m py_compile src\cyj\scaling_provenance.py src\cyj\prepare_scaling_data.py src\cyj\fit_classic_scaling.py
& $py -m unittest discover -s src\cyj\tests -p 'test_*.py' -q
& $py src\cyj\prepare_scaling_data.py --input-version cf297a4ad47e235acf5a9b6e890a5df5e05b07e5
& $py src\cyj\fit_classic_scaling.py --input-version cf297a4ad47e235acf5a9b6e890a5df5e05b07e5
```

准备与拟合命令各执行两次；两次之间和之后对 `outputs/cyj/classic/` 的 9 个文件取 SHA256 并比较。

## 修复与结果证据

1. `--input-version` 仍校验两个清单属于精确提交；新增对 B1/B4/B5 的 bytes 与 SHA256 核对，对参与生成的 cyj 代码文件逐个核对 Git blob。拟合前还用已核验的 B1 和 manifest 划分策略重建准备表，逐行比较。
2. 原先实验/交接中的不存在文件名 `B1_neural_scaling_law.csv` 已改为实际的 `pythia_training_log_existing.csv`。历史生成程序本来就使用实际文件，模型数值不受该笔误影响。
3. `0.001` 是首次结果后加入的 near-exact 诊断阈值，实验记录不再称其为“预设”。
4. 两份 JSON 移除随运行时间变化的 `generated_at_utc`，provenance 固定到输入代码提交并新增原始文件身份和代码核对状态；schema v1→v2。相同代码/数据/依赖/默认路径下连续两次完整运行的 9 个输出 SHA256 全部一致。
5. `py_compile` PASS；`unittest` 14/14 PASS，包含同字节数 CSV 篡改被拒绝的测试。B1 准备 1,176 行/8 组、token-tail 816/360；B4/B5 仍为描述性、不计算跨口径 RMSE。
6. 数值未改变：全样本 RMSE 0.0001465764；8 折 LOSO RMSE 均值 0.0001461277；token-tail RMSE 0.0001160041。近乎精确重构的来源仍未查明，不能称独立真实泛化。
7. `classic_data_manifest.json`：4,719 bytes，SHA256 `5edf56694d63b74ab715c50c8ce2bf1ebb510f40fcd184d58ae714788e8e067e`；`classic_fit.json`：8,461 bytes，SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`。两者的 `git_commit` 均为 `cf297a4...`。

## 接口变化

- `interfaces/cyj/CONTRACT.md` 升为生产者侧 draft v1.4；经典基线 JSON schema v2，新增已核验的原始输入身份和代码版本语义；输出哈希更新。
- `ready_for_Q3=false` 不变。Q、p、Q1 domain Loss 到 B1 `val_loss` 的桥接、参数区间与 Loss–Benchmark 桥接均未建立。
- 现有消费者若读取旧 JSON 的 `generated_at_utc`、`source_b1_sha256` 或 `git_code_paths_dirty_at_generation_start`，必须改读 schema v2 的 `source_files` 和 `code_files_verified_against_input_commit`。当前尚无已验收消费者。

## 对照团队要求的当前进度

| 项目 | 当前状态 | 证据/限制 |
|---|---|---|
| 附件 B 审计 | 已完成 Stage 1 | 155 pass、5 warning、0 fail；B1/B4/B5 身份本轮再次核验 |
| B1 经典 N-D 基线 | 已运行、draft | 组留出和 token-tail 已做；near-exact 来源未明 |
| B2/B3 稳健性与轨迹检查 | 未完成 | 不得写成独立真实验证 |
| B4/B5 外部 Loss 验证 | 未完成 | tokenizer、语料、Loss 单位可比性未建立；只有描述性预测 |
| B6–B8 质量项、B9/B10 外推 | 未完成 | 半合成/估算边界维持原审计用途 |
| 参数及预测区间 | 未完成 | 尚无分组 bootstrap/模型形式不确定性 |
| chm Q/p 与 Loss 联合接口 | 未冻结 | chm 清洁集成分支 `7a958d7b5760bce4e7136a5c80e6b9275de60eaf` 的 `Q2_BRIDGE.md` 仅给可识别性边界，尚待 cyj 消费者验收 |
| Q3 正式预测接口、Q2 章节 | 未完成 | 当前 `ready_for_Q3=false`；`paper/sections/cyj/` 尚不存在 |

因此本轮符合分支、文件归属、输入溯源、可复现记录和“不把草案当验证版”的协作要求；尚不符合 TASK_PLAN 中 Q2 验证版和 Q3 启动门槛，不能报告 Q2 已完成。`team/chm-data` 明示含不可直接集成的历史祖先，今后仅从 chm 清洁集成分支读取待验收 Q1 接口，不把其个人分支普通 merge 到 main。

## 未验证项、下一步与负责人

1. cyj：查明或限定 B1 近乎精确重构的来源；审查 B1 8 个 C 恒等式离群点并做敏感性。
2. cyj：完成 B2/B3 及 B4/B5 分层验证边界，按规模 bootstrap 和预测区间；如外部 Loss 口径不可证，明确降级为趋势/情景。
3. chm+cyj：在 clean chm 接口上联合确认 Q 的不可识别边界、Loss anchor/p 桥接与不确定性，记录采用的精确 commit/文件哈希；未取得证据不得默认跨附件映射。
4. cyj：在上述输入与验证齐备后形成 `L(N,D,Q,p)` 可调用接口与 Q2/Q3 理论章节；chm 才能正式 Q3 优化。
5. zhh/集成人：验收后更新公共进度和 `interfaces/README.md`；C7 作为外生情景，Q4 传播 Loss–Benchmark 桥接误差。
6. 本机全库 2,014 文件校验的附件 A 四个 LFS 指针问题仍以先前记录为准；本轮未重新运行 `git lfs pull` 或全库校验，不能声称已解决。官方提交规则仍待集成人核验。
