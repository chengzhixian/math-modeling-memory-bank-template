# F 题资料入口

用户于 2026-09-23 明确要求将题面和原始附件迁入协作仓库，让其他成员获取。原始资料按项目职责放入 problem/ 与 data/raw/，本文件作为 memory bank 的统一入口。远端当前为公开仓库。

| 内容 | 仓库位置 |
|---|---|
| F 题题面 | [题面 DOCX](../problem/F/算力约束下提升大语言模型能力的资源配置建模.docx) |
| 数据说明 | [数据说明 PDF](../problem/F/数据说明.pdf) |
| 附件 A：数据质量与配比 | [A_data_value](../data/raw/real_attachments/A_data_value/) |
| 附件 B：标度律 | [B_scaling_laws](../data/raw/real_attachments/B_scaling_laws/) |
| 附件 C：评测与技术演进 | [C_efficiency_evolution](../data/raw/real_attachments/C_efficiency_evolution/) |
| 原始来源清单 | [source_manifest.json](../data/raw/real_attachments/source_manifest.json) |
| 本次全部文件的字节数与 SHA256 | [F_MANIFEST.json](../data/raw/F_MANIFEST.json) |
| 完整性校验脚本 | [verify_raw_data.ps1](../scripts/verify_raw_data.ps1) |

共 2,014 个原始文件，551,761,350 字节（约 526.2 MiB）。其中 2 个为题面/数据说明，2,012 个为附件。迁移不改写内容，原始资料在 .gitattributes 中禁用换行转换。

## 队友如何获取完整文件

电脑先安装 Git 与 Git LFS。在仓库目录执行：

```sh
git lfs install --local
git fetch origin
```

尚未 clone 的成员先按 TEAM_WORKFLOW.md 克隆。已有个人分支按协作流程合并 origin/main；在 main 上且工作区干净时可用 `git pull --ff-only`。随后执行：

```sh
git lfs pull
```

四个 `.jsonl.xz` 由 Git LFS 保存实际内容。只下载普通 Git 指针不等于下载数据；不要把网页下载 ZIP 作为完整性凭据。Windows 在仓库根目录运行：

```powershell
./scripts/verify_raw_data.ps1
```

校验结果必须为 PASS、Files=2014、Bytes=551761350。其他系统可以使用 PowerShell 7 运行同一脚本，或按 JSON 清单逐文件核对 SHA256 与字节数。

后续分析程序的数据根目录统一指向 `data/raw/real_attachments`；如采用环境变量，可在 PowerShell 设置 `$env:F_DATA_ROOT = (Resolve-Path 'data/raw/real_attachments').Path`。当前尚无分析程序，该设置是后续实现约定。

原始资料只读；清洗结果写入 data/processed/ 或成员 outputs/。模型开始工作时先读本索引，随后按需要读取题面、说明与本人负责的附件，不应将全部数据塞入对话上下文。
