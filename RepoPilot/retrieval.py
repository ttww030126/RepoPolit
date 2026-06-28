"""混合检索（Hybrid Retrieval）。

对标 MemoryBear 的“关键词 + 语义向量”双通道融合检索，但坚持 repopilot 的
零依赖约束：这里用“特征哈希（feature hashing）+ TF 加权 + 余弦相似度”
实现一个轻量本地语义通道，避免引入 BERT、faiss、向量数据库等重依赖。

融合策略（与 MemoryBear 思路一致：语义召回扩候选，关键词/强度做精排）：

    score = w_kw * kw_overlap_norm
          + w_sem * cosine_sim
          + w_recency * recency_norm
          + w_strength * strength_norm

权重可配置。语义通道是“锦上添花”，关键词与记忆强度仍是主排序信号，
因此即使在纯英文短文本上 embedding 不强，检索质量也不会退化。
"""

import hashlib
import math
import re

from .memory_decay import compute_strength

DEFAULT_DIM = 256
DEFAULT_WEIGHTS = {
    "keyword": 0.45,
    "semantic": 0.30,
    "recency": 0.10,
    "strength": 0.15,
}

_TOKEN_RE = re.compile(r"[A-Za-z0-9_\u4e00-\u9fff]+")


def tokenize(text):
    """同时切英文词与中文字符，给中英混合场景一个基础语义信号。"""
    tokens = []
    for chunk in _TOKEN_RE.findall(str(text)):
        if re.search(r"[\u4e00-\u9fff]", chunk):
            tokens.extend(list(chunk))  # 中文按字切，简单但稳定
        else:
            tokens.append(chunk.lower())
    return tokens


def _bucket(token, dim):
    digest = hashlib.md5(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % dim


def embed(text, dim=DEFAULT_DIM):
    """把文本映射成固定维度的稀疏 TF 向量（dict: index -> weight）。

    这是确定性的、可离线、可测试的“伪 embedding”。它捕捉不到深层语义，
    但能在零依赖前提下提供同义/共现层面的相似度信号。
    """
    vec = {}
    for token in tokenize(text):
        idx = _bucket(token, dim)
        vec[idx] = vec.get(idx, 0.0) + 1.0
    # L2 归一化，便于直接做余弦
    norm = math.sqrt(sum(value * value for value in vec.values())) or 1.0
    return {idx: value / norm for idx, value in vec.items()}


def cosine(vec_a, vec_b):
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    return sum(weight * vec_b.get(idx, 0.0) for idx, weight in vec_a.items())


def _recency_norm(created_at):
    # 简单地把 ISO 时间转成 [0,1]，越新越接近 1。
    from .memory_decay import _age_days, _now

    age = _age_days(created_at, _now())
    return 1.0 / (1.0 + age)  # 0 天 -> 1，30 天 -> ~0.032


class HybridRetriever:
    def __init__(self, dim=DEFAULT_DIM, weights=None):
        self.dim = dim
        self.weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    def score_note(self, note, query_tokens, query_vec):
        text = note.get("text", "")
        note_tokens = set(tokenize(text)) | {t.lower() for t in note.get("tags", [])}
        overlap = len(query_tokens & note_tokens)
        kw_norm = overlap / max(1, len(query_tokens))

        sem = cosine(query_vec, embed(text, self.dim))
        recency = _recency_norm(note.get("created_at"))
        strength = compute_strength(note)
        strength_norm = strength / (1.0 + strength)

        weights = self.weights
        return (
            weights["keyword"] * kw_norm
            + weights["semantic"] * sem
            + weights["recency"] * recency
            + weights["strength"] * strength_norm
        )

    def search(self, query, notes, limit=3, min_score=1e-6):
        """对一组笔记做混合检索，返回 (note, score) 列表（已按分数降序）。"""
        query_tokens = set(tokenize(query))
        query_vec = embed(query, self.dim)
        ranked = []
        for note in notes:
            score = self.score_note(note, query_tokens, query_vec)
            if score <= min_score:
                continue
            ranked.append((note, round(score, 6)))
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:limit]
