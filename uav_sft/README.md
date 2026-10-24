# 无人机中文 SFT 试验数据

交付文件：[train.jsonl](../train.jsonl)，位于 `C:\LLM\train.jsonl`。整理日期：2026-10-24。

## 数量与格式

| 类别 | 条数 |
| --- | ---: |
| 无人机基础知识 | 700 |
| 自主飞行场景判断 | 600 |
| 任务规划与步骤分解 | 400 |
| PX4 / MAVLink / ROS 等工程知识 | 200 |
| 通用简单指令 | 100 |
| 总计 | 2000 |

文件使用 UTF-8 无 BOM，每个物理行是一条 JSON。只含两个非空字符串字段：`instruction`、`output`。回答中的换行保存为 JSON 转义，不会拆成多个物理行。数据已使用固定种子打散。

```json
{"instruction":"GPS正常是否就代表避障可靠？","output":"不是，定位信息不能替代障碍物感知。"}
```

问题长度中位数为 22 字符，回答长度中位数为 21 字符；最长问题 84 字符、最长回答 96 字符。这里统计的是字符，不是 tokenizer token。普通无人机回答控制在 1～4 句话；任务计划为 3～8 个编号步骤。

## 来源与整理方式

本数据是**依据官方文本整理、并作简单场景组合的合成试验集**，不是从官方发布的 SFT 数据包抽取，也不是 2000 条真实飞行事件。

- PX4 项目贡献者：[基础概念](https://github.com/PX4/PX4-Autopilot/blob/main/docs/en/getting_started/px4_basic_concepts.md)、[EKF](https://github.com/PX4/PX4-Autopilot/blob/main/docs/en/advanced_config/tuning_the_ecl_ekf.md)、[VIO](https://github.com/PX4/PX4-Autopilot/blob/main/docs/en/computer_vision/visual_inertial_odometry.md)、[失效保护](https://github.com/PX4/PX4-Autopilot/blob/main/docs/en/config/safety.md)、[Offboard](https://github.com/PX4/PX4-Autopilot/blob/main/docs/en/flight_modes/offboard.md)、任务与飞行模式、传感器校准、控制及电源文档。文档声明为 [CC BY 4.0](https://docs.px4.io/main/en/contribute/docs#licence)。
- ArduPilot 项目贡献者：[EKF 概述](https://github.com/ArduPilot/ardupilot_wiki/blob/master/common/source/docs/common-apm-navigation-extended-kalman-filter-overview.rst)。Wiki [LICENSE](https://github.com/ArduPilot/ardupilot_wiki/blob/master/LICENSE) 为 CC BY-SA 3.0；涉及该来源的行在元数据中标明。
- ROS 2 项目贡献者：[Humble 概念文档](https://github.com/ros2/ros2_documentation/tree/humble/source/Concepts/Basic)，覆盖节点、话题、服务、动作和参数。文档仓库标示 CC BY 4.0。
- SLAM 概念补充：Steve Macenski 等维护者的 [SLAM Toolbox README](https://github.com/SteveMacenski/slam_toolbox/blob/ros2/README.md)，参考其中定位、建图和二维系统说明，仅用于 5 条入门概念问答。文档单独许可未在本轮确认，元数据中保留该区别，不宣称整份训练集已取得统一的宽松许可。
- 100 条通用指令为自行编写的简单算术、排序、列表、信息提取和短句整理，不使用外部通用语料。

已读取的具体文档 URL、读取日期、分支与文件 blob SHA 记录在 [sources.json](sources.json)。blob SHA 是文件内容标识，**不是整个仓库的 commit SHA**。少量路径读取失败或仅返回重定向，也有记录，但没有将其作为实质知识来源。

知识卡包含一个定义与四个不同角度的问题，选用 140 张基础卡和 40 张工程卡。基础卡文件中留有未使用的备用卡，生成器只选前 140 张。场景题基于 60 个异常骨架，分别组织处理、核查、恢复、错误建议判断、原因与附加约束等 10 类问题；任务题由 40 个任务骨架结合 10 种流程约束组成。场景、条件和表达均经过改写，未直接复制原文段落。来源标签表示主题依据，并不表示官方文档逐字给出了该合成场景的答案。

因此，条目数不等于独立知识点数；仍有相关概念与组合近似样本。已避免仅通过同义改写、替换地点名或重复输出扩充数量，但没有做完整语义去重或专家逐条认证。这份数据适合用户指定的小规模 LoRA 试验用途，数据表现应通过另外准备的评估题观察。

## 核查结果

- 最终磁盘文件 2000 行，逐行 JSON 解析通过。
- 每行字段完全一致，`instruction` / `output` 均为非空字符串。
- 完全重复样本为 0；统一 Unicode 与空白后的重复问题为 0；同问题冲突答案为 0。
- 未发现替换字符、空字符、控制乱码、占位符或超出长度上限的条目。
- 400 条任务分解均为 3～8 步，其余非列表无人机回答均不超过 4 句话。
- 已检查固定分层抽样及全部 60 个场景的首答；并未据此声称所有技术细节经过实飞验证。
- 没有加入原始 IMU、GPS、PWM 数值日志，也没有生成“传感器数据 → 电机 PWM”样本。

定位异常的回答区分单个来源故障与整体估计无效；没有把“GPS失效”一律写成“切VIO”，也没有在位置条件不明时保证返航或悬停可用。任务分解明确以多旋翼定位、电量和航线满足要求为前提。

详细机器检查见 [validation_report.json](validation_report.json)，抽查文本见 [review_samples.md](review_samples.md)。[train_metadata.jsonl](train_metadata.jsonl) 为独立逐行索引，记录最终行号、类别、骨架、来源 ID、整理方式和样本散列；这些辅助字段**没有混入训练文件**。

## 复现与训练接口

生成脚本为 [generate_dataset.py](generate_dataset.py)，只使用 Python 标准库。运行它只会重建本交付文件与辅助记录，不启动训练。

当前工作区的 `minimind/dataset/lm_dataset.py` 读取 `conversations`，而本文件按要求使用 `instruction/output`。在使用该读取器前，需要映射成用户/助手消息，或另行适配读取器；不能将本文件直接传入该版本而不做映射。本次没有修改训练代码、配置或启动训练，也未另建不同字段格式的训练文件。

本轮没有 tokenizer 统计、训练集/验证集切分或模型效果测试。若后续切分，应按知识主题、场景骨架或任务骨架分组，避免同一骨架的变体分到训练和验证两侧。
