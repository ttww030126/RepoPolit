# mneme 使用说明

> `mneme` 是一个带类人记忆的本地 coding agent。本文覆盖安装、配置、日常用法、MCP 与 Skill 的接入，以及目录结构说明。

---

## 1. 环境要求

- Python 3.10+
- 可选：`uv`（推荐的依赖/运行管理器）、`rg`（ripgrep，加速代码搜索）、Ollama（本地模型）
- 运行时**零第三方依赖**（纯标准库），`pytest` / `ruff` 仅用于开发。

## 2. 安装

```bash
# 方式一：uv（推荐）
uv sync

# 方式二：当前 Python 环境，可编辑安装
pip install -e .
```

安装后会得到一个命令行命令 `mneme`，也可以用 `python -m mneme` 启动。

## 3. 配置模型后端

启动时会自动读取项目根目录的 `.env`。先复制模板：

```bash
cp .env.example .env
```

配置优先级：`显式 CLI 参数 > .env 里的 MNEME_* 变量 > 通用回退变量 > 代码默认值`。

### 默认：DeepSeek（推荐，已启用前缀缓存）

```dotenv
MNEME_DEEPSEEK_API_BASE=https://api.deepseek.com/anthropic
MNEME_DEEPSEEK_API_KEY=你的key
MNEME_DEEPSEEK_MODEL=deepseek-v4-pro
```

```bash
mneme                       # 默认 provider 即 deepseek
mneme "修复失败的测试并给出方案"   # 一次性任务
```

DeepSeek 走 Anthropic 兼容接口，多步任务会用 `cache_control` 复用「稳定前缀」（工具手册 + 工作区快照）的缓存，降低 token 成本与首 token 延迟。

### 其它后端

```bash
# Ollama（本地）
ollama serve && ollama pull qwen3.5:4b
mneme --provider ollama --model qwen3.5:4b

# OpenAI 兼容
mneme --provider openai

# Anthropic 兼容
mneme --provider anthropic
```

对应 `.env` 变量：`MNEME_OPENAI_*` / `MNEME_ANTHROPIC_*`。若多个兼容接口复用同一套 key，`mneme` 支持从 `MNEME_ANTHROPIC_API_KEY` 回退到 `ANTHROPIC_API_KEY` 等通用名。

## 4. 常用启动参数

```bash
mneme --cwd /path/to/repo          # 指定工作目录
mneme --approval ask|auto|never    # 高风险动作（写文件/跑命令）的审批策略
mneme --resume latest              # 恢复最近一次会话
mneme --no-mcp                     # 本次启动不拉起 MCP server
mneme --model <name> --base-url <url>
```

## 5. REPL 内置命令

| 命令 | 作用 |
|---|---|
| `/help` | 查看内置命令 |
| `/memory` | 查看提炼后的工作记忆（任务、最近文件、文件摘要、持久主题） |
| `/reflect` | 巩固记忆：去重合并 → 价值评估 → 遗忘扫描，输出报告并落盘 |
| `/skills` | 查看已安装技能目录 |
| `/session` | 查看当前会话文件路径 |
| `/reset` | 清空当前会话状态 |
| `/exit`、`/quit` | 退出 |

## 6. 记忆是怎么工作的

`mneme` 的记忆分多层，保存在 `.mneme/` 下：

- **工作记忆**：当前任务摘要 + 最近接触的文件。
- **情节笔记**：跨轮的小笔记，带 tag 与时间，并带**记忆强度**。
- **文件摘要**：用文件内容的 SHA256 做新鲜度校验，文件变了摘要自动失效。
- **持久记忆**：`MEMORY.md` + `topics/*.md`，长期事实按主题沉淀。

**遗忘引擎**：每条记忆的强度随时间指数衰减、随被检索命中而强化；强度跌破阈值且超龄会进入「归档」（移出工作集但写入 `.mneme/memory/archive.jsonl`，可恢复，不是删除）。

**混合检索**：召回时同时看「关键词命中 + 本地语义相似度 + 时效 + 记忆强度」的融合分数，支持中英混合，比纯字面匹配更能召回同义表达。

**自反思**：`/reflect` 会合并近似重复、淘汰低价值、归档过期记忆，让记忆随用随优。

