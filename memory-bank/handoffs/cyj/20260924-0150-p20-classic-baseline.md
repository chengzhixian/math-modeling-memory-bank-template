# cyj 交接：P20 无泄漏经典 N-D 基线

- 角色：cyj。
- 任务：完成 B1 数据准备、经典 N-D 标度律基线、按规模留组与 token-tail 验证，并建立 B4/B5 可比性边界。
- 状态：代码和正式输出已运行验证；接口为 draft，`ready_for_Q3=false`。
- 分支：`team/cyj-scaling`。
- 工作起点 SHA：`35a777e76ef37261ee4c3f37ee96bea58994d394`。
- main 基线：`a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。
- 正式代码/输入 SHA：`3b9cbff1362349bd9dc9d94d56c409f7d93654be`。

## 输入版本与边界

- B1 输入：`data/raw/real_attachments/B_scaling_laws/B1_neural_scaling_law.csv`，1,176 行、8 个 N 规模组、每组 147 行。
- B4/B5：仅作 Loss 可比性审查和描述性预测；未建立绝对 Loss 等价性。
- `data/raw/F_MANIFEST.json` SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`。
- `data/raw/real_attachments/source_manifest.json` SHA256 `34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。
- 准备脚本 SHA256 `127f581474be09e6fc5ee8613b5688d7a73cd9b02cd91439687e65a40406ed48`；拟合脚本 SHA256 `8fa1e199786d5cc9140a39833713b23cebae2dff6b62c25a99e1e33b4125296a`；共享数学工具 SHA256 `1fd6c6bd34e27a7f177224c3e43a236f4f241605fcee681d53a4db827867507d`。
- 外部评审 Markdown 只作为建议输入，未将其中断言直接当事实；未读取或恢复被禁历史提交，也未使用隐藏 PDF 内容。

## 修改文件

- `src/cyj/scaling_common.py`
- `src/cyj/prepare_scaling_data.py`
- `src/cyj/fit_classic_scaling.py`
- `src/cyj/tests/test_classic_scaling.py`
- `outputs/cyj/classic/` 下 9 个正式输出
- `experiments/cyj/20260924-classic-baseline.md`
- `problem/cyj/classic_scaling_baseline.md`
- `problem/cyj/environment.md`
- `interfaces/cyj/CONTRACT.md`
- `memory-bank/members/cyj.md`
- 本交接文件

未修改公共 memory-bank、公共 interface、他人成员目录或原始数据。

## 实际命令

```powershell
git status --short --branch
git rev-parse HEAD

$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m py_compile src\cyj\scaling_common.py src\cyj\prepare_scaling_data.py src\cyj\fit_classic_scaling.py
& $py -m unittest discover -s src\cyj\tests -p 'test_*.py' -v
& $py src\cyj\prepare_scaling_data.py --input-version 3b9cbff1362349bd9dc9d94d56c409f7d93654be
& $py src\cyj\fit_classic_scaling.py --input-version 3b9cbff1362349bd9dc9d94d56c409f7d93654be
```

Python 3.12.14、NumPy 2.3.5、pandas 3.0.1。pytest、SciPy、scikit-learn、statsmodels、JAX、PyTorch 未安装；测试使用 `unittest`，拟合使用纯 NumPy 固定种子多起点 Nelder-Mead，没有把未运行工具写成已验证。

## 结果证据

- `py_compile` PASS；13/13 `unittest` PASS。
- 数据准备 PASS：B1 1,176 行/8 组；每组前 102 行训练、后 45 行 token-tail 测试，总计 816/360；没有随机逐行拆分。
- 模型：`L=E+A*N^-alpha+B*D^-beta`，N/B、D/B token、L/B1 `val_loss`；每个 N 组总拟合权重相等。
- 参数：E=1.6898377713、A=0.3539687193、B=1.2402746295、alpha=0.3399854258、beta=0.2798924656。
- 全样本 RMSE 0.0001465764；8 折 LOSO RMSE 均值 0.0001461277（标准差 0.0000343734）；token-tail RMSE 0.0001160041。
- M0 log-linear 对照 RMSE 0.1030262627。
- 三种验证均低于 0.001，正式输出标记 `near_exact_reconstruction_triggered=true`。解释只写为可能存在共同确定性构造或强预处理，不作为独立真实泛化事实。
- B4 57 行、49 行 N/D 外推；B5 44 行、36 行 N/D 外推。原始差值仅作描述性风险证据，不是 external error metric。
- `classic_fit.json`：7,759 bytes，SHA256 `b3706500bf79c191b7b05bf7af3dd963d1fb149fe47e304edb30cc9ad023893e`。
- `classic_data_manifest.json`：4,109 bytes，SHA256 `2fd70f2f174e5398a21cafa423309be68f6f3c702d1e22a0331c6547b0e2bc9a`。
- `prepared_b1.csv`：125,664 bytes，SHA256 `2eb418f022c414db13af89d2177b2b90c62d3ad3b29300adf7fb1de570927704`。
- 两个 JSON 的 provenance 均记录输入提交 `3b9cbff...`，且生成开始时相关代码路径 clean。

## 未验证项

1. B1 近乎精确重构的生成机制尚未查明；不能据此声称独立真实泛化。
2. B1 8 个 `C/(0.006ND)` 离群点原因未判定，也未完成保留/排除敏感性。
3. 未做按规模 bootstrap 或其他参数/预测区间；五参数仅为点估计。
4. B4/B5 的 tokenizer、评估语料、Loss 定义和单位可比性未建立；未报告 external RMSE。
5. 没有 Q/p、Q mapping、Loss anchor、广义 `L(N,D,Q,p)` 或 Loss–Benchmark 桥接。
6. 附件 A 的 4 个 LFS 文件在此前全库校验中仍是指针；本轮只消费已按清单核验的附件 B。

## 接口变化

- `interfaces/cyj/CONTRACT.md` 从生产者侧 draft v1.2 升为 v1.3，新增经典 N-D 基线、单位、适用范围、参数、验证指标、结果哈希和明确状态。
- 新接口仍为 `draft_classic_baseline_not_validated_predictor`，显式 `ready_for_Q3=false`；chm 不得启动 Q3 正式优化。
- B4/B5 `absolute_loss_comparability=not_established`；描述性预测不得改称外部误差。
- 没有改变全队 Q/p/Loss 公共规则，也没有把 B6–B8 Q_score 等同 Q_A、把 13 domain Loss 等同 B1 `val_loss` 或把 Loss 等同 Benchmark。

## 下一步与负责人

1. cyj：审计 B1 Loss 的构造/预处理证据，解释或限定 near-exact reconstruction。
2. cyj：对 8 个 C 恒等式离群点做保留/排除敏感性，并补分组 bootstrap/预测区间。
3. cyj：继续建立 B4/B5 tokenizer、语料、Loss 定义和单位证据；证据不足时保持分层描述。
4. chm+cyj：经典接口证据充分后再共同冻结 Q mapping、Loss anchor、p 接法和传递不确定性。
5. 集成人：验收后可把“经典 B1 draft 已运行但近乎精确重构原因未明、仍非 Q3 validated predictor”汇总到公共记忆；不得写成 Q2 或 Q3 已完成。
