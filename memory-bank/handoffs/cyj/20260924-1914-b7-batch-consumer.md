# cyj：补推与 B7 批量消费入口

起点/模型交付提交 `2c5e7122e4b05c86a38cfe01d0a50155aece183b`，本人分支 team/cyj-scaling。开工 ls-remote 实测远端仍为 `6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b`，说明前轮断连推送并未完成。已重试正常 push，遇 GitHub 443 连接失败，不把 Everything up-to-date 当成成功。

本轮新增本人 `src/cyj/predict_quality.py`、测试和 `outputs/cyj/interfaces/b7_example_request.json`，更新 QUALITY_API 与本人记忆。输入仍为已冻结 B7 模型 SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`，代码/拟合输入 `6c17cb4`；没有改参数或重做拟合。main 已合入 `968ef7a`，上游 CHM/zhh 未重新采用新版本。

接口变化：新增 `cyj.b7_batch.v1` JSON 包装，唯一 request_id、显式 mode、固定模型哈希、严格数字类型及字段检查；整批失败时不输出部分成功，CLI 退出 2。不替换原 Python API，输出仍保留 B7 Loss 坐标与同编号条件样本，Q3/Q4 ready=false。

命令（本机 python 替换为 bundled Python 完整路径）：

```powershell
python -B src/cyj/predict_quality.py --request outputs/cyj/interfaces/b7_example_request.json
python -B -m unittest discover -s src/cyj/tests
git diff --check
git push origin team/cyj-scaling
git rev-parse HEAD
git ls-remote origin refs/heads/team/cyj-scaling
```

证据：37/37 测试通过，包括从仓库外目录调用 CLI、双请求样本编号一致、真实请求预测 3.492870995028143、重复 ID/字符串 Q/null/formal 拒绝。git diff --check 通过；本轮无原始 CSV 或公共记忆修改，不产生过程输出/缓存。

未验证：其他成员设备的实际消费、完整跨 Loss/Q/p/Benchmark 桥接、B7 嵌套验证等保持上轮状态，不因 CLI 完成而放行正式优化。下一步先确认本轮远端 SHA，再由 chm/zhh 按样例联调，cyj 继续补模型选择偏差验证。最终备份结果见收尾 Git 核验；若失败保留本地提交并优先补推。
