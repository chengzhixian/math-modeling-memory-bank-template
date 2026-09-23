# chm 交接：Q1 逐域 RegMix、尺度传递与质量方法冻结

日期：2026-09-23 19:33（北京时间）
角色：chm
分支：team/chm-data
状态：进行中
工作基线：本次工作从 Q1 首轮数据审计之后继续。

## 本次完成

### A. 配比模型从“平均 Loss”纠正为“逐目标域”

初始诊断 EXP-CHM-Q1-001 证明直接平均 13 个原始 Loss 会显著破坏跨尺度排序信号，因此主模型改为 13 个目标域分别建模。

逐域 Ridge 仅用 A4+A5 做 5 折 CV 选 alpha，在 A6–A11 上一次性检验。

Pile-CC Spearman：
- 1M 约 0.902；
- 60M 约 0.893；
- 1B 约 0.881。

全部 13 域的中位 Spearman：
- 1M 约 0.838；
- 60M 约 0.838；
- 1B 约 0.696。

A6/A8 为同一组 256 配方，其真实 Loss 1M↔60M 的逐域 Spearman 中位数约 0.9944。

### B. 组成约束接口

p 在建模前归一化。Ridge 系数转换为零和对比形式，保证在 \sum(p)=1 的单纯形上参数表示唯一到“均值平移”规范：

\[
\sum_j \beta_{k,j}=0.
\]

输出：
- outputs/chm/mixture_effect_ridge_v0.csv
- outputs/chm/mixture_effect_ridge_v0_manifest.json
- src/chm/q1_mixture_interface.py

### C. 配比效应规模衰减

完成验证后，使用 A6–A11 做 post-validation calibration：

\[
L_k(N,p)=a_k(N)+b_k(N)s_k(p)+epsilon.
\]

13 域 b_k 全部为正。公共固定效应尺度衰减：

\[
\log b_k(N)=c_k-\eta\log(N/10^6)+epsilon.
\]

得到：
- eta ≈ 0.14537；
- bootstrap 95% CI ≈ [0.10787, 0.18686]；
- eta_k 范围约 [0.04467, 0.30742]。

只作为经验尺度传递，不作为正式 Scaling Law。

输出：
- outputs/chm/mixture_scale_calibration_v0.csv
- outputs/chm/mixture_reference_v0.csv
- outputs/chm/mixture_scale_transfer_v0_manifest.json
- src/chm/q1_mixture_scale_transfer.py

### D. 质量 Q 方法和程序

完成：
- problem/chm/q1_quality_method.md
- src/chm/q1_quality_analysis.py

脚本会在 git lfs pull 后实际处理 A1–A3，做：
- 8 个列表型字段压缩；
- 稳健变换与标准化；
- 自动方向锚定；
- 冲突指标分析；
- 三类指标平衡聚合 Q；
- bootstrap CI；
- arxiv/github sample vs extended 验证；
- expectation vs argmax 压缩敏感性。

当前网页环境未读取 A1–A3 LFS 正文，所以这些结果仍为待运行，禁止填假数字。

### E. Q1 论文工作稿

已生成：
- paper/sections/chm/q1_draft.md

其中真实已验证配比结果已写入；质量结果使用 [PENDING-LFS] 占位。

### F. 接口文档

interfaces/chm/CONTRACT.md 已更新至 v1.2，明确：
- 不交“13 域原始 Loss 平均值”；
- p 接口以 13 个目标域代理函数为主；
- 提供 centered mixture effect 与尺度传递；
- Q2 必须根据 Loss 口径选择 anchor，并做多目标域敏感性。

## 需要 Codex / 本地继续执行

在 team/chm-data 最新提交上：

```powershell
git pull --ff-only
git lfs pull
powershell -ExecutionPolicy Bypass -File scripts/verify_raw_data.ps1
python src/chm/q1_regmix_domainwise.py
python src/chm/q1_mixture_interface.py
python src/chm/q1_mixture_scale_transfer.py
python src/chm/q1_quality_analysis.py
```

若安装 LightGBM，再运行：

```powershell
python src/chm/q1_regmix_domainwise.py --run-lightgbm
```

注意：
- 本地复跑与仓库记录不一致时，不得静默覆盖；
- A12–A15 始终标为 estimated/extrapolated；
- 禁止恢复作废历史隐藏文字衍生方法和数值。

## 给 cyj 的最短说明

请先读 interfaces/chm/CONTRACT.md v1.2。Q2 的 p 项不要使用 13 域原始 Loss 平均值。当前可用的是逐目标域 `mixture_effect_ridge_v0` 和经验 `mixture_scale_transfer_v0`。若你的 Q2 Loss 可与某一目标域对应，可选 anchor，并至少用多个目标域做敏感性；pile_cc 是候选但不是自动默认。Q 的正式数值仍待 A1–A3 LFS 实跑。

## 下一步

chm 下一块优先做：
1. 配比结果自动图表与表格生成；
2. Q1 结果摘要和论文图表接口；
3. 等 LFS 实跑后冻结 domain_quality；
4. 完成 Q1 后转入 Q3。
