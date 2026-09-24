# B8 来源冲突补充审计

脚本 `src/cyj/audit_b8_conflict_source.py` LF SHA256 `703d8c8b5b41721893a5f2ed7b9b68f2c92ebaf9e9be538640b9d120bcb6165e`；输入 B7/B8 SHA256 分别为 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a` / `bda0d449f75c73bbd04141e5cffbf4bea7002073e34b7fa95a638570fa095ffe`。复用原审计的精确坐标键和固定组趋势函数；无随机种子。Python 3.12.14 + NumPy 2.3.5。

```powershell
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/audit_b8_conflict_source.py
```

输出 `outputs/cyj/diagnostics/b8_conflict_source.json` SHA256 `cea833c19f44963fada3e4b627d0889d22184ea8d07fb6b0a73de9777ac8f530`。224 个 B7/B8 共坐标全异；B8 calibrated/extrapolated 在固定 ND 组均为 Q 端点上升，0.5 堆积分别 129/233。输出逐 Q/N 记录 floor 分布、共坐标差值和未识别来源字段。状态保持 `unresolved_keep_isolated`，没有调换 Q 的方向。
