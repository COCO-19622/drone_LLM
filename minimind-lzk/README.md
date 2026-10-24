# minimind-lzk

以工作区现有 `../minimind-3` 成品模型为基础的独立 LoRA 实验。当前仅完成准备，尚未微调；实验名称不会自动改变模型的自我介绍。

- `base/`：原模型及分词器的独立副本，以及转换后的 `minimind3_base_768.pth`，供训练读取。
- `adapter/`：训练后保存 `minimind-lzk_768.pth` LoRA 参数，推理需要配合本目录对应的基础模型。
- `checkpoints/`：本实验的完整恢复状态。
- `dataset/train.jsonl`：2000 条问答训练数据，已从工作区根目录 `../train.jsonl` 的 `instruction/output` 格式转换为 `conversations/role/content`；根目录原文件保留。训练入口使用本目录下的转换版本，修改原文件不会自动同步。
- `lora_config.json`：适配 8GB 显存的保守起步参数，实际训练时需观察显存与效果。
- `preparation.json`：转换验证记录。

在 Windows 命令提示符执行以下命令，只检查配置，不启动训练：

```bat
cd /d C:\LLM\minimind-lzk
..\minimind\.venv311\Scripts\python.exe -X utf8 train.py
```

用上述命令追加 `--start` 开始训练；追加 `--start --resume` 恢复本实验。默认不启用 SwanLab。独立评估问题仍需另备。

可运行 `..\minimind\.venv311\Scripts\python.exe -X utf8 validate_dataset.py`，用实际分词器和 SFT 加载器检查全部样本、截断情况和有效监督标签；结果保存为 `dataset_validation.json`。此命令不启动训练。

原 `minimind-3` 目录保持原样。之前未完成预训练的三份权重/恢复文件已按用户要求删除，原始预训练语料与历史日志保留。
