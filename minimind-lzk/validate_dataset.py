"""Validate the configured LoRA data with the actual tokenizer and SFT loader."""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'minimind'))

import datasets  # Import before torch, matching the Windows training entrypoint.
from transformers import AutoTokenizer
from dataset.lm_dataset import SFTDataset, post_processing_chat


def main():
    config = json.loads((ROOT / 'lora_config.json').read_text(encoding='utf-8'))
    path = (ROOT / config['data_path']).resolve()
    tokenizer = AutoTokenizer.from_pretrained(str(ROOT / config['tokenizer_path']))
    dataset = SFTDataset(str(path), tokenizer, max_length=config['max_seq_len'])
    lengths, supervised = [], []
    truncated, invalid = [], []
    # The loader sometimes adds a system message; check that case too.
    with_system_lengths = []
    random.seed(42)
    for index, sample in enumerate(dataset.samples):
        messages = sample['conversations']
        assert [m['role'] for m in messages] == ['user', 'assistant'], index + 1
        assert all(isinstance(m['content'], str) and m['content'].strip() for m in messages), index + 1
        prompt = post_processing_chat(dataset.create_chat_prompt(messages), remove_empty_think=False)
        length = len(tokenizer(prompt).input_ids)
        lengths.append(length)
        system_messages = [{'role': 'system', 'content': '你是一个知识丰富的AI，尽力为用户提供准确的信息。'}] + messages
        system_prompt = post_processing_chat(dataset.create_chat_prompt(system_messages), remove_empty_think=False)
        with_system_lengths.append(len(tokenizer(system_prompt).input_ids))
        if length > config['max_seq_len']:
            truncated.append(index + 1)
        input_ids, labels = dataset[index]
        count = int((labels[1:] != -100).sum())
        supervised.append(count)
        if count == 0 or input_ids.shape != labels.shape or len(input_ids) != config['max_seq_len']:
            invalid.append(index + 1)
    ordered = sorted(lengths)
    report = {
        'data_path': str(path), 'samples': len(dataset),
        'max_seq_len': config['max_seq_len'],
        'tokens': {'min': min(lengths), 'median': ordered[len(ordered)//2],
                   'p95': ordered[int((len(ordered)-1)*0.95)], 'max': max(lengths)},
        'max_tokens_with_checked_system_prompt': max(with_system_lengths),
        'truncated_rows_without_system': truncated,
        'rows_over_limit_with_checked_system_prompt': [i+1 for i, n in enumerate(with_system_lengths) if n > config['max_seq_len']],
        'invalid_or_zero_supervision_rows': invalid,
        'min_supervised_tokens_after_shift': min(supervised),
        'training_started': False,
    }
    (ROOT / 'dataset_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if invalid or truncated or any(n > config['max_seq_len'] for n in with_system_lengths):
        raise SystemExit('Dataset requires repair; see dataset_validation.json')


if __name__ == '__main__':
    main()
