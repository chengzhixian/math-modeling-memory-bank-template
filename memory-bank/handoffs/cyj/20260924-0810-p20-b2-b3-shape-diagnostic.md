# cyj / P20 B2-B3 轨迹形状交接

状态：描述性诊断已运行、待集成人验收；Q2 未完成、Q3 predictor 未 validated。个人分支 `team/cyj-scaling`，本轮工作起点/已核远端 SHA `4a68df4f0967046581bbd80d03d6259d6f42b375`，当时 `origin/main=a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。诊断代码/输入提交 `3cd66aeb23d9ceccc3958371bf41a212f6699658`；本交接自身的最终提交 SHA 以 Git 记录为准。

## 范围、输入与命令

- 本次只修改 `src/cyj/diagnose_b2_b3_shapes.py` 及其测试、`outputs/cyj/diagnostics/b2_b3_shapes.json`、cyj 实验/问题/接口文件、本人记忆和本交接；未修改原始 CSV、公共记忆、其他成员文件或原经典基线结果。
- B2 `cerebras_training_log.csv`：89,643 bytes，SHA256 `178f878cad2cb31e4ec104c670553de23818197876d824a113fdb911125951a6`。B3 为 8 个 `training_trajectories/*.csv`，各文件 bytes/SHA256 全列在结果 JSON。`F_MANIFEST.json` SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`，source_manifest SHA256 `34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。脚本校验代码与清单属于指定 Git 提交、逐文件校验数据身份。

```powershell
git status --short --branch
$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m py_compile src/cyj/diagnose_b2_b3_shapes.py src/cyj/tests/test_b2_b3_shapes.py
& $py -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
& $py src/cyj/diagnose_b2_b3_shapes.py --input-version 3cd66aeb23d9ceccc3958371bf41a212f6699658
Get-FileHash outputs/cyj/diagnostics/b2_b3_shapes.json -Algorithm SHA256
```

## 实际证据与解释边界

- `unittest` 19/19 PASS、编译 PASS。B2 1,029 行分成 7×147；各组首末 Loss 下降，但 1,022 对相邻 checkpoint 中 328 对上升。各组 143 个不同显示 D，尾部 5 行同为 2050.000，形成 4 对 D 平台；不能把平台处 `ΔD=0` 当有效斜率，亦未静默去重。
- B3 8×500 全部标为插值，各曲线首末 Loss 下降，但 3,992 对相邻插值点中 566 对上升。每文件只有 117 个不同 `step` 标签、383 对相邻重复；按唯一递增 D 而非 `step` 做顺序检查。
- 结果 `outputs/cyj/diagnostics/b2_b3_shapes.json` schema v1，12,567 bytes，固定 LF，SHA256 `bea31afe812a68bb3d2af9c1ea1f0efcbe557e5dee8ad58f785c86cafe9d189e`；连续两次重跑哈希一致。B2 半合成、B3 插值的数据性质来自可见数据说明，不能将形状检查写成独立真实外部验证。本轮没有计算 B1→B2 绝对 RMSE。

## 未验证、接口变化、依赖与下一步

- B2 生成代码、Pythia 校准目标、评测语料/分词器和与 B1 的 Loss 同尺度关系未独立核实；B3 行级插值/噪声程序、B1 原始 Loss 来源也未核实。不能从总体下降推断逐点单调、独立泛化或跨来源绝对误差。
- `interfaces/cyj/CONTRACT.md` v1.5→v1.6，仅新增 schema v1 的形状诊断，原经典基线五参数与 `ready_for_Q3=false` 不变。Q_A 与 B6-B8 Q_score 不等同、13 域 Loss 与 B1 val_loss 不等同；chm+cyj 仍需联合冻结 Q mapping、Loss anchor/p 接法及误差。zhh 的 C7 为外生情景，Q4 仍须传播 Loss–Benchmark 桥接误差。
- cyj 下一步：B1 按规模不确定性、B2 生成/同尺度证据、B4/B5 分层 Loss 可比性；未获得独立证据时只交趋势/情景。chm 在 cyj validated predictor 出现前不启动 Q3 正式优化。集成人核验结果后再更新公共记忆，勿将本交接结论提前视为 main 共识。
- PR：已推送的 B1 检查点在 GitHub 内置浏览器中因未登录暂未能创建 draft PR；用户已被请求登录。若后续创建，标题使用 `cyj：完成的内容` 格式且保持 draft 直到接口验收。
