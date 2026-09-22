# 技术环境与复现状态

## 已检查

- 操作系统/终端：Windows / PowerShell。
- 工作区：`H:\研究生数模`；Git 项目：其下 `math-modeling-memory-bank-template/`。
- 当前分支：main；远端：`https://github.com/chengzhixian/math-modeling-memory-bank-template.git`。
- 原始资料位置：项目相邻目录 `../F题/`；包含题面 DOCX、数据说明 PDF 和 `real_attachments/`。
- 附件存在 A_data_value、B_scaling_laws、C_efficiency_evolution 三类目录及 source_manifest.json；尚未完成编号/字段/记录数审计。
- Git 推送兼容方式见 `AGENTS.md`；环境凭证、密钥不写入仓库。
- 成员分支命名方案为 team/a-data、team/b-scaling、team/c-frontier，当前尚未实际创建。每人不同 clone，不通过网盘共享 .git。

## 尚未验证

Python 解释器、科学计算依赖、CPU/GPU/内存、文件读取速度、全量计算耗时均未检查。尚未创建环境锁文件或运行模型，不能宣称已有可复现实验。

## 下一阶段约定

确认运行环境后再固定依赖；代码使用项目相对路径或显式数据根目录参数，不在分析代码内写死个人机器路径。质量信号含压缩 JSONL 和大文件，先评估分块/流式读取；清洗、拟合、优化、绘图拆为可重复执行步骤。

跨机器约定：各成员拟用本地 F_DATA_ROOT 环境变量指向附件根目录，当前还没有分析程序实现读取。各自环境记录在 problem/a|b|c/environment.md，公共最小依赖由集成人协调锁定。原始附件不随当前 clone 自动出现，须另外获取并核对哈希；不同设备结果按明确容差复核。

拟保留的项目布局：`src/` 代码，`experiments/` 实验记录，`outputs/` 图表结果，`paper/` 论文，`problem/` 需求和来源，`data/processed/` 可再生中间数据（默认忽略）。原始资料留在现有位置，待核对共享许可后再决定是否入库。
