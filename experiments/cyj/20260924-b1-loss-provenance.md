# B1 Loss 来源数值审计记录

## 输入、代码与命令

- B1 SHA256 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`；B12 索引 SHA256 `0f7f63535cbc1bbef5165776562e71401af9f762cfe02aaea30c824f45fbc9ed`；source manifest SHA256 `34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`；既有 fit SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`。
- 脚本 `src/cyj/audit_b1_loss_provenance.py` LF SHA256 `bb75057abf7ff6efa70c79c30f4154fcd5a9d0c5a78a9aafec2e8e7df8be32ba`；Python 3.12.14 / NumPy 2.3.5，无随机种子。
- 实际命令：

```powershell
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/audit_b1_loss_provenance.py
```

输出 `outputs/cyj/diagnostics/b1_loss_provenance.json` SHA256 `a36bff5075da6911b90b6d2c50ad29a64586f268542fc61e0659cdec3df582da`。脚本严格检查输入哈希、1176 行、`run_id` 唯一、8×147 网格和非有限值；逐 N 计算残差、相邻差与 lag-1 相关，不跨轨迹混合。

## 实际结果与边界

B1 147 个唯一 steps 全在 B12 step 集合；全行 D 与 `steps×2,097,152` token 的三位小数显示相容。`C_FLOPs_1e21` 与 `6ND` 单位换算之差仅在显示舍入带。`ppl` 与自然指数显示舍入全行相容，但这不证明评估语料或聚合方式。`val_loss` 4/3/2 位小数行数为 1055/113/8；8 个 N 轨迹都严格下降；相邻真实变化与既有五参数式变化的 RMSE `0.0002047693`。这些数只描述当前 CSV 及既有同源 fit，不能识别原始生成式或外部误差。完整每组统计在 JSON。

外部官方 Pythia 文档只作为训练条件背景，链接及访问时间见同日问题记录；其模型卡资料并未逐行证明赛题 CSV 的 Loss。下一步若有原始训练日志或评估脚本，应按 checkpoint commit、step、tokenizer、语料及未舍入 Loss 做逐行配对；否则继续标 `unknown`。
