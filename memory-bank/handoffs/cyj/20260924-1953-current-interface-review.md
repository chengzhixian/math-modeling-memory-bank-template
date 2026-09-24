# cyj → 团队：当前 Q2/Q3 接口审查与状态修订

时间：2026-09-24 19:53 北京时间。角色 cyj。分支 `team/cyj-scaling`，审查起点 `e84c0a529ad7f56e83db5c91b3b62c9e43200d99`；已合并公共 `origin/main@af4857045e5df62afc9815bce4b98dbbb8867253`。此前本地待推工作已补推，`ls-remote` 与本地 `157e340eb3310e5313ec49dd740947b701ff1841` 一致。本交接所在提交与最终远端 SHA 以收尾 Git 核验为准。

## 变更与输入版本

- 新增 `problem/cyj/20260924-current-interface-review.md`，按 `REPOSITORY_REVIEW_PROTOCOL.md` 记录审查范围、题目—数据与变量追溯、可识别性、角色/泄漏、公式—代码、验证、跨成员桥接、从零反事实和结论。更新本人合同 v1.11、`Q3_API.md` 使用状态及成员记忆；没有修改代码、旧机器包或其他成员目录。
- 题面 DOCX SHA256 `bc99a72460fa3d947a442d502969a13212cebff3b55339da4c4`；数据说明用清理版视觉页面与 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`，未使用历史隐藏文字。B1 fit SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`；B7 fit SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`；`q3_bundle` SHA256 `a153cbb6a45925317dcae1727d50bd0b20e2ec6b85767981b4d8a689b5144332`。chm 当前推荐分支 `integration/chm-q1-clean-20260923@a552593` 的 v1.2 manifest 明确 `scale_transfer_status=not_identified_from_attachment_A`；旧 cyj bundle 仍固定 chm `q1.v1@7c14a0c`。zhh C7/桥接仅候选，未作联合验收。

## 运行命令与实际证据

```powershell
git status --short --branch
git -c http.sslBackend=openssl fetch origin --prune
git merge --no-edit origin/main
git show origin/integration/chm-q1-clean-20260923:interfaces/chm/CONTRACT.md
git show origin/integration/chm-q1-clean-20260923:interfaces/chm/q1_interface_v1_2.json
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/q3_interface.py --request outputs/cyj/interfaces/b1_example_request.json
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/predict_quality.py --request outputs/cyj/interfaces/b7_example_request.json
```

37/37 软件测试通过；B1 样例 Loss=`4.738637013477364`，B7 首请求 Loss=`3.492870995028143`；formal 与跨 Q/Loss 混用仍由旧 API 拒绝。审查发现旧 p/eta scenario 虽可运行，却依赖 chm 已撤回的跨规模估计。B1/B7/A 无同坐标联合训练数据，故完整 `L(N,D,Q,p)` 不可识别，Q3 `ready=false` 保持。详见本轮审查文件的 BLOCKER/MAJOR 清单。未对全部 A/C 原始数据、论文终稿或外部文献原文做独立全仓审查。

## 接口变化、未验证与下一步

本次是**文档状态降级**：`interfaces/cyj/CONTRACT.md` v1.11 与 `Q3_API.md` 明确旧 `cyj.q3.v1` p/eta scenario 不再是推荐接口，只可历史复现；B1 diagnostic、独立 B7 diagnostic、题面成本定义的受限用途继续保留。机器 schema、请求/响应、参数和哈希均未变；消费者若要切换正式版本，必须等待新版本，不能把这次文字修订解释为已经完成兼容迁移。

cyj 下一步固定 chm v1.2 的精确 commit/manifest，开发不含假定 eta 的新版消费者；p 仅保留 1M 13-target contrast 或有证据的 sensitivity policy。继续核对 B1/B7 Loss 来源、B4/B5 可比性及 B7 独立验证。chm 验收新版 p policy 与 Q3 结果；zhh 只消费同坐标且带桥接误差的 Loss；集成人验收后更新公共记忆与 main。全库 A 的四个 LFS 指针问题仍待具备实体附件的机器补齐，不能据本轮软件测试宣布全库数据已验证。
