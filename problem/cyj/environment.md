# cyj 运行环境

记录时间：2026-09-24 00:15（Asia/Shanghai）。

## 已验证

- 操作系统：Microsoft Windows NT 10.0.26200.0。
- 分支：`team/cyj-scaling`。
- 本次正式审计代码/输入版本：`6880af29f2a1fc089e5fc601d0df873c0be042a3`。
- Python：3.12.14，来自 Codex 工作区依赖运行时。
- pandas：3.0.1；NumPy：2.3.5。
- Git：2.55.0.windows.1；Git LFS：3.7.1。
- `pytest`：当前 Python 环境未安装；本次测试使用标准库 `unittest`，不新增依赖。
- 当前清理版 `problem/F/数据说明.pdf` 已通过 `scripts/build_safe_pdf_context.py --check`。
- AI 入口规则已通过 `scripts/check_ai_reading_rules.py`，报告 24 个受保护入口。
- 附件 B 的 19 个 CSV 均与 `data/raw/F_MANIFEST.json` 的字节数和 SHA256 一致。

## 数据完整性限制

`./scripts/verify_raw_data.ps1` 未通过：附件 A 的 4 个 Git LFS 文件仍是指针，报 4 个 size mismatch。该失败不涉及附件 B，但本机不能声明全库 2,014 个原始文件完整。后续需要标准 Git/LFS 网络恢复后执行 `git lfs pull` 并重跑全库校验。

## 可复现命令

```powershell
$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py scripts\build_safe_pdf_context.py --check
& $py scripts\check_ai_reading_rules.py
& .\scripts\verify_raw_data.ps1
& $py -m unittest discover -s src\cyj\tests -p 'test_*.py' -v
& $py src\cyj\audit_b_scaling_laws.py --input-version 6880af29f2a1fc089e5fc601d0df873c0be042a3
```

当前未运行拟合、优化或绘图，也未固定公共依赖文件。
