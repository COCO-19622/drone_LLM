# MiniMind 项目记忆

- 2026-10-24：用户新增工作区根目录 `../train.jsonl`，2000 条 UTF-8 JSONL，字段 instruction/output；全量解析成功、无完全重复记录。按用户授权修复适配：保留根目录原件，逐条无损转换到 `../minimind-lzk/dataset/train.jsonl` 的 conversations/user/assistant 格式，匹配现有 lora_config.json，无需改训练代码。新增实验级 validate_dataset.py 和 dataset_validation.json，并更新 README。Windows .venv311 实际加载全部 2000 条、逐条生成训练张量通过；token 长度 min/median/p95/max 为 29/51/153/168，检查用 system 提示下最长186，低于340；无截断、无零监督样本，移位后有效监督最少3 token。train.py 配置展示确认实际路径 C:\LLM\minimind-lzk\dataset\train.jsonl。原件与转换版本内容逐条一致；以后修改原件不会自动同步。未启动训练；独立评估集仍未准备。

- 2026-10-24：针对 8GB 显存与现有成品 MiniMind-3（约 63.91M 参数）的 LoRA 数据规模咨询，建议先用 1000–2000 条做流程与效果试验，再以 5000–10000 条高质量文本问答作为首轮正式规模；若独立评估持续改善再扩至 20000–30000 条。此为起步建议，未经本机训练验证，用户尚未确认执行。当前实验配置为 batch=1、累积16、长度340、1轮；真实训练集仍待准备。总样本数主要影响耗时，峰值显存需结合 batch、长度和实际运行测试判断；候选清单中的预训练文本与多模态轨迹不能直接计为可用文本 QA。未启动训练。

本文件只记录 `/mnt/c/LLM/minimind` 项目的信息。以下内容依据当前仓库文件整理；未实际运行的命令不代表已验证。

## 项目用途

MiniMind 是用于学习和复现小型语言模型的开源项目，覆盖分词器、从零预训练、监督微调、LoRA、偏好优化、强化学习、蒸馏及推理示例。当前仓库包含 MiniMind-3 的模型配置和本地 Transformers 格式模型目录 `minimind-3/`。

## 技术栈

- Python；项目 README 给出的参考环境为 Python 3.10.16、Ubuntu 20.04、CUDA 12.2。
- PyTorch 实现模型与训练流程；`transformers` 用于模型加载及兼容格式，`torchrun` 用于多卡训练。
- 依赖列于 `requirements.txt`，包括 Transformers、Datasets、Streamlit、FastAPI、Uvicorn、SwanLab 等。PyTorch 在该文件中为注释项，实际安装版本待确认。
- 核心目录：`model/` 模型和分词器，`dataset/` 数据加载，`trainer/` 训练脚本，`scripts/` 演示与服务脚本。

## 启动与测试命令

以下命令均在项目根目录执行，除非另有说明。运行前需安装依赖，并准备对应模型权重或训练数据。

```bash
pip install -r requirements.txt
python eval_llm.py --load_from ./minimind-3
python eval_llm.py --load_from ./model --weight full_sft
cd trainer && python train_pretrain.py
cd trainer && python train_full_sft.py
```

- Web 演示：README 指示先将 Transformers 格式模型目录放入 `scripts/`，再执行 `cd scripts && streamlit run web_demo.py`。
- 推理检查：`eval_llm.py` 启动后可选自动提示词模式（输入 `0`），作为手动功能检查；需要可加载的权重。
- 自动化测试：仓库中未发现明确的测试套件或统一测试命令；待确认。
- 上述命令本次未实际运行，环境与模型可用性待确认。

## 重要决策

- 2026-10-20：项目记忆保存在本仓库 `docs/project-memory.md`，由根目录 `AGENTS.md` 约束读取与维护；只记录本项目内容，不存储秘密。
- README 描述的主线流程是预训练后进行全参数监督微调；当前本地要采用的训练或部署方案待确认。

## 当前进度

