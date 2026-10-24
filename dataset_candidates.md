# LoRA / SFT 数据候选清单

核查日期：2026-10-24（北京时间）。共 12 个候选：A 类 6 个、B 类 6 个。仅搜索、阅读 README、许可与数据卡、查看文件目录；未下载数据集、克隆仓库、清洗或启动训练。

**主要结论：本轮没有找到足够成熟、许可明确、可直接用于纯文本 LLM SFT 的无人机专用 QA 数据。** A 类因此包含 3 个官方文档来源和 3 个多模态数据集；文档来源不是现成 SFT 数据集，也不计为现成 QA。不能把导航指令本身当成 instruction/response 训练对。

Stars 为核查时 GitHub 页面显示值，k 是页面约数；表示关联仓库热度，不表示数据下载量或质量。数据规模沿用发布方口径，消息、轨迹和 QA 数不能横向等同。“适合 LoRA”主要按当前**纯文本语言模型**判断；“直接”仅指已有输入/目标文本，仍需训练框架字段映射，本阶段没有转换。

## A 类：无人机自主飞行及相关领域

| 数据集 | GitHub | Stars | 领域 | 语言 | 数据规模 | License | 数据地址 | 是否适合Lora | 简单评价 |
| --- | ------ | ----- | -- | -- | ---- | ------- | ---- | -------- | ---- |
| PX4 官方文档（知识来源，非成品数据集） | [PX4-Autopilot/docs](https://github.com/PX4/PX4-Autopilot/tree/main/docs) | 约 12.9k（整个飞控仓库） | PX4 / ROS / MAVLink；control；SLAM / localization；UAV autonomous flight | 英文、中文等；译文覆盖可能不同 | 持续更新文档；无现成 QA 数量 | 文档 CC BY 4.0；飞控代码 BSD-3-Clause，不能混用许可口径 | [官方文档](https://docs.px4.io/main/en/)；[中文](https://docs.px4.io/main/zh/) | **需先从文档转换 QA** | 无人机知识、Offboard、状态估计、接口和排障价值高。旧 PX4-user_guide README 已声明迁移，优先新 docs；转换时应保留固件版本与来源。 |
| ArduPilot Wiki（知识来源，非成品数据集） | [ardupilot_wiki](https://github.com/ArduPilot/ardupilot_wiki) | 679 | ArduPilot / MAVLink；control；path planning；obstacle avoidance；localization | 英文为主 | 文档库；无现成 QA 数量 | [仓库 LICENSE](https://github.com/ArduPilot/ardupilot_wiki/blob/master/LICENSE)：CC BY-SA 3.0 | [Copter 文档](https://ardupilot.org/copter/)；[开发者文档](https://ardupilot.org/dev/) | **需先从文档转换 QA** | 飞行模式、任务、参数、避障与故障排查相关性强；不是问答数据包，需按机型和版本组织。 |
| ROS 2 官方文档（知识来源，非成品数据集） | [ros2_documentation](https://github.com/ros2/ros2_documentation) | 约 1.0k | ROS；robotics；工程接口 | 英文为主 | 多发行版教程与概念文档；无现成 QA 数量 | CC BY 4.0（仓库标示） | [ROS 2 文档入口](https://docs.ros.org/en/)；[源码](https://github.com/ros2/ros2_documentation/tree/rolling/source) | **需先从文档转换 QA** | 适合 ROS 通信、节点、QoS、构建与调试知识；无人机相关性间接，不能等同飞行控制数据。应选择具体发行版。 |
| OpenFly | [OpenFly-Platform](https://github.com/SHAILAB-IPEC/OpenFly-Platform) | 375 | UAV autonomous flight；path planning；perception；multimodal | 英文指令 | 约 100k 飞行轨迹；论文覆盖 18 场景 | [数据卡](https://huggingface.co/datasets/IPEC-COMMUNITY/OpenFly)：Apache-2.0；平台代码 MIT | [官方数据与文件目录](https://huggingface.co/datasets/IPEC-COMMUNITY/OpenFly/tree/main) | **不直接适合纯文本 LLM；适合 VLM/VLA** | 含图像、指令、动作、位置及朝向，README 有结构示例。**这不是可以直接用于当前 LLM LoRA 的 SFT 数据，更适合视觉模型、控制模型或多模态训练。** 目录可见，数据预览器超时。 |
| TravelUAV / TRAVEL | [TravelUAV](https://github.com/prince687028/TravelUAV) | 293 | UAV autonomous flight；path planning；perception；multimodal | 英文指令为主 | 论文约 12k 轨迹 | **未在所查 README / 数据卡确认明确数据许可**，作为待确认候选 | [官方数据目录](https://huggingface.co/datasets/wangxiangyu0814/TravelUAV/tree/main) | **不直接适合纯文本 LLM；适合导航多模态训练** | 目标导向导航与连续轨迹关联强；不能直接提取指令当完整 SFT。**这不是可以直接用于当前 LLM LoRA 的 SFT 数据，更适合视觉模型、控制模型或多模态训练。** 页面和分卷文件可见，预览器报 BadZipFile。 |
| RoboVQA | [google-deepmind/robovqa](https://github.com/google-deepmind/robovqa) | 37（官方加载示例仓库） | robotics；机器人推理；multimodal | 英文 | 829,502 视频/文本对；29,520 个独特指令；约 238 小时视频 | README：软件 Apache-2.0，其他材料 CC BY 4.0 | [官方项目与数据入口](https://robovqa.github.io/)；[项目链接的 HF 目录](https://huggingface.co/datasets/Tianli/robovqa/tree/main/tfrecord) | **不直接适合纯文本 LLM；适合视频 QA 微调** | 规划、任务成功判断、可供性、过去描述和未来预测；主要是机器人操作，并非无人机导航。**这不是可以直接用于当前 LLM LoRA 的 SFT 数据，更适合视觉模型、控制模型或多模态训练。** 去掉视频通常会丢失回答依据。 |

### A 类核查说明

- PX4 许可依据为[官方文档贡献说明](https://docs.px4.io/main/en/contribute/docs#licence)，迁移依据为[旧仓库 README](https://github.com/PX4/PX4-user_guide)。ROS、ArduPilot 的仓库链接包含 README 与许可入口。
- OpenFly 的训练数据入口由 README 的 Data Preparation 指向，不能把其 DataGen 仿真环境包当训练 QA。数据页标注 Apache-2.0，与平台 MIT 分开记录。
- TravelUAV 规模依据[官方论文](https://arxiv.org/abs/2410.07087)，不能由公开下载地址推断其训练授权。
- RoboVQA 规模依据[官方论文](https://arxiv.org/abs/2311.00899)，许可依据官方代码仓库 README。其 GitHub Stars 较低，因为该仓库主要提供数据加载示例，不代表完整项目影响力。
- 本轮对 flight control QA、ROS QA、无人机 instruction/QA 等方向进行了搜索，但未确认可优先采用的成熟纯文本数据包。没有用纯图像检测集、SLAM 传感器序列或强化学习轨迹凑数；这些方向也不能替代无人机技术问答。

## B 类：其他通用能力

| 数据集 | GitHub | Stars | 领域 | 语言 | 数据规模 | License | 数据地址 | 是否适合Lora | 简单评价 |
| --- | ------ | ----- | -- | -- | ---- | ------- | ---- | -------- | ---- |
| Alpaca Chinese Dataset | [open-chinese/alpaca-chinese-dataset](https://github.com/open-chinese/alpaca-chinese-dataset) | 218 | 中文通用指令 / QA | 中文＋英文对应字段 | 约 52k 双语条目，不应计为 104k 独立任务 | **所查 README / 仓库页未明确数据许可**；上游及翻译授权待确认 | [数据目录](https://github.com/open-chinese/alpaca-chinese-dataset/tree/main/data)；README 指向 alpaca-chinese-52k.json | **结构直接适合；许可待确认** | instruction/input/output，另有英文对应字段；README 也出现 zh_* 字段示例，实际版本字段待后续检查。作者披露翻译质量问题并给出评分；适合作为小规模中文候选，不因可访问就视为已获授权。 |
| Code Alpaca 20K | [sahil280114/codealpaca](https://github.com/sahil280114/codealpaca) | 约 1.5k | 代码生成、修改、优化 | 英文＋代码 | 约 20k 条 | 仓库 Apache-2.0；README 说明由 text-davinci-003 生成，并提及上游条款 | [数据目录](https://github.com/sahil280114/codealpaca/tree/master/data)（code_alpaca_20k.json） | **直接适合** | 明确 instruction/input/output，规模小、格式清晰；历史合成数据，README 尚未提供完整评测，不应默认所有代码可运行。 |
| MetaMathQA | [meta-math/MetaMath](https://github.com/meta-math/MetaMath) | 457 | 数学 / 分步推理 | 英文 | 约 395k 条 | [数据卡 MIT](https://huggingface.co/datasets/meta-math/MetaMathQA)；代码仓库 Apache-2.0 | [官方 HF 数据卡与预览](https://huggingface.co/datasets/meta-math/MetaMathQA) | **直接适合** | query/response，含 original_question 和 type；基于数学题增强生成，适合数学推理。不是工程控制问答；评估时需留意与上游数学题的重合。 |
| ScienceQA | [lupantech/ScienceQA](https://github.com/lupantech/ScienceQA) | 739 | STEM / 科学 QA（也含语言、社会科学） | 英文 | 21,208 题；train 12,726，val/test 各 4,241 | **数据 CC BY-NC-SA 4.0**；不能用代码 MIT 替代数据许可 | [官方数据目录](https://github.com/lupantech/ScienceQA/tree/main/data)；[项目入口](https://scienceqa.github.io/) | **有条件：纯文本可解训练子集，或多模态模型** | question/choices/answer/lecture/solution 等可组成 SFT。含依赖图像的题，不能删除图像后直接用于纯文本 LLM；只用训练切分。是基础科学教育题，不是专业工程手册。 |
| databricks-dolly-15k | [databrickslabs/dolly](https://github.com/databrickslabs/dolly) | 约 10.8k | 通用助手、问答、总结、信息抽取 | 英文 | 约 15k 条 | [数据卡 CC BY-SA 3.0](https://huggingface.co/datasets/databricks/databricks-dolly-15k)；代码 Apache-2.0 | [官方数据卡与预览](https://huggingface.co/datasets/databricks/databricks-dolly-15k) | **直接适合** | instruction/context/response/category；人工编写、规模紧凑，适合通用能力补充。单轮为主，README 明确说明有质量与偏差局限。 |
| OpenAssistant OASST2 | [LAION-AI/Open-Assistant](https://github.com/LAION-AI/Open-Assistant) | 约 37.4k | 多轮对话 / 通用助手 | 多语言，含中文 | ready 版 13,854 棵对话树、135,174 条消息；其中中文 8,615 条消息 | [数据卡 Apache-2.0](https://huggingface.co/datasets/OpenAssistant/oasst2) | [官方 OASST2 数据卡与预览](https://huggingface.co/datasets/OpenAssistant/oasst2) | **适合；需还原对话树并筛选回复** | text/role/parent_id/lang/rank 等字段；不是现成扁平 messages 样本。优先质量审核过的 assistant 分支。项目已结束，README 仍指向最终数据发布。中文数不是中文 QA 对数。 |

### 访问与格式核查边界

以上 GitHub 项目及所列数据入口在核查时可打开；Code Alpaca、中文 Alpaca、ScienceQA 查看了 README 和数据目录，未读取完整数据文件。MetaMathQA、Dolly、OASST2 可见网页预览及字段；OpenFly、TravelUAV 文件目录可见，但预览器报错。RoboVQA 官方项目链接的 HF TFRecord 目录可打开。**没有执行实际数据加载或全量下载，因此不保证每个分片可成功下载、解压或加载。**

许可栏记录发布方声明与缺口；没有将代码许可自动套到数据上。Stars、README 完整度是辅助信号，推荐优先考虑任务匹配度、文本监督是否完整、数据许可是否明确。ScienceQA 的非商业限制、中文 Alpaca 与 TravelUAV 的许可缺口已单列。

## 无人机 / 自主飞行方向最推荐

1. **[PX4 官方文档](https://github.com/PX4/PX4-Autopilot/tree/main/docs)**：最适合**无人机知识、控制、ROS / PX4**。若当前目标是纯文本无人机技术助手，这是优先知识来源；需要另阶段按版本转成可核查的 QA，目前没有现成训练对。
2. **[ArduPilot Wiki](https://github.com/ArduPilot/ardupilot_wiki)**：最适合**无人机知识、控制、任务规划与排障**。可补充不同飞控生态；同样需要文档转 QA。
3. **[ROS 2 官方文档](https://github.com/ros2/ros2_documentation)**：最适合**ROS 工程知识**。用于节点、通信、配置与调试基础，需转 QA；不能单靠它获得无人机自主导航决策能力。
4. **[OpenFly](https://github.com/SHAILAB-IPEC/OpenFly-Platform)**：最适合**自主导航、感知与动作预测**。是 UAV 多模态方向的优先候选，已有较清楚的数据入口与格式；当前纯文本 LLM LoRA 不直接采用。
5. **[RoboVQA](https://github.com/google-deepmind/robovqa)**：最适合**机器人推理、任务规划、成功判断**。视频 QA 监督丰富，适合以后多模态扩展；不是无人机专用文本 QA。

TravelUAV 保留为导航备选，数据许可未确认，暂不排入优先推荐。对于当前纯文本目标，前三项是“值得构造 QA 的来源”，后两项是“后续多模态候选”，没有把它们宣称为可直接混合的 SFT 数据。

## 通用能力方向最推荐

1. **[OASST2](https://huggingface.co/datasets/OpenAssistant/oasst2)**：优先补**中文通用与多轮对话**。许可明确、有中文消息；需要按 lang 和对话树选择质量合适的分支，中文规模有限。
2. **[Code Alpaca 20K](https://github.com/sahil280114/codealpaca)**：优先补**代码**，输入输出格式简单，适合作为首批代码候选。
3. **[MetaMathQA](https://huggingface.co/datasets/meta-math/MetaMathQA)**：优先补**数学推理**，已有分步 response 和清晰数据卡；主要是英文。
4. **[ScienceQA](https://github.com/lupantech/ScienceQA)**：补**STEM 基础科学问答**，附解释；仅在非商业许可适用且选用纯文本可解训练题时适合当前目标，图像依赖题留给多模态模型。
5. **[Dolly 15K](https://huggingface.co/datasets/databricks/databricks-dolly-15k)**：补**通用问答、总结与指令遵循**，人工编写、规模小，但以英文单轮为主。

中文 Alpaca 52K 的结构更接近现成中文指令集，但本轮未确认数据许可，先作为次选记录；优先推荐许可声明明确的 OASST2 中文部分，不把格式适配性等同于授权完备。
