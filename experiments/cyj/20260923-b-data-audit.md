# P01 附件 B 审计记录

状态：已运行；结构审计通过，保留 3 项 warning。

## 输入

- Git 起点：`e85956fe7cd3ce7e6a6c8b930ae444b1ee93184d`。
- 数据清单：`data/raw/F_MANIFEST.json`。
- 数据：`data/raw/real_attachments/B_scaling_laws/`。
- 审计脚本：`src/cyj/audit_b_scaling_laws.py`。

## 命令

```powershell
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  src\cyj\audit_b_scaling_laws.py `
  --input-version e85956fe7cd3ce7e6a6c8b930ae444b1ee93184d
```

## 结果证据

- 退出码：0。
- 标准输出：`PASS: audited 19 CSV files / 10484 rows; checks={'pass': 97, 'warn': 3}`。
- 输出：`outputs/cyj/b_data_audit.json`。
- 输出 SHA256：`0fa89425b2c37eb00dac1db8f8889199e895f5d8245d3e174ca30e18dded5e36`。
- warning：B2 三列运行监控字段全空；B9 非正 D/缺失 FLOPs；B9 一个模型键含嵌入换行。

## 未验证

- 未运行 B1 拟合或任一预测。
- 未决定异常值、权重、损失函数和参数不确定性方法。
- 未取得 chm 的 Q/p 正式接口，也未取得 zhh 的 C7 情景表。
- 全库原始数据校验仍因附件 A 的 4 个 LFS 指针失败。
