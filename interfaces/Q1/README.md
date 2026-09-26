# Q1 正式接口

`q1_interface_v2.json` 是原 CHM `chm.q1.v2.0` 冻结发布清单，SHA256 为 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`，保持原字节。清单中的历史 `outputs/chm/q1_v2/` 路径由 `src/chm/q1_interface_v2.py` 只读映射至 `outputs/Q1/`，逐文件按 LF 规范哈希核验。`code_manifest.json` 另记 main 路径适配后的实际代码哈希，不冒用原发布代码身份。

输入配方必须包含恰好 17 个命名域、有限非负且总和为 1；超出单纯形或凸包的方案会给出支持状态，不能悄悄归一化。输出是 13 个验证域的 A 侧 1M 交互代理 Loss、相对参考配方效应、梯度和 A1 描述性质量代理。Q 的未知映射域保持 `null`；不返回已标定的 B 侧质量、跨规模绝对 Loss 或跨附件因果效应。接口与当前生产复现见 [Q1 实验记录](../../experiments/Q1/CORE_VALIDATION.md)。
