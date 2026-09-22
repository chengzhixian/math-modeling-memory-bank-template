# 数据说明可提取正文

[PDF-HIDDEN-TEXT-BLOCK]

用户禁止参考原件的隐藏页边文字。本派生文本仅移除已核实的隐藏字符，其余可提取字符保留；复杂表格、公式和排版仍须核对可见页面。使用前先读 AI_READING_RULES.md。

## 原 PDF 第 1 页

数据说明 1
数据说明
对应赛题《算力约束下提升大语言模型能力的资源配置建模》。本说明给出各数据文件的结构、字段与跨附
件兼容性；各文件均使用英文文件名，赛题正文中以编号 A1–A18、B1–B12、C1–C10 指代，编号与英文文
件名的对照见《编号与读取速查》。
本赛题以真实公开数据为主，并包含经真实数据校准、已明确标注的半合成补充数据。全部附件位于 real
_attachments/ 目录下，本文所有路径均相对于该目录。按实际文件占用的存储空间（即磁盘上的字节数）
统计，总体积约 0.55 GB（压缩后，原始约 1.66 GB），其中绝大部分为必用数据（见《强制使用清单》）。参
赛队伍可在个人电脑上使用 Python、Matlab 或 R 完成全部处理，无须 GPU。
如本文档、source_manifest.json、attachment_size_summary.csv 与实际文件出现差异，以实际附件
为准。
编号与读取速查
本节集中给出编号索引、各文件绑定问题与读取要求，便于与赛题正文分开查阅。各文件的完整字段与规
模见后文《附件 A/B/C》各节。
数据总表
下表为各数据文件的编号—英文文件名对照，并标出每个文件绑定的问题与在解题中的角色。
性质栏口径统一如下：真实 = 直接观测或公开数据；半合成 = 基于真实数据校准并叠加噪声；外推/估算
= 由模型外推或预估，非直接观测；插值 = 由检查点插值生成；子集 = 取自其他表的子集，非独立实验；
混合 = 来源口径不完全统一，须分层使用；参考/说明 = 辅助文件。
附件 A（问题一）A_data_value/
编号 英文文件名 中文说明 性质 绑定问题·角色
A1 A_data_value/slimpajama 质量信号抽样集 真实 问题一·质量主样
_quality_signal_sample. （51,230 条，27 字 本
jsonl.xz 段；来自
SlimPajama-
Meta-rater 按域
抽样）
A2 A_data_value/slimpajama arxiv 扩展质量信 真实 问题一·必用
_quality_extended/arxiv 号
_*.jsonl.xz

## 原 PDF 第 2 页

数据说明 2
编号 英文文件名 中文说明 性质 绑定问题·角色
A3 A_data_value/slimpajama github 扩展质量 真实 问题一·必用
_quality_extended/githu 信号
b_*.jsonl.xz
A4 A_data_value/regmix_tab 训练配比（512 真实 问题一·配方·训
les/train_mixture_1m.cs 组） 练
v
A5 A_data_value/regmix_tab 训练 Loss 真实 问题一·Loss·训
les/train_pile_loss_1m. 练
csv
A6 A_data_value/regmix_tab 检验配比 1M 真实 问题一·配方·检
les/test_mixture_1m.csv （256 组） 验
A7 A_data_value/regmix_tab 检验 Loss 1M 真实 问题一·Loss·检
les/test_pile_loss_1m.c 验
sv
A8 A_data_value/regmix_tab 检验配比 60M 真实 问题一·配方·检
les/test_mixture_60m.cs 验
v
A9 A_data_value/regmix_tab 检验 Loss 60M 真实 问题一·Loss·检
les/test_pile_loss_60m. 验
csv
A10 A_data_value/regmix_tab 检验配比 1B（64 真实 问题一·配方·检
les/test_mixture_1B.csv 组） 验
A11 A_data_value/regmix_tab 检验 Loss 1B 真实 问题一·Loss·检
les/test_pile_loss_1B.c 验
sv
A12 A_data_value/regmix_tab 外推配比 10B 子集 问题一·配方·外
les/est_mixture_10b.csv （train 子集） 推
A13 A_data_value/regmix_tab 外推 Loss 10B 外推 问题一·Loss·外
les/est_pile_loss_10b.c 推
sv
A14 A_data_value/regmix_tab 外推配比 70B 子集 问题一·配方·外
les/est_mixture_70b.csv （train 子集） 推
A15 A_data_value/regmix_tab 外推 Loss 70B 外推 问题一·Loss·外
les/est_pile_loss_70b.c 推
sv
A16 A_data_value/domain_map 17 域 → 质量域 参考 问题一·域映射
ping_guide.csv 映射表

