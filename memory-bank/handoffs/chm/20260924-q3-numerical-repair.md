# Q3 工程修复检查点

基线：3d0ac45392b03614c19037eef8759c2221108cec；范围：chm Q3 数值与发布接口。

审查发现及修复：旧发布协议仍要求撤回 eta；任意模型默认 B1 支持域；KKT 绝对容差掩盖 tiny benefit/FLOPs 违反；SLSQP 原始预算约束尺度失衡，且失败解仍可被选中。均已针对性修改。

数据/可识别性边界：不读取隐藏 PDF 文字，不修改上游理论；B7 semi-synthetic ready_for_Q3=false，A/B bridge 未识别。支持范围由调用方提供，不将软件正确性等同科学有效性。

验证：PYTHONPATH 指向 src/chm 与 H:/研究生数模/.q3-deps，Python 3.12 执行 unittest discover -s src/chm -p test_q3_*.py，32 项通过。SciPy 1.18.1 安装于仓库外独立依赖目录。

下一步（chm）：B7 全局误差界、连续预算扫描、转移点复核、支持域敏感性及论文更新。正式结果仍等待 cyj 的独立验证，不发布 formal 数据。
