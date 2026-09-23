# P20 经典 N-D 标度律基线

状态：已运行；仅为 B1 经典基线草案，不是 validated predictor，不可启动 Q3 正式优化。

## 输入与复现边界

- 分支：`team/cyj-scaling`。
- 复核后正式代码/输入提交：`cf297a4ad47e235acf5a9b6e890a5df5e05b07e5`；原版见历史提交 `3b9cbff1362349bd9dc9d94d56c409f7d93654be`。
- main 基线：`a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。
- 输入：`data/raw/real_attachments/B_scaling_laws/pythia_training_log_existing.csv`；1,176 行，8 个 N 规模组，每组 147 行。
- 原始文件 SHA256：B1 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`；B4 `2272983ded93de35e05f9acbf95ebceedf43f283345e4be72b54fee94080391e`；B5 `dd858c5e48610e28589340d5db023d6abfb31df597506789ccdfc6a546731bbd`。运行前逐一按清单核对字节数和 SHA256。
- 输入身份：`F_MANIFEST.json` SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`；`source_manifest.json` SHA256 `34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。
- 参考评审文件 `CYJ_scaling_branch_review_and_next_steps.md` 仅作为建议输入；模型与结论由当前可见题面、数据和实际运行重新建立证据。

## 方法

经典模型为：

`L(N,D) = E + A*N^(-alpha) + B*D^(-beta)`。

N 的单位为十亿参数（B），D 的单位为十亿 token（B），L 为 B1 的 `val_loss`。五个参数均通过对数参数化保持为正。拟合目标为 `log(predicted_loss)-log(actual_loss)` 的 Huber 损失；每个 N 组的总权重相等。优化器是纯 NumPy、固定种子、多起点 Nelder-Mead。

验证不使用随机逐行拆分：

1. Leave-One-Model-Size-Out：依次留出 8 个 N 规模组。
2. Token-tail：每个 N 组按 D、steps 排序，前 70%（实际 102 行）训练，后 30%（45 行）测试；总计 816/360 行。
3. M0 对照：`Loss = intercept + b_N log(N) + b_D log(D)`。

B1 的 8 个计算恒等式 warning 行保留在主拟合中，未静默删除。B4/B5 缺少足以建立 tokenizer、评估语料、Loss 定义和单位等价性的本地证据，因此只输出描述性预测，不报告外部误差指标。

## 实际命令

```powershell
$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m py_compile src\cyj\scaling_common.py src\cyj\prepare_scaling_data.py src\cyj\fit_classic_scaling.py
& $py -m unittest discover -s src\cyj\tests -p 'test_*.py' -v
& $py src\cyj\prepare_scaling_data.py --input-version cf297a4ad47e235acf5a9b6e890a5df5e05b07e5
& $py src\cyj\fit_classic_scaling.py --input-version cf297a4ad47e235acf5a9b6e890a5df5e05b07e5
```

## 已验证结果

- `py_compile` 通过；`unittest` 14/14 通过，包含同字节数 CSV 篡改拒绝测试。
- 两个输出 JSON 已升为 schema v2；执行代码逐文件与输入提交核对，B1/B4/B5 原始字节与清单核对，拟合前还重建并逐行比较 B1 准备表。
- 参数：E=1.6898377713，A=0.3539687193，B=1.2402746295，alpha=0.3399854258，beta=0.2798924656。
- 全样本：RMSE 0.0001465764，MAE 0.0001051548，R² 0.9999998164。
- LOSO：8 折 RMSE 均值 0.0001461277，标准差 0.0000343734，范围 0.0001014255–0.0002144818。
- Token-tail：RMSE 0.0001160041，MAE 0.0000888370，R² 0.9999997528。
- M0 对照：RMSE 0.1030262627，R² 0.9092836575。
- 三种检查的 RMSE 均小于本轮诊断阈值 0.001，`near_exact_reconstruction_triggered=true`。阈值是在首次结果后加入的诊断标记，并非事前注册的判定规则。这可能来自共同的确定性构造或强预处理，不能据此证明独立真实泛化。
- B4：57 行，其中 49 行超出 B1 的 N/D 矩形范围；原始 `predicted-observed` 范围 -1.0477173 至 0.1474063。
- B5：44 行，其中 36 行超出 B1 的 N/D 矩形范围；原始 `predicted-observed` 范围 -0.4194763 至 0.4508518。
- 上述 B4/B5 差值只用于暴露口径风险，不是误差指标，也未用于模型选择。

## 输出证据

- `classic_data_manifest.json`：4,719 bytes，SHA256 `5edf56694d63b74ab715c50c8ce2bf1ebb510f40fcd184d58ae714788e8e067e`。
- `classic_fit.json`：8,461 bytes，SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`。
- `prepared_b1.csv`：125,664 bytes，SHA256 `2eb418f022c414db13af89d2177b2b90c62d3ad3b29300adf7fb1de570927704`。
- `classic_predictions.csv`：220,514 bytes，SHA256 `d0e0263e50d654b76fd5a77dbaae7fff87b62dff613643f6feee5dc5be27b7a2`。
- `classic_loso_predictions.csv`：143,532 bytes，SHA256 `162e7143cbde79e35de6710613c6d4811a8fb30c5d831f411d0526d8737d6519`。
- `classic_token_tail_predictions.csv`：40,870 bytes，SHA256 `f0d646949296bf1ce2fd22740caa3da652cf8858339ffecc0af01d8d0ddeefcf`。
- 其余文件及内部哈希由两个 JSON manifest 记录。
- 两份 JSON 不再嵌入运行时钟时间；固定输入提交、代码、依赖环境和默认输出路径时连续两次运行的 9 个输出 SHA256 完全一致。实验实际执行时间记录在本实验/交接中；不同 NumPy 或平台仍需按数值容差复核。

## 未验证与下一步

- 尚未查明 B1 近乎精确重构的生成机制，也未证明 B1 是独立观测误差下的泛化样本。
- B1 8 个 C 恒等式离群点的原因与敏感性尚未核验。
- B4/B5 的绝对 Loss 可比性未建立；没有外部 RMSE。
- 尚未做按组 bootstrap 或参数/预测区间；当前五参数点估计不能作为正式不确定性接口。
- 尚未消费 chm 的 Q mapping、Loss anchor 与 p 接法；没有 `L(N,D,Q,p)`。
- 下一步先审计 B1/B4/B5 的 Loss 构造与口径，再做分组不确定性和离群敏感性；只有证据充分后才能把经典接口候选升级，再进入 chm+cyj 的 Q/p 联合冻结。