## 原 PDF 第 3 页

数据说明 3
编号 英文文件名 中文说明 性质 绑定问题·角色
A17 A_data_value/regmix_dom 域摘要 真实 问题一·辅助（本
ain_summary.csv 版未接入求解，供
扩展分析）
A18 A_data_value/regmix_dom 域原始文本样例 真实 可选·辅助
ain_sample.jsonl.xz
说明：A4–A5为训练表（train），A6–A11为检验表（test），A12–A15为外推表（est，即estimated）。
配方表与对应 Loss 表各为一个文件，按 index 列对应。
附件 B（问题二）B_scaling_laws/
编号 英文文件名 中文说明 性质 绑定问题·角色
B1 B_scaling_laws/pythia_t Pythia 训练日志 真实 问题二·主拟合
raining_log_existing.cs （1,176 行）
v
B2 B_scaling_laws/cerebras Cerebras 训练日 半合成 问题二·族外验证
_training_log.csv 志（1,029 行）
B3 B_scaling_laws/training Pythia 插值轨迹 插值 问题二·轨迹验证
_trajectories/（8 个） （8×500）
B4 B_scaling_laws/scaling_ 跨族收敛点（57 真实 问题二·跨族验证
baseline.csv 行，12 族）
B5 B_scaling_laws/publishe 文献标度律数据 真实 问题二·文献验证
d_scaling_data.csv （44 行）
B6 B_scaling_laws/suppleme NQ 半合成实验 半合成 问题二·质量 Q·
ntary_NQ_experiment.csv （360 点） 基础
B7 B_scaling_laws/suppleme NQ 半合成实验 半合成 问题二·质量 Q·
ntary_NQ_experiment_exp （450 点） 扩展
anded.csv
B8 B_scaling_laws/suppleme NQ 半合成实验 半合成 问题二·质量 Q·
ntary_NQ_experiment_lar （1,704 点，含外 大规模
ge.csv 推）
B9 B_scaling_laws/suppleme 大模型元数据 真实 问题二·大模型参
ntary_large_models.csv （100B–10000B） 数
B10 B_scaling_laws/suppleme 大模型预估 Loss 估算 问题二·大模型外
ntary_large_baseline.cs （100B–10000B） 推
v
B11 B_scaling_laws/open_mod 模型族元数据 真实 问题二·辅助
el_family_metadata.csv

## 原 PDF 第 4 页

