# cyj → 团队：P20 B9/B10 外推证据审计

时间：2026-09-24 19:36 北京时间。状态：审计已运行，Q2 完整验证仍进行中；分支 `team/cyj-scaling`，工作起点 `622d58a77c6eaf40da779d397de81c20819dcfd7`，先合并 `origin/main@670d726` 至 `b54310c67be84f1cac932021ebc7955e540f93c9`。先前两次 cyj 提交已推送并用 `ls-remote` 核对到 `622d58a`；本交接所在提交及远端 SHA 以最终 Git 核验为准。

远端状态补记：审计本地提交 `b52a0d3` 已创建；第一次推送报 github.com:443 无法连接、第二次报 connection reset、第三次 HTTP/1.1 重试仍无法连接。此时**尚未完成远端备份**，下一次网络可用时先推送并用 `ls-remote` 核验，不能把本地 commit 当作上传成功。

## 本次变更与输入版本

- 新增 `src/cyj/audit_large_extrapolation.py`、`outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json`、`experiments/cyj/20260924-b9-b10-extrapolation-audit.md`；更新本人记忆。未编辑其他成员目录或公共六文件，公共规则仅经 main merge 进入。
- 当前 F 题 DOCX SHA256 `bc99a72460fa3d947a442d502969a13212cebff3b55339da4c4`；清理版数据说明 PDF SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；机器正文为 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。
- 原始 B9/B10 SHA256 `ee794c1c586ed33c485a9eb9a2a3d993790402b63297e9b2765a1387930e940e` / `a240e210c5b37444356c28eea96c6cc36be79c29baae1621c2e08aff727ccfeb`，按 `F_MANIFEST.json`（SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`）核对。B1 draft 曲线 JSON SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`，其原拟合代码/输入版本 `cf297a4ad47e235acf5a9b6e890a5df5e05b07e5`。
- 已读取 `origin/main` 新增 `REPOSITORY_REVIEW_PROTOCOL.md`。历史隐藏文字与作废 Gemini 历史结果未使用。

## 复现命令与证据

```powershell
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/audit_large_extrapolation.py
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
Get-FileHash outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json -Algorithm SHA256
./scripts/verify_raw_data.ps1
```

前两命令实际通过：B9=132、B10=128、精确 join=128；现有测试 37/37。审计输出连续两次 SHA256 一致，为 `53977e436fed3afabd5cb6ba908ff6d1f90a4cd42873209c5ba0d888db311068`；脚本 SHA256 `d44ff78157aa535a3a1c334207a67deeef2566a601445b93b8d10544f88c9c16`。原始 B9 独有 4 个 D=0 模型，B10 全部 N 超出 B1 范围；102 行 D 高于 B1、3 行低于 B1；B10 的 5 个重复 N/D 组内估算 Loss 一致。与 B1 draft 曲线的 RMSE 0.0011047668 仅是描述差异，不能记作真实外推验证。

`git lfs pull` 等待后无进展并已中止；全量校验实际失败：附件 A 的四个压缩文件仍是 LFS 指针，报 size mismatch。B9/B10 已分别通过字节数和哈希核对，不能宣称全库 2,014 文件校验成功。

## 未验证、接口变化与下一步

- **接口变化：无。** `cyj.q3.v1`、`cyj.b7_quality.v1` 与两个 ready=false 保持原状。B10 的 `val_loss` 由可见说明标为估算，来源机制、Loss 坐标和独立性尚不明；本轮只允许“estimated extrapolation stress”使用，不得调参或给外部 RMSE。公共记忆的这一结论请集成人验收后汇总。
- cyj：继续 B1 行级 Loss 来源、B4/B5 绝对可比性与 B7 选模后验证；把完整 Q2 predictor 门槛维持未通过。chm：正式 Q3 不消费 B10 为实测；zhh：能力桥接不把 B10 视为独立验证。全库 LFS 完整性由具备实体 A 数据的成员重跑；官方规则及 2026 模板符合性仍待团队核验。
