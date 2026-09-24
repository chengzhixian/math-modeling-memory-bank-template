# CYJ → CHM：Q2 条件 v3 与真实求解器联调（2026-09-25）

## 输入与发布

- CYJ 分支：`team/cyj-scaling`；不可变 v3 发布提交：`e36aa23143bda9f027853f5af825728625750c5b`。该提交的 `chm_consumer_smoke_v3.py --release-commit e36aa23143bda9f027853f5af825728625750c5b` 为 PASS，2 请求；manifest SHA256 `059ecb420f7277a93c0f20714c76978ea5e739d3a3dff9c916fff11df2ff9f66`。GitHub 连接超时后已补推，`ls-remote` 核实远端 `team/cyj-scaling` 与该发布提交同 SHA。
- CHM 目标精确提交 `92e0592000cba58fca355a881dc59caadbd446b2`；固定 Q1 生产者 `a5525935b37f873235d2f650e4810a787b9a8788`，manifest SHA256 `5885317d072739b02cdbb434fc730dde07510eb284dc857e35863adc877e914d`。
- B7 原件 SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`；模型输出 `ed6b01b113110b90b25c5f6cc01d7686cb77602f29464bc068843b36d881c9bf`；留级验证 `cae1c827587c49d6484d2fcdb7686f9202f522aacdb39d5f63f74085d422491d`；经验不确定性 `54c2ceb24472aa1bc53f3207d0064529545fa37385f6f5845114b88657121608`。

## 模型、范围和科学状态

$L_B=E+AN^{-\alpha}+BD^{-\beta}+(1-Q)[G_0+G_N\ln N+G_D\ln(D/100)]$。完整 B7 拟合 $(E,A,B,\alpha,\beta,G_0,G_N,G_D)=(1.6235020159,0.4533304306,1.2544668587,0.2832175643,0.2995752931,0.3694134188,-0.0539598879,-0.0147389370)$。N=[0.07,11.97] 十亿参数，D=[10,600] 十亿 token，Q=[0.1,1] B 原生分数；支持域外拒绝。Q 增益在整个矩形内为正。24 折 N/D/Q 固定族留级、1350 条 OOF、500 次 ND 簇 bootstrap 均已记录；三轴平均 RMSE 0.051936/0.050207/0.050061，低于恒定 G 基线。经验预测区间已有数值，但未独立校准。

接口 `cyj.chm.v3` 的 `candidate_result_scope=NDQ_with_p_sensitivity`；`formal_result_scope=null`、`ready_for_Q3=false`。B7 族在查看完整数据后提出，此后固定族重复 CV 不能充当未触碰最终测试。B7 也属半合成，不能说已被真实训练外测。A 侧 17 域 p 仅来自 CHM Q1 v1.2 的 13 target 局部敏感性，`B_loss_addition_allowed=false`、`unique_p_claim_allowed=false`；A/B Loss 和 Q 桥接未识别，U4=null，Q4 Benchmark 桥接 U5 不属 CYJ 且未消费。没有旧 eta、默认 lambda 或统一四维 Loss。

## 测试与消费者用法

- `python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q`：51/51 PASS；v3 manifest 两次重建 SHA 相同；批量 CLI 两请求 PASS；XeLaTeX 总稿编译 7 页 PASS，无 Overfull/Undefined。
- CYJ 本机从 CHM 精确 Git 对象导入原版 `q3_generic_solver.py`，经 `CHMAdapterV3.value_grad → Support → solve_generic` 跑 27 场景：24 可行收敛、KKT 必要条件检查通过；3 个预算 1e19、上下文 131072 的场景明确 `infeasible_by_supported_domain`。输出 SHA256 `0a6dc8e9696dabf70cf625d26d8f98ee1b063fedd674df4eb9b529e6b8daf839`。这是本机软件联调，不是 CHM 所有者 acceptance，数值最优点不作正式论文结论。
- CHM 拉取精确发布后，按 `interfaces/cyj/CHM_API_V3.md` 运行 builder、release smoke、`CHMAdapterV3(mode="conditional_diagnostic")`，把 `bounds` 映射为本人求解器的 `Support(N,D,Q)`，D 下界必须为 10。`value_grad` 可直接消费；SLSQP 边界浮点容差须由 CHM 包装明确处理，不能放宽科学域。`evaluate` 返回点预测、梯度、弹性、替代率、经验区间、成本和分开的 p 敏感性。低预算应明确报支持域不可行。
- CHM 需在本人分支验收并记录：精确 CYJ release 与 CHM commit、release smoke、1 个可行 solver case、27 场景状态、`bounds → Support` 包装及是否承认仅条件诊断。集成人验收后才可更新公共记忆和正式 Q3 状态。
- 随后的接口目录清理已把 `CONTRACT.md` 当前入口改为条件 v3，并在 `CHM_API_V2.md` 标明 `deprecated_for_formal_Q3=true`；v2 旧 solver 边界描述仅作当时发布历史。此文档清理不改 v3 不可变代码发布及 manifest。
- 此清理及交接的远端检查点已核实为 `33a214a89c7cf2e2cd535fe20b71697c2c83b63b`（`ls-remote` 与 PR head 一致）；PR #3 已更新并保持 Draft。

## 分支合并检查

对 `CYJ@e36aa23143bda9f027853f5af825728625750c5b` 与 `CHM@92e0592000cba58fca355a881dc59caadbd446b2` 运行 `git merge-tree --write-tree --name-only --messages`；merge base `968ef7a36f1503aa222a0b09c8a8cb5d0f535ecd`。仅 `paper/latex/sections/cyj/q2.tex`、`paper/latex/sections/cyj/q3_theory.tex` 两处内容冲突，均属 CYJ 章节。集成人合并时应以本发布的 CYJ 正文取代 CHM 占位稿并重新编译，且核对 CHM 之后是否对占位稿做了实质修改。未在本人分支合并 CHM 文件。

## 未解决问题与负责人

cyj：补足真正独立的族验证／预测区间覆盖校准证据后才能请求正式 gate；继续维持 v3 条件状态。chm：现可拉取精确发布，完成本人分支 consumer acceptance 和 Q3 正式准入判断。集成人：处理两处论文冲突、验收并更新公共记忆。PR #3 保持 Draft，描述应写科学门槛和团队验收未完成。
