# chm 接口采用、Q3 定义与 B1 项消融

日期：2026-09-24。角色/分支：cyj / `team/cyj-scaling`。本轮代码/输入提交 `6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`；安全合并的 main 为 `7d8081fbf50cd380904505759c116580356f102d`，merge commit `5ada51f9a29877dd2ee98a9b4d1b0760e1f5b818`，无冲突。结果只在本人分支，未视作团队验收。

## 接口采用与实现核验

读取 chm `integration/chm-q1-clean-20260923@7c14a0c894072048d09f04bd03653be1301f7257` 的全部活动接口；接受 `chm.q1.v1` 的 A 侧定义与可识别性边界，直接调用原生 `Q1Interface`，不重读 A 原始文件。其 manifest SHA256 `c3525c2f58baa97a44bd5e4dd497b2ea9e23752c7f03e4bfad309f0af95f238d`。消费记录/双重文件哈希在 `outputs/cyj/interfaces/q3_bundle.json`，SHA256 `a153cbb6a45925317dcae1727d50bd0b20e2ec6b85767981b4d8a689b5144332`，5,718 bytes。

首次原样 Git blob 联调被生产者校验拒绝，原因确认是 coefficients/reference/validation 三 CSV 的发布哈希按 CRLF 计算，Git 对象为 LF。适配器只有在恢复 CRLF 后逐字节命中原发布 SHA 才继续；未更改 chm manifest 或系数。临时文件随上下文退出删除，进程内缓存读取对象。该换行可移植性问题应由 chm 在后续发布规范修复。

`interfaces/cyj/Q3_API.md` 定义 B1 Loss 坐标、支持域、五 target/lambda/eta 接法、B-native Q 保留字段、三项题面成本、预算/单纯形残差、导数/边际/结构转移规则。Q 性能项、Loss anchor/lambda 仍缺拟合或定标证据；软件验收不提升 `ready_for_Q3`。真实 B1 首行输出 4.738637013477364，chm 发布配比扰动例复算为 0.001309803924525102；26/26 测试通过，包括失败输入、哈希恢复不能掩盖数据变化、N/D 导数差分、三成本单位及 Q0 单侧导数。

## 消融设计及输入身份

完整模型 `L=E+A*N^-alpha+B*D^-beta` 固定原基线。分别去 E（E=0）、去 N（A=0，alpha 不再拟合）、去 D（B=0，beta 不再拟合），**重新拟合剩余参数**。目标仍为按 N 组等权的 log-Loss Huber，delta=0.05；各折 8 starts、最多 1800 iterations，seed 与原冻结折一致（20260924+fold，tail 用 +100）。预计算 log N/D/L 减少每次目标计算开销。

复用原 8 折 leave-one-model-size-out（每折 1029/147 行）与按轨迹 token-tail（816/360），断言 train/test sample_id 不重叠。完整模型不重新挑参数，从冻结 CV 参数复算全部 9 折预测并核对原 RMSE；删项模型只使用相同 train 进行优化，test 不参与拟合或模型选择。没有逐行随机拆分，没有把 Q/p 假定已拟合后做伪消融。

B1 原始 CSV 先按固定 `F_MANIFEST.json` 核对；prepared 与 CV CSV 分别按原 fit provenance/output 哈希核对。原 fit SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`；输入身份、全部折参数、收敛/触边和逐折指标保存为一个紧凑结果 `outputs/cyj/ablation/b1_terms.json`：SHA256 `592c945cabd928892339b14f3008071abb5c308632e1e38367b0f333e3acfea8`，24,658 bytes。

| 模型 | 8 折 LOSO RMSE 均值 | token-tail RMSE |
|---|---:|---:|
| 完整 E+N+D | 0.0001461277 | 0.0001160041 |
| 去 E | 0.0636845167 | 0.0466495733 |
| 去 N | 0.2126046868 | 0.2420496692 |
| 去 D | 0.2552874888 | 0.1018466408 |

27/27 删项拟合收敛且不触参数边界；三种删项均在全部 9 个划分劣于完整模型。阶段结论是 E/N/D 三项对**当前 B1 重构**均有贡献，保留原模型；不同删项的误差大小不构成跨实际训练过程的因果重要性排序。B1 近乎精确重构来源仍未解释，消融不增加独立真实性或外部有效性证据。

## 复现命令

在仓库根目录，Python 3.12.14（路径见 `problem/cyj/environment.md`；以下 `python` 代指该解释器）：

```powershell
python -B src/cyj/q3_interface.py --build --chm-version 7c14a0c894072048d09f04bd03653be1301f7257 --input-version 6e3fa709dbac03c224f6ba3d42f99f56ab1322f3
python -B src/cyj/q3_interface.py --request outputs/cyj/interfaces/b1_example_request.json
python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
python -B src/cyj/ablate_b1_terms.py --input-version 6e3fa709dbac03c224f6ba3d42f99f56ab1322f3
```

上述生成/测试/消融均已实际执行；本消融运行一次，未声称做第二轮哈希重复。旧 B1 bootstrap 的两次复跑属于其独立实验。跨机若有浮点差异，用明确数值容差验收，不静默换输入或改清单。

## 清理及未验证项

精简当前合同与成员记忆，详细历史仍由实验/交接和 Git 提交保留。删除仅限 `src/cyj/__pycache__` 和 `src/cyj/tests/__pycache__` 的 13 个可再生 `.pyc`（152,005 bytes），以后本轮命令使用 `-B`。未删除 prepared B1、CV 预测、基线/诊断脚本：它们被当前结果 manifest 或复现命令引用，是证据链的一部分。没有永久复制 chm 系数表，没有修改原始附件或他人目录。

仍需 cyj 完成 B6–B8 原生质量项及 B1 同尺度证据、B1 Loss 来源、B4/B5 可比性、B9/B10 外推讨论；chm 接收本 API 复核、修复其发布换行规则；zhh 更新正式 C7/桥接合同并传播桥接误差；集成人验收后更新公共记忆。本轮没有发布正式 Q3 最优配置或总体预测区间。
