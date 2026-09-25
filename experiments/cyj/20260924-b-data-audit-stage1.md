# P01 附件 B 审计加固与重跑

状态：已运行。Stage 1 审计加固通过；保留 5 项 warning；未开始模型拟合。

## 参考材料与输入

- 外部评审参考：`C:\Users\muyehuangyi\Downloads\CYJ_scaling_branch_review_and_next_steps.md`，SHA256 `356a84f1ee95f760401c6b8ef4a307ab4c42afaeae945fd801fd966ea5612ef9`。其中建议只作为审查输入，本记录只采纳经仓库代码/数据验证的部分。
- 分支：`team/cyj-scaling`。
- 正式审计代码/输入提交：`6880af29f2a1fc089e5fc601d0df873c0be042a3`。
- main 基线：`a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。
- 数据：`data/raw/real_attachments/B_scaling_laws/`。
- 输入清单 SHA256：`3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`。
- 来源清单 SHA256：`34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。
- 脚本 SHA256：`8fb3859344405af81664346ad80b156c6a459a30465d1a50d4e7a7d827d5880a`。

## 实施内容

- 修复 `0.0 or math.inf` 导致零值漏检的问题。
- 将任意 `--input-version` 改为必须精确解析的 40 位 commit，并校验输入清单与该提交一致。
- 新增完整 B CSV inventory、严格必需数值缺失、已填数值有限性、正值、CSV 行宽和 B8 枚举检查。
- `C≈6ND` 从只看中位数改为检查每行，并输出最大、P95、P99 偏差及超阈值行。
- B8 明确 calibrated 为拟合候选、extrapolated 为仅评估，并输出两类 ID 与交集检查。
- 输出升级为 schema v2，记录代码/脚本/清单/Python/生成时间，并强制 LF 写出。
- 冻结生产者侧数据角色：B2=半合成稳健性、B3=轨迹形状、B10=估计参考；验证 B1 为 8 个规模组、每组 147 checkpoint。

## 实际命令

```powershell
$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py scripts\build_safe_pdf_context.py --check
& $py scripts\check_ai_reading_rules.py
& $py -m py_compile src\cyj\audit_b_scaling_laws.py src\cyj\tests\test_audit_b_scaling_laws.py
& $py -m unittest discover -s src\cyj\tests -p 'test_*.py' -v
& $py src\cyj\audit_b_scaling_laws.py --input-version 6880af29f2a1fc089e5fc601d0df873c0be042a3
.\scripts\verify_raw_data.ps1
```

另一次误传的未核验 40 位 SHA 被 `rev-parse --verify` 拒绝，退出码 2，未覆盖正式输出；随后先用 `git rev-parse HEAD` 取得上述真实 SHA 再运行。

## 结果证据

- PDF 安全上下文：PASS。
- AI 入口规则：PASS，24 个入口。
- `py_compile`：PASS。
- `unittest`：9/9 PASS；环境没有安装 pytest，因此未声称运行 pytest。
- 正式审计：退出码 0；19 CSV、10,484 行；155 pass、5 warning、0 fail。
- 输出：`outputs/cyj/b_data_audit.json`，schema v2，138,365 bytes，LF，SHA256 `120b97a4089c3272fd121a8d7ae4867d0c65754d4953a4ec74723d67c2b7bed7`。
- provenance：代码/输入提交 `6880af29...`，代码路径在生成开始时干净；脚本与两个 manifest 哈希已写入 JSON。
- 零值修复证据：B9 精确检出 4 个 `D_tokens_B=0` 模型。
- B1 分组证据：8 个 `N_params_B` 组、每组 147 行；1,176 个 `run_id` 全部唯一，不能把 `run_id` 当轨迹组或随机逐行拆分。
- B8 隔离证据：calibrated 984、extrapolated 720，未知枚举 0，跨标签 ID 交集 0。

## 5 项 warning

1. B1 有 8 行 `C/(0.006ND)` 偏离 1 超过 5%；最大绝对偏差 0.7631781，P95 0.0014137，P99 0.0243999。原因未判定。
2. B2 三个运行监控字段各 1,029 行全空。
3. B9 有 4 个非正 D。
4. B9 有 11 个 FLOPs 缺失。
5. B9 有一个模型键含嵌入换行。

审计 JSON 中 B9 正值和建模就绪度分别报告同一组原始限制，因此检查层面共有 5 个 warning；上面按研究问题合并表述。

## 未验证

- 全库校验仍失败：附件 A 的 4 个 LFS 文件 size mismatch；未执行 `git lfs pull`，避免在 cyj 任务中改动他人原始输入范围。附件 B 19 个 CSV 已逐文件匹配清单。
- B1 计算恒等式 8 个离群点原因未核验，未决定排除、修正或加权。
- B4/B5 的 tokenizer、评估语料、Loss 定义和单位可比性尚未建立证据表。
- 未运行 B1 经典拟合、分组 CV、token-tail 外推、外部验证、bootstrap 或任何广义模型。
- chm 的 Q/p 正式接口和 zhh 的正式 C7/桥接接口尚未消费。