数据说明 4
编号 英文文件名 中文说明 性质 绑定问题·角色
B12 B_scaling_laws/pythia_c Pythia 检查点索 真实 问题二·辅助
heckpoint_index.csv 引
说明：B1 为主拟合数据；B2/B3 用于模型族外或插值轨迹验证；B4/B5 用于跨族或文献验证；
B6–B8 是唯一含质量 𝑄 的数据，用于把 𝑄 纳入标度律；B9/B10 用于百亿参数以上外推。
问题二在问题一输出的质量评分 𝑄 与配比 𝑝 基础上构建广义标度律；附件 A 为同一数据集，本
问不直接重复读取其原始文件，质量与配比信息通过问题一结果引入。
附件 C（问题三、四）C_efficiency_evolution/
编号 英文文件名 中文说明 性质 绑定问题·角色
C1 C_efficiency_evolution/ 排行榜（4,576 行， 真实 问题四·主用
leaderboard_cleaned.csv 6 维）
C2 C_efficiency_evolution/ 排行榜增强 真实 问题四·可替代
leaderboard_enhanced.cs C1
v
C3 C_efficiency_evolution/ 排行榜时序 混合 问题四·时序
leaderboard_extended_ti
meseries.csv
C4 C_efficiency_evolution/ 全模型元数据 真实 问题四·宏观元数
epoch_all_ai_models.csv 据
C5 C_efficiency_evolution/ Loss–Benchmark 混合 问题四·桥接·可
loss_benchmark_bridge.c 桥接（43 条） 对照
sv
C6 C_efficiency_evolution/ 桥接扩展（75 条） 混合 问题四·桥接·主
loss_benchmark_bridge_e 用
xpanded.csv
C7 C_efficiency_evolution/ 架构元数据（含 真实 问题三·主用；问
model_architecture_meta 上下文长度） 题四
data.csv
C8 C_efficiency_evolution/ 逐任务评测 真实 问题四·必用
detailed_results/（1,863 JSON（约 0.23
目录 / 1,958 JSON） GB）
C9 C_efficiency_evolution/ Leaderboard 原始 真实 问题四·与 C1 等
data/*.parquet Parquet 价（本版未使用，
供扩展分析）
C10 C_efficiency_evolution/ 评测说明目录 说明 参考·不可替代
pythia_*_eval_details/ （仅 README） C8

## 原 PDF 第 5 页

数据说明 5
说明：问题三除 C7 外，另需使用问题一、二的输出（质量评分、配比、标度律参数）。
数据读取说明
数据可能存在缺失、噪声与冗余，须由参赛队伍自行预处理。大文件已提供 xz 压缩版（.jsonl.xz），可用
Python 的 lzma.open() 直接读取，无须解压。
• 流式与分块：流式即逐行读取，分块即按固定行数批量读取，目的都是避免将大文件一次性载入内存。
附件 A 质量信号 JSONL（A1–A3）宜流式或分块读取；不得以内存为由放弃大文件。
• 大文本字段：content / text 字段若仅用于统计特征，可不全文入库，仅在线提取统计量。
• 附件 A：A4 与 A5 通过 index 列对应；配比列为 train_the_pile_*（17 列），Loss 列为 metric/t
he_pile_*_val_loss（13 列）。
• 附件 B：B1 每行记录某模型在某时刻的 N_params_B、D_tokens_B 与 val_loss。
• 附件 C：C1 含 IFEval、BBH、MATH Lvl 5、GPQA、MUSR、MMLU-PRO 六维得分；C8 下每个
子目录对应一个模型的逐任务 JSON。
• 单位换算（全文通用）：N_params_B、D_tokens_B 以十亿为单位（如 1.04 表示 1.04×109），代入
𝐶 =6𝑁𝐷 时须乘以 109；C_FLOPs_1e21 的单位为 1021 FLOPs。
强制使用清单
优先级 路径 约计体积 绑定问题 最低使用方式
必用 A_data_value/slimpajam 约 0.04 GB 问题一 处理全文记录，估计
a_quality_extended/*.j （压缩） arxiv/github 域级 𝑄，并与
sonl.xz 抽样集对照
必用 A_data_value/slimpajam ~0.10 GB（压 问题一 22 维质量评价与冲突消解
a_quality_signal_sampl 缩） 主样本
e.jsonl.xz
必用 C_efficiency_evolution ~0.23 GB 问题四 至少一项逐任务聚合分析
/detailed_results/
必用 附件 A/B/C 全部主 CSV 数十 MB 各问 按赛题要求接入模型
（配方、Pythia、榜单、桥
接、架构、Epoch 等）
任选其一 C_efficiency_evolution ~1 MB 问题四 CSV 与 Parquet 内容等价，
/data/*.parquet 与 lead 不必重复计算
erboard_*.csv

## 原 PDF 第 6 页

数据说明 6
跨附件兼容性与表头速查
附件 核心文件 关键字段 兼容性与连接键
A A_data_value/regmix_t index，17 个域配比 通过 index 与 Loss 表对应
ables/train_mixture_1
m.csv
A A_data_value/regmix_t index，13 个域 Loss 通过 index 与配方表对应
ables/train_pile_loss
_1m.csv
A A_data_value/slimpaja _source_domain，22 个质 需通过领域映射与 17 域体系建立
ma_quality_signal_sam 量指标 联系
ple.jsonl.xz
A A_data_value/slimpaja 同质量指标字段 必用；与抽样集字段一致，覆盖
ma_quality_extended/* arxiv/github
.jsonl.xz
A A_data_value/regmix_d text，_source_domain 可选；辅助跨域映射
omain_sample.jsonl.xz
A A_data_value/domain_m mixture_domain，qualit 17 个配方域到质量域的参考映射
apping_guide.csv y_domain，mapping_type
B B_scaling_laws/pythia N_params_B，D_tokens_B， 真实训练轨迹；标度律拟合核心数
_training_log_existin val_loss 据
g.csv
B B_scaling_laws/scalin family，N_params_B，D_t 跨族收敛点；泛化验证
g_baseline.csv okens_B，val_loss
B B_scaling_laws/supple N_params_B，D_tokens_B， 半合成 N-D-Q 实验点
mentary_NQ_experiment Q_score，val_loss
.csv
C C_efficiency_evolutio Model，#Params (B)，Sub 核心评测表
n/leaderboard_cleaned mission Date，6 维得分
.csv
C C_efficiency_evolutio Model，Val_Loss，LB_*， Loss 到 Benchmark 桥接；按可比
n/loss_benchmark_brid Loss_Comparability 性分层
ge_expanded.csv
C C_efficiency_evolutio model_name，n_layers，n 架构和上下文长度分析
n/model_architecture_ _heads，max_position_e
metadata.csv mbeddings
C C_efficiency_evolutio 逐任务 JSON 必用；细粒度评测聚合
n/detailed_results/

## 原 PDF 第 7 页

数据说明 7
附件 A：数据配方实验与质量信号
数据来源
• 配方实验数据：RegMix 项目（ICML 2024），https://github.com/sail-sg/regmix
• 质量信号数据与扩展质量信号（arxiv、github 两域完整数据文件）：SlimPajama-Meta-rater，https:
//huggingface.co/datasets/opendatalab/SlimPajama-Meta-rater；其中 A1 抽样集为该数据源各质量
信号域的按域抽样记录，非另行生成的独立实验数据
文件结构与说明
文件 格式 规模 性质 说明
A_data_value/regmix_ta CSV 512 行 × 18 真实 512 个训练配方，17 个
bles/train_mixture_1m. 列 The Pile 子领域配比
csv
A_data_value/regmix_ta CSV 512 行 × 14 真实 对应配方的 13 个验证域
bles/train_pile_loss_1 列 交叉熵损失
m.csv
A_data_value/regmix_ta CSV 256 行 × 18 真实 1M 参数规模检验配方
bles/test_mixture_1m.c 列
sv
A_data_value/regmix_ta CSV 256 行 × 14 真实 1M 检验配方对应 Loss
bles/test_pile_loss_1m 列
.csv
A_data_value/regmix_ta CSV 256 行 × 18 真实 60M 参数规模检验配方
bles/test_mixture_60m. 列
csv
A_data_value/regmix_ta CSV 256 行 × 14 真实 60M 检验配方对应 Loss
bles/test_pile_loss_60 列
m.csv
A_data_value/regmix_ta CSV 64 行 × 18 真实 1B 参数规模检验配方
bles/test_mixture_1B.c 列
sv
A_data_value/regmix_ta CSV 64 行 × 14 真实 1B 检验配方对应 Loss
bles/test_pile_loss_1B 列
.csv

## 原 PDF 第 8 页

数据说明 8
文件 格式 规模 性质 说明
A_data_value/regmix_ta CSV 63 行 × 14 外推 10B 尺度预估配方 Loss
bles/est_pile_loss_10b 列
.csv
A_data_value/regmix_ta CSV 63 行 × 14 外推 70B 尺度预估配方 Loss
bles/est_pile_loss_70b 列
.csv
A_data_value/regmix_ta CSV 63 行 × 18 子集 10B 尺度配比（train 子
bles/est_mixture_10b.c 列 集）
sv
A_data_value/regmix_ta CSV 63 行 × 18 子集 70B 尺度配比（train 子
bles/est_mixture_70b.c 列 集）
sv
A_data_value/regmix_do CSV 17 行 × 5 真实 各领域文本抽样统计信息
main_summary.csv 列
A_data_value/domain_ma CSV 17 行 × 4 参考 17 个配方域与质量信号域
pping_guide.csv 列 的映射指南
A_data_value/slimpajam JSONL（xz 51,230 条 × 真实 22 个质量指标，覆盖 7
a_quality_signal_sampl 压缩） 27 字段 个域；
e.jsonl.xz SlimPajama-Meta-rater
质量信号按域抽样子集
（必用）
A_data_value/slimpajam JSONL（xz 17,523 条 × 真实 arxiv 域扩展质量信号
a_quality_extended/arx 压缩） 24 字段 （必用，约 3.5 MB（压缩））
iv_*.jsonl.xz
A_data_value/slimpajam JSONL（xz 203,752 条 真实 github 域扩展质量信号
a_quality_extended/git 压缩） × 24 字段 （必用，约 36 MB（压缩））
hub_*.jsonl.xz
A_data_value/regmix_do JSONL（xz 138,034 条 真实 RegMix 各域原始文本抽
main_sample.jsonl.xz 压缩） 样（可选，约 0.16 GB
（xz 压缩））
性质说明：真实 = 来自公开论文与数据集的直接观测值。外推 = est_pile_loss_10b.csv、es
t_pile_loss_70b.csv 从 1M/60M/1B 三尺度幂律外推，非直接观测。子集 = est_mixture_1
0b.csv、est_mixture_70b.csv 取自 train 配比子集，非独立实验。参考 =domain_mapping_g
uide.csv 为人工整理，非实验数据。

## 原 PDF 第 9 页

数据说明 9
核心字段说明
配方表：index 为配方编号；train_the_pile_* 共 17 列，表示 17 个 The Pile 子领域的训练配比（即领
域配比 𝑝 的取值），每行和约为 1（存在千分位级舍入误差）。
17 个训练领域：arxiv，freelaw，nih_exporter，pubmed_central，wikipedia_en，dm_mathematics，
github，philpapers，stackexchange，enron_emails，gutenberg_pg_19，pile_cc，ubuntu_irc，eur
oparl，hackernews，pubmed_abstracts，uspto_backgrounds。
Loss 表：index 对应配方编号；metric/the_pile_*_val_loss 共 13 列。17 个训练域中，nih_exporter、
enron_emails、europarl、philpapers 仅有训练配比列，无对应交叉熵损失列。参赛队伍可选择保留、合
并、正则化处理或仅在训练配比模型中解释其间接影响，但需说明理由。
质量信号：A1 每行一个 JSON 对象，共 27 个字段，其中 22 个为质量指标字段（14 个标量指标 + 8 个
多维列表型指标），其余 5 个为辅助字段（id、content、sub_path、_source_domain、_source_path）。
A2/A3 每行 24 个字段，为 22 个质量指标、id 与 sub_path；已去除 content、_source_domain、_sour
ce_path，来源域由文件名或路径推断。
22 个质量指标：fineweb_edu，fluency_en，modernbert_cleanliness，modernbert_readability，mo
dernbert_reasoning，modernbert_professionalism，dsir_books，dsir_wiki，dsir_math，qurater，
ad_en，rps_doc_word_count，rps_doc_num_sentences，rps_doc_unigram_entropy，rps_doc_frac_u
nique_words，rps_doc_frac_no_alph_words，rps_doc_frac_chars_top_2gram，rps_doc_frac_chars
_top_3gram，rps_lines_uppercase_letter_fraction，rps_lines_ending_with_terminal_punctutio
n_mark，rps_lines_numerical_chars_fraction，rps_doc_mean_word_length。
其中 8 个列表型字段需先压缩为标量后再参与建模。扩展集与抽样集的 22 个质量指标字段一致，宜使用同
一套预处理流程。
域映射：质量信号覆盖 7 个域（arxiv、book、c4、commoncrawl、github、stackexchange、wikipedia），配
方实验涉及上述 17 个域。二者域名并不一一相同。domain_mapping_guide.csv 以配方域为行，给出到质
量域的参考对应：direct / near_direct / inferred。其中 c4 仅出现在质量信号侧，配方 17 域中无同名列。
附件 B：模型训练动态轨迹与标度律补充数据
数据来源
• Pythia 训练日志：EleutherAI Pythia Scaling Suite，https://github.com/EleutherAI/pythia
• Cerebras-GPT 轨迹：根据 Pythia 标度律和公开 Cerebras-GPT 训练设定校准生成
• 跨族基准点：从公开模型族文档与论文整理
• 大模型缩放参数：Epoch AI 数据库，https://epoch.ai/data/all_ai_models.csv
• 已发表标度律数据：Kaplan et al. (2020)、Hoffmann et al. (2022) 等文献

## 原 PDF 第 10 页

数据说明 10
文件结构与说明
文件 格式 规模 性质 说明
B_scaling_laws/pythia_ CSV 1,176 行 × 真实 8 个 Pythia 模型检查点
training_log_existing. 15 列 的真实训练轨迹
csv
B_scaling_laws/cerebra CSV 1,029 行 × 半合成 7 个 Cerebras 模型训练轨
s_training_log.csv 15 列 迹（校准 + 噪声）
B_scaling_laws/scaling CSV 57 行 × 5 真实 12 个模型族的跨族收敛基
_baseline.csv 列 准点
B_scaling_laws/supplem CSV 360 行 半合成 N-D-Q 实验点
entary_NQ_experiment.c
sv
B_scaling_laws/supplem CSV 450 行 半合成 扩展版
entary_NQ_experiment_e
xpanded.csv
B_scaling_laws/supplem CSV 1,704 行 半合成 大规模矩阵，含更大参数
entary_NQ_experiment_l 外推
arge.csv
B_scaling_laws/supplem CSV 132 行 真实 100B 以上开源模型缩放
entary_large_models.cs 参数（Epoch AI 公开报
v 告值）
B_scaling_laws/supplem CSV 128 行 估算 100B 以上模型预估 Loss
entary_large_baseline.
csv
B_scaling_laws/publish CSV 44 行 真实 已发表标度律基准点
ed_scaling_data.csv
B_scaling_laws/trainin CSV 8 × 500 = 插值 8 个 Pythia 模型插值训
g_trajectories/*.csv 4,000 行 练轨迹
B_scaling_laws/pythia_ CSV 1,386 行 真实 Pythia 检查点索引元数据
checkpoint_index.csv
B_scaling_laws/open_mo CSV 18 行 真实 模型族仓库元数据
del_family_metadata.cs
v
性质说明：真实 = 直接观测值或公开报告值。半合成 = cerebras_training_log.csv、suppl
ementary_NQ_experiment*.csv 基于真实标度律校准并叠加噪声，非直接实验观测。估算 = s
upplementary_large_baseline.csv 用已拟合标度律参数估算 Loss，非观测值。插值 = trai
ning_trajectories/*.csv 从 Pythia 检查点插值生成。

## 原 PDF 第 11 页

数据说明 11
核心字段说明
pythia_training_log_existing.csv：N_params_B 为参数量，D_tokens_B 为已训练数据量，C_FLOPs_1
e21 为累计计算量，val_loss 为验证集交叉熵损失。四者的单位换算统一见《数据读取说明》。
Pythia 日志中 C_FLOPs_1e21 与 6𝑁𝐷 的中位比值约为 1。Cerebras 半合成轨迹已统一 D_tokens_B 单位
为十亿 tokens，并与 C_FLOPs_1e21 保持 6𝑁𝐷 量级一致。
pythia_checkpoint_index.csv 收录多个 Pythia 模型的检查点索引，而 pythia_training_log_existi
ng.csv 仅包含其中 8 个模型（约 70M–12B）的训练轨迹。
标度律数据汇总
数据集 N 范围 来源
Pythia 真实轨迹（1,176 0.07–12B EleutherAI Pythia
点）
Cerebras 半合成轨迹 0.11–13B Pythia 标度律校准
（1,029 点）
跨族收敛基准（57 点） 0.07–72B 12 个模型族公开数据
已发表基准（44 点） 约 0.5–280B 公开论文整理
大模型缩放参数（132 点） 100B 以上 Epoch AI 数据库
N-D-Q 半合成实验（360 / 含更大参数外推 校准 + 插值 + 外推
450 / 1,704 点）
附件 C：模型评测与演进数据
数据来源
• Open LLM Leaderboard v2：https://huggingface.co/datasets/open-llm-leaderboard-old/results
• Epoch AI Models Dataset：https://epoch.ai/data/all_ai_models.csv
• 技术报告与模型配置：用于 Loss–Benchmark 桥接和架构元数据整理
• HuggingFace Open LLM Leaderboard 详细评测结果：https://huggingface.co/datasets/open-llm-
leaderboard/results
文件结构与说明

## 原 PDF 第 12 页

数据说明 12
文件 格式 规模 性质 说明
C_efficiency_evolution CSV 4,576 行 × 真实 6 维 Benchmark 评测得分
/leaderboard_cleaned.c 12 列
sv
C_efficiency_evolution CSV 4,576 行 × 真实 cleaned + Epoch AI 发布
/leaderboard_enhanced. 15 列 日期等
csv
C_efficiency_evolution CSV 4,599 行 × 混合 约 2019–2025 年时序（含
/leaderboard_extended_ 11 列 历史模型）
timeseries.csv
C_efficiency_evolution CSV 3,523 行 × 真实 Epoch AI 全量模型元数
/epoch_all_ai_models.c 57 列 据（不含评测得分）
sv
C_efficiency_evolution CSV 43 行 混合 原始 Loss–Benchmark 桥
/loss_benchmark_bridge 接
.csv
C_efficiency_evolution CSV 75 行 混合 扩展桥接（高可比 + 中可
/loss_benchmark_bridge 比）
_expanded.csv
C_efficiency_evolution CSV 45 行 × 7 真实 主流开源模型架构元数据
/model_architecture_me 列
tadata.csv
C_efficiency_evolution JSON 1,863 个模 真实 各模型 6 维 Benchmark
/detailed_results/ 型子目录 / 逐任务详细评测结果（必
1,958 个 用，约 0.23 GB；4 个
JSON JSON 截断，宜按目录取
最新可解析记录）
C_efficiency_evolution 文本 7 个目录 说明 目前仅含 README（数
/pythia_*_eval_details 据集说明），不能替代 det
/ ailed_results/ 的逐任
务 JSON
C_efficiency_evolution Parquet 4,576 行 × 真实 原始 Leaderboard
/data/train-00000-of-0 36 列 Parquet；核心六维与 C1
0001.parquet 等价，另含原始附加列，
任选其一
性质说明：真实 = 来自公开 Leaderboard 或公开元数据（含 data/*.parquet）。混合 =loss_b
enchmark_bridge*.csv 的 Loss 来源与验证集不完全统一，须按可比性分层；leaderboard_ex
tended_timeseries.csv 不同年份评测标准可能不完全一致。说明 = pythia_*_eval_details

## 原 PDF 第 13 页

数据说明 13
/ 仅含数据集说明文本。
核心字段说明
leaderboard_cleaned.csv：关键字段包括 Model、#Params (B)、Submission Date、IFEval / BBH / MA
TH Lvl 5 / GPQA / MUSR / MMLU-PRO（6 维评测得分）、均分列、Hub License、Type。
leaderboard_enhanced.csv：在 cleaned 基础上增加 Epoch AI 相关匹配列。
epoch_all_ai_models.csv：不包含评测得分，主要提供发布时间、组织、参数量、训练计算量、训练数据
量、开源权重等宏观元数据。部分文本字段可能包含换行，建议用标准 CSV 解析后计数。
Loss–Benchmark 桥接：loss_benchmark_bridge_expanded.csv 包含 75 个模型同时具备交叉熵损失与 6
维 Benchmark 得分。其中高可比样本主要来自 Pythia（Loss 可与附件 B 对照），其余为中可比样本（Loss
来源于不同技术报告或论文）。Loss_Comparability 字段标注可比性等级。
模型架构元数据：model_architecture_metadata.csv 包含层数、注意力头数、隐藏维度、词表大小、最
大上下文长度（max_position_embeddings）和训练数据量等字段。模型名称与 Leaderboard 的 Model 字
段不一定完全一致，匹配时需说明规则。
数据使用说明
1. 先满足问题绑定必用集，再展开方法设计；附录须附数据利用清单。
2. 半合成与外推数据（supplementary_NQ_experiment*.csv、cerebras_training_log.csv、est_pi
le_loss_*.csv、supplementary_large_baseline.csv）非直接观测，应在论文中标注。
3. scaling_baseline.csv 可用于跨族验证；若用作盲测，应说明其与训练日志的近邻关系。
4. 开源筛选可依据 Leaderboard 的 Hub License 或 Epoch AI 的 Open model weights?，须说明口径。
5. 三套附件数据源相互独立采集，四问建模逻辑需递进耦合；桥接关系主要通过 Loss、Model、(𝑁,𝐷)
与领域映射建立。
6. C8 共 1,863 个模型子目录、1,958 个 JSON；其中 4 个 JSON 截断，1,860 个目录含至少一个可解析
JSON，1,854 个模型六维完整。逐任务聚合时宜按目录取最新可解析记录，跳过损坏文件并说明处理
方式。