> 想让某条信息进入**持久记忆**，在请求里带「记住 / 保存 / 记录 / 长期记忆」等意图词，并让最终答案以可识别的条目形式给出（详见 `core/runtime.py` 的提升规则）。

## 7. 接入 MCP（外部工具）

在 `.env` 里用一个 JSON 配置外部 MCP server：

```dotenv
MNEME_MCP_SERVERS={"fs":{"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","."]}}
```

- 启动时会自动拉起这些 server，把它们的工具注册成 `mcp__<server>__<tool>`。
- MCP 工具默认归为高风险（需审批），复用 `mneme` 既有的审批/脱敏/裁剪护栏。
- 单个 server 起不来不会拖垮 agent；`--no-mcp` 可一键关闭。

可接入的社区 server 很多：filesystem、git、github、fetch、sqlite 等。

## 8. 编写 Skill（沉淀团队知识）

技能就是一份带极简 frontmatter 的 Markdown，放在：

```
.mneme/skills/<slug>/SKILL.md
```

示例（`.mneme/skills/run-tests/SKILL.md`）：

```markdown
---
name: run-tests
description: 在本仓库正确运行测试并定位失败用例
keywords: test, pytest, ci
---
当用户要求“跑测试/修复测试失败”时使用本技能。
1. 先确认运行方式与测试目录。
2. 用 run_shell 执行测试命令。
3. 阅读失败 traceback，先读实现再决定改实现还是改测试。
```

- 启动时只把「技能目录」（名字 + 一句话）放进 prompt，成本极低（渐进式披露）。
- agent 需要时调用 `use_skill` 才把**正文**注入工作记忆并在后续轮次稳定召回。
- 仓库已内置 `run-tests`、`repo-conventions` 两个示例。

## 9. 安全与产物

- 高风险动作（`run_shell` / `write_file` / `patch_file` / MCP 调用）受审批模式控制。
- 子 agent（`delegate`）以只读、限步数运行，仅返回结论。
- shell 执行使用过滤后的环境变量，secret 形态文本会被脱敏。
- 每次运行在 `.mneme/runs/<run_id>/` 下产出 `task_state.json` / `trace.jsonl` / `report.json`，便于复盘缓存命中、工具调用、记忆变化。

## 10. 测试

```bash
# 新增能力的单测（纯标准库，无需安装任何东西）
python -m unittest tests.test_enhancements -v

# 全量（需要 pytest）
uv run pytest -q
# 代码风格
uv run ruff check .
```

## 11. 目录结构速查

```
mneme/
├── cli/app.py                 命令行入口、参数、REPL
├── core/
│   ├── runtime.py             控制循环 Mneme、SessionStore
│   ├── task_state.py          任务状态机
│   ├── context_manager.py     分段预算 / 上下文裁剪
│   └── enhancements.py        Skill/MCP 装配、/reflect 实现
├── memory/
│   ├── layered.py             分层记忆 LayeredMemory
│   ├── decay.py               遗忘引擎
│   ├── retrieval.py           混合检索
│   └── reflection.py          自反思巩固
├── models/clients.py          四类模型后端 + DeepSeek 缓存
├── tools/registry.py          工具白名单
├── skills/registry.py         技能加载
├── mcp/client.py              MCP stdio 客户端
├── workspace/context.py       仓库快照
├── config/env.py              .env 加载
├── store/run_store.py         运行工件落盘
└── evaluation/                基准与指标
```

跨层调用统一用绝对导入 `from mneme.<层> import ...`；每层的公共 API 在该层 `__init__.py` 里 re-export。

## 12. 改名说明（给二次开发者）

本项目由 `pico` 重构而来：完成了**分层目录拆分**与**全量改名**（包名 `mneme`、命令 `mneme`、核心类 `Mneme`、状态目录 `.mneme/`、环境变量前缀 `MNEME_`）。若要再次改名，主要集中在：`pyproject.toml` 的 `name`/`scripts`、各处 `MNEME_*` 环境变量名、`core/runtime.py` 的系统提示词与 `.mneme` 目录常量、`workspace/context.py` 的 `IGNORED_PATH_NAMES`。
