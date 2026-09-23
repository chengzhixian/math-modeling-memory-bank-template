# zhh 运行环境

- 操作系统：Windows，PowerShell。
- 项目位置：`E:\研数模\math-modeling-memory-bank-template`。
- 运行时：Node.js v24.19.0。
- 分析脚本：`src/zhh/q4_analysis.js`，只使用 Node.js 标准库，无需安装第三方依赖。
- 随机种子：20260923，用于 300 次 Bootstrap。
- 复现命令：

```powershell
& 'C:\Program Files\nodejs\node.exe' 'src\zhh\q4_analysis.js'
```

输入文件均来自 `data/raw/real_attachments/C_efficiency_evolution/`，未改写原始数据。
