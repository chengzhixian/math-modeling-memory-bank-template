# B1 显示计算量精度与八行敏感性（P20，2026-09-24）

状态：已运行的同源诊断；不是独立来源验证、外部验证或 Q3 validated predictor。

## 输入与复现

- 本轮代码/输入提交：`351ea0e0eaeab0226550311d8fcb9a855cebcc2d`；`origin/main` 起点 `a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。
- B1：`pythia_training_log_existing.csv`，111,459 bytes，SHA256 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`；`F_MANIFEST.json` SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`；source_manifest SHA256 `34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。
- 原 B1 prepared SHA256 `2eb418f022c414db13af89d2177b2b90c62d3ad3b29300adf7fb1de570927704`；原 classic_fit SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`，基线代码/输入提交 `cf297a4ad47e235acf5a9b6e890a5df5e05b07e5`。
- 运行前校验代码与指定提交相同、B1 与清单相同、原拟合与已审哈希相同、prepared 与原拟合 provenance 相同。原 CSV 和原基线输出均未改写。

```powershell
$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
& $py src/cyj/diagnose_b1_precision.py --input-version 351ea0e0eaeab0226550311d8fcb9a855cebcc2d
Get-FileHash outputs/cyj/diagnostics/b1_precision_sensitivity.json -Algorithm SHA256
```

## 结果与推断边界

- 全部 1,176 行显示计算量与 `round(0.006*N_params_B*D_tokens_B, 4)` 匹配，最大绝对误差 `4.994688e-05`（`1e21 FLOPs`）。相对误差超过 5% 的 8 行 ID 为 8、9、10、11、162、163、316、317；绝对差均在四位小数舍入半单位内。结论限于 CSV 表示精度，不能确认原始未舍入 FLOPs 是测量值还是推算值。
- 保留全部行的原基线 RMSE `0.0001465764192`。仅剔除上述 8 行并以相同 seed=20260924、24 starts、1600 最大迭代重拟合：收敛；新拟合在全部行上的 RMSE `0.0001466067481`，在保留的 1,168 行上 RMSE `0.0001442004291`，全部行最大预测变化 `7.6651953e-06`。
- 这是同一附件 B1 上的点估计敏感性，不是与原拟合独立的数据。近乎精确重构的 Loss 来源问题仍未解决。可见数据说明称 B1 为 Pythia 轨迹；[EleutherAI 官方仓库](https://github.com/EleutherAI/pythia)与[模型卡](https://huggingface.co/EleutherAI/pythia-70m)只用于背景交叉核对（2026-09-24 访问），不能代替本地逐条 `val_loss` 的评估记录、分词器/评测语料或 checkpoint 映射。
- 新输出 `outputs/cyj/diagnostics/b1_precision_sensitivity.json`：schema v1，7,010 bytes，SHA256 `c7c8b346e4cdbec6034aead4f959ea7f60aa14b52ad6cd00169ea98033356fd7`，固定 LF 换行。同一命令连续两次输出 SHA256 一致；`unittest` 16/16 PASS。结果 JSON 的 `unverified` 保留来源、Q/p 与 Loss anchor 未验证项。

## 下一步

cyj：寻找 B1 逐条 Loss 生成/评估配置的独立可核验证据；若得不到，保持近乎精确重构的来源警报。继续按规模 bootstrap、B2/B3 结构与 B4/B5 分层可比性。chm+cyj 联合冻结 Q mapping、Loss anchor 和 p 接法之前，不给 Q3 validated predictor。
