# CYJ → CHM：可直接拉取的诊断接口发布

## 发布身份与状态

```text
CYJ_RELEASE_COMMIT=587bbb505b730ba8654089650365191bb1493ce0
CYJ_INTERFACE_SCHEMA=cyj.chm.v2
CHM_PRODUCER_COMMIT=a5525935b37f873235d2f650e4810a787b9a8788
ready_for_Q3=false
```

`team/cyj-scaling` 在发布时的远端 SHA 经 `git ls-remote origin refs/heads/team/cyj-scaling` 核对与 `587bbb505b730ba8654089650365191bb1493ce0` 相同。发布 commit 中的 `outputs/cyj/interfaces/chm_v2_manifest.json` SHA256 为 `846d72b583ba5f065a6ea2f6915e49f2ce77962848dd496f23054fc3cd2a248e`。chm v1.2 manifest SHA256 为 `5885317d072739b02cdbb434fc730dde07510eb284dc857e35863adc877e914d`；新接口还逐一核验所有消费的 chm blob SHA。旧 `cyj.q3.v1` 仅历史审计，`formal_use_allowed=false`。

## CHM 在本人分支的拉取和实际消费

先确认本人工作区可安全合并；如果有未提交改动，先按 chm 的检查点规则保存。以下命令由 **chm 在其电脑和分支** 执行，cyj 没有代替 chm 完成验收：

```powershell
git status
git fetch origin --prune
git switch integration/chm-q1-clean-20260923
git pull --ff-only
git merge --no-ff 587bbb505b730ba8654089650365191bb1493ce0

python -B src/cyj/chm_consumer_smoke.py --release-commit 587bbb505b730ba8654089650365191bb1493ce0
python -B src/cyj/chm_adapter_v2.py --request outputs/cyj/interfaces/chm_v2_request.json
```

若 chm 使用其他 Q3 工作分支，将 `git switch` 的分支名替换为本人实际分支，实验记录仍须保存 `CYJ_RELEASE_COMMIT`。若不合并 cyj 分支，则通过精确提交获取整套代码和机器包，不抄 JSON 数值或公式参数。需要 Python 3.12、NumPy、Git 可读取 `CHM_PRODUCER_COMMIT`。`model.bounds` 必须作为求解器 N/D/Q 边界，B7 D_min=10；不能继承 B1 D_min=.134。

## CYJ 本地已执行的测试

```powershell
python -B src/cyj/build_chm_release_v2.py
python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
python -B src/cyj/chm_consumer_smoke.py --release-commit 587bbb505b730ba8654089650365191bb1493ce0
```

结果：44/44 CYJ 单测 PASS；smoke test 输出 `PASS`、2 条样例、`ready_for_Q3=false`。smoke test 逐文件检查本地代码、manifest 和样例等于发布 Git 对象，然后实际调用 `value_grad` 和两条 B7 诊断/独立配比敏感性请求。返回有 `loss_coordinate`、`support`、`uncertainty`、`p_policy`、上游来源与 formal 阻塞。无旧 eta、无 A Loss 到 B7 Loss 的自动加法。CYJ 尚未运行 chm 求解器或在 chm 电脑执行 pull。

## CHM 验收与限制

请 chm 在 `memory-bank/handoffs/chm/` 按本人写入权记录：实际消费 CYJ SHA、smoke PASS/FAIL、实际调用、求解器能否消费返回结构、需要的适配、科学 blocker。若仍需手抄参数或改 CYJ 源码，接口工程问题未解决。`ready_for_Q3=false` 是 B7 半合成模型选择后的独立验证、总预测不确定性及团队正式验收尚缺，不应被软件通过改为 true。A 侧 p 仅 1M 13-target sensitivity；Q_A↔Q_score 与 A target Loss↔B7 Loss 未识别。完整 `L(N,D,Q,p)` 仍 `not_identified`。

## 下一步

chm：实际拉取此精确提交并运行消费测试，随后在自身诊断求解器中调用 v2 返回结构；若失败记录输入和错误。cyj：继续 B7 交互候选的预注册比较及 B1/B4/B5/B8 来源审查；科学门槛达标前保持 Draft。集成人：等待双方 handoff 再判断是否可写“接口问题已解决”。
