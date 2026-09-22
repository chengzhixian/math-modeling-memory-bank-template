# 技术环境与复现状态

## 已检查

- 操作系统/终端：Windows / PowerShell。
- 工作区：`H:\研究生数模`；Git 项目：其下 `math-modeling-memory-bank-template/`。
- 当前分支：main；远端：`https://github.com/chengzhixian/math-modeling-memory-bank-template.git`。
- 原始资料位置：仓库 `problem/F/`（题面 DOCX、数据说明 PDF）与 `data/raw/real_attachments/`（全部附件）。统一索引为 `memory-bank/DATA_INDEX.md`。
- Git LFS 已在本机本仓库初始化，四个 .jsonl.xz 由 LFS 管理，其余附件正常 Git 管理；.gitattributes 对原始资料禁用换行转换。
- 本机沙箱内 LFS 启动器路径不稳定，仓库本地 filter 与新安装的 LFS hooks 已改用 `H:/Git/mingw64/bin/git-lfs.exe` 实体程序；这些仅属于 .git 本机配置，不随克隆分发。其他成员正常安装 Git LFS 即可。
- 迁移前后逐文件校验通过：2,014 文件、551,761,350 字节；清单 `data/raw/F_MANIFEST.json`，命令 `./scripts/verify_raw_data.ps1`。这只证明内容完整，不代表数据字段或研究结论已验证。
- 附件存在 A_data_value、B_scaling_laws、C_efficiency_evolution 三类目录及 source_manifest.json；尚未完成编号/字段/记录数审计。
- Git 推送兼容方式见 `AGENTS.md`；环境凭证、密钥不写入仓库。
- 成员分支命名方案为 team/a-data、team/b-scaling、team/c-frontier，当前尚未实际创建。每人不同 clone，不通过网盘共享 .git。

## 尚未验证

Python 解释器、科学计算依赖、CPU/GPU/内存、文件读取速度、全量计算耗时均未检查。尚未创建环境锁文件或运行模型，不能宣称已有可复现实验。

## 下一阶段约定

确认运行环境后再固定依赖；代码使用项目相对路径或显式数据根目录参数，不在分析代码内写死个人机器路径。质量信号含压缩 JSONL 和大文件，先评估分块/流式读取；清洗、拟合、优化、绘图拆为可重复执行步骤。

跨机器约定：各成员拟用本地 F_DATA_ROOT 环境变量指向仓库 data/raw/real_attachments，当前还没有分析程序实现读取。各自环境记录在 problem/a|b|c/environment.md，公共最小依赖由集成人协调锁定。clone/pull 后执行 git lfs install --local、git lfs pull，并运行完整性校验；不同设备计算结果按明确容差复核。

项目布局：`src/` 代码，`experiments/` 实验记录，`outputs/` 图表结果，`paper/` 论文，`problem/` 题面/需求/来源，`data/raw/` 原始附件及完整性清单，`data/processed/` 可再生中间数据（默认忽略）。原始资料只读，未来变更必须保留版本和来源。
