# B7 原生质量模型运行结果

cyj，2026-09-24。按先行提交的 `20260924-b7-quality-protocol.md` 执行，没有看完本轮结果再变更候选、划分或选择准则。

代码与数据/清单版本 `6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b`。main 输入 `968ef7a36f1503aa222a0b09c8a8cb5d0f535ecd`。B6/B7 两文件通过原始 bytes/SHA 校验，B6 完整子集校验后仅使用 B7 450 行；9 N × 5 D × 10 Q，无重复坐标。

## 复现和结果

```powershell
$py = 'C:/Users/muyehuangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py -B src/cyj/quality_scaling.py --input-version 6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b
& $py -B -m unittest discover -s src/cyj/tests
Get-FileHash outputs/cyj/quality/b7_quality_fit.json -Algorithm SHA256
```

两次完整运行输出相同 SHA256：`e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`。Python/NumPy 版本和代码 LF 哈希在 JSON；bootstrap seed=20260924。34 项单元测试通过，包含真实样例、哈希/范围拒绝、全部三维导数差分以及多配置 sample_id 一致性。

| 候选 | 按 N 留出平均 RMSE | 按 D 留出平均 RMSE | 按 Q 留出平均 RMSE |
|---|---:|---:|---:|
| 无 Q 消融 | 0.1158118921 | 0.1183482818 | 0.1187936637 |
| 线性 Q | 0.0582312178 | 0.0570906129 | 0.0576169721 |
| 对数 Q | 0.0660807089 | 0.0657056561 | 0.0723200946 |

共 72 折均收敛未触指数边界；这支持在本候选集合/B7 中保留线性 Q，但候选选择使用同一验证分数，尚非嵌套无偏性能评估。不得用“72 折通过”宣称真实训练泛化已验证。

全样本线性模型参数：E=1.5216740250105982，A=0.5291238092297949，B=1.3285646767250843，G=0.36199528619528626，alpha=0.283217561405495，beta=0.29957529838453234。全样本 MSE=0.0031695593467731525。最终调用以 JSON 为唯一参数源。

N,D 组重采样 50/50 接受，固定族、每组十个 Q 同时重采样。样例 N=.07B、D=10B、Q=.5：B7 原始行 362 观测 3.568，预测 3.492870995028143，条件均值百分位区间 [3.4743295908372973,3.5124959966188487]。观测不在该区间并不矛盾：该区间没有包含残差/个体预测误差，不是总预测区间。50 次尾部分位数较粗，仅初版诊断。

## 可交付与未验证

`interfaces/cyj/QUALITY_API.md` 定义独立 B7-native 预测、梯度、等 Loss 替代率及配对条件样本。B1/p 接口没有被改写或静默附加 Q 项。对 chm/zhh 正式就绪均 false；两个 Loss 不能相加或直接互换，不能省略 Benchmark 桥接误差。

未验证：候选之外模型形式、嵌套/独立验证、B7 真实生成/评估口径、B1/B7/A 共同尺度、p 主 anchor/lambda、总体预测区间、B9/B10 外推及成员消费验收。B8 两类全部排除，没有擅自反转 Q。

下一步优先做 B7 选模后的独立/嵌套检查和来源证据，再与 chm/zhh 联合冻结可用坐标/误差字段。机器包同时携带 ready 状态和缺失口径，不以软件接口可运行替代科研验收。未新增中间 CSV/图/缓存；必要结果只保留一个 JSON，原始附件和公共记忆未改写。
