"""Extend the existing MiniMind conversations set, without loading/training a model."""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations
import json
import os
from pathlib import Path
import random
import re
import statistics
import unicodedata

HOME = Path(__file__).resolve().parent
ROOT = HOME.parent
DATA = ROOT / "minimind-lzk" / "dataset"
TARGET = DATA / "train.jsonl"
BACKUP = DATA / "train.before_expand_2000.jsonl"
SEED = 2026102408
RNG = random.Random(SEED)
added = []


def norm(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def table(name):
    rows = []
    for line in (HOME / name).read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            fields = line.split("|")
            assert len(fields) == 7
            rows.append(fields)
    return rows


def add(question, answer, category, family, refs=(), sources=()):
    added.append({"sample": {"conversations": [
        {"role": "user", "content": question.strip()},
        {"role": "assistant", "content": answer.strip()}]},
        "category": category, "origin": "expanded", "family": family,
        "seed_refs": list(refs), "source_ids": list(sources)})


def balanced_pairs(cards, groups, target):
    available = set(cards)
    candidates = set()
    for group in groups:
        members = group.split("、")
        assert set(members) <= available, set(members) - available
        candidates.update(tuple(sorted(pair)) for pair in combinations(members, 2))
    assert len(candidates) >= target, (len(candidates), target)
    candidates = sorted(candidates)
    RNG.shuffle(candidates)
    counts = Counter()
    chosen = []
    # Prefer pairs whose concepts have appeared less often, rather than allowing
    # one large group to dominate. Sorted seed inputs make the build reproducible.
    while len(chosen) < target:
        pair = min(candidates, key=lambda p: (counts[p[0]] + counts[p[1]], max(counts[p[0]], counts[p[1]])))
        candidates.remove(pair)
        chosen.append(pair)
        counts.update(pair)
    return chosen


def short_definition(topic, definition):
    text = definition.rstrip("。")
    for prefix in (topic + "是", topic + "指", topic):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    return text


def concept_pairs(filename, groups, pair_count, category):
    cards = {r[0]: r for r in table(filename)}
    pairs = balanced_pairs(cards, groups, pair_count)
    for i, (a, b) in enumerate(pairs):
        da, db = cards[a][1], cards[b][1]
        sa, sb = short_definition(a, da), short_definition(b, db)
        sources = sorted(set(cards[a][-1].split(",") + cards[b][-1].split(",")))
        refs = (f"{filename}:{a}", f"{filename}:{b}")
        add(f"简要区分{a}与{b}。", da + db, category,
            "concept_comparison", refs, sources)
        topic, description = (a, sa) if i % 2 == 0 else (b, sb)
        add(f"在{a}和{b}中，哪一个符合这项说明：{description}？只回答名称。",
            topic, category, "concept_identification", refs, sources)
        add(f"下面的配对颠倒了，请纠正：{a}——{sb}；{b}——{sa}。",
            f"{a}：{sa}。{b}：{sb}。", category,
            "concept_misassignment_correction", refs, sources)


BASIC_GROUPS = [
    "无人机、多旋翼、固定翼、垂直起降无人机、飞控、飞行控制软件、机架、电机、螺旋桨、电调、执行机构、电池、电源模块、载荷、相机载荷、云台、电机映射、电机转向、控制分配",
    "IMU、加速度计、陀螺仪、磁力计、气压计、GPS、GNSS、定位质量、状态估计、传感器融合、EKF、传感器偏置、测量噪声、振动、时间同步、数据延迟、位置漂移、VIO、视觉里程计、光流、动作捕捉、外部视觉定位、测距传感器、SLAM、单传感器故障、冗余传感器、局部定位、全球定位、定位恢复",
    "姿态、横滚、俯仰、偏航、航向、机体坐标系、局部坐标系、NED坐标系、高度参考、速度、加速度、角速度、位姿、坐标转换、单位一致性、全球与局部位置关系、航点高度",
    "路径规划、全局路径、局部路径、轨迹、航点、航点顺序、到达判定、任务步骤、任务前置条件、任务完成条件、任务中止、返航、起飞点、返航位置、备用安全点、降落、降落区、悬停、任务超时、任务反馈、任务优先级、任务暂停、安全退出、任务验证、任务记录、返回与降落选择",
    "位置保持、姿态稳定、高度保持、位置控制器、速度控制器、姿态控制器、角速度控制器、级联控制、反馈控制、设定值、跟踪误差、PID、比例项、积分项、微分项、稳态误差、超调、振荡、控制饱和、速度限制、加速度限制、轨迹平滑、风扰动",
    "障碍物感知、避障、碰撞预防、安全间距、传感器视场、传感器量程、制动距离、障碍数据丢失、未覆盖方向、航线被阻挡、地理围栏、安全高度、路径规划、全局路径、局部路径",
    "传感器校准、飞控安装方向、水平校准、加速度计校准流程、陀螺仪校准流程、磁力计校准流程、预飞检查、就绪状态、解锁检查报告、起飞检查与解锁、故障排查顺序、短航线测试、仿真、软件在环、硬件在环",
    "剩余电量估计、电池串数、电流积分、低电量告警、电池、电源模块、失效保护、告警动作、持续监控、任务优先级、安全退出",
    "遥控失联、数传失联、Offboard链路丢失、位置丢失、人工接管、飞行模式、失效保护、持续监控、定位质量、遥测、遥控器、地面站",
    "地面站、遥测、遥控器、伴随计算机、机载计算延迟、数据更新率、数据有效性、数据一致性、数据时效性、时间同步、数据延迟、任务反馈",
]

ENGINEERING_GROUPS = [
    "PX4、MAVLink、ROS、ROS2、uORB、通信中间件、MAVROS、MAVSDK、QGroundControl、固件版本、SITL测试、HITL测试",
    "ROS2节点、ROS2话题、发布者、订阅者、ROS2消息、ROS2服务、服务客户端、服务端、ROS2动作、动作目标、动作反馈、动作结果、ROS2参数、节点参数名、节点命名空间、节点发现",
    "Offboard模式、Arm、Disarm、Mission模式、Hold模式、Land模式、Return模式、Offboard控制目标、存活信号、任务上传、消息与命令、MAVLink遥测流",
    "MAVLink、MAVROS、MAVSDK、uORB、通信中间件、存活信号、消息与命令、MAVLink遥测流、任务上传、Offboard控制目标、ROS2消息",
]


def simultaneous_faults():
    cases = table("scenario_cases.txt")
    ground = {21, 22, 23, 33, 34, 38, 39, 45, 53, 55, 56}
    # These indexes are checked against names below to avoid stage mixing.
    ground_names = {"加速度计校准未通过", "陀螺仪校准反复重启", "姿态显示与实际倾斜方向不符",
                    "电机编号与实际响应不一致", "电机转向与机型要求相反",
                    "电压读数与实际电池明显不符", "电池串数设置与实物不一致",
                    "任务上传失败", "任务航点高度参考不明确", "目标位置单位与接口规定不一致",
                    "已落地但电机仍在转动"}
    state_families = [
        ["GPS失效", "GPS刚恢复", "卫星定位质量"],
        ["VIO相机", "VIO输出", "视觉位置运动", "视觉定位原点"],
        ["本地位置有效", "GPS失效且没有", "位置估计持续", "定位消息到达"],
        ["剩余电量不足", "电量已接近", "电池剩余量"],
        ["任务上传", "当前航点", "拍照任务"],
        ["电机编号", "电机转向"],
    ]
    conflicts = [
        ("GPS失效且没有有效替代定位", "本地位置有效但全球位置无效"),
        ("GPS失效且没有有效替代定位", "GPS失效但已配置VIO仍有效"),
        ("GPS刚恢复但位置仍跳变", "GPS失效但已配置VIO仍有效"),
    ]
    candidates = []
    for ia, ib in combinations(range(len(cases)), 2):
        a, b = cases[ia][0], cases[ib][0]
        if (a in ground_names) != (b in ground_names):
            continue
        if "已落地" in a or "已落地" in b:
            continue
        if any(any(t in a for t in group) and any(t in b for t in group) for group in state_families):
            continue
        if any({a, b} == set(pair) for pair in conflicts):
            continue
        candidates.append((ia, ib))
    RNG.shuffle(candidates)
    selected, degrees = [], Counter()
    while len(selected) < 450:
        pair = min(candidates, key=lambda p: (degrees[p[0]] + degrees[p[1]], max(degrees[p[0]], degrees[p[1]])))
        candidates.remove(pair)
        selected.append(pair)
        degrees.update(pair)

    def severity(row):
        issue = row[0]
        if "没有有效替代" in issue or "下降通道" in issue or "停止所需" in issue:
            return 0
        if "剩余电量不足" in issue or "控制响应" in issue or "异常振动" in issue:
            return 1
        if "电量" in issue or "风力" in issue or "障碍" in issue:
            return 2
        return 3

    for ia, ib in selected:
        ca, cb = cases[ia], cases[ib]
        # The ordering is only for a concise checklist; it is not a universal
        # ranking of flight-control actions, which depend on current state.
        ca, cb = sorted((ca, cb), key=severity)
        a, fa, qa, ra, wa, why_a, sa = ca
        b, fb, qb, rb, wb, why_b, sb = cb
        sources = sorted(set(sa.split(",") + sb.split(",")))
        refs = (f"scenario:{ia+1}", f"scenario:{ib+1}")
        stage = "地面检查时" if a in ground_names else "任务过程中"
        condition = f"{stage}，同时出现“{a}”和“{b}”"
        pairs = [
            (condition + "。列出两项需要落实的处理。",
             f"1. {fa}\n2. {fb}"),
            (condition + "。分别检查什么？",
             f"1. {qa}\n2. {qb}"),
            (f"“{a}”已经处理，但“{b}”尚未排除，能直接恢复原任务吗？",
             "不能仅凭一个问题恢复就继续。" + rb),
            (condition + "。能只处理第一个问题就认为全部恢复吗？",
             "不能，还要分别确认两个问题的恢复条件。" + ra + rb),
        ]
        for q, answer in pairs:
            add(q, answer, "自主飞行场景判断", "two_condition_scenario", refs, sources)


def compositional_plans(prior_module):
    prior_module.rows.clear()
    prior_module.plans()
    groups = defaultdict(dict)
    for row in prior_module.rows:
        _, action, route, variant = row["seed_id"].split(":")
        groups[(action, route)][int(variant)] = row
    assert len(groups) == 40
    for key in sorted(groups):
        variants = groups[key]
        normal = variants[1]["sample"]
        base = [re.sub(r"^\d+\. ", "", s) for s in normal["output"].splitlines()]
        description = normal["instruction"].split("分解任务：", 1)[1].split("；", 1)[0]
        constraints = {}
        for i in range(2, 11):
            sample = variants[i]["sample"]
            requirement = sample["instruction"].split("；", 1)[1].split("。只列步骤", 1)[0]
            new_steps = [re.sub(r"^\d+\. ", "", s) for s in sample["output"].splitlines()]
            difference = list((Counter(new_steps) - Counter(base)).elements())
            assert len(difference) == 1
            constraints[i] = (requirement, difference[0])
        combos = list(combinations(range(2, 11), 2))
        RNG.shuffle(combos)
        for first, second in combos[:30]:
            steps = list(base)
            for i in sorted((first, second)):
                extra = constraints[i][1]
                if i in (2, 3, 9):
                    steps.insert(0, extra)
                elif i == 4:
                    steps.insert(steps.index("起飞") + 1, extra)
                elif i in (5, 6):
                    steps.insert(steps.index("返回起点"), extra)
                elif i == 8:
                    steps.insert(steps.index("降落"), extra)
                else:
                    steps.append(extra)
            if len(steps) > 8:
                # Combine adjacent steps while preserving both actions and order.
                if first in (2, 3, 9) and second in (2, 3, 9):
                    steps[:2] = [steps[0] + "，并" + steps[1]]
                elif 7 in (first, second):
                    j = steps.index("降落")
                    after = "确认已落地、解除解锁且电机停转"
                    steps.remove(after)
                    steps[j] = "降落后确认解除解锁且电机停转"
                elif 4 in (first, second):
                    j = steps.index("起飞")
                    steps[j:j+2] = ["起飞后在起点附近确认位置稳定"]
                else:
                    j = steps.index("返回起点")
                    k = steps.index("降落")
                    steps[j:k+1] = ["，然后".join(steps[j:k+1])]
            assert 3 <= len(steps) <= 8
            prompt = ("多旋翼的定位、电量与航线均满足要求。分解任务：" + description + "。"
                      + "附加要求：" + constraints[first][0] + "；" + constraints[second][0] + "。只列步骤。")
            answer = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))
            add(prompt, answer, "任务规划与步骤分解", "two_constraint_plan",
                (f"plan:{key[0]}:{key[1]}:{first}", f"plan:{key[0]}:{key[1]}:{second}"),
                variants[first]["source_ids"])


