# EXP-CHM-Q1-LOCAL：网页成果本地复跑差异

起点：4627133；未恢复或读取作废建模历史。原始附件完整性校验通过。

原网页输出与当前仓库代码不完全匹配。当前代码统一使用 KFold(n_splits=5, shuffle=False)，只使用 A4/A5 选择 alpha。旧网页表的完整折分与生成过程不能由已提交文件确认，不猜测差异原因，也不根据 held-out 结果反向调整折分。

本地复跑发现四个 alpha 改变：wikipedia_en 0.01→0.1，stackexchange 0.1→0.01，gutenberg_pg_19 0.001→0.1，pile_cc 0.001→0.01。完整数值差异见 outputs/chm/q1_local_reproduction_check.json；旧 CV 对照表可从 Git 历史 `44e8db4` 读取。

旧输出已从当前文件树清除，历史快照在 Git 提交 `44e8db4`；本次可复现配比交付统一放在 outputs/chm/local_recheck_v1/。其中文件名沿用脚本的 v0 名称，但目录是新版本边界；不得将旧系数与新尺度校准混用。

本地 Pile-CC Spearman：1M=0.900735、60M=0.891900、1B=0.887592。13 域中位数为 0.838053、0.838115、0.706685。公共 eta=0.14503317，目标域 bootstrap 95% CI=[0.10686793,0.18669841]。总体排序迁移的定性结论未改变。

复现（按序，输出到同一新版目录；命令省略 --output-dir 时也默认写入该目录）：

```powershell
./.venv/Scripts/python.exe src/chm/q1_regmix_domainwise.py --output-dir outputs/chm/local_recheck_v1
./.venv/Scripts/python.exe src/chm/q1_mixture_interface.py --output-dir outputs/chm/local_recheck_v1
./.venv/Scripts/python.exe src/chm/q1_mixture_scale_transfer.py --output-dir outputs/chm/local_recheck_v1
```

这些复跑只用了现有代码及原始附件，没有使用检验集选择新版模型。LightGBM 未运行；Q3 仍缺 cyj 已验证预测接口。
