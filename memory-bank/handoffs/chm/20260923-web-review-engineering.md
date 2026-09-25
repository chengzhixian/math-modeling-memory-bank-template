# chm 网页审查工程修复交接

日期：2026-09-23。来源：用户提供的网页版审查文本。角色 chm，当前研究分支 `team/chm-data`。

本轮范围：修复 Git 历史集成方式和配比结果默认路径；其余审查问题完整记录于 `problem/chm/20260923_web_review_open_issues.md`，暂不改变数学模型、统计结论和其他代码。

已修复的路径问题：三个配比生成脚本、绘图脚本默认指向 `outputs/chm/local_recheck_v1/`；九个旧版配比文件原样迁入 `outputs/chm/archive/web_v0/`。差异对照程序改读归档。旧结果不再占据当前根路径。

历史隔离已完成：从干净 `origin/main` 建立 `integration/chm-q1-clean-20260923`，只导入 chm 归属路径的最终文件快照。首个干净提交为 `c57ec6916a03dce53734a1c5254f3f53d4f7b9f2`，唯一父提交为 main 的 `a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。比较结果为 ahead 1 / behind 0，共 69 个变更文件，全部位于 chm 合法归属范围。**不得直接将 `team/chm-data` merge 到 main**。

验证：原始资料校验 PASS 2014 / 564436312 字节。三个配比脚本以默认参数重跑，未覆盖旧归档；`q1_verify_local.py` 仍能输出网页与本地差异；质量分析 3 项回归测试通过。绘图脚本的依赖与默认运行另核对。

后续：集成人仅对干净集成分支做验收；Q 方向、权重、尺度外推措辞、η 条件区间、合同旧版归档等见问题清单，按用户要求稍后修改。清理版 PDF 和可见正文规则继续有效。


## 远端核验补记

- clean integration：`integration/chm-q1-clean-20260923`
- 首个干净提交：`c57ec6916a03dce53734a1c5254f3f53d4f7b9f2`
- 父提交：`a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`
- 相对 main：ahead 1 / behind 0；merge-base 即当前 main。
- 变更文件：69 个；越界文件：0。
- 文件树与 `team/chm-data@c6aca3bdbe` 的最终文件树一致，因此成果内容未丢失，但污染祖先未被带入该分支。
