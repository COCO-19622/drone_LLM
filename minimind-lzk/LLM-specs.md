# MiniMind-3 / minimind-lzk：模型与训练规划参考

更新日期：2026-10-21。本文依据本地模型配置、权重文件、训练脚本和实验配置整理，供制定后续执行计划使用。基础模型是 `minimind-lzk/base/` 中的 MiniMind-3 成品模型副本；`minimind-lzk` 是计划中的 LoRA 实验名，目前不是已完成微调的新模型。

## 基础模型关键数据

| 项目 | 数值或实现 |
| --- | --- |
| 模型类型 | Decoder-only 因果语言模型；Transformers 配置为 `Qwen3ForCausalLM` |
| Transformer 层数 | **8 层**（权重含第 0 至 7 层） |
| 隐藏维度 | **768** |
| 注意力 | 因果自注意力、GQA；8 个 Query 头、4 个 Key/Value 头，每头 96 维（每个 KV 头供 2 个 Query 头使用） |
| 前馈网络 | SwiGLU 风格，`hidden_act=silu`，中间维度 **2432** |
| 词表大小 | **6400** tokens |
| 位置编码 | RoPE，`rope_theta=1,000,000`；基础配置的 `rope_scaling=null` |
| 配置中的最大位置数 | **32768**；这是模型配置值，不等于已验证可稳定处理 32768 token |
| 归一化 | RMSNorm，`eps=1e-6`；注意力中另有 Q/K norm |
| Dropout / 偏置 | 注意力 dropout 0；注意力线性层无 bias |
| 输出权重 | 输入 embedding 与输出 head 共享（`tie_word_embeddings=true`） |
| MoE | 当前基础模型和 LoRA 实验均为 Dense，`use_moe=0` |
| 权重精度 | 基础 `model.safetensors` 的 90 个张量均为 FP16 |
| 基础参数量 | **63,912,192（约 63.91M）**；从 `model.safetensors` 张量形状求和，按共享权重只计一次 |

权重文件约 122 MiB；供原生训练脚本读取的转换权重为 `base/minimind3_base_768.pth`，约 132 MiB。`preparation.json` 记录：严格加载和重载通过，同一输入下 HF 与原生 FP32 logits 最大差为 0；这只是转换验证，不是任务效果评估。

## 当前 LoRA 实验配置

配置来源：`lora_config.json`；入口：`train.py` → `../minimind/trainer/train_lora.py`。

| 项目 | 当前设置 |
| --- | --- |
| 基础权重 | `base/minimind3_base_768.pth`，来自成品 MiniMind-3 |
| 适配器名称及输出 | `minimind-lzk`；训练后拟保存至 `adapter/minimind-lzk_768.pth` |
| LoRA 作用位置 | 原生 `apply_lora` 选取输入、输出维度相同的线性层；本模型对应每层注意力的 `q_proj` 和 `o_proj`，共 16 处 |
| LoRA rank | 16；代码采用 A、B 两个低秩矩阵相加，未设置 LoRA alpha 缩放 |
| LoRA 可训练参数 | 按当前 16 处、rank 16 计算为 **393,216（约 0.393M）**；基础模型参数冻结 |
| 序列长度 | `max_seq_len=340` tokens；超出时从右侧截断 |
| Batch / 梯度累积 | 每设备 batch size 1，累积 16 步；单设备有效 batch 约 16 条 |
| 训练轮数 / 初始学习率 | 1 epoch / `1e-4`；脚本逐步调整学习率 |
| 混合精度 / 数据加载 | BF16 autocast；`num_workers=0` |
| 日志 / 保存间隔 | 每 10 step 记录，每 100 step 保存；恢复状态写入本实验 `checkpoints/` |
| 运行设备 | 训练脚本在 CUDA 可用时默认选择 `cuda:0`；此前本机检测到 RTX 5060 Laptop GPU，约 8 GiB 显存。当前空闲显存和实际可运行 batch 待确认 |
| 实验跟踪 | 默认未启用 SwanLab |

数据文件预期为 `dataset/train.jsonl`，UTF-8 JSONL，每行一个对象，包含 `conversations` 数组；每条消息至少有 `role` 和 `content`。训练脚本以 SFT 数据集处理，只对 assistant 回复计算监督标签。`dataset/train.example.jsonl` 仅是格式示例，真实 `dataset/train.jsonl` 目前不存在。须留意 340 token 截断会不会截掉目标回复。

## 当前状态与计划所需待办

- 已完成：基础模型和分词器复制、原生权重转换及加载一致性验证；实验目录及配置已建立。
- 未完成：明确微调目标、准备真实训练集和独立评估问题；尚未启动 LoRA 训练，`adapter/` 与 `checkpoints/` 目前为空。
- 制定计划时应先确认数据来源、数量、质量和授权，再检查 token 长度分布及 assistant 标签是否保留；随后设置基线评估、训练、训练后评估和回退标准。
- 模型在目标任务上的基线质量、340 token 对数据的覆盖率、训练耗时与峰值显存均**待确认**；不能从架构配置推断实际效果或长上下文能力。
- 启动方式：在 Windows 命令提示符进入 `C:\LLM\minimind-lzk`，运行 `..\minimind\.venv311\Scripts\python.exe -X utf8 train.py` 仅检查配置；数据准备好后追加 `--start` 训练，追加 `--start --resume` 恢复。不要仅凭本文启动训练。

## 核对来源

- 模型配置：`base/config.json`；权重：`base/model.safetensors`（参数量由 safetensors 元数据计算）。
- 原生结构及 LoRA 实现：`../minimind/model/model_minimind.py`、`../minimind/model/model_lora.py`。
- 实验参数和状态：`lora_config.json`、`preparation.json`、`README.md`、`../minimind/trainer/train_lora.py`。
