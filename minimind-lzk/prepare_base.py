"""复制成品模型并验证原生训练权重；不执行训练。"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "minimind-3"
sys.path.insert(0, str(ROOT.parent / "minimind"))

import datasets  # noqa: F401; Windows DLL initialization order
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from model.model_minimind import MiniMindConfig, MiniMindForCausalLM


def main():
    base = ROOT / "base"
    base.mkdir(exist_ok=True)
    for name in ("model.safetensors", "config.json", "generation_config.json",
                 "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
                 "chat_template.jinja"):
        src = SOURCE / name
        if src.exists():
            shutil.copy2(src, base / name)
    for name in ("adapter", "checkpoints", "dataset", "logs"):
        (ROOT / name).mkdir(exist_ok=True)
    hf = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.float32).eval()
    config = json.loads((base / "config.json").read_text(encoding="utf-8"))
    config.pop("model_type", None)
    native = MiniMindForCausalLM(MiniMindConfig(**config)).eval()
    native.load_state_dict(hf.state_dict(), strict=True)
    tokenizer = AutoTokenizer.from_pretrained(base)
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": "你好，请介绍一下自己。"}],
        tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        expected = hf(**inputs).logits
        actual = native(input_ids=inputs.input_ids, attention_mask=inputs.attention_mask).logits
    error = (expected - actual).abs().max().item()
    torch.testing.assert_close(actual, expected, atol=1e-3, rtol=1e-3)
    output = base / "minimind3_base_768.pth"
    torch.save({k: v.half().cpu() for k, v in native.state_dict().items()}, output)
    restored = MiniMindForCausalLM(MiniMindConfig(**config))
    restored.load_state_dict(torch.load(output, map_location="cpu", weights_only=True), strict=True)
    report = {
        "model_name": "minimind-lzk", "source": "../minimind-3",
        "source_sha256": hashlib.sha256((SOURCE / "model.safetensors").read_bytes()).hexdigest(),
        "strict_load": True, "saved_weight_strict_reload": True,
        "hf_native_max_logit_error": error, "training_started": False,
    }
    (ROOT / "preparation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