- 已建立项目级记忆文档和维护规则。
- 已确认预训练脚本位于 `C:\LLM\minimind\trainer\train_pretrain.py`；Windows 命令提示符需先进入项目根目录，再执行 README 中的 `cd trainer && python train_pretrain.py`。用户当前位于 `C:\Users\34942`，直接执行该相对路径会找不到目录。
- 用户在 Windows 运行预训练脚本时遇到 `ModuleNotFoundError: No module named 'datasets'`；`requirements.txt` 固定 `datasets==3.6.0`。当前 Windows `python` 对应的环境及依赖安装状态待确认。
- 安装 `datasets==3.6.0` 时，用户的 pip 24.0 在访问 `files.pythonhosted.org` 遇到 `CERTIFICATE_VERIFY_FAILED: self-signed certificate in certificate chain`。建议先尝试 pip 的 `--use-feature=truststore` 使用 Windows 系统证书；若失败，需确认代理或组织根证书配置。尚未验证解决。
- 用户已可在 Windows `trainer` 目录运行脚本，下一报错为 `ModuleNotFoundError: No module named 'torch'`。`requirements.txt` 中 PyTorch 安装行被注释；Windows Python 版本、NVIDIA GPU 及 CUDA 驱动情况待确认，应按 PyTorch 官方安装选择器安装匹配版本。
- 本机 WSL `nvidia-smi` 检测到 NVIDIA GeForce RTX 5060 Laptop GPU、8151 MiB 显存、驱动 596.13、计算能力 12.0（sm_120）。查询时约 3162 MiB 已用、4738 MiB 空闲。适合 CUDA 12.8+ 的 PyTorch GPU 构建；先前建议的 PyTorch 2.6.0 不适合此 GPU。默认 batch_size=32，8GB 显存可能不足，应从较小 batch 开始验证。默认训练数据 `dataset/pretrain_t2t_mini.jsonl` 当前不存在，数据准备待确认。
- 仓库已有 `minimind-3/` 模型文件和多个训练、推理脚本；模型能否在当前环境成功运行待确认。
- 建立本记忆前，工作区已有多处未提交改动；其目的和完成状态待确认，本次未修改业务代码。
- 2026-10-20：再次核对预训练入口：从 `trainer/` 执行 `train_pretrain.py`，默认从零开始、模型维度 768、8 层、数据路径 `../dataset/pretrain_t2t_mini.jsonl`，输出到 `../out/pretrain_768.pth`；数据要求 JSONL，每行含 `text` 字段。本地该数据文件仍不存在。
- 当前 WSL 的 `python` 命令不存在；`python3` 为 3.10.12，但未安装 `torch`。项目 `.venv` 与 `.venv311` 为 Windows 虚拟环境，是否能用于训练待确认。本次未启动训练。
- 2026-10-20：预训练数据由 `PretrainDataset` 通过 Hugging Face Datasets 的 `load_dataset('json', data_files=..., split='train')` 读取，要求每条记录含字符串 `text`。训练入口用 `--data_path` 指向文件；每条样本单独分词，截断到 `max_seq_len - 2` token，再加 BOS/EOS 并填充，填充标签置为 `-100`。当前没有数据文件，数据内容与规模待确认。
- 2026-10-20：预训练脚本的 `--use_wandb` 实际执行 `import swanlab as wandb`；启用后记录 loss、logits_loss、aux_loss、learning_rate、epoch_time，`--wandb_project` 指定 SwanLab 项目名。默认不启用；待数据和 PyTorch 环境可训练后再决定是否用于长期实验跟踪。
- 2026-10-20：再次搜索 `/mnt/c/LLM`，未找到 `pretrain_t2t_mini.jsonl`。已在官方 Hugging Face 数据集 `jingyaogong/minimind_dataset` 的文件页核实该文件存在，约 1.24 GB，直接下载地址为 `https://huggingface.co/datasets/jingyaogong/minimind_dataset/resolve/main/pretrain_t2t_mini.jsonl`；项目 README 同时提供 ModelScope 数据集页面。下载后应置于 `dataset/`。
- 2026-10-20：确认默认读取链路为 `argparse --data_path` 默认值 `../dataset/pretrain_t2t_mini.jsonl` → `PretrainDataset(args.data_path, ...)` → `load_dataset('json', data_files=data_path, split='train')`。相对路径基于启动进程的当前工作目录；从 `trainer/` 启动时解析到项目 `dataset/`。可用 `--data_path` 覆盖。
- 2026-10-20：已按用户要求将下载的 `pretrain_t2t_mini.jsonl` 从 `C:\Users\34942\Downloads` 移至 `C:\LLM\minimind\dataset\pretrain_t2t_mini.jsonl`。文件大小 1,241,043,656 字节；首行可解析为 JSON，且含字符串 `text` 字段；原下载位置已无该文件。尚未完整扫描数据集或启动训练。
- 2026-10-20：为便于 VS Code 查看大文件，已从预训练数据原件复制前 100 行到 `dataset/pretrain_t2t_mini_preview_100.jsonl`（76,366 字节）；原训练文件未修改。预览文件仅供查看，训练仍使用原文件。