def general_tasks():
    for i in range(30):
        a, b = 40 + 2*i, 6 + i
        add(f"求和，只写整数结果：{a}加{b}。", str(a+b), "通用简单指令", "addition")
        a, b = 80 + 3*i, 15 + i
        add(f"求差，只写整数结果：{a}减{b}。", str(a-b), "通用简单指令", "subtraction")
    for i in range(20):
        a, b = i + 2, 3 + i % 7
        add(f"计算{a}乘{b}，只写结果。", str(a*b), "通用简单指令", "multiplication")
    for i in range(60):
        values = RNG.sample(range(10, 150), 3 + i % 3)
        desc = i % 2 == 0
        q = "从大到小" if desc else "从小到大"
        add(f"按{q}的顺序整理：" + "，".join(map(str, values)) + "。",
            "、".join(map(str, sorted(values, reverse=desc))), "通用简单指令", "sort")
    people = ["小夏", "小梅", "小何", "小郑", "小宋", "小叶", "小朱", "小高", "小许", "小唐",
              "小马", "小杜", "小冯", "小方", "小邓", "小袁", "小陆", "小白", "小罗", "小苏"]
    places = ["阅览室", "活动室", "打印室", "资料室", "接待室", "实验室", "休息室", "大厅", "门口", "餐厅"]
    for i, person in enumerate(people):
        place = places[i % 10]
        time = "周" + "一二三四五六日"[i % 7] + "上午"
        text = f"{person}将在{time}前往{place}。"
        for field, answer in [("人物", person), ("时间", time), ("地点", place)]:
            add(f"从这句话提取{field}，只写答案：{text}", answer, "通用简单指令", "entity_extraction")
    lists = ["毛巾、牙刷、牙膏", "西瓜、葡萄、橙子", "报纸、杂志、画册", "文件夹、订书机、回形针",
             "围巾、帽子、手套", "白菜、土豆、胡萝卜", "游泳、跑步、骑车", "计划、执行、复查",
             "耳机、键盘、鼠标", "咖啡、茶、果汁"]
    for text in lists:
        parts = text.split("、")
        options = [
            ("把顿号列表改为逗号列表", "，".join(parts)),
            ("每行列出一项，不加编号", "\n".join(parts)),
            ("只提取第一项", parts[0]),
            ("只提取最后一项", parts[-1]),
            ("计算项目数，只写数字", str(len(parts))),
        ]
        for task, answer in options:
            add(f"{task}：{text}。", answer, "通用简单指令", "list_processing")
    # Explicit string operations have exact targets without introducing new facts.
    objects = ["收拾书桌", "准备午餐", "核对名单", "整理书架", "清理文件", "准备讲稿", "检查材料", "保存图片", "联系同事", "归还图书"]
    for text in objects:
        options = [
            (f"把“{text}”写成一句礼貌请求。", f"请帮忙{text}，谢谢。"),
            (f"在“{text}”前加“今天需要”，末尾加句号。", f"今天需要{text}。"),
            (f"将“计划：{text}”中的“计划”替换为“任务”。", f"任务：{text}"),
            (f"将“{text}”的每个字用空格分隔。", " ".join(text)),
            (f"去掉“{' '.join(text)}”中的空格。", text),
        ]
        for task, answer in options:
            add(task, answer, "通用简单指令", "short_text_editing")


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("prior_dataset", HOME / "generate_dataset.py")
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    original_bytes = TARGET.read_bytes()
    original = [json.loads(line) for line in original_bytes.decode("utf-8-sig").splitlines()]
    if len(original) != 2000:
        raise SystemExit(f"Expected the original 2000 rows; found {len(original)}. Refusing to overwrite.")
    original_info = [json.loads(line) for line in (HOME / "train_metadata.jsonl").read_text(encoding="utf-8").splitlines()]
    old_format = [json.loads(line) for line in (ROOT / "train.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(original_info) == len(old_format) == 2000
    for old, row in zip(old_format, original):
        assert row == {"conversations": [{"role": "user", "content": old["instruction"]}, {"role": "assistant", "content": old["output"]}]}

    concept_pairs("basic_cards.txt", BASIC_GROUPS, 700, "无人机基础知识")
    concept_pairs("engineering_cards.txt", ENGINEERING_GROUPS, 200, "工程知识")
    simultaneous_faults()
    compositional_plans(previous)
    general_tasks()
    expected_added = {"无人机基础知识": 2100, "工程知识": 600, "自主飞行场景判断": 1800,
                      "任务规划与步骤分解": 1200, "通用简单指令": 300}
    assert Counter(r["category"] for r in added) == expected_added
    assert len(added) == 6000
    all_rows = []
    for row, info in zip(original, original_info):
        all_rows.append({"sample": row, "category": info["category"], "origin": "original_2000",
                         "family": "preserved_original", "seed_refs": [info["seed_id"]], "source_ids": info["source_ids"]})
    all_rows.extend(added)
    seen_questions, seen_rows = {}, set()
    lengths, step_lengths = [], []
    for row in all_rows:
        sample = row["sample"]
        assert set(sample) == {"conversations"}
        messages = sample["conversations"]
        assert len(messages) == 2
        assert [m["role"] for m in messages] == ["user", "assistant"]
        assert all(set(m) == {"role", "content"} for m in messages)
        assert all(isinstance(m["content"], str) and m["content"].strip() for m in messages)
        q, a = (m["content"] for m in messages)
        key = norm(q)
        assert key not in seen_questions, ("Duplicate question", q)
        seen_questions[key] = a
        pair = (q, a)
        assert pair not in seen_rows
        seen_rows.add(pair)
        for text in (q, a):
            assert not any(c in text for c in ("\ufffd", "\x00", "TODO", "待补充", "<unk>"))
            assert not any(ord(c) < 32 and c not in "\n\t" for c in text)
        assert len(q) <= 230, (len(q), q)
        assert len(a) <= 220, (len(a), a)
        if row["category"] == "任务规划与步骤分解":
            steps = a.splitlines()
            assert 3 <= len(steps) <= 8
            assert all(s.startswith(f"{i}. ") for i, s in enumerate(steps, 1))
            step_lengths.append(len(steps))
        lengths.append((len(q), len(a)))
    assert len(all_rows) == 8000
    counts = Counter(r["category"] for r in all_rows)
    assert counts == {"无人机基础知识": 2800, "工程知识": 800, "自主飞行场景判断": 2400,
                      "任务规划与步骤分解": 1600, "通用简单指令": 400}
    RNG.shuffle(all_rows)
    content = "".join(json.dumps(r["sample"], ensure_ascii=False) + "\n" for r in all_rows).encode("utf-8")
    decoded = [json.loads(l) for l in content.decode("utf-8").splitlines()]
    assert len(decoded) == 8000
    original_pairs = {tuple(m["content"] for m in r["conversations"]) for r in original}
    final_pairs = {tuple(m["content"] for m in r["conversations"]) for r in decoded}
    assert original_pairs <= final_pairs
    if BACKUP.exists():
        assert BACKUP.read_bytes() == original_bytes, "A different backup already exists"
    else:
        with BACKUP.open("xb") as backup:
            backup.write(original_bytes)
    temp = DATA / "train.expanding.tmp"
    temp.write_bytes(content)
    disk_rows = [json.loads(l) for l in temp.read_text(encoding="utf-8").splitlines()]
    assert disk_rows == decoded
    os.replace(temp, TARGET)
    metadata = []
    for line, row in enumerate(all_rows, 1):
        metadata.append({"line": line, **{k: v for k, v in row.items() if k != "sample"},
                         "sample_sha256": sha256(json.dumps(row["sample"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
    (DATA / "train_8000_metadata.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in metadata), encoding="utf-8")
    report = {"path": str(TARGET), "backup": str(BACKUP), "original_count": 2000, "added_count": 6000,
              "final_count": 8000, "preserved_original_count": len(original_pairs & final_pairs),
              "category_counts": dict(counts), "new_family_counts": dict(Counter(r["family"] for r in added)),
              "checks": {"all_json_parse": True, "schema_and_roles": True, "empty_fields": 0,
                         "exact_duplicate_samples": 0, "normalized_duplicate_instructions": 0,
                         "conflicting_same_instruction": 0, "replacement_or_control_characters": 0,
                         "plan_steps_min": min(step_lengths), "plan_steps_max": max(step_lengths)},
              "character_lengths": {"question_max": max(x[0] for x in lengths), "answer_max": max(x[1] for x in lengths),
                                    "question_median": statistics.median(x[0] for x in lengths), "answer_median": statistics.median(x[1] for x in lengths)},
              "source_manifest": str(HOME / "sources.json"), "seed": SEED,
              "original_sha256": sha256(original_bytes).hexdigest(), "expanded_sha256": sha256(content).hexdigest(),
              "training_started": False,
              "notes": ["新增数据为现有文本知识的辨析与条件组合，不代表新增6000个独立知识点。",
                        "精确与规范化问题去重通过；未声称完成全部语义近似去重或专家认证。",
                        "未修改模型、训练参数或工作区根目录的旧版train.jsonl。"]}
    (DATA / "expansion_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preview = ["# 8000条版本新增样本抽查", ""]
    for category in counts:
        selected = [(i, row) for i, row in enumerate(all_rows, 1) if row["origin"] == "expanded" and row["category"] == category]
        selected = random.Random(SEED).sample(selected, 12)
        preview.extend(["## " + category, ""])
        for i, row in selected:
            q, a = (m["content"] for m in row["sample"]["conversations"])
            preview.extend([f"### 第{i}行", "", q, "", a, ""])
    (DATA / "expansion_review.md").write_text("\n".join(preview), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
