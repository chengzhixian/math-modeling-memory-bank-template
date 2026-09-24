# B2/B3 轨迹形状诊断（P20，2026-09-24）

状态：已运行的描述性诊断；不是独立外部验证，也未估计 B1→B2 的绝对 Loss 误差。

## 输入、方法与命令

- 代码/输入提交 `3cd66aeb23d9ceccc3958371bf41a212f6699658`；先前 cyj 远端起点 `4a68df4f0967046581bbd80d03d6259d6f42b375`，所含 `origin/main` 为 `a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。
- B2 `cerebras_training_log.csv`：89,643 bytes，SHA256 `178f878cad2cb31e4ec104c670553de23818197876d824a113fdb911125951a6`。B3 为 `training_trajectories/*.csv` 8 文件、每文件 500 行；各文件身份见结果 JSON 的 `source_files`。所有文件先与 `F_MANIFEST.json`（SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`）逐文件核验；source_manifest SHA256 `34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。
- 可见数据说明将 B2 标为按 Pythia 标度律校准的半合成数据，将 B3 标为 Pythia checkpoint 插值。因此仅计算每个 N 组的首末 Loss 变化和相邻升降次数；不把任一表当作 B1 的独立真实测试集，不计算 B1→B2 绝对 Loss RMSE。

```powershell
$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m py_compile src/cyj/diagnose_b2_b3_shapes.py src/cyj/tests/test_b2_b3_shapes.py
& $py -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
& $py src/cyj/diagnose_b2_b3_shapes.py --input-version 3cd66aeb23d9ceccc3958371bf41a212f6699658
Get-FileHash outputs/cyj/diagnostics/b2_b3_shapes.json -Algorithm SHA256
```

## 实际结果与限制

- B2：1,029 行、7 个 N 组，每组 147 行。按 `steps` 排序，各组首末 `val_loss` 均下降（降幅 3.0342–3.1001）；合计 328/1,022 对相邻 checkpoint 的 Loss 上升。每组只有 143 个不同的显示 D，最后 5 行同为 `D_tokens_B=2050.000`，形成每组 4 对相邻 D 相同；不去重，也不在 `ΔD=0` 处计算斜率。
- B3：8×500=4,000 行、全部 `interpolated=1`。按唯一递增的 D 排序，各组首末 Loss 均下降（降幅 1.9218–1.9293），合计 566/3,992 对相邻插值点 Loss 上升。各文件 `step` 只有 117 个不同值、383 对相邻标签重复，因此不能将 `step` 当作 500 个独立 checkpoint ID。
- 诊断只说明整体下降与局部波动并存。由于 B2 半合成、B3 插值，不得到独立泛化结论，也不证明原经典基线的来源机制。B2 的生成代码、校准目标及与 B1 `val_loss` 的同一评估口径，B3 的行级插值/噪声程序仍未验证。
- 输出 `outputs/cyj/diagnostics/b2_b3_shapes.json`：schema v1，12,567 bytes，固定 LF，SHA256 `bea31afe812a68bb3d2af9c1ea1f0efcbe557e5dee8ad58f785c86cafe9d189e`。连续两次运行哈希一致，完整测试 19/19 PASS。

## 后续

cyj：先核对 B2 的 Loss 生成与 B1 评估配置是否可比；若不可证，只使用组内形状或归一化敏感性而不报跨源绝对误差。继续 B4/B5 分层可比性与 B1 规模分组不确定性。集成人验收后再更新公共记忆；chm 不得将此诊断当作 Q3 validated predictor。
