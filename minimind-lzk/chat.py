"""使用本实验的基础模型和 LoRA 权重进行命令行问答。"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "minimind"))

import datasets  # noqa: F401; match the Windows training import order
import torch
from transformers import AutoTokenizer, TextStreamer
from model.model_minimind import MiniMindConfig, MiniMindForCausalLM
from model.model_lora import apply_lora


def main():
    parser = argparse.ArgumentParser(description="minimind-lzk 命令行问答（仅推理）")
    parser.add_argument("--prompt", help="单次提问；不提供则进入交互问答")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()
    if args.max_new_tokens < 1:
        parser.error("--max-new-tokens 必须大于 0")
    config = json.loads((ROOT / "lora_config.json").read_text(encoding="utf-8"))
    base = ROOT / config["base_dir"]
    suffix = "_moe" if config["use_moe"] else ""
    base_path = base / f'{config["from_weight"]}_{config["hidden_size"]}{suffix}.pth'
    adapter_path = ROOT / config["save_dir"] / f'{config["lora_name"]}_{config["hidden_size"]}{suffix}.pth'
    for path in (base_path, adapter_path):
        if not path.is_file():
            parser.error(f"找不到权重：{path}")
    model_config = json.loads((base / "config.json").read_text(encoding="utf-8"))
    model_config.pop("model_type", None)
    model = MiniMindForCausalLM(MiniMindConfig(**model_config))
    model.load_state_dict(torch.load(base_path, map_location="cpu", weights_only=True), strict=True)
    apply_lora(model)
    adapter = torch.load(adapter_path, map_location="cpu", weights_only=True)
    expected = {name for name in model.state_dict() if ".lora." in name}
    if set(adapter) != expected:
        parser.error("LoRA 参数名称不匹配，请检查基础模型和适配器版本")
    model.load_state_dict(adapter, strict=False)
    dtype = torch.float16 if args.device.startswith("cuda") else torch.float32
    model = model.to(device=args.device, dtype=dtype).eval()
    tokenizer = AutoTokenizer.from_pretrained(str(ROOT / config["tokenizer_path"]))
    tokenizer.truncation_side = "left"
    print(f"已加载 minimind-lzk（基础模型 + LoRA），设备：{args.device}", flush=True)

    def answer(question):
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": question}], tokenize=False,
            add_generation_prompt=True, open_thinking=False)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to(args.device)
        print("minimind-lzk：", end="", flush=True)
        with torch.inference_mode():
            model.generate(
                input_ids=inputs.input_ids, attention_mask=inputs.attention_mask,
                max_new_tokens=args.max_new_tokens, do_sample=False,
                pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id,
                streamer=TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True))

    if args.prompt is not None:
        answer(args.prompt)
        return
    print("输入问题后回车；输入 exit 或 quit 退出。每次提问独立处理。")
    while True:
        question = input("你：").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            answer(question)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print()
