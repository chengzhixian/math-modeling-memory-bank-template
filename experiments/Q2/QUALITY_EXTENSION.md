# Q2 v8 冻结质量扩展实验

精确数值来源为 CYJ v8 生产者 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`；后续远端 `team/cyj-scaling@74e678e319b58e2aab230a7b7233fa53f3053fa5` 只新增 Q3 合作计划，没有替换 v8 冻结参数。完整命令和文件哈希见 `outputs/Q2/upstream_manifest.json`，本目录仅登记主实验的可复现逻辑与评价边界。

1. B1 的 1,176 条 Pythia 日志以 `N_params_B,D_tokens_B,val_loss` 建立五参数 `L_0(N,D)`。八个模型规模组的留组检验用于同源重构，不当作独立外部实验。参数与基线证据见 `B1_BASELINE.md` 及 `outputs/Q2/model_coefficients.json`。
2. 在固定 B1 主干后，用 B7 的 450 条**半合成** `Q_score,val_loss` 估计三参数 `G(N,D)=G0+GN ln N+GD ln(D/100)`，形成 `L_B=L_0+(1-Q)G`。岭强度 0、0.001、0.01 由内部留级选择；N/D/Q 三轴各留一等级，共 24 个外层折。冻结文件 `outputs/Q2/b7_quality_extension.json` 记录每折选择与误差，三轴外层平均 RMSE 为 0.048738、0.048751、0.048639。比较文件 `b7_backbone_comparison.csv` 保留基线与质量项消融。B6 坐标嵌在 B7 中，不能重复当独立外测；B8 冲突源隔离。
3. Q1 的 `Q_A(p)` 到 B7 `Q_score` 的保序代理和 A 侧相对配比效应到 B 侧 Loss 的指数桥是显式条件假设。`outputs/Q2/quality_bridge_sensitivity.csv` 用不同映射斜率展示数值依赖；`requirement_evidence.csv` 固定每项题面要求、数据角色和证据。没有 A/B 同条件成对样本，因此桥接系数、独立 Q/p 作用和跨源因果效应不可识别。

在来源提交运行 `python -B src/cyj/fit_b7_quality_extension_from_b1.py`，再运行 `python -B src/cyj/build_q2_v8.py`；以 `src/cyj/verify_v8_fixtures.py` 和 `src/cyj/tests/test_ndqp_v8.py` 核对接口。输入 B1/B7、Q1 清单、代码及结果的 SHA256 见上游清单。正式 N/D 支持交集为 N `[0.070542,11.965825]` 十亿参数、D `[10,299.893]` 十亿 token；支持外推、B10 estimated 和 B4/B5 跨家族绝对 Loss 都不作主模型验证。
