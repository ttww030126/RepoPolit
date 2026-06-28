"""记忆层。

四个子模块共同构成一套“类人记忆”体系：
- layered:    分层工作记忆（工作集 / 情节笔记 / 文件摘要 / 持久记忆）
- decay:      遗忘引擎（记忆强度 + 时间衰减 + 三段生命周期）
- retrieval:  混合检索（关键词 + 本地语义向量 融合排序）
- reflection: 自反思巩固（去重合并 + 价值评估 + 遗忘扫描）

注意：本包对外统一 re-export `layered` 中的公共 API。runtime 与测试都通过
`mneme.memory.<name>`（而非深入子模块）来访问这些函数，因此这里必须保持
导出完整——历史上漏导出 `file_freshness` / `summarize_read_result` 曾导致
`ask()` 主循环在第一次工具执行后崩溃。
"""
from mneme.memory import decay, layered, reflection, retrieval  # noqa: F401
from mneme.memory.layered import (  # noqa: F401
    DurableMemoryStore,
    LayeredMemory,
    append_note,
    canonicalize_path,
    default_memory_state,
    file_freshness,
    invalidate_file_summary,
    invalidate_stale_file_summaries,
    is_effectively_empty,
    normalize_memory_state,
    remember_file,
    render_memory_text,
    resolve_workspace_path,
    retrieval_candidates,
    retrieval_view,
    set_file_summary,
    set_task_summary,
    summarize_read_result,
)

# `canonical_path` 是 runtime 侧偶尔会用到的别名（与 LayeredMemory.canonical_path 对应）。
canonical_path = canonicalize_path

__all__ = [
    "decay", "layered", "reflection", "retrieval",
    "DurableMemoryStore", "LayeredMemory", "append_note", "canonical_path",
    "canonicalize_path", "default_memory_state", "file_freshness",
    "invalidate_file_summary", "invalidate_stale_file_summaries",
    "is_effectively_empty", "normalize_memory_state", "remember_file",
    "render_memory_text", "resolve_workspace_path", "retrieval_candidates",
    "retrieval_view", "set_file_summary", "set_task_summary",
    "summarize_read_result",
]
