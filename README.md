# drone_LLM / minimind-lzk

基于 [MiniMind](https://github.com/jingyaogong/minimind) 的无人机领域语言模型 LoRA 微调项目，实验名称为 `minimind-lzk`。

- `minimind/`：MiniMind 模型、数据加载及各阶段训练代码；原项目许可证见 `minimind/LICENSE`。
- `minimind-lzk/`：独立 LoRA 配置、启动脚本、训练数据及数据检查工具，详见其中的 README。
- `uav_sft/`：无人机领域资料卡、数据生成脚本及来源记录。
- `train.jsonl`：工作区整理的问答数据。
- `dataset_candidates.md`：候选数据集说明。
- `minimind-3/`：基础模型配置与分词器。

本仓库不包含虚拟环境、模型权重、训练检查点、运行日志和大型预训练语料。克隆后需要另行安装依赖并准备基础权重。

基础模型使用 `jingyaogong/minimind-3`，将对应 Transformers 模型权重及配置放入工作区根目录的 `minimind-3/` 后，可运行 `minimind-lzk/prepare_base.py` 复制并验证训练基础权重。此脚本会更新实验的 `base/`，应在首次训练前运行。

已具备依赖和基础权重时，在 Windows 命令提示符中启动：

```bat
cd /d C:\LLM\minimind-lzk
..\minimind\.venv311\Scripts\python.exe -X utf8 train.py
..\minimind\.venv311\Scripts\python.exe -X utf8 train.py --start
```

第一条 Python 命令仅展示配置，第二条执行训练。训练数据路径由 `minimind-lzk/lora_config.json` 中的 `data_path` 指定。
