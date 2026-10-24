"""读取本实验配置；必须显式传入 --start 才会训练。"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="minimind-lzk LoRA")
    parser.add_argument("--start", action="store_true", help="开始训练")
    parser.add_argument("--resume", action="store_true", help="恢复本实验训练")
    args = parser.parse_args()
    config = json.loads((ROOT / "lora_config.json").read_text(encoding="utf-8"))
    for key in ("base_dir", "tokenizer_path", "save_dir", "checkpoint_dir", "data_path"):
        config[key] = str((ROOT / config[key]).resolve())
    config["from_resume"] = int(args.resume)
    print(json.dumps(config, ensure_ascii=False, indent=2), flush=True)
    if not args.start:
        print("仅展示配置，未启动训练。准备 dataset/train.jsonl 后使用 --start。")
        return
    data = Path(config["data_path"])
    if not data.is_file() or not data.stat().st_size:
        parser.error("请先准备非空 dataset/train.jsonl；train.example.jsonl 仅为格式示例。")
    trainer = ROOT.parent / "minimind" / "trainer"
    command = [sys.executable, "-X", "utf8", "-u", str(trainer / "train_lora.py")]
    for key, value in config.items():
        command.extend(["--" + key, str(value)])
    subprocess.run(command, cwd=trainer, check=True)


if __name__ == "__main__":
    main()
