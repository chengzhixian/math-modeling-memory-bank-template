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
./.venv/Scripts/python.exe src/chm/q1_regmix_domainwise.py --output-dir outputs/chm/local_recheck_v1
./.venv/Scripts/python.exe src/chm/q1_mixture_interface.py --output-dir outputs/chm/local_recheck_v1
./.venv/Scripts/python.exe src/chm/q1_mixture_scale_transfer.py --output-dir outputs/chm/local_recheck_v1
./.venv/Scripts/python.exe src/chm/q1_verify_local.py
./.venv/Scripts/python.exe -m unittest discover -s src/chm -p test_q1_quality_analysis.py
```

质量 bootstrap=1000、尺度 bootstrap=10000、随机种子=20260923；配比 CV 为五折不打乱。当前路径从仓库根执行；质量脚本支持 F_DATA_ROOT，配比脚本用 --data-root。原始资料只读。
