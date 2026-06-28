# RepoPilot

RepoPilot 是一个面向本地代码仓库的智能开发助手。它运行在终端中，能够读取当前工作区、理解项目结构、调用受控工具执行搜索/读写/命令运行，并通过可恢复会话与分层记忆机制持续保留项目上下文。

它更适合用来完成“持续型代码工作”，例如排查测试失败、阅读陌生仓库、按项目约定修改代码、沉淀团队经验、连接外部工具，以及在多轮会话中接续上一次的开发状态。

---

## 目录

- [核心能力](#核心能力)
- [适用场景](#适用场景)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [运行机制概览](#运行机制概览)
- [环境要求](#环境要求)
- [安装方式](#安装方式)
- [模型配置](#模型配置)
- [快速开始](#快速开始)
- [CLI 参数说明](#cli-参数说明)
- [REPL 内置命令](#repl-内置命令)
- [记忆系统说明](#记忆系统说明)
- [Skill 系统](#skill-系统)
- [MCP 工具接入](#mcp-工具接入)
- [安全机制](#安全机制)
- [运行产物与审计](#运行产物与审计)
- [测试与质量检查](#测试与质量检查)
- [评测脚本](#评测脚本)
- [常见问题](#常见问题)
- [二次开发建议](#二次开发建议)
- [许可证](#许可证)

---

## 核心能力

RepoPilot 的目标不是只做一次性问答，而是成为可以在仓库里持续协作的本地代码 Agent。

主要能力包括：

- **工作区感知**：启动时读取 Git 状态、当前分支、近期提交、项目文档与仓库摘要。
- **受控工具调用**：支持列文件、读文件、全文搜索、运行命令、写文件、精确补丁修改等操作。
- **交互式 REPL**：可在终端内多轮对话，持续推进同一个开发任务。
- **一次性任务模式**：也可直接传入 prompt，让 Agent 执行单轮任务后退出。
- **多模型后端**：支持 DeepSeek、OpenAI 兼容接口、Anthropic 兼容接口与本地 Ollama。
- **分层记忆**：维护当前任务、近期文件、会话笔记、文件摘要与长期项目知识。
- **混合检索**：综合关键词、轻量语义向量、时效性和记忆强度召回上下文。
- **遗忘机制**：对过期、低价值或重复记忆进行衰减、合并与归档。
- **自反思巩固**：通过反思命令合并重复记忆、清理低价值记录、沉淀关键事实。
- **Skill 扩展**：将团队规范、仓库惯例、测试流程等知识沉淀为可复用技能。
- **MCP 扩展**：可接入外部 MCP server，将 filesystem、git、GitHub、fetch、sqlite 等能力接入工具系统。
- **安全审计**：高风险工具需要审批，敏感环境变量会脱敏，运行 trace 与 report 会落盘。

---

## 适用场景

RepoPilot 适合以下工作流：

1. **阅读陌生仓库**
   - 让 Agent 先梳理目录、核心模块、启动流程和测试方式。
   - 适合接手新项目、代码评审、重构前调研。

2. **排查测试失败**
   - Agent 可以读取 traceback、搜索相关实现、运行测试、提出修改方案。
   - 支持小步修改并复跑验证。

3. **持续开发任务**
   - 多轮会话中保留当前任务摘要、已读文件、关键决策和中间结论。
   - 支持恢复最近会话继续工作。

4. **沉淀项目知识**
   - 将“本仓库如何运行测试”“接口命名规范”“发布注意事项”等内容写成 Skill。
   - 后续任务中按需加载，不必每次重复说明。

5. **连接外部工具**
   - 通过 MCP 接入文件系统、Git、GitHub、数据库、网页抓取等外部能力。
   - 适合更复杂的工程自动化场景。

---

## 技术栈

- **语言**：Python 3.10+
- **运行方式**：命令行工具 / Python module
- **依赖管理**：支持 `uv`，也支持 `pip install -e .`
- **模型后端**：
  - DeepSeek
  - OpenAI-compatible API
  - Anthropic-compatible API
  - Ollama
- **测试工具**：
  - `unittest`
  - `pytest`
  - `ruff`
- **可选工具**：
  - `rg` / ripgrep：提升搜索速度
  - Node.js / npx：运行部分 MCP server
  - Ollama：运行本地模型

---

## 项目结构

推荐对外发布时使用如下结构命名：

```text
RepoPilot/
├── repopilot/
│   ├── cli/             # 命令行入口、参数解析、REPL
│   ├── config/          # .env 加载与 provider 配置读取
│   ├── core/            # Agent 控制循环、上下文管理、任务状态
│   ├── evaluation/      # 基准任务、评测指标与实验入口
│   ├── mcp/             # MCP server 配置、启动与工具注册
│   ├── memory/          # 分层记忆、遗忘、检索、自反思
│   ├── models/          # 模型客户端适配层
│   ├── skills/          # Skill 注册、发现与加载
│   ├── store/           # 会话与运行产物持久化
│   ├── tools/           # 内置工具白名单与执行逻辑
│   └── workspace/       # Git/文档/路径相关的工作区快照
├── benchmarks/          # 代码任务基准数据
├── docs/                # 架构、使用说明、优化记录等文档
├── scripts/             # 实验与指标采集脚本
├── tests/               # 单元测试与安全测试
├── .env.example         # 环境变量模板
├── pyproject.toml       # Python 项目配置
└── README.md
```

各层职责建议保持单向依赖：

```text
cli
 ↓
core
 ↓
memory / tools / skills / mcp
 ↓
models / workspace / config / store / evaluation
```

这样可以保证 CLI 只负责启动和装配，核心控制循环不直接绑定某个模型厂商，能力层之间也更容易测试与扩展。

---

## 运行机制概览

RepoPilot 的一次请求大致经历以下流程：

1. **加载项目环境**
   - 从当前仓库或上级目录查找 `.env`。
   - 读取模型 provider、API key、模型名、MCP 配置等。

2. **构建工作区快照**
   - 识别 Git 根目录、当前分支、默认分支、工作区状态。
   - 读取 README、项目配置等关键文档作为初始上下文。

3. **构建 Agent**
   - 初始化模型客户端。
   - 初始化会话存储、记忆系统、工具注册表、上下文管理器。
   - 按需加载 Skill 与 MCP 工具。

4. **模型决策**
   - 模型在系统提示、工作区摘要、记忆、工具说明的约束下生成响应。
   - 如果需要操作仓库，模型输出结构化工具调用。

5. **工具校验与执行**
   - 对路径、命令、读写范围、风险等级进行校验。
   - 高风险动作根据审批策略决定是否执行。

6. **记录与更新**
   - 保存工具结果、任务状态、trace、report。
   - 更新工作记忆、近期文件、会话笔记和可恢复状态。

7. **返回结果**
   - 当模型输出最终答案时，任务结束。
   - 用户可继续在同一 REPL 会话中追问，也可恢复会话继续工作。

---

## 环境要求

基础要求：

- Python >= 3.10
- Git
- 可访问至少一个模型后端

推荐安装：

```bash
pip install uv
```

可选安装：

```bash
# 更快的代码搜索
# macOS
brew install ripgrep

# Windows 可使用 winget
winget install BurntSushi.ripgrep.MSVC

# 本地模型
# 安装 Ollama 后拉取模型
ollama pull qwen3.5:4b
```

---

## 安装方式

### 方式一：使用 uv

```bash
uv sync
```

### 方式二：使用 pip 可编辑安装

```bash
pip install -e .
```

安装后建议确认命令是否可用：

```bash
repopilot --help
```

也可以使用 Python module 启动：

```bash
python -m repopilot --help
```

> 如果当前源码中的包名、命令名、环境变量前缀仍是历史命名，请在正式发布前同步改为 `repopilot` / `RepoPilot` / `REPOPILOT_` 风格，否则 README 中的命令需要根据实际代码调整。

---

## 模型配置

复制环境变量模板：

```bash
cp .env.example .env
```

然后按使用的 provider 填写对应配置。

### DeepSeek

```dotenv
REPOPILOT_DEEPSEEK_API_BASE=https://api.deepseek.com/anthropic
REPOPILOT_DEEPSEEK_API_KEY=your_api_key_here
REPOPILOT_DEEPSEEK_MODEL=deepseek-chat
```

启动：

```bash
repopilot --provider deepseek
```

### OpenAI 兼容接口

```dotenv
REPOPILOT_OPENAI_API_BASE=https://your-api.example/v1
REPOPILOT_OPENAI_API_KEY=your_api_key_here
REPOPILOT_OPENAI_MODEL=gpt-4.1
```

启动：

```bash
repopilot --provider openai
```

### Anthropic 兼容接口

```dotenv
REPOPILOT_ANTHROPIC_API_BASE=https://your-api.example/v1
REPOPILOT_ANTHROPIC_API_KEY=your_api_key_here
REPOPILOT_ANTHROPIC_MODEL=claude-sonnet-4
```

启动：

```bash
repopilot --provider anthropic
```

### Ollama 本地模型

先启动 Ollama：

```bash
ollama serve
```

拉取模型：

```bash
ollama pull qwen3.5:4b
```

启动：

```bash
repopilot --provider ollama --model qwen3.5:4b
```

---

## 快速开始

### 进入交互模式

在项目根目录运行：

```bash
repopilot
```

指定工作目录：

```bash
repopilot --cwd /path/to/your/repo
```

进入后可以直接输入任务，例如：

```text
请阅读这个仓库，告诉我它的启动方式和测试方式。
```

或：

```text
测试失败了，请先定位原因，再给出最小修改方案。
```

### 一次性任务模式

不进入 REPL，直接执行一条任务：

```bash
repopilot "阅读 README 和 pyproject.toml，概括这个项目的技术栈"
```

指定模型：

```bash
repopilot --provider openai --model gpt-4.1 "帮我分析 tests 目录下的失败用例"
```

恢复最近会话：

```bash
repopilot --resume latest
```

---

## CLI 参数说明

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `prompt` | 空 | 可选的一次性任务文本 |
| `--cwd` | `.` | 指定工作目录 |
| `--provider` | `deepseek` | 模型后端，可选 `ollama` / `openai` / `anthropic` / `deepseek` |
| `--model` | 根据 provider 决定 | 覆盖默认模型名 |
| `--host` | `http://127.0.0.1:11434` | Ollama 服务地址 |
| `--base-url` | 空 | OpenAI / Anthropic / DeepSeek 兼容接口 base URL |
| `--ollama-timeout` | `300` | Ollama 请求超时时间，单位秒 |
| `--openai-timeout` | `300` | 兼容接口请求超时时间，单位秒 |
| `--resume` | 空 | 指定会话 ID，或使用 `latest` 恢复最近会话 |
| `--approval` | `ask` | 高风险工具审批策略：`ask` / `auto` / `never` |
| `--no-mcp` | 关闭 | 本次启动不加载 MCP server |
| `--secret-env-name` | 可多次传入 | 额外指定需要脱敏的环境变量名 |
| `--max-steps` | `6` | 单次请求最多模型/工具迭代步数 |
| `--max-new-tokens` | `512` | 每步最大生成 token 数 |
| `--temperature` | `0.2` | 采样温度 |
| `--top-p` | `0.9` | top-p 采样参数 |

示例：

```bash
repopilot \
  --cwd ./my-project \
  --provider deepseek \
  --approval ask \
  --max-steps 8 \
  "修复当前失败的测试，并解释修改原因"
```

---

## REPL 内置命令

进入交互模式后，可使用以下命令：

| 命令 | 作用 |
|---|---|
| `/help` | 查看帮助信息 |
| `/memory` | 查看当前提炼后的工作记忆 |
| `/reflect` | 运行记忆反思与巩固流程 |
| `/skills` | 查看已安装的 Skill |
| `/session` | 查看当前会话文件路径 |
| `/reset` | 清空当前会话状态 |
| `/exit` | 退出 |
| `/quit` | 退出 |

---

## 记忆系统说明

RepoPilot 的记忆不是简单把聊天记录无限追加，而是分层管理、按需召回、定期清理。

### 1. 工作记忆

工作记忆保存当前任务的高频上下文，例如：

- 当前任务摘要
- 最近读过或修改过的文件
- 最近工具调用结果
- 当前会话中的关键中间结论

这部分内容会优先进入 prompt，帮助 Agent 在多轮任务中保持连续性。

### 2. 情节笔记

情节笔记记录会话中的阶段性事实，例如：

- 某个测试失败的根因
- 某个文件已经读过
- 某个方案被排除
- 某次命令运行结果有参考价值

情节笔记会携带时间、标签、类型和访问次数，用于后续排序与遗忘。

### 3. 文件摘要

对重要文件生成摘要时，会记录文件内容哈希。

如果文件内容发生变化，旧摘要会被判定为过期，从而避免 Agent 基于旧信息继续推理。

### 4. 长期记忆

长期记忆适合保存稳定信息，例如：

- 项目约定
- 关键架构决策
- 依赖事实
- 用户偏好
- 团队流程

建议将长期记忆保存在：

```text
.repopilot/memory/
├── MEMORY.md
└── topics/
    ├── project-conventions.md
    ├── key-decisions.md
    ├── dependency-facts.md
    └── user-preferences.md
```

### 5. 混合检索

当用户提出新问题时，RepoPilot 会从记忆中召回相关内容。召回分数综合考虑：

- 关键词匹配
- 轻量语义相似度
- 笔记新鲜度
- 记忆强度
- 标签命中
- 访问次数

这比单纯关键词搜索更适合处理“同义表达”“中英混合”“多轮上下文延续”等场景。

### 6. 遗忘与归档

每条记忆会随着时间衰减。

低价值、过期、重复或弱相关的笔记会被移出活跃工作集，并写入归档文件，而不是直接删除。这样既能控制上下文噪音，也保留必要的可恢复性。

---

## Skill 系统

Skill 用来沉淀可复用的项目知识。

一个 Skill 通常是一份 `SKILL.md` 文件，放在：

```text
.repopilot/skills/<skill-name>/SKILL.md
```

示例：

```markdown
---
name: run-tests
description: 在本仓库正确运行测试并定位失败用例
keywords: test, pytest, ci
---

当用户要求“跑测试”“修复测试失败”“检查 CI 失败”时使用本技能。

1. 先阅读项目文档，确认测试命令。
2. 优先运行最小测试范围。
3. 阅读失败 traceback。
4. 先判断是实现问题、测试问题还是环境问题。
5. 修改后复跑相关测试。
6. 输出修改原因、影响范围和验证结果。
```

Skill 的好处：

- 不必把全部团队规范塞进系统提示词。
- 启动时只加载 Skill 目录摘要。
- 需要时再加载具体 Skill 正文。
- 适合沉淀测试流程、发布流程、代码规范、仓库惯例。

---

## MCP 工具接入

RepoPilot 支持通过 MCP 接入外部工具。

在 `.env` 中配置：

```dotenv
REPOPILOT_MCP_SERVERS={"fs":{"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","."]}}
```

启动后，MCP server 暴露的工具会被注册到 Agent 的工具系统中。

常见可接入能力：

- filesystem：文件系统访问
- git：Git 操作
- github：Issue / PR / Repo 操作
- fetch：网页抓取
- sqlite：本地数据库查询

如果临时不希望启动 MCP：

```bash
repopilot --no-mcp
```

建议：

- 对不可信 MCP server 保持审批模式为 `ask`。
- 不要把敏感目录暴露给没有必要的 server。
- 给 MCP server 配置最小权限。
- 对写操作保留人工确认。

---

## 安全机制

RepoPilot 内置多层安全约束。

### 1. 路径逃逸防护

工具访问路径时会校验目标路径是否仍位于工作区内。

例如以下访问会被拒绝：

```text
../outside.txt
```

指向工作区外部的符号链接也会被拒绝。

### 2. 高风险工具审批

以下操作属于高风险：

- 运行 shell 命令
- 写文件
- 修改文件
- 调用外部 MCP 工具

审批策略：

| 策略 | 行为 |
|---|---|
| `ask` | 执行前询问用户确认 |
| `auto` | 自动执行 |
| `never` | 一律拒绝高风险动作 |

推荐日常使用：

```bash
repopilot --approval ask
```

在受控测试环境中可使用：

```bash
repopilot --approval auto
```

### 3. 敏感信息脱敏

RepoPilot 会对常见敏感环境变量进行脱敏，例如：

- API key
- token
- secret
- password
- 自定义传入的 secret env name

添加额外脱敏变量：

```bash
repopilot --secret-env-name GITHUB_TOKEN --secret-env-name INTERNAL_API_KEY
```

### 4. 子 Agent 只读约束

当主 Agent 委派子任务时，子 Agent 默认以受限只读方式运行，适合做并行调查、代码阅读、信息汇总，而不是直接修改仓库。

---

## 运行产物与审计

RepoPilot 会在本地状态目录中保存会话和运行产物：

```text
.repopilot/
├── sessions/
│   └── <session-id>.json
├── runs/
│   └── <run-id>/
│       ├── task_state.json
│       ├── trace.jsonl
│       └── report.json
├── memory/
└── skills/
```

### sessions

保存可恢复的会话状态，包括：

- 会话 ID
- 历史消息
- 当前工作记忆
- checkpoint 信息
- runtime 配置摘要

### runs

每次用户请求都会生成独立运行目录，便于复盘：

- `task_state.json`：任务状态机快照
- `trace.jsonl`：模型输出、工具调用、工具结果等事件流
- `report.json`：运行摘要、统计信息、错误信息、记忆变化等

这些文件适合用于：

- 调试 Agent 决策
- 复盘工具调用
- 分析失败任务
- 统计模型效果
- 采集实验指标

---

## 测试与质量检查

运行标准库单测：

```bash
python -m unittest tests.test_enhancements -v
```

运行全量测试：

```bash
uv run pytest -q
```

代码风格检查：

```bash
uv run ruff check .
```

建议在提交前运行：

```bash
uv run pytest -q
uv run ruff check .
```

---

## 评测脚本

项目包含实验脚本与 benchmark 数据，可用于评估 Agent 在代码任务上的表现。

常见脚本：

```bash
python scripts/run_provider_experiments.py
python scripts/run_large_scale_experiments.py
python scripts/collect_resume_metrics.py
```

建议将实验产物输出到 `artifacts/` 目录，并在报告中记录：

- provider
- model
- 任务数量
- 通过率
- 平均工具步数
- 平均尝试次数
- 失败类型分布
- 上下文压缩效果
- 记忆召回效果
- 恢复会话效果

---

## 常见问题

### 1. `repopilot` 命令找不到

先确认是否已安装：

```bash
pip install -e .
```

或使用：

```bash
uv sync
```

如果仍无法识别，使用 module 方式启动：

```bash
python -m repopilot
```

### 2. 模型连接失败

请检查：

- `.env` 是否存在
- API key 是否填写
- base URL 是否正确
- base URL 前后是否有隐藏空格、制表符或换行
- provider 是否与配置匹配
- 当前网络是否能访问模型服务

尤其注意：复制 URL 时不要把缩进一起复制进去。建议整行删除后手动重新输入。

### 3. 工具调用一直被拒绝

检查审批策略：

```bash
repopilot --approval ask
```

如果使用：

```bash
repopilot --approval never
```

所有写文件、运行命令等高风险操作都会被拒绝。

### 4. MCP server 启动失败

可以先禁用 MCP：

```bash
repopilot --no-mcp
```

再检查：

- Node.js / npx 是否安装
- MCP server 命令是否正确
- 当前目录是否有权限
- `.env` 中的 JSON 是否合法

### 5. Agent 读不到项目文档

确认启动目录是否正确：

```bash
repopilot --cwd /path/to/repo
```

RepoPilot 会优先从 Git 根目录和当前工作目录读取项目文档。建议在仓库根目录启动。

### 6. 记忆内容过多或变乱

可以在 REPL 中运行：

```text
/reflect
```

它会尝试合并重复记忆、归档低价值内容，并输出反思报告。

### 7. 如何继续上一次任务

使用：

```bash
repopilot --resume latest
```

如果要恢复指定会话，可以先在 REPL 中使用：

```text
/session
```

查看当前会话文件路径和 ID。

---

## 二次开发建议

如果你准备将 RepoPilot 作为正式项目发布，建议统一以下命名：

- Python 包名：`repopilot`
- CLI 命令：`repopilot`
- 状态目录：`.repopilot/`
- 环境变量前缀：`REPOPILOT_`
- 文档标题、截图文件名、示例命令统一使用 `RepoPilot`
- `pyproject.toml` 中的 `project.name` 与 `project.scripts` 同步更新
- 测试中的 import 路径同步更新
- README、USAGE、ARCHITECTURE 等文档同步更新
- CI、发布脚本、benchmark 输出路径同步更新

建议重命名后运行：

```bash
uv run pytest -q
uv run ruff check .
```

并检查是否还有历史命名残留：

```bash
rg -n "old_name|legacy_name" .
```

---

## 贡献指南

欢迎围绕以下方向改进 RepoPilot：

- 增强模型 provider 兼容性
- 优化上下文压缩策略
- 改进记忆召回排序
- 增加更多安全策略
- 增加 MCP server 示例
- 增加真实仓库 benchmark
- 改进 Windows / macOS / Linux 下的安装体验
- 补充更多 Skill 模板

建议提交 PR 前完成：

1. 说明改动动机。
2. 补充或更新测试。
3. 运行全量测试和风格检查。
4. 更新相关文档。
5. 确认不提交 API key、token、日志中的敏感信息。

---

## 许可证

请根据项目实际情况补充许可证信息。

如果该项目计划开源，建议在仓库根目录添加 `LICENSE` 文件，并在这里写明许可证名称，例如：

```text
MIT License
```

或：

```text
Apache License 2.0
```

---

## 一句话总结

RepoPilot 是一个具备工作区感知、受控工具调用、分层记忆、Skill 扩展、MCP 接入和审计能力的本地代码仓库智能助手，适合在真实工程项目中完成持续型代码协作任务。
