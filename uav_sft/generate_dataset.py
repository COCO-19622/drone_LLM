"""Build a small, source-informed Chinese SFT trial set; never start training."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TARGET = ROOT / "train.jsonl"
SEED = 20261024
rows: list[dict] = []


def add(instruction, output, category, seed_id, source_ids=(), kind="source_informed_synthesis"):
    instruction, output = instruction.strip(), output.strip()
    assert instruction and output
    rows.append({"sample": {"instruction": instruction, "output": output},
                 "category": category, "seed_id": seed_id,
                 "source_ids": list(source_ids), "kind": kind})


def read_table(name):
    result = []
    for line in (HERE / name).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("|")
        assert len(fields) == 7, (name, fields[0], len(fields))
        result.append(fields)
    return result


def knowledge():
    # Each card contains one definition and four separately authored questions,
    # rather than five interchangeable phrasings of the same question.
    for filename, category, count in [("basic_cards.txt", "无人机基础知识", 140),
                                      ("engineering_cards.txt", "工程知识", 40)]:
        cards = read_table(filename)
        assert len(cards) >= count
        for idx, fields in enumerate(cards[:count], 1):
            topic, definition, *rest = fields
            sources = rest.pop().split(",")
            pairs = [(f"什么是{topic}？", definition)]
            for item in rest:
                question, answer = item.split("^", 1)
                pairs.append((question, answer))
            assert len(pairs) == 5
            for facet, (question, answer) in enumerate(pairs, 1):
                add(question, answer, category, f"{filename}:{idx}:{facet}", sources)


def scenarios():
    cases = read_table("scenario_cases.txt")
    assert len(cases) == 60
    ground_cases = {"加速度计校准未通过", "陀螺仪校准反复重启", "姿态显示与实际倾斜方向不符",
                    "电机编号与实际响应不一致", "电机转向与机型要求相反",
                    "电压读数与实际电池明显不符", "电池串数设置与实物不一致",
                    "任务上传失败", "任务航点高度参考不明确", "目标位置单位与接口规定不一致",
                    "已落地但电机仍在转动"}
    for idx, (issue, first, check, resume, wrong, reason, source_text) in enumerate(cases, 1):
        bad, correction = wrong.split("^", 1)
        sources = source_text.split(",")
        pairs = [
            (f"遇到{issue}，应先怎么处理？", first + check),
            (f"排查“{issue}”时，应核对哪些信息？", check),
            (f"处理“{issue}”后，何时才考虑恢复相关任务？", resume),
            (f"遇到{issue}，有人建议{bad}，是否合适？", correction),
            (f"为什么{issue}时不应机械继续原计划？", reason),
        ]
        if issue in ground_cases:
            pairs.extend([
                (f"准备起飞时发现{issue}，任务又要求立即出发，如何取舍？",
                 "应暂缓起飞，不能用赶时间代替检查。" + first + check),
                (f"地面发现{issue}，能用自动返航代替排查吗？",
                 "不能。尚在地面时应处理当前故障，不应启动返航来代替检查。" + check),
                (f"地面处理{issue}时数传也中断，能只凭旧遥测判断正常吗？",
                 "不能，旧遥测不能代表当前状态。应结合现场观察和可用连接核对设备状态。" + check),
            ])
        else:
            pairs.extend([
                (f"出现{issue}，同时剩余续航只够就近结束，还应继续任务吗？",
                 "不应继续非必要任务。" + first + "应依据仍有效的估计与控制能力选择可达的结束方式，避免长时间等待或勉强远距离返航。"),
                (f"处理{issue}时，全球位置也无效，能直接保证自动返航可用吗？",
                 "不能保证。自动返航需要相应有效位置和参考，应按当前仍有效的状态、控制能力和已配置保护处理。" + first),
                (f"出现{issue}后数传也中断，如何判断当前处理结果？",
                 "不能仅凭最后一次遥测宣布处理完成。应结合现场可观察状态、可用链路及机载保护核对实际状态。" + first),
            ])
        pairs.extend([
            (f"{issue}的提示暂时消失但尚未完成检查，能直接恢复任务吗？",
             "不能只凭提示消失作判断。" + check + resume),
            (f"把“{issue}”的处理整理成三个简短步骤。",
             f"1. {first}\n2. {check}\n3. {resume}"),
        ])
        assert len(pairs) == 10
        for variant, (question, answer) in enumerate(pairs, 1):
            add(question, answer, "自主飞行场景判断", f"scenario:{idx}:{variant}", sources,
                "synthetic_scenario_grounded_in_documentation")


def plans():
    actions = [
        ("拍摄一张照片", "悬停稳定后拍摄一张照片"),
        ("录制一段短视频", "稳定飞行状态并录制短视频"),
        ("悬停观察目标", "悬停并观察目标"),
        ("将机头转向观察目标", "在允许条件下将机头转向目标"),
        ("记录当前位置", "确认位置有效并记录当前位置"),
        ("记录当前电量", "读取并记录当前电量"),
        ("确认位置估计有效", "检查位置估计是否有效"),
        ("确认遥测持续更新", "检查遥测是否持续更新"),
        ("调整云台朝向目标", "调整云台并确认朝向目标"),
        ("汇报已到达目标点", "确认到达并汇报当前任务点"),
    ]
    modifiers = [
        ("按正常顺序执行", None, None),
        ("起飞前先确认电量足够", "start", "确认电量足够完成任务并保留降落余量"),
        ("起飞前先确认定位满足模式要求", "start", "确认定位有效并满足所选模式要求"),
        ("起飞后先在起点附近确认位置稳定", "after_takeoff", "在起点附近确认位置稳定"),
        ("完成目标动作后先汇报结果再返航", "before_return", "汇报目标动作的完成结果"),
        ("返航前先核对返回路线", "before_return", "确认返回路线仍可通行"),
        ("落地后确认电机停转", "end", "确认已落地、解除解锁且电机停转"),
        ("降落前确认降落区清空", "before_land", "确认降落区域清空且下降通道可用"),
        ("起飞前先核对任务顺序", "start", "核对航点顺序和任务动作"),
        ("任务结束后记录完成情况", "end", "记录任务完成情况和异常"),
    ]
    for ai, (intent, execution) in enumerate(actions, 1):
        routes = [
            (f"起飞后飞到A点，{intent}，然后返回起点并降落",
             ["起飞", "飞向A点", execution, "返回起点", "降落"]),
            (f"起飞后经过A点飞到B点，在B点{intent}，然后返回起点并降落",
             ["起飞", "飞向A点", "飞向B点", execution, "返回起点", "降落"]),
            (f"起飞后依次到A点和B点，在两个点分别{intent}，最后返回起点并降落",
             ["起飞", "飞向A点", f"在A点{execution}", "飞向B点", f"在B点{execution}", "返回起点", "降落"]),
            (f"起飞后依次经过A点、B点到C点，仅在C点{intent}，然后返回起点并降落",
             ["起飞", "飞向A点", "飞向B点", "飞向C点", execution, "返回起点", "降落"]),
        ]
        for ri, (description, base_steps) in enumerate(routes, 1):
            for mi, (requirement, where, extra) in enumerate(modifiers, 1):
                steps = list(base_steps)
                if where == "start":
                    steps.insert(0, extra)
                elif where == "after_takeoff":
                    steps.insert(1, extra)
                elif where == "before_return":
                    steps.insert(steps.index("返回起点"), extra)
                elif where == "before_land":
                    steps.insert(steps.index("降落"), extra)
                elif where == "end":
                    steps.append(extra)
                assert 3 <= len(steps) <= 8
                # Explicit normal conditions prevent a generic flight plan from
                # teaching takeoff/return despite invalid position or energy.
                prompt = (f"多旋翼的定位、电量与航线均满足要求。分解任务：{description}；"
                          f"{requirement}。只列步骤。")
                output = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))
                add(prompt, output, "任务规划与步骤分解", f"plan:{ai}:{ri}:{mi}",
                    ("mission", "return", "land", "preflight", "basic", "battery", "ekf", "hold", "mavlink"), "compositional_synthetic_task")


def general():
    # Everyday tasks authored here; no sensor-value-to-actuator data.
    for i in range(10):
        a, b = i + 2, i + 5
        add(f"计算{a}+{b}，只输出结果。", str(a+b), "通用简单指令", f"arithmetic:add:{i}", kind="authored_simple_task")
        a, b = 25 + 2 * i, i + 3
        add(f"计算{a}-{b}，只输出结果。", str(a-b), "通用简单指令", f"arithmetic:subtract:{i}", kind="authored_simple_task")
    rng = random.Random(SEED + 1)
    seen = set()
    for i in range(20):
        while True:
            values = rng.sample(range(1, 60), 3 + i % 3)
            if tuple(values) not in seen:
                seen.add(tuple(values))
                break
        descending = i % 2 == 1
        order = "从大到小" if descending else "从小到大"
        add(f"把这些数{order}排列：" + "、".join(map(str, values)) + "。",
            "、".join(map(str, sorted(values, reverse=descending))),
            "通用简单指令", f"sort:{i}", kind="authored_simple_task")
    lists = ["苹果、香蕉、梨", "铅笔、橡皮、尺子", "红色、蓝色、绿色", "书包、水杯、雨伞",
             "周一、周三、周五", "面包、牛奶、鸡蛋", "桌子、椅子、台灯", "春天、夏天、秋天、冬天",
             "阅读、散步、听音乐", "北京、上海、广州", "杯子、盘子、勺子", "写作、绘画、唱歌",
             "猫、狗、兔子", "米饭、面条、饺子", "开会、整理资料、发送邮件", "洗菜、切菜、煮饭",
             "准备材料、制作、检查、收纳", "历史、地理、语文", "起床、洗漱、早餐", "车站、图书馆、公园"]
    for i, text in enumerate(lists):
        add(f"把这些内容整理成编号列表：{text}。",
            "\n".join(f"{n}. {x}" for n, x in enumerate(text.split("、"), 1)),
            "通用简单指令", f"numbered_list:{i}", kind="authored_simple_task")
    names = ["小林", "小王", "小周", "小李", "小陈", "小杨", "小吴", "小赵", "小刘", "小孙"]
    places = ["图书馆", "公园", "办公室", "教室", "车站", "食堂", "书店", "会议室", "操场", "展览馆"]
    for i in range(20):
        person, place = names[i % 10], places[(i*3+1) % 10]
        time = ("上午" if i < 10 else "下午") + str(8 + i % 4 if i < 10 else 2 + i % 4) + "点"
        sentence = f"{person}计划在{time}到{place}。"
        key = ("人物", "时间", "地点")[i % 3]
        answer = {"人物": person, "时间": time, "地点": place}[key]
        add(f"提取句子中的{key}，只输出答案：{sentence}", answer,
            "通用简单指令", f"extract:{i}", kind="authored_simple_task")
    rewrites = [
        ("把这句话改得礼貌一些：把窗户关上。", "请帮忙关上窗户，谢谢。"),
        ("把这句话改得礼貌一些：把文件发给我。", "请把文件发给我，谢谢。"),
        ("把这句话改得简短些：由于现在下雨的原因，所以我们今天暂时不出去散步。", "今天下雨，暂不外出散步。"),
        ("把这句话改得简短些：我们需要在明天上午的时候召开一次讨论项目进度的会议。", "明天上午开会讨论项目进度。"),
        ("将句子补上句号：今天的工作已经完成", "今天的工作已经完成。"),
        ("将句子补上问号：你准备好了吗", "你准备好了吗？"),
        ("用一句话提醒大家开会前关闭手机铃声。", "请大家在开会前关闭手机铃声。"),
        ("用一句话提醒大家带上雨伞。", "外出前请记得带上雨伞。"),
        ("写一条简短的会议改期通知，新时间为周三上午。", "会议改至周三上午，请大家准时参加。"),
        ("写一句感谢同事帮忙整理资料的话。", "谢谢你帮忙整理资料。"),
        ("把“先检查，再出发”拆成两个编号步骤。", "1. 检查\n2. 出发"),
        ("把“保存文件”和“关闭窗口”合成一句有先后顺序的话。", "先保存文件，再关闭窗口。"),
        ("用三个词描述安静的图书馆。", "安静、整洁、有序。"),
        ("为一份读书计划拟一个简短标题。", "每周读书计划"),
        ("把这句话改为否定句：今天需要开会。", "今天不需要开会。"),
        ("把这句话改为疑问句：资料已经准备好了。", "资料已经准备好了吗？"),
        ("用一句话说明为什么要备份文件。", "备份文件可以减少资料意外丢失造成的影响。"),
        ("用一句话说明清单有什么用。", "清单可以帮助明确事项，减少遗漏。"),
        ("把两个短句合成一句：小林完成了作业。小林去散步。", "小林完成作业后去散步。"),
        ("回复“谢谢你的帮助”，保持简短。", "不客气，很高兴能帮上忙。"),
    ]
    for i, (question, answer) in enumerate(rewrites):
        add(question, answer, "通用简单指令", f"writing:{i}", kind="authored_simple_task")


def validate_and_write():
    expected = {"无人机基础知识": 700, "自主飞行场景判断": 600,
                "任务规划与步骤分解": 400, "工程知识": 200, "通用简单指令": 100}
    sources = {x["id"]: x for x in json.loads((HERE / "sources.json").read_text(encoding="utf-8"))}
    unique = []
    seen_pairs, questions = set(), {}
    removed = 0
    for row in rows:
        sample = row["sample"]
        assert set(sample) == {"instruction", "output"}
        assert all(isinstance(v, str) and v.strip() for v in sample.values())
        assert all(sources[s]["status"] == "read" for s in row["source_ids"]), row
        pair = tuple(sample.values())
        if pair in seen_pairs:
            removed += 1
            continue
        seen_pairs.add(pair)
        # NFKC plus whitespace normalization catches accidental formatting-only copies.
        norm = re.sub(r"\s+", "", unicodedata.normalize("NFKC", sample["instruction"]))
        assert norm not in questions, (sample["instruction"], questions.get(norm))
        questions[norm] = sample["output"]
        for text in sample.values():
            assert not any(c in text for c in ["\ufffd", "\x00", "<unk>", "TODO", "待补充", "..."])
            assert not any(ord(c) < 32 and c != "\n" for c in text)
        assert len(sample["instruction"]) <= 180
        assert len(sample["output"]) <= 220
        if row["category"] == "任务规划与步骤分解":
            steps = sample["output"].splitlines()
            assert 3 <= len(steps) <= 8
            assert all(s.startswith(f"{i}. ") for i, s in enumerate(steps, 1))
        elif row["category"] != "通用简单指令" and "\n" not in sample["output"]:
            assert len(re.findall(r"[。！？]", sample["output"])) <= 4, sample
        unique.append(row)
    counts = dict(collections.Counter(r["category"] for r in unique))
    assert counts == expected, counts
    assert len(unique) == 2000
    random.Random(SEED).shuffle(unique)
    body = "".join(json.dumps(r["sample"], ensure_ascii=False) + "\n" for r in unique)
    TARGET.write_text(body, encoding="utf-8", newline="\n")
    # Round-trip the final disk artifact, not only the in-memory objects.
    decoded = [json.loads(line) for line in TARGET.read_text(encoding="utf-8").splitlines()]
    assert len(decoded) == 2000 and decoded == [r["sample"] for r in unique]
    metadata = []
    for line_no, row in enumerate(unique, 1):
        metadata.append({"line": line_no, **{k: v for k, v in row.items() if k != "sample"},
                         "sample_sha256": hashlib.sha256(json.dumps(row["sample"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
    (HERE / "train_metadata.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in metadata), encoding="utf-8", newline="\n")
    output_counts = collections.Counter(r["output"] for r in decoded)
    question_lengths = [len(r["instruction"]) for r in decoded]
    answer_lengths = [len(r["output"]) for r in decoded]
    report = {
        "file": str(TARGET), "date": "2026-10-24", "encoding": "UTF-8 without BOM",
        "total": len(decoded), "category_counts": counts, "seed": SEED,
        "generation": {"knowledge_cards": 140, "engineering_cards": 40, "scenario_seeds": 60,
                       "scenario_variants_per_seed": 10, "plan_skeletons": 40, "plan_constraints": 10},
        "checks": {"json_parsing": "passed", "schema": "passed", "nonempty": "passed",
                   "exact_duplicates_removed": removed, "remaining_exact_duplicates": 0,
                   "normalized_duplicate_instructions": 0, "conflicting_same_instructions": 0,
                   "replacement_or_control_characters": 0, "plan_steps_3_to_8": "passed",
                   "nonlist_answers_1_to_4_sentences": "passed"},
        "length_characters": {"instruction_max": max(question_lengths), "instruction_median": statistics.median(question_lengths),
                              "output_max": max(answer_lengths), "output_median": statistics.median(answer_lengths)},
        "most_common_identical_answers": [{"output": a, "count": n} for a, n in output_counts.most_common(8)],
        "source_sample_counts": dict(collections.Counter(s for r in unique for s in r["source_ids"])),
        "sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(),
        "limitations": ["Document-informed synthetic examples, not 2000 independent verified flight incidents.",
                        "No exhaustive semantic deduplication or expert validation; related concept facets remain.",
                        "Safety recommendations assume a small multirotor unless another vehicle is explicitly specified.",
                        "instruction/output requires mapping before the existing MiniMind conversations reader can load it.",
                        "No tokenizer statistics, model training or original sensor logs used."]}
    (HERE / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Stratified review companion, with every scenario including its first answer.
    review = ["# 数据抽查样本", "", "以下为最终文件中的固定抽查与全部场景首答，行号对应 train.jsonl。", ""]
    for category in expected:
        chosen = [(i, r) for i, r in enumerate(unique, 1) if r["category"] == category]
        if category == "自主飞行场景判断":
            chosen = [(i, r) for i, r in chosen if r["seed_id"].endswith(":1")]
        else:
            chosen = random.Random(SEED).sample(chosen, 10)
        review.extend([f"## {category}", ""])
        for i, r in chosen:
            review.extend([f"### 第 {i} 行", "", r["sample"]["instruction"], "", r["sample"]["output"], ""])
    (HERE / "review_samples.md").write_text("\n".join(review), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["file", "total", "category_counts", "checks", "length_characters", "sha256"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    knowledge()
    scenarios()
    plans()
    general()
    validate_and_write()
