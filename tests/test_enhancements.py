"""新增能力的单元测试：遗忘引擎 / 混合检索 / 反思 / 技能 / MCP 配置 / DeepSeek 缓存。

刻意只用标准库 unittest，既能被 pytest 收集，也能直接
`python -m unittest tests.test_enhancements` 运行，匹配 mneme 的零依赖风格。
"""

import json
import unittest
from datetime import datetime, timedelta, timezone

from mneme import memory_decay, reflection, retrieval, skills
from mneme.mcp import MCPError, load_mcp_config
from mneme.models import DeepSeekModelClient


def _iso(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


class ForgettingEngineTests(unittest.TestCase):
    def test_recent_note_is_active(self):
        note = {"text": "fresh", "kind": "episodic", "created_at": _iso(0)}
        self.assertEqual(memory_decay.lifecycle_stage(note), memory_decay.STAGE_ACTIVE)

    def test_old_episodic_decays_below_recent(self):
        old = {"text": "old", "kind": "episodic", "created_at": _iso(40), "last_access": _iso(40)}
        new = {"text": "new", "kind": "episodic", "created_at": _iso(0)}
        self.assertLess(memory_decay.compute_strength(old), memory_decay.compute_strength(new))

    def test_durable_decays_slower_than_episodic(self):
        durable = {"text": "d", "kind": "durable", "created_at": _iso(20), "last_access": _iso(20)}
        episodic = {"text": "e", "kind": "episodic", "created_at": _iso(20), "last_access": _iso(20)}
        self.assertGreater(
            memory_decay.compute_strength(durable), memory_decay.compute_strength(episodic)
        )

    def test_access_reinforces_strength(self):
        note = {"text": "x", "kind": "episodic", "created_at": _iso(10), "last_access": _iso(10)}
        before = memory_decay.compute_strength(note)
        reinforced = memory_decay.reinforce(note)
        after = memory_decay.compute_strength(reinforced)
        self.assertGreater(after, before)
        self.assertEqual(reinforced["access_count"], 1)

    def test_sweep_archives_old_weak_notes(self):
        notes = [
            {"text": "keep", "kind": "durable", "created_at": _iso(1)},
            {"text": "forget", "kind": "process", "created_at": _iso(60), "last_access": _iso(60)},
        ]
        kept, archived, report = memory_decay.forgetting_sweep(notes)
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(archived), 1)
        self.assertEqual(kept[0]["text"], "keep")
        self.assertGreaterEqual(report["redundancy_ratio"], 0.0)


class HybridRetrievalTests(unittest.TestCase):
    def test_keyword_match_ranks_first(self):
        notes = [
            {"text": "parser fails on empty input", "tags": ["parser"], "created_at": _iso(1)},
            {"text": "unrelated note about deployment", "tags": [], "created_at": _iso(1)},
        ]
        retriever = retrieval.HybridRetriever()
        results = retriever.search("parser empty bug", notes, limit=2)
        self.assertTrue(results)
        self.assertIn("parser", results[0][0]["text"])

    def test_semantic_channel_returns_score(self):
        vec_a = retrieval.embed("database connection pool")
        vec_b = retrieval.embed("database connection pool")
        self.assertAlmostEqual(retrieval.cosine(vec_a, vec_b), 1.0, places=5)
        self.assertLess(retrieval.cosine(vec_a, retrieval.embed("totally different topic")), 1.0)

    def test_chinese_tokenization(self):
        tokens = retrieval.tokenize("修复解析器 parser bug")
        self.assertIn("parser", tokens)
        self.assertIn("修", tokens)


class ReflectionTests(unittest.TestCase):
    def test_dedupe_merges_near_duplicates(self):
        notes = [
            {"text": "the parser fails on empty input", "created_at": _iso(1)},
            {"text": "the parser fails on empty input", "created_at": _iso(0)},
            {"text": "deployment uses docker compose", "created_at": _iso(1)},
        ]
        kept, merged = reflection.deduplicate(notes)
        self.assertEqual(len(kept), 2)
        self.assertEqual(len(merged), 1)

    def test_reflect_produces_report(self):
        notes = [
            {"text": "fact a", "kind": "durable", "created_at": _iso(1)},
            {"text": "fact a", "kind": "durable", "created_at": _iso(0)},
            {"text": "stale", "kind": "process", "created_at": _iso(90), "last_access": _iso(90)},
        ]
        kept, archived, report = reflection.reflect(notes)
        self.assertEqual(report["input_notes"], 3)
        self.assertGreaterEqual(report["merged_pairs"], 1)
        self.assertIn("Reflection report", reflection.render_report(report))


class SkillTests(unittest.TestCase):
    def test_discover_and_load(self):
        import tempfile
        from pathlib import Path

        root = Path(tempfile.mkdtemp())
        skill_dir = root / "skills" / "run-tests"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: run-tests\ndescription: run and fix tests\nkeywords: test, pytest\n---\n"
            "Use `python -m pytest -q`. Read the implementation before editing tests.",
            encoding="utf-8",
        )
        registry = skills.SkillRegistry(root)
        registry.discover()
        self.assertIn("run-tests", registry.skills)
        self.assertIn("run and fix tests", registry.catalog_text())
        suggestions = registry.suggest("my pytest is failing")
        self.assertTrue(suggestions)

        class _Mem:
            def __init__(self):
                self.notes = []

            def append_note(self, text, **kwargs):
                self.notes.append((text, kwargs))

        class _Agent:
            memory = _Mem()

        tools = skills.build_skill_tools(registry)
        out = tools["use_skill"]["run"](_Agent(), {"slug": "run-tests"})
        self.assertIn("Skill loaded", out)


class MCPConfigTests(unittest.TestCase):
    def test_valid_config(self):
        raw = json.dumps({"fs": {"command": "npx", "args": ["-y", "server"]}})
        config = load_mcp_config(raw)
        self.assertIn("fs", config)

    def test_missing_command_rejected(self):
        with self.assertRaises(MCPError):
            load_mcp_config(json.dumps({"bad": {"args": []}}))

    def test_empty_returns_empty(self):
        self.assertEqual(load_mcp_config(""), {})


class DeepSeekCacheTests(unittest.TestCase):
    def test_supports_prompt_cache(self):
        client = DeepSeekModelClient(
            model="deepseek-v4-pro",
            base_url="https://api.deepseek.com/anthropic",
            api_key="x",
            temperature=0.0,
            timeout=5,
        )
        self.assertTrue(client.supports_prompt_cache)


if __name__ == "__main__":
    unittest.main()
