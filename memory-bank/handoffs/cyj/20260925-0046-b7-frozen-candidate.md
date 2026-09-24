# CYJ Handoff：B7 双交互候选冻结检查点

## Task / input

任务单 `CYJ_NEXT_TASKS_Q2_FINAL_AND_CHM_INTEGRATION_20260925.md` 的 P0-1 初始实现与 P0-4 梯度检查。分支 `team/cyj-scaling`，起点 `35e16d6c8f2fb5510303dded78fb53cbb3dd3b9f`；main 仍需后续远端同步核验。B7 源文件 `supplementary_NQ_experiment_expanded.csv` SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`，通过既有 `source_data()` 再校验 B6 是 B7 精确子集；不使用历史隐藏 PDF 或作废提交。

## Changes / reproducibility

- `src/cyj/b7_formal_model.py`：只冻结先前已比较的 `Q_x_logN_logD` 家族，基于 B7 450 个唯一点重拟合；实现解析 N/D/Q 梯度、弹性、等 Loss 局部替代率、有限支持域拒绝。未引入新模型族。
- `outputs/cyj/quality/b7_frozen_model.json`：重建两次 SHA256 均 `ed6b01b113110b90b25c5f6cc01d7686cb77602f29464bc068843b36d881c9bf`；模型参数与 `b7_interaction_comparison.json` 全样本项一致。质量收益在声明矩形的四角最小为 `0.2090545734100474`，因其对 `ln N, ln D` 仿射，故全域为正、`dL/dQ<0`。
- `src/cyj/tests/test_b7_formal_model.py`：三处内部/边界邻近点中心差分、支持域和派生量检查。

实际命令：`python -B src/cyj/b7_formal_model.py` 两次；`python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q`。结果 46 total、46 pass、0 fail。Python 3.12.14、NumPy 2.3.5；生成函数无随机采样。

## Evidence level and blocker

这是 **B7 半合成同源条件候选**，不是已验收正式性能律。此前函数族发明受全 B7 诊断启发；将来对同一 B7 重跑固定族留 N/D/Q 虽可检验稳定性，不能变成未接触过的独立 final test。按 `REPOSITORY_REVIEW_PROTOCOL.md` 数据角色与 claim ladder，本检查点保持 `ready_for_Q3=false`，不提前发布 `cyj.chm.v3` validated 状态。完整 `L(N,D,Q,p)` 仍未识别，B8 保持隔离，B9/B10 不作外测。

## Next / owners

cyj：做固定模型 grouped OOF、残差/区间与公式代码复核；结果只在 B7 条件范围报告，必要时维持诊断门禁。再完成 CHM `Support` 包装及 27 场景本地真 solver 测试，并在本人目录记录。chm：实际 pull/merge 并写 consumer acceptance；新 stable-LOO 主 Q_A 未重跑冻结前不能把旧 sign-only quality() 当成新主 Q_A，配比 Ridge/排序不受此次方向修订影响。zhh/集成人：后续桥接与公共状态验收。A 侧四个 LFS 附件本机仍为指针，不能宣称全库原始数据校验 PASS。
