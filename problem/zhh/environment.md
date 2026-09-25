# zhh Q4 v2运行环境

2026-09-26接力在Windows/PowerShell，新clone `H:/研究生数模/zhh-q4-continuation-20260926`，分支team/zhh-frontier。Python3.12.14、NumPy2.3.5、Pandas3.0.1、Node24.19.0；绘图matplotlib3.11.2。模型仅需NumPy/Pandas，Node历史聚合只需标准库。

本机matplotlib安装在忽略目录data/processed/zhh_runtime，MPLCONFIGDIR可指向data/processed/zhh_mpl_cache；依赖不随Git上传。运行命令在Q4_FINAL_ANSWER_V2.md和manifest中，跨机可 `pip install -r src/zhh/requirements-q4.txt`。

模型seed=20260926，开发者块bootstrap200次；桥接斜率bootstrap1000次独立seed+1。所有数据路径由项目根推导，原始附件只读。Git本机HTTP/LFS启动问题按AGENTS命令级兼容方式处理，不改全局设置。

两项安全阅读门禁与原始2014文件SHA校验PASS。旧Node空预测保存在legacy_baseline，当前发布由q4_complete.py生成，源码、输入和输出逐hash见manifest。
