# B4/B5 支持域与口径复查

脚本 `src/cyj/audit_b4_b5_comparability.py` LF SHA256 `5a3b352afec0acaecf46c16ad4b1ac0fd3d6a88298241b80f46d066cee786d28`。输入 B1/B4/B5 原件 SHA256 分别为 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`、`2272983ded93de35e05f9acbf95ebceedf43f283345e4be72b54fee94080391e`、`dd858c5e48610e28589340d5db023d6abfb31df597506789ccdfc6a546731bbd`。Python 3.12.14，无随机抽样。

```powershell
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/audit_b4_b5_comparability.py
```

输出 `outputs/cyj/diagnostics/b4_b5_comparability.json` SHA256 `28c3efa18b2acdd417e2a2f31d5163ead256ed07eabe7f9bf5fdd077611f79e1`。57 个 B4 中仅 8 个在 B1 N/D 矩形内，44 个 B5 中仅 8 个在内。B4 有 8 个 Pythia 标称规模行，但与 B1 同评价 checkpoint/语料/计算公式无法逐行匹配；近邻展示只为发现风险，不能成为误差指标。脚本不计算池化 RMSE，机器门槛显式为 `same_loss_coordinate=not_established`。
