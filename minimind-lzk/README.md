# minimind-lzk

以工作区现有 `../minimind-3` 成品模型为基础的独立 LoRA 实验。2026-10-24 已从原始 MiniMind-3 成品权重重新初始化 LoRA，使用 8000 条训练样本完成 1 轮微调；实验名称不会自动改变模型的自我介绍。

- `base/`：原模型及分词器的独立副本，以及转换后的 `minimind3_base_768.pth`，供训练读取。
- `adapter/`：训练后保存 `minimind-lzk_768.pth` LoRA 参数，推理需要配合本目录对应的基础模型。
- `checkpoints/`：本实验的完整恢复状态。
- `dataset/train.jsonl`：已扩展为 8000 条 `conversations/role/content` 格式的问答训练数据。保留原有 2000 条，新增 6000 条；旧的根目录 `../train.jsonl` 已移除，训练统一读取本文件。
- `dataset/train.before_expand_2000.jsonl`：扩展前的数据来源快照，用于核对原始样本；不包含旧模型权重。
- `dataset/expansion_validation.json`：8000 条数据的数量、类别、格式与去重检查；`dataset/expansion_review.md` 提供分层抽查样本；`dataset/train_8000_metadata.jsonl` 记录逐条来源和生成类别。
- `lora_config.json`：适配 8GB 显存的保守起步参数，实际训练时需观察显存与效果。
- `preparation.json`：转换验证记录。

在 Windows 命令提示符执行以下命令，只检查配置，不启动训练：

```bat
cd /d C:\LLM\minimind-lzk
..\minimind\.venv311\Scripts\python.exe -X utf8 train.py
```

用上述命令追加 `--start` 开始训练；追加 `--start --resume` 恢复本实验。当前配置已启用 SwanLab 云端可视化（`use_wandb: true`，项目名 `minimind-lzk`）；脚本参数沿用 wandb 命名，实际使用 swanlab。独立评估问题仍需另备。

可运行 `..\minimind\.venv311\Scripts\python.exe -X utf8 validate_dataset.py`，用实际分词器和 SFT 加载器检查全部样本、截断情况和有效监督标签；结果保存为 `dataset_validation.json`。此命令不启动训练。

原 `minimind-3` 目录保持原样。之前未完成预训练的三份权重/恢复文件已按用户要求删除，原始预训练语料与历史日志保留。

本轮训练从原始基础模型开始，未恢复旧 LoRA、旧步数或优化器；参数为 1 epoch、batch 1、梯度累积 16、长度 340、初始学习率 1e-4、BF16。完成 8000/8000 batch、500 次优化器更新，用时约 6 分 31 秒。SwanLab 实验：[9t8s85ok](https://swanlab.cn/@COCO-19622/minimind-lzk/runs/9t8s85ok)，SDK 确认上传 5050 条记录，训练错误日志为空。

已验证所有权重为有限值、基础权重保持冻结、LoRA 与完整检查点一致；验证后覆盖活动适配器和恢复检查点，按用户要求清理此前 2000 条训练及误启动的旧模型备份。最新权重路径仍为 `adapter/minimind-lzk_768.pth`，恢复状态为 `checkpoints/minimind-lzk_768_resume.pth`。权重、检查点和日志按仓库约定仅保存在本地，不纳入 GitHub；本轮数据、来源记录及 [training_summary.json](training_summary.json) 纳入版本控制。

本轮最后一个 batch 的 loss 为 4.0772，这是单批训练值，不是评估分数。新权重已通过 GPU 严格加载和单次生成检查；该检查仅验证可运行，尚未进行独立质量评估。

## 启动已训练模型

在 Windows CMD 中执行：

```bat
cd /d C:\LLM\minimind-lzk
..\minimind\.venv311\Scripts\python.exe -X utf8 chat.py
```

该入口严格加载 base 下的基础模型，再加载 adapter 下的 LoRA 参数；仅推理，不训练。输入问题后回车，输入 `exit` 或 `quit` 退出；每次提问独立处理。单次提问可追加 `--prompt "什么是无人机的失控保护？"`，可用 `--max-new-tokens 128` 设置回答长度上限。
