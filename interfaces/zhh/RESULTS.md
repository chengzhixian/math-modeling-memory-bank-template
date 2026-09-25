# zhh Q4 v2结果索引

状态：**NOT READY（完整Q4未验收）**。2026-09-26重新阅读官方原件，发现技术贡献解释、均值→q90前沿转移、跨题Loss坐标及误差影响尚未闭环；详细证据见 `experiments/zhh/20260926-q4-requirement-reaudit.md`。已有数据/数值与软件复现保留，尚未进入main。

- `outputs/zhh/Q4_FINAL_ANSWER_V2.md`：完整推导、数据角色、贡献、桥接、12/24月及局限。
- `outputs/zhh/q4_results.json` / `q4_v2/results.json`：当前机器结果。
- `outputs/zhh/frontier_forecast.csv`：16条主条件格；chat/领域微调12月算力对数增长减半点值53.488、范围40.409--65.959。范围是情景包络，非95%预测区间。
- `q4_v2/c4_resource_audit.csv` / `c4_usable_resources.csv`：3523行审计、81主资源记录，实际使用Token数。
- `q4_v2/historical_contributions.csv`：窗口/开放性/类型带符号分解及未解释项；占比不解释为因果技术份额。
- `q4_v2/rolling_frontier_backtest_primary.csv`：主10折诊断，后训练组常数/趋势/动力学RMSE2.326/1.605/1.760；基础4折13.006/10.228/14.043，长期预测弱。
- `q4_v2/bridge_validation.csv` / `bridge_source_diagnostics.csv` / `bridge_mappings.csv`：分层模型、来源、支持；formal仍unidentified。
- `q4_v2/q3_bridge_sensitivity.csv`：固定Q3 v8的72条分级记录，33条在支持内允许显式同坐标假设换算，没有实证标定分数或联合CI。
- `c8_bbh_task_aggregation.csv`：1860×24 BBH任务，宏平均/标准差/最弱任务中位49.401/16.934/14.000，4损坏JSON另列。
- `context_scenarios.csv`：C7 2048/8192/131072外生Token接口，哈希保持。
- `q4_v2/manifest.json` / `answer_manifest.json`：输入、代码、Q3、环境与输出哈希。
- `paper/sections/zhh/q4.md` / `paper/latex/sections/zhh/q4.tex`：同步稿；`paper/latex/figures/zhh/`三图。
- `experiments/zhh/20260926-q4-v2-full-review.md`：18阶段Gate和从零red-team。

Node旧基线及撤回预测只在legacy_baseline，不作为当前论文预测。接口调用规则详见CONTRACT.md。
