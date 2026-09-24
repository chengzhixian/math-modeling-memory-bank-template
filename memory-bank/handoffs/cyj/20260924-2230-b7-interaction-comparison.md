# CYJ Handoff：B7 交互候选探索性比较

## Task / Changes

完成任务清单 Task 4 的**算法预注册与同源探索性比较**：`experiments/cyj/20260924-b7-interaction-preregistered-protocol.md`、`src/cyj/compare_b7_quality_interactions.py`、`outputs/cyj/quality/b7_interaction_comparison.json`、结果记录 `experiments/cyj/20260924-b7-interaction-results.md`。未将候选替换已发布 CHM 诊断接口。

## Input / Commands / Tests

分支 `team/cyj-scaling`，CYJ 发布起点 `587bbb505b730ba8654089650365191bb1493ce0`；B7 源 SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`，协议 SHA256 `bf6aad298e36e60c41877dd09c898f51b08e558a7c0da23b2bb426c2f05c2e4e`，代码 LF SHA256 `a32109a9b0c9e49391aa03ec804011be3520d8079c30c89fbe0114dbd72a93eb`。运行命令和环境见结果记录；程序成功退出，输出 SHA256 `1d28169ce10f5bc274a82037320fdf003f7e3d2148eff2be91d3c3618708925b`。CYJ 既有单测上轮 44/44 PASS；本项独立脚本含源哈希/网格强校验，未新增镜像实现式测试。

## Results / Identifiability / Claim

24 个外层留级，22 折选双 log 交互，2 折选单 logN；在 N/D/Q 轴，双交互候选平均 RMSE `.051936/.050207/.050061`，constant-G `.058231/.057091/.057617`。100/100 ND 组 bootstrap 对五候选均有效；梯度未在 24 选中折的全矩形角点变号。最高为 B7 半合成同源条件预测的**探索性 L2**，不具备独立外测、L3 结构、L4 因果或 L5 外推证据。完整 `L(N,D,Q,p)` 仍 `not_identified`。

## Limitations / Interface Impact / Ready

候选形式受到运行前 Task 3 全 B7 诊断启发，因此 nested CV 不能消除研究者模型发明造成的选择偏差；真正未见 B7 同机制样本不存在。CHM 继续消费原 v2 constant-G 诊断，`ready_for_Q3=false`、`ready_for_Q4=false`。下一步 cyj 追溯 B1、B4/B5、B8 的来源与口径；CHM 仍需对发布 commit 做实际 pull/消费验收。
