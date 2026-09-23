# chm 本地环境与复现

系统：Windows / PowerShell，CPU 运行，无 GPU 要求。
Python 3.12.14，NumPy 2.3.5，pandas 3.0.1，SciPy 1.18.1，scikit-learn 1.9.1。
本机通过 Codex bundled Python 建立仓库 .venv（--system-site-packages）；.venv 不提交。其他机器可用 Python 3.12 安装上述版本。

```powershell
./.venv/Scripts/python.exe scripts/build_safe_pdf_context.py --check
./.venv/Scripts/python.exe scripts/check_ai_reading_rules.py
./scripts/verify_raw_data.ps1
./.venv/Scripts/python.exe src/chm/q1_quality_analysis.py
./.venv/Scripts/python.exe src/chm/q1_quality_delivery.py
./.venv/Scripts/python.exe src/chm/q1_quality_sensitivity.py
./.venv/Scripts/python.exe src/chm/q1_regmix_domainwise.py --output-dir outputs/chm/local_recheck_v1
./.venv/Scripts/python.exe src/chm/q1_mixture_interface.py --output-dir outputs/chm/local_recheck_v1
./.venv/Scripts/python.exe src/chm/q1_mixture_scale_transfer.py --output-dir outputs/chm/local_recheck_v1
./.venv/Scripts/python.exe src/chm/q1_figures.py
./.venv/Scripts/python.exe -m unittest discover -s src/chm -p test_q1_quality_analysis.py
```

质量 bootstrap=1000、尺度 bootstrap=10000、随机种子=20260923；配比 CV 为五折不打乱。当前路径从仓库根执行；质量脚本支持 F_DATA_ROOT，配比脚本用 --data-root。原始资料只读。


## Git 时间与同步口径

- 团队审计统一使用父提交关系、完整 SHA 和远端 ref 判断先后，不再用 GitHub 页面显示的时钟时间判定因果顺序；此前两台环境存在约 8 小时显示差异。
- 本机/脚本记录的人类可读时间统一注明 `Asia/Shanghai`。查看提交建议使用 `git log --date=iso-strict-local`。
- 个人研究工作后续以 `integration/chm-q1-clean-20260923` 的干净血缘为可集成起点；接收公共规则必须执行 `git fetch origin` 后 `git merge origin/main`，禁止再次通过逐文件复制伪造“已同步 main”的提交历史。
- 提交顺序审计示例：`git rev-list --parents --topo-order <ref>`；冲突时以拓扑而非时间戳为准。
