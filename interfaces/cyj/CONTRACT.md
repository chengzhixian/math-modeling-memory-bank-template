# cyj 交付约定 草案 v1.3

生产者 cyj；使用者 chm（Q3）、zhh（桥接及论文）。本版为生产者侧草案，尚未取得 chm/zhh 验收，不能标记 validated。

## 已有审计交付

- `outputs/cyj/b_data_audit.json`，schema_version=2，状态为 audit-only。
- 输入/代码版本：`6880af29f2a1fc089e5fc601d0df873c0be042a3`。
- 输出 SHA256：`120b97a4089c3272fd121a8d7ae4867d0c65754d4953a4ec74723d67c2b7bed7`，138,365 bytes，LF 换行。
- 生成命令：`python src/cyj/audit_b_scaling_laws.py --input-version <SHA>`；实际 Python 路径和版本见 `problem/cyj/environment.md`。
- 输出字段：逐文件 path/bytes/SHA256/rows/columns/header/missing/duplicate/row-width/numeric/positivity/source metadata，以及 check_id/status/evidence/note；provenance 记录 commit、脚本/清单 SHA、Python 版本和生成时间。
- 该文件不包含拟合参数或预测，不得作为 Q3 的预测接口。

数据使用边界：B1 为主拟合候选并按模型规模/轨迹分组；B2 只作半合成稳健性；B3 只作插值轨迹形状检查；B4/B5 经 Loss 可比性核对后作外部验证候选；B6–B8 保持半合成标记且 B8 extrapolated 不进入拟合；B9 为大模型元数据，B10 只作附件估计一致性参考而非 ground truth。完整限制见 `problem/cyj/b_data_audit.md`。

## 计划中的模型交付

建议交付：
- 模型说明：Loss 精确定义、尺度、数学表达式、N/D/Q/p 顺序与单位、有效范围、模型族及跨来源假设。
- 参数文件：参数名/估计值、拟合方式、不确定性表达、输入版本、实测/估算/半合成来源标记。具体模型形式由团队确定。
- 可调用预测入口或独立复现命令：输入 N/D/Q/p，输出预测 Loss；同时给出小型真实核验案例和容差。占位案例只能用于接口测试，不能用于论文。
- Q3 理论说明：目标、三项成本、约束、质量基线、边界条件、成本参数来源、结构性转移的识别定义；与 chm 协商实现但不修改 chm 代码。
- 验证结果：B1 拟合、B2/B3、B4/B5、质量补充、B9/B10 外推的分别表现。

输出放 outputs/cyj/，预测实现归 src/cyj/；chm 通过约定接口调用。zhh 使用可比的 Loss 定义和版本，禁止把异质验证损失直接拼接。

模型接口必须另发版本并包含 manifest、参数单位、有效范围、验证结果与小型真实核验案例。在该文件出现并通过实际验证前，消费者不得用审计 JSON 替代预测结果。

## 经典 N-D 基线交付（draft，不可启动 Q3）

- 代码/输入提交：`3b9cbff1362349bd9dc9d94d56c409f7d93654be`。
- 模型：`L(N,D)=E+A*N^(-alpha)+B*D^(-beta)`；N=十亿参数，D=十亿 token，L=B1 `val_loss`。
- 有效拟合范围：N 0.070542–11.965825 B，D 0.134–299.893 B token；范围外必须标注外推。
- 参数：E=1.6898377713，A=0.3539687193，B=1.2402746295，alpha=0.3399854258，beta=0.2798924656。
- 主结果：`outputs/cyj/classic/classic_fit.json`，7,759 bytes，SHA256 `b3706500bf79c191b7b05bf7af3dd963d1fb149fe47e304edb30cc9ad023893e`。
- 数据 manifest：`outputs/cyj/classic/classic_data_manifest.json`，4,109 bytes，SHA256 `2fd70f2f174e5398a21cafa423309be68f6f3c702d1e22a0331c6547b0e2bc9a`。
- 验证：全样本 RMSE 0.0001465764；按规模留组 8 折 RMSE 均值 0.0001461277；每组 token-tail 70/30 RMSE 0.0001160041；没有随机逐行拆分。
- 状态：`draft_classic_baseline_not_validated_predictor`，`ready_for_Q3=false`。

三种验证均触发 near-exact reconstruction 诊断。该现象可能来自共同的确定性构造或强预处理，不是独立真实泛化证据。B4/B5 的 tokenizer、评估语料、Loss 定义和单位等价性没有本地证据支持，因此 `absolute_loss_comparability=not_established`；`external_predictions_unvalidated.csv` 只供描述性检查，不提供 external RMSE。

本版没有 Q、p、参数/预测区间、Loss–Benchmark 桥接或 Q3 可调用的 validated predictor。chm/zhh 不得把五参数点估计或 B4/B5 原始差值当作全队冻结接口；后续升级需先完成 Loss 来源审计、分组不确定性，并由 chm+cyj 联合冻结 Q mapping 与 Loss/anchor/p 接法。
