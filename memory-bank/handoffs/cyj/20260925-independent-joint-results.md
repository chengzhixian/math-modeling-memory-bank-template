# CYJ 独立任务：joint 拟合第一检查点

已运行八参数联合约束 SSE、12 起点、24 折 joint/staged 对照、宽搜索界检查与200次 ND 簇 bootstrap。全部数值见 `experiments/cyj/20260925-b7-joint-fit.md`；新参数只作为后续独立诊断候选，不替换历史 v3 发布。新增完整边际/弹性/等损失替代和成本/KKT 推导 `20260925-q2-q3-mathematics.md`。模型输出 SHA256 `c7426036164238d41b92ca08e9ca9087224aeb0c74554478b66093774a5b5b1a`。

联合拟合三轴平均 RMSE 0.049764/0.049008/0.049352 均优于 staged；200次 bootstrap 全成功。A-alpha 强相关，不能将各参数单独作强结构解释。数值 Jacobian/模拟参数恢复测试2/2通过；尚未重新跑全部测试。科学状态保持 ready=false。

`nested_cv_b7.py` 与 `quality_substitution.py` 在本检查点为未运行后续脚本；绘图库正在安装，嵌套验证和留出区间覆盖尚待运行。待办以独立协议清单为准；不依赖 CHM/ZHH 即可继续。
