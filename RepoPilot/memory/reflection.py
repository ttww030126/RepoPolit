"""记忆自反思与巩固引擎（Reflection / Consolidation Engine）。

对标 MemoryBear 的“定时自反思”：一致性检查、价值评估、关联优化。
在 mneme 里，反思被设计成一个确定性的、可手动触发（/reflect）或在会话结束时
自动运行的离线过程，输出一份可读 report，并对工作记忆做三件事：

1. 一致性 / 去重：合并近似重复笔记（token Jaccard 高于阈值），冲突时保留更新的；
2. 价值评估：用记忆强度（访问频率 + 时间衰减）筛掉低价值条目；
3. 遗忘巩固：执行一次 forgetting_sweep，把 archived 笔记写入冷存储。

它不依赖外部服务，也不“静默改写”用户事实——所有动作都会进入 report。
"""

from mneme.memory.decay import compute_strength, forgetting_sweep
from mneme.memory.retrieval import tokenize


def _jaccard(a_tokens, b_tokens):
    if not a_tokens or not b_tokens:
        return 0.0
    inter = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return inter / union if union else 0.0


def deduplicate(notes, threshold=0.82):
    """合并近似重复的笔记。保留 access_count/strength 更高、时间更新的版本。

    返回 (kept_notes, merged_pairs)。merged_pairs 用于 report 解释合并了什么。
    """
    kept = []
    kept_tokens = []
    merged = []
    for note in sorted(notes, key=lambda n: compute_strength(n), reverse=True):
        toks = set(tokenize(note.get("text", "")))
        duplicate_of = None
        for index, existing_tokens in enumerate(kept_tokens):
            if _jaccard(toks, existing_tokens) >= threshold:
                duplicate_of = index
                break
        if duplicate_of is None:
            kept.append(note)
            kept_tokens.append(toks)
        else:
            winner = kept[duplicate_of]
            # 把被合并条目的访问次数累加到留存条目，体现“关联强化”。
            winner["access_count"] = int(winner.get("access_count", 0)) + int(
                note.get("access_count", 0)
            )
            merged.append((note.get("text", ""), winner.get("text", "")))
    return kept, merged


def value_filter(notes, keep_top=None, min_strength=0.05):
    """价值评估：去掉强度过低的条目；可选地只保留 top-N。"""
    scored = [(note, compute_strength(note)) for note in notes]
    scored = [(note, strength) for note, strength in scored if strength >= min_strength]
    scored.sort(key=lambda item: item[1], reverse=True)
    if keep_top is not None:
        scored = scored[:keep_top]
    return [note for note, _ in scored]


def reflect(notes, dedupe_threshold=0.82, keep_top=None):
    """运行一次完整的反思流水线，返回 (kept_notes, archived_notes, report)。

    顺序刻意是：先去重（减少干扰）-> 价值过滤 -> 遗忘扫描（分层），
    这样 report 里的数字能清楚反映每一步的收益。
    """
    original_count = len(notes)
    deduped, merged_pairs = deduplicate(notes, threshold=dedupe_threshold)
    valued = value_filter(deduped, keep_top=keep_top)
    kept, archived, sweep_report = forgetting_sweep(valued)

    report = {
        "input_notes": original_count,
        "after_dedupe": len(deduped),
        "merged_pairs": len(merged_pairs),
        "after_value_filter": len(valued),
        "kept": len(kept),
        "archived": len(archived),
        "lifecycle": sweep_report,
        "merged_examples": merged_pairs[:5],
    }
    return kept, archived, report


def render_report(report):
    """把反思 report 渲染成给人/给模型看的简短文本。"""
    lines = [
        "Reflection report:",
        f"- input: {report['input_notes']} notes",
        f"- merged duplicates: {report['merged_pairs']} pair(s)",
        f"- archived (forgotten): {report['archived']}",
        f"- kept active/dormant: {report['kept']}",
        f"- redundancy_ratio: {report['lifecycle']['redundancy_ratio']}",
    ]
    for old, new in report.get("merged_examples", []):
        lines.append(f"  merged: {old[:40]!r} -> {new[:40]!r}")
    return "\n".join(lines)
