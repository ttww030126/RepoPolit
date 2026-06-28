"""Skill 系统：可插拔的“专家手册”。

借鉴 Claude Skills / SKILL.md 的渐进式披露（progressive disclosure）思路：
mneme 默认 prompt 只放“技能目录”（名字 + 一句话描述）这种低成本元信息，
只有当 agent 主动 use_skill 时，才把对应技能的完整正文注入到工作记忆里。

这样做的价值：
- 把领域知识/团队规范/操作手册和核心 agent 逻辑解耦，新增能力无需改代码；
- 控制上下文成本：不会一上来就把所有手册塞进 prompt；
- 让“这个仓库该怎么改”这种隐性知识沉淀成可版本化的 .md 文件。

技能目录结构：
    .mneme/skills/<slug>/SKILL.md

SKILL.md 顶部用极简 YAML-ish frontmatter 声明元信息：
    ---
    name: run-tests
    description: 在本仓库里正确地运行与定位失败的测试
    keywords: test, pytest, ci
    ---
    <正文：何时使用、步骤、注意事项>
"""

import re
from pathlib import Path

SKILLS_DIRNAME = "skills"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


def _parse_frontmatter(text):
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta_block, body = match.group(1), match.group(2)
    meta = {}
    for line in meta_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip()
    return meta, body.strip()


class Skill:
    def __init__(self, slug, name, description, keywords, body, path):
        self.slug = slug
        self.name = name
        self.description = description
        self.keywords = keywords
        self.body = body
        self.path = path

    def matches(self, query):
        haystack = " ".join([self.name, self.description, " ".join(self.keywords)]).lower()
        return any(token in haystack for token in re.findall(r"[a-z0-9]+", query.lower()))


class SkillRegistry:
    def __init__(self, root):
        # root 是 .mneme 目录（与 memory/runs 同级）
        self.skills_dir = Path(root) / SKILLS_DIRNAME
        self.skills = {}

    def discover(self):
        self.skills = {}
        if not self.skills_dir.exists():
            return self.skills
        for skill_md in sorted(self.skills_dir.glob("*/SKILL.md")):
            slug = skill_md.parent.name
            try:
                text = skill_md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, body = _parse_frontmatter(text)
            keywords = [
                token.strip()
                for token in meta.get("keywords", "").split(",")
                if token.strip()
            ]
            self.skills[slug] = Skill(
                slug=slug,
                name=meta.get("name", slug),
                description=meta.get("description", ""),
                keywords=keywords,
                body=body,
                path=str(skill_md),
            )
        return self.skills

    def catalog_text(self):
        """低成本技能目录，注入 prompt prefix。只暴露名字与一句话描述。"""
        if not self.skills:
            return ""
        lines = ["Available skills (call use_skill to load full instructions):"]
        for slug, skill in self.skills.items():
            lines.append(f"- {slug}: {skill.description or skill.name}")
        return "\n".join(lines)

    def get(self, slug):
        return self.skills.get(slug)

    def suggest(self, query, limit=3):
        hits = [skill for skill in self.skills.values() if skill.matches(query)]
        return hits[:limit]


# ---- 注册成 mneme 工具 -------------------------------------------------------

LIST_SKILLS_SPEC = {
    "schema": {},
    "risky": False,
    "description": "List skill modules available in this repository.",
}

USE_SKILL_SPEC = {
    "schema": {"slug": "str"},
    "risky": False,
    "description": "Load the full instructions of a skill into working memory.",
}


def build_skill_tools(registry):
    """返回可直接并入 runtime 工具注册表的 {name: spec}。

    use_skill 会把技能正文写入 agent.memory 的一条高重要度 note，
    从而被后续 prompt 的“相关记忆”召回，实现按需注入。
    """

    def run_list(agent, args):  # noqa: ARG001
        text = registry.catalog_text()
        return text or "(no skills installed; create .mneme/skills/<name>/SKILL.md)"

    def run_use(agent, args):
        slug = str((args or {}).get("slug", "")).strip()
        if not slug:
            raise ValueError("slug must not be empty")
        skill = registry.get(slug)
        if skill is None:
            raise ValueError(f"unknown skill: {slug}")
        memory = getattr(agent, "memory", None)
        if memory is not None and hasattr(memory, "append_note"):
            # importance 调高，确保后续轮次能稳定召回这条技能指令
            memory.append_note(
                f"[skill:{slug}] {skill.body}",
                tags=["skill", slug, *skill.keywords],
                source=f"skill:{slug}",
                kind="durable",
            )
        return f"# Skill loaded: {skill.name}\n\n{skill.body}"

    return {
        "list_skills": {**LIST_SKILLS_SPEC, "run": run_list},
        "use_skill": {**USE_SKILL_SPEC, "run": run_use},
    }