- 2026-10-20：已为 `model/model_minimind.py` 补充 Transformer 关键路径的中文注释，涵盖 Decoder-only 总览、RMSNorm、RoPE/YaRN、GQA、因果掩码、KV 缓存、SwiGLU、MoE、Pre-Norm 残差及下一个 token 的标签对齐；未改动执行逻辑。已用 Python AST 对比确认修改前后代码结构一致并通过语法解析；未运行模型训练或推理。
- 2026-10-21：用户在 Windows 的 `trainer/` 用裸 `python` 启动时仍报缺少 `torch`。检查确认项目 `.venv311`（Python 3.11.9）已有 `torch 2.9.0+cu130`、`datasets 3.6.0`、`transformers 4.57.6`，`torch.cuda.is_available()` 为 True，GPU 为 RTX 5060 Laptop GPU；用该解释器执行 `train_pretrain.py --help` 成功。`.venv`（Python 3.10.11）没有 `torch` 和 `datasets`。应从 `trainer/` 显式运行 `..\.venv311\Scripts\python.exe train_pretrain.py`，或激活 `.venv311` 后再运行。
- 2026-10-21：按用户要求已通过 Windows `.venv311` 后台启动完整预训练（PID 17192）：`-u train_pretrain.py --batch_size 2 --accumulation_steps 16 --num_workers 0 --log_interval 10 --save_interval 1000`，工作目录 `C:\LLM\minimind\trainer`，默认 2 epoch、长度 340、无 SwanLab。数据成功加载 1,270,238 条；GPU 运行中，已超过首轮 1,050/635,119 batch，loss 从约 8.96 降到约 6.69。标准输出和错误分别在 `trainer/pretrain_run.log` 与 `trainer/pretrain_error.log`；首个 `out/pretrain_768.pth` 和 `checkpoints/pretrain_768_resume.pth` 已于第 1000 batch 保存。完整训练尚未结束。

## 待办

- 2026-10-21：用户已在本机完成 SwanLab 登录，现已从第 5000 batch 检查点启用 SwanLab 云端续训（原参数加 `--from_resume 1 --use_wandb`）。第一次尝试因 Windows GBK 无法输出 SwanLab 图标而退出；通过 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8` 和 `python -X utf8` 修复启动环境，未修改训练代码。当前 Windows 启动进程 PID 61324，已运行超过首轮第 6190 batch。SwanLab 实验链接 `https://swanlab.cn/@COCO-19622/MiniMind-Pretrain/runs/lcaldwhv`；日志为 `trainer/pretrain_swanlab_utf8_run.log` / `trainer/pretrain_swanlab_utf8_error.log`（检查时错误日志为空）。原第 5000 batch 之前的日志未导入 SwanLab，曲线从本次续训开始记录；完整训练仍在进行。
- 2026-10-21：用户看到两个 SwanLab 实验显示运行中。核对本机仅一组训练父子进程（61324 / 26032），训练超过 7820 batch。本地有首次编码错误退出的实验 `qvb5h3k4` 与正常续训实验 `lcaldwhv`；前者可能未同步结束状态，云端状态本次未直接查询或修改。
- 2026-10-21：核对训练耗时差异：当前约 66930/635119 batch，`epoch_time` 为当前轮剩余约 530 分钟；共运行 2 epoch。实际参数 batch_size=2、accumulation_steps=16、num_workers=0，为适配 8GB 显存先前采用的保守配置；仓库默认 batch_size=32。官方训练开销表以单卡 RTX 3090、1 epoch 估算（64M 预训练约 1.21h、SFT 约 1.10h），标题另有 SFT 单轮两小时的注释，未提供充分基准参数，不能直接按标题等同比较。当前 GPU 快照利用率 41%、功耗约 57W，不足以单独确认瓶颈；批量与数据加载吞吐待实际测试。未变更当前训练参数。
- 2026-10-21：按用户“先停止本次训练”要求，已终止训练进程树 PID 61324 / 26032，并确认 GPU 已释放，当前无预训练任务运行。停止前日志约第 138700 batch；已实际加载检查点确认可恢复到第 1 轮第 138000 batch，包含优化器状态和 SwanLab 实验 ID `lcaldwhv`。模型权重在 `out/pretrain_768.pth`（约 132 MiB），续训检查点在 `checkpoints/pretrain_768_resume.pth`（约 619 MiB），原始训练语料仍在 `dataset/pretrain_t2t_mini.jsonl`；训练尚未完成。以后恢复需遵循用户新指示，使用原参数和 `--from_resume 1 --use_wandb`，并保持 Windows UTF-8 环境。

- 确认本地 Python、PyTorch、设备及依赖环境，并实际验证所需推理或训练命令。
- 确认是否有项目约定的自动化测试命令；如有，补充到本文件。
- 后续任务完成时，及时更新重要决策、进度和待办。

