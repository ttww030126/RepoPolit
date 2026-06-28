"""记忆遗忘引擎（Forgetting Engine）。

灵感来自 MemoryBear 的“记忆强度 + 时间衰减”双维度建模，以及人脑突触修剪
（synaptic pruning）的三段生命周期：active -> dormant -> archived。

设计取向：
- 仍然保持 mneme 的零依赖、纯标准库风格，遗忘逻辑是确定的、可解释的、可测试的；
- 不引入 embedding，也不需要外部数据库；
- 衰减只改变“检索优先级”，不会静默删除高价值笔记，archived 仍可恢复。

记忆强度模型（Ebbinghaus 式指数遗忘，叠加访问强化）：

    S(t) = S0 * exp(-lambda * dt) * (1 + alpha * ln(1 + n_access))

其中 dt 是“距上次访问的天数”，lambda 是按 kind 配置的衰减速率，
n_access 是被检索命中的累计次数，alpha 控制访问强化幅度。
"""

import math
from datetime import datetime, timezone

# 默认按记忆类型设定衰减速率（每天）。durable（长期事实）几乎不衰减，
# episodic（情节笔记）衰减较快，process（过程性临时记录）衰减最快。
DEFAULT_DECAY_RATES = {
    "durable": 0.01,
    "episodic": 0.08,
    "process": 0.20,
}

# 生命周期阈值：强度高于 ACTIVE 视为活跃；低于 DORMANT 且超龄进入归档。
DEFAULT_LIFECYCLE = {
    "active_threshold": 0.45,
    "dormant_threshold": 0.15,
    "archive_age_days": 30.0,
    "initial_strength": 1.0,
    "access_boost_alpha": 0.35,
}

STAGE_ACTIVE = "active"
STAGE_DORMANT = "dormant"
STAGE_ARCHIVED = "archived"


def _parse_ts(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _now():
    return datetime.now(timezone.utc)


def _age_days(reference, now):
    ref = _parse_ts(reference)
    if ref is None:
        return 0.0
    delta = now - ref
    return max(0.0, delta.total_seconds() / 86400.0)


def compute_strength(note, now=None, config=None):
    """计算单条笔记的当前记忆强度，返回 [0, +inf) 的浮点数。

    输入是一条已规范化的笔记 dict（至少包含 kind / created_at；
    可选 last_access / access_count / importance）。
    importance 是 [0,1] 的人工/启发式重要度，相当于 MemoryBear 里
    “抽取质量 + 重要度标签”决定的初始强度。
    """
    config = {**DEFAULT_LIFECYCLE, **(config or {})}
    rates = DEFAULT_DECAY_RATES
    now = now or _now()

    kind = str(note.get("kind", "episodic"))
    lam = rates.get(kind, rates["episodic"])
    importance = float(note.get("importance", config["initial_strength"]))
    s0 = max(0.05, min(importance, 2.0))

    # 距上次“访问”的天数；从未被检索命中过则退化为距创建时间。
    last_access = note.get("last_access") or note.get("created_at")
    dt = _age_days(last_access, now)
    access_count = int(note.get("access_count", 0))

    decay = math.exp(-lam * dt)
    boost = 1.0 + config["access_boost_alpha"] * math.log1p(access_count)
    return s0 * decay * boost


def lifecycle_stage(note, now=None, config=None):
    """根据强度和年龄判定笔记所处的生命周期阶段。"""
    config = {**DEFAULT_LIFECYCLE, **(config or {})}
    now = now or _now()
    strength = compute_strength(note, now=now, config=config)
    age = _age_days(note.get("created_at"), now)

    if strength >= config["active_threshold"]:
        return STAGE_ACTIVE
    if strength >= config["dormant_threshold"]:
        return STAGE_DORMANT
    if age >= config["archive_age_days"]:
        return STAGE_ARCHIVED
    return STAGE_DORMANT


def reinforce(note, now=None):
    """记忆被检索命中时调用：累加访问次数并刷新 last_access。

    对应 MemoryBear 中“被关联/被调用的知识获得强化”。返回新的 note dict
    （不原地修改入参，方便上层做不可变更新）。
    """
    now = now or _now()
    updated = dict(note)
    updated["access_count"] = int(note.get("access_count", 0)) + 1
    updated["last_access"] = now.isoformat()
    return updated


def annotate(notes, now=None, config=None):
    """为一批笔记打上当前 strength 与 stage，按强度从高到低排序返回。

    这是给检索层和 /memory 仪表盘用的只读视图，不改变持久化顺序。
    """
    now = now or _now()
    config = {**DEFAULT_LIFECYCLE, **(config or {})}
    annotated = []
    for note in notes:
        strength = compute_strength(note, now=now, config=config)
        stage = lifecycle_stage(note, now=now, config=config)
        annotated.append({**note, "strength": round(strength, 4), "stage": stage})
    annotated.sort(key=lambda item: item["strength"], reverse=True)
    return annotated


def forgetting_sweep(notes, now=None, config=None):
    """执行一次遗忘扫描，把笔记切分成 kept（活跃/休眠）与 archived（归档）。

    归档不是删除：archived 笔记会从主工作集移出、停止占用 prompt 预算，
    但仍可由上层写入冷存储（.mneme/memory/archive.jsonl）以便日后恢复。
    返回 (kept, archived, report)。
    """
    now = now or _now()
    config = {**DEFAULT_LIFECYCLE, **(config or {})}
    kept = []
    archived = []
    counts = {STAGE_ACTIVE: 0, STAGE_DORMANT: 0, STAGE_ARCHIVED: 0}
    for note in notes:
        stage = lifecycle_stage(note, now=now, config=config)
        counts[stage] += 1
        if stage == STAGE_ARCHIVED:
            archived.append({**note, "stage": stage})
        else:
            kept.append(note)
    report = {
        "active": counts[STAGE_ACTIVE],
        "dormant": counts[STAGE_DORMANT],
        "archived": counts[STAGE_ARCHIVED],
        "kept": len(kept),
        "redundancy_ratio": round(counts[STAGE_ARCHIVED] / max(1, len(notes)), 4),
    }
    return kept, archived, report
