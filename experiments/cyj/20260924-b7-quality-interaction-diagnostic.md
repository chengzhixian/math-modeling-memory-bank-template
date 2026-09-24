# B7 组内质量斜率诊断（2026-09-24）

状态：已运行，**L1 描述性**；B7 是半合成数据。本诊断在模型比较前使用全部 B7 点，后续候选形式因此属于探索性提出，不能把同一批 B7 分数叫作未见最终测试。

## 输入和复现

- B7 `supplementary_NQ_experiment_expanded.csv`：450 行，SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`；B6 360 行与之精确重叠，按 `quality_scaling.source_data` 排除。
- 现有 B7 constant-G fit：`outputs/cyj/quality/b7_quality_fit.json` SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`。
- 脚本 `src/cyj/diagnose_b7_quality_interaction.py` LF 标准化 SHA256 `096b7e08b2baa0fceb141e97560d1b96476fae28f1070909c2a1741fd3a0d3f1`。Python 3.12.14，NumPy 2.3.5；无随机抽样。运行命令：

```powershell
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/diagnose_b7_quality_interaction.py
```

输出 `outputs/cyj/diagnostics/b7_quality_interaction.json` SHA256 `7977a3ed0614e896e82c316d770b9bb50a3195e4f5e790541ebee6005dc99f50`，包含 45 组原始坐标、每组 Q 斜率/截距/R²/残差统计、按 N/D 汇总、对 `log N/log D` 的二级描述回归，以及绘制五种建议图所需的逐点残差数据。

## 实际结果

450 点构成 45 个固定 `(N,D)` 组，每组 10 个 Q。组内一元 OLS 斜率范围 `[-0.60721818,-0.19307879]`；原 constant-G 给统一斜率 `-0.36199529`，对 45 组斜率的 RMSE `0.10780881`。按 N 组均值由 N=0.07 的 `-0.54468848` 变化到 N=11.97 的 `-0.23461697`。按 D 组均值由 D=10 的 `-0.40450572` 到 D=600 的 `-0.33001886`。斜率与自然对数 `log N`、`log D`、二者同时的描述性 R² 分别为 `0.81592`、`0.04422`、`0.86014`。

这说明 constant-G 的边际斜率在 B7 网格上存在系统失配，支持预注册少量交互候选。二级回归是对已观察 45 个斜率的描述，不是因果效应、真实训练规律，也不证明外推。后续比较须报告 no-Q、constant-G、交互式，按组防止同 `(N,D)` 的十个 Q 泄漏；由于候选灵感来自全部 B7，最终无偏泛化声称需要新的独立数据。