- 2026-10-21：核对后续微调可行性：`out/pretrain_768.pth` 与 `checkpoints/pretrain_768.pth` 均约 132 MiB，续训状态约 619 MiB；当前为未完成预训练的中间模型。LoRA 脚本可用 `--from_weight pretrain` 从该权重启动，冻结基础参数、单独保存适配器；需要另备 `conversations` 格式数据，现有 `text` 预训练语料不能直接用于该脚本。SFT/LoRA/DPO/GRPO/PPO 均有入口，但默认 `full_sft` 权重与相关数据当前未见。`init_model` 从 `../out/{weight}_{hidden_size}.pth` 加载；另存实验要区分输出目录及权重名称，因为恢复检查点固定写入 `../checkpoints`。用户目前询问可行性，尚未复制模型、修改训练代码或启动新训练。

- 2026-10-21：用户明确希望以工作区已有的成品模型继续训练，而不是以自行预训练的中间检查点为基础。已定位工作区根目录 `../minimind-3/` 与仓库内 `minimind-3/` 两份 Transformers 模型，权重 SHA256 相同，均为 127,834,168 字节；配置为 Qwen3ForCausalLM、768 维、8 层、词表 6400。根目录模型的 tokenizer.json 与仓库 model/tokenizer.json 字节一致，但 tokenizer_config.json 不同，后续应保留并核对原模型的聊天模板。现有训练入口加载 out 下的 .pth，需先用 convert_transformers2torch 转换成独立名称并验证加载兼容性，或扩展加载入口。具体成品模型训练阶段未独立核实；尚未转换、复制或启动新训练，训练目标与新数据待确认。

- 2026-10-21：按用户要求删除未完成预训练产物 `out/pretrain_768.pth`、`checkpoints/pretrain_768.pth`、`checkpoints/pretrain_768_resume.pth`；旧预训练已无法从这些检查点恢复。原始预训练语料、预览文件和历史日志保留，原成品模型未修改。已建立工作区独立实验 `../minimind-lzk/`，模型/LoRA 名称为 minimind-lzk；base 中保存成品模型与原分词器副本以及转换后的 `minimind3_base_768.pth`。Windows .venv311 实测严格加载、保存后严格重载均通过，同一输入的 HF 与原生 FP32 logits 最大差为 0。LoRA 脚本增加 base_dir/tokenizer_path/checkpoint_dir 参数以隔离实验；配置 batch=1、累积16、长度340、1轮、lr=1e-4、workers=0。`../minimind-lzk/train.py` 默认只展示配置，显式 --start 才训练；Windows 配置检查通过。仅建立格式示例 train.example.jsonl，真实 dataset/train.jsonl 尚未准备，未启动训练。准备说明见该目录 README.md，验证见 preparation.json。

- 2026-10-21：已向用户核对 LoRA 数据与启动方式：train_lora.py 通过 SFTDataset 读取 conversations/role/content JSONL，仅 assistant 部分参与监督；minimind-lzk 配置读取其自身 dataset/train.jsonl，UTF-8、每行一个对话对象。当前 max_seq_len=340，完整对话超长会从右侧截断，需确保 assistant 回答保留。Windows CMD 使用项目 .venv311 解释器执行 minimind-lzk/train.py，默认展示配置，--start 训练，--start --resume 恢复；脚本无自动验证集评估。本次仅阅读和说明，未启动训练。

- 2026-10-23：已按当前磁盘状态梳理项目框架：仓库 out/、checkpoints/ 为空；成品 Transformers 权重在 minimind-3/model.safetensors，配置 768 维、8 层、8 个 Q 头、4 个 KV 头、词表 6400。eval_llm.py 用 --load_from 切换模型目录，原生权重用 --save_dir/--weight；加载分支实际以路径是否包含字符串 model 判断。--open_thinking 0/1 控制聊天模板思考开关，没有独立高/中/低推理强度参数；hidden_size/层数/MoE 必须匹配权重，不能直接调参提升已有模型。独立 minimind-lzk 实验仍只有基础模型和格式示例，真实 train.jsonl 未准备。本次仅检查文件并说明，未启动训练或推理。

- 2026-10-24：按用户要求在工作区根目录建立 drone_LLM Git 仓库（main），目标远端 https://github.com/COCO-19622/drone_LLM.git；原内嵌仓库 Git 元数据已保存在根 .git/nested-repositories/，使源码以普通目录纳入根仓库，未创建子模块。根 .gitignore 排除虚拟环境、所有模型权重、检查点、日志、凭据文件和大型预训练语料；纳入无人机 SFT 数据及来源材料、minimind-lzk 配置和脚本。提交前候选139文件约37.75 MiB，未发现超过10 MiB的单文件，常见令牌/私钥模式检查未发现匹配。GitHub 连接器报告目标仓库公开且为空、连接器无 push 权限；拟使用 Windows Git 凭据推送。远端同步状态以实际 Git 分支状态为准。
