# RepoPilot

RepoPilot 是一个运行在本地代码仓库中的命令行智能开发助手。它可以读取项目文件、检索代码、运行受控命令、写入或补丁修改文件，并在多轮会话中保存任务上下文，帮助开发者完成代码阅读、问题定位、测试修复、项目改造和工程知识沉淀。

本项目当前采用**扁平模块结构**：核心代码集中在 `RepoPilot/*.py` 文件中。README 中的项目结构也按当前代码组织方式描述。

---

## 目录

- [功能特点](#功能特点)
- [适用场景](#适用场景)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [核心模块说明](#核心模块说明)
- [工作流程](#工作流程)
- [环境要求](#环境要求)
- [安装](#安装)
- [模型配置](#模型配置)
- [快速开始](#快速开始)
- [CLI 参数](#cli-参数)
- [REPL 内置命令](#repl-内置命令)
- [内置工具](#内置工具)
- [记忆机制](#记忆机制)
- [Skill 扩展](#skill-扩展)
- [MCP 扩展](#mcp-扩展)
- [安全机制](#安全机制)
- [运行产物](#运行产物)
- [测试](#测试)
- [评测与实验](#评测与实验)
- [常见问题](#常见问题)
- [开发者注意事项](#开发者注意事项)
- [许可证](#许可证)

---

## 功能特点

RepoPilot 的目标是让 AI 能够在本地仓库中进行可控、可审计、可恢复的开发协作。

主要能力包括：

- **代码仓库感知**：启动后读取当前工作区、Git 状态、项目文档和关键配置文件。
- **交互式开发助手**：支持终端 REPL 多轮对话，适合持续推进一个开发任务。
- **一次性任务模式**：可以直接传入 prompt，完成单轮分析或修改任务。
- **受控工具调用**：支持列目录、读文件、搜索、运行命令、写文件、精确补丁修改。
- **多模型后端**：支持 Ollama、本地模型、OpenAI 兼容接口、Anthropic 兼容接口和 DeepSeek。
- **上下文记忆**：保存当前任务摘要、最近文件、情节笔记、文件摘要和持久主题。
- **混合召回**：结合关键词、本地语义、时间因素和记忆强度召回相关上下文。
- **遗忘与归档**：对低价值、过期或重复的记忆进行衰减和归档，减少上下文噪声。
- **Skill 机制**：把测试流程、团队规范、项目惯例沉淀为可复用技能。
- **MCP 接入**：可以把外部 MCP server 暴露的能力注册为工具。
- **安全审批**：运行命令、写文件、外部工具调用等高风险行为可要求人工确认。
- **运行审计**：每次请求生成 trace、report 和任务状态文件，便于复盘和调试。

---

## 适用场景

RepoPilot 适合以下任务：

1. **阅读陌生项目**

   - 梳理目录结构、启动方式、核心模块和测试命令。
   - 适合接手项目、代码审查、重构前调研。

2. **排查测试失败**

   - 根据 traceback 搜索相关代码。
   - 读取实现与测试文件。
   - 给出最小修改方案并复跑测试。

3. **持续开发任务**

   - 在多轮对话中保留任务状态。
   - 支持恢复最近会话继续处理未完成任务。

4. **仓库自动化操作**

   - 执行受控 shell 命令。
   - 写入文件或做精确文本替换。
   - 记录每一步操作结果。

5. **团队知识沉淀**

   - 将项目约定、测试方式、发布流程写成 Skill。
   - 后续任务中按需加载，不必反复说明。

6. **外部工具扩展**
   - 通过 MCP 接入文件系统、Git、网页抓取、数据库或其他工具服务。
   - 适合更复杂的本地开发自动化场景。

---

## 技术栈

- **语言**：Python 3.10+
- **运行方式**：命令行工具 / Python module
- **依赖管理**：支持 `uv`，也支持 `pip install -e .`
- **模型后端**：
  - Ollama
  - OpenAI-compatible API
  - Anthropic-compatible API
  - DeepSeek
- **测试工具**：
  - `pytest`
  - `unittest`
  - `ruff`
- **可选工具**：
  - `ripgrep`：提升代码搜索速度
  - Node.js / npx：运行部分 MCP server
  - Ollama：运行本地大模型

---

## 项目结构

当前项目是扁平模块结构，核心 Python 文件直接位于 `RepoPilot/` 包目录下：

```text
RepoPilot/
├── RepoPilot/
│   ├── __init__.py              # 对外导出核心对象
│   ├── __main__.py              # python -m 启动入口
│   ├── cli.py                   # 命令行参数解析、REPL、Agent 装配
│   ├── config.py                # .env 加载和环境变量读取
│   ├── context_manager.py       # 上下文预算、压缩和提示词片段管理
│   ├── enhancements.py          # Skill、MCP 等增强能力装配
│   ├── evaluator.py             # benchmark 评测入口和任务执行器
│   ├── mcp.py                   # MCP server 管理和工具桥接
│   ├── memory.py                # 记忆状态、文件摘要、持久主题和召回视图
│   ├── memory_decay.py          # 记忆强度衰减、生命周期和归档策略
│   ├── metrics.py               # 指标聚合、实验报告和评测统计
│   ├── models.py                # Ollama / OpenAI / Anthropic / DeepSeek 模型客户端
│   ├── retrieval.py             # 关键词 + 本地语义的混合检索
│   ├── runtime.py               # Agent 主循环、会话恢复、工具调度和审计记录
│   ├── run_store.py             # 单次运行产物保存
│   ├── skills.py                # Skill 发现、解析和工具注册
│   ├── task_state.py            # 任务状态机和停止原因
│   ├── tools.py                 # 内置工具定义、校验和执行逻辑
│   └── workspace.py             # 工作区快照、Git 状态、路径裁剪和输出裁剪
├── benchmarks/
│   └── coding_tasks.json        # 代码任务 benchmark 数据
├── docs/
│   ├── ARCHITECTURE.md          # 架构说明
│   ├── USAGE.md                 # 使用说明
│   ├── architecture/
│   └── review-pack/
├── scripts/
│   ├── collect_resume_metrics.py
│   ├── run_large_scale_experiments.py
│   └── run_provider_experiments.py
├── tests/
│   ├── fixtures/
│   ├── test_context_manager.py
│   ├── test_enhancements.py
│   ├── test_evaluator.py
│   ├── test_memory.py
│   ├── test_metrics.py
│   ├── test_repopilot.py
│   ├── test_run_store.py
│   ├── test_safety_invariants.py
│   └── test_task_state.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## 核心模块说明

### `cli.py`

负责命令行入口：

- 解析 `--provider`、`--model`、`--cwd`、`--approval` 等参数。
- 加载 `.env`。
- 构建模型客户端。
- 构建或恢复会话。
- 进入一次性任务模式或 REPL 交互模式。

### `runtime.py`

这是 Agent 的核心运行时，负责：

- 组织系统提示词、上下文和工具说明。
- 调用模型生成下一步响应。
- 解析模型输出中的工具调用。
- 执行工具校验和审批。
- 记录 trace、report、task state。
- 保存和恢复 session。
- 维护当前任务上下文。

### `tools.py`

定义内置工具，包括：

- `list_files`
- `read_file`
- `search`
- `run_shell`
- `write_file`
- `patch_file`
- `delegate`

工具在执行前会经过参数校验、路径校验和风险判断。高风险工具受审批策略控制。

### `models.py`

封装不同模型后端：

- `OllamaModelClient`
- `OpenAICompatibleModelClient`
- `AnthropicCompatibleModelClient`
- `FakeModelClient`

DeepSeek 通过 Anthropic 兼容接口接入。

### `memory.py`

维护项目记忆状态，包括：

- 当前任务摘要
- 最近访问文件
- 情节笔记
- 文件摘要
- 持久主题
- 相关记忆召回视图

### `memory_decay.py`

负责记忆生命周期管理：

- 根据时间和访问情况计算记忆强度。
- 标记 active、dormant、archived 等阶段。
- 对低价值记忆做归档处理。

### `retrieval.py`

实现本地混合检索：

- 关键词 token 匹配。
- 轻量向量嵌入。
- 余弦相似度。
- 时间新鲜度。
- 综合分数排序。

### `skills.py`

负责 Skill 管理：

- 扫描 `.repopilot/skills/`。
- 解析 `SKILL.md` frontmatter。
- 提供 `list_skills` 和 `use_skill` 工具。
- 支持渐进式加载 Skill 正文。

### `mcp.py`

负责 MCP 接入：

- 读取 MCP server 配置。
- 启动外部 MCP 进程。
- 注册 MCP 工具。
- 将外部工具结果返回给 Agent。

### `workspace.py`

负责工作区信息：

- 识别仓库根目录。
- 获取 Git 状态。
- 读取项目文档。
- 限制工具输出长度。
- 处理路径裁剪和安全路径解析。

### `run_store.py`、`task_state.py`、`metrics.py`

负责运行记录和指标：

- 保存每次请求的运行状态。
- 记录停止原因。
- 聚合 benchmark 和运行指标。
- 生成实验报告。

---

## 工作流程

RepoPilot 的一次请求大致如下：

1. **启动程序**

   - 用户运行 `repopilot` 或 `python -m RepoPilot`。
   - CLI 解析参数并加载 `.env`。

2. **构建工作区上下文**

   - 识别当前工作目录。
   - 读取 Git 状态和项目文档。
   - 初始化 `.repopilot/` 状态目录。

3. **初始化模型和工具**

   - 根据 provider 创建模型客户端。
   - 注册内置工具。
   - 按需加载 Skill 和 MCP 工具。

4. **生成提示词**

   - 拼接系统规则、工作区摘要、记忆内容、工具说明和用户任务。

5. **模型决策**

   - 模型可以直接回答，也可以输出工具调用。
   - 工具调用以受控格式被解析。

6. **工具执行**

   - 安全工具直接执行。
   - 高风险工具根据审批策略决定是否执行。
   - 执行结果返回给模型继续推理。

7. **记录运行产物**

   - 保存任务状态。
   - 保存 trace 日志。
   - 保存运行报告。

8. **返回最终答案**
   - 当模型给出最终回答或达到步数限制时，本轮任务结束。
   - REPL 模式下可继续输入下一条任务。

---

## 环境要求

基础要求：

- Python 3.10+
- Git
- 可访问至少一个模型服务

推荐工具：

```bash
pip install uv
```

可选工具：

```bash
# macOS
brew install ripgrep

# Windows
winget install BurntSushi.ripgrep.MSVC
```

如果使用本地模型，需要安装并启动 Ollama：

```bash
ollama serve
```

---

## 安装

### 使用 uv

```bash
uv sync
```

### 使用 pip

```bash
pip install -e .
```

安装完成后查看帮助：

```bash
repopilot --help
```

如果当前环境还没有安装命令行入口，也可以使用 module 方式启动：

```bash
python -m RepoPilot --help
```

> 建议正式发布前确认 `pyproject.toml` 中的项目名、命令行入口和包发现规则已经统一为 RepoPilot 对应配置。

---

## 模型配置

复制环境变量模板：

```bash
cp .env.example .env
```

Windows PowerShell 可使用：

```powershell
Copy-Item .env.example .env
```

然后按使用的 provider 填写配置。

### DeepSeek

```dotenv
REPOPILOT_DEEPSEEK_API_BASE=https://api.deepseek.com/anthropic
REPOPILOT_DEEPSEEK_API_KEY=your_api_key_here
REPOPILOT_DEEPSEEK_MODEL=deepseek-v4-pro
```

启动：

```bash
repopilot --provider deepseek
```

### OpenAI 兼容接口

```dotenv
REPOPILOT_OPENAI_API_BASE=https://your-api.example/v1
REPOPILOT_OPENAI_API_KEY=your_api_key_here
REPOPILOT_OPENAI_MODEL=gpt-5.4
```

启动：

```bash
repopilot --provider openai
```

### Anthropic 兼容接口

```dotenv
REPOPILOT_ANTHROPIC_API_BASE=https://your-api.example/v1
REPOPILOT_ANTHROPIC_API_KEY=your_api_key_here
REPOPILOT_ANTHROPIC_MODEL=claude-sonnet-4-6
```

启动：

```bash
repopilot --provider anthropic
```

### Ollama

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

进入 REPL 后可以输入：

```text
请阅读这个项目，告诉我它的启动方式、核心模块和测试命令。
```

或者：

```text
测试失败了，请定位原因，并给出最小修改方案。
```

### 一次性任务模式

```bash
repopilot "阅读 README 和 pyproject.toml，总结这个项目的技术栈"
```

指定模型后端：

```bash
repopilot --provider deepseek "帮我分析 tests 目录下的测试覆盖范围"
```

恢复最近会话：

```bash
repopilot --resume latest
```

使用更严格的审批策略：

```bash
repopilot --approval ask
```

---

## CLI 参数

| 参数                |                   默认值 | 说明                                                          |
| ------------------- | -----------------------: | ------------------------------------------------------------- |
| `prompt`            |                       空 | 可选的一次性任务文本                                          |
| `--cwd`             |                      `.` | 指定工作目录                                                  |
| `--provider`        |                 `openai` | 模型后端，可选 `ollama` / `openai` / `anthropic` / `deepseek` |
| `--model`           |       根据 provider 决定 | 覆盖默认模型名                                                |
| `--host`            | `http://127.0.0.1:11434` | Ollama 服务地址                                               |
| `--base-url`        |                       空 | OpenAI / Anthropic / DeepSeek 兼容接口地址                    |
| `--ollama-timeout`  |                    `300` | Ollama 请求超时时间，单位秒                                   |
| `--openai-timeout`  |                    `300` | 兼容接口请求超时时间，单位秒                                  |
| `--resume`          |                       空 | 指定会话 ID，或使用 `latest` 恢复最近会话                     |
| `--approval`        |                    `ask` | 高风险工具审批策略：`ask` / `auto` / `never`                  |
| `--secret-env-name` |               可多次传入 | 额外指定需要脱敏的环境变量名                                  |
| `--no-mcp`          |                     关闭 | 本次运行不启动 MCP server                                     |
| `--max-steps`       |                      `6` | 单次请求最多模型/工具迭代步数                                 |
| `--max-new-tokens`  |                    `512` | 每步最大生成 token 数                                         |
| `--temperature`     |                    `0.2` | 采样温度                                                      |
| `--top-p`           |                    `0.9` | top-p 采样参数                                                |

示例：

```bash
repopilot \
  --cwd ./your-project \
  --provider deepseek \
  --approval ask \
  --max-steps 8 \
  "修复当前失败的测试，并说明修改原因"
```

---

## REPL 内置命令

进入交互模式后，可以使用以下命令：

| 命令       | 作用                     |
| ---------- | ------------------------ |
| `/help`    | 查看帮助                 |
| `/memory`  | 查看当前提炼后的工作记忆 |
| `/skills`  | 查看已安装 Skill         |
| `/session` | 查看当前会话文件路径     |
| `/reset`   | 清空当前会话历史和记忆   |
| `/exit`    | 退出                     |
| `/quit`    | 退出                     |

当前版本不包含记忆反思命令。

---

## 内置工具

RepoPilot 提供一组明确边界的内置工具：

| 工具                    | 风险等级 | 说明                                         |
| ----------------------- | -------- | -------------------------------------------- |
| `list_files`            | 安全     | 列出工作区内目录                             |
| `read_file`             | 安全     | 按行读取 UTF-8 文本文件                      |
| `search`                | 安全     | 在工作区中搜索文本，有 `ripgrep` 时优先使用  |
| `run_shell`             | 高风险   | 在仓库根目录执行 shell 命令                  |
| `write_file`            | 高风险   | 写入或覆盖文本文件                           |
| `patch_file`            | 高风险   | 使用精确 `old_text -> new_text` 替换文件片段 |
| `delegate`              | 安全     | 派生只读子 Agent 调查子任务                  |
| `list_skills`           | 安全     | 列出 Skill                                   |
| `use_skill`             | 安全     | 加载指定 Skill                               |
| `mcp__<server>__<tool>` | 高风险   | 由 MCP server 暴露的外部工具                 |

`patch_file` 的替换规则比较严格：`old_text` 必须在目标文件中**只出现一次**。这可以避免误改多个位置，让修改更可控。

---

## 记忆机制

RepoPilot 会在 `.repopilot/` 中维护本地记忆，帮助 Agent 在多轮任务中保持连续性。

### 当前任务摘要

记录当前正在处理的任务，例如：

```text
正在定位测试失败原因，重点关注 runtime.py 和 tools.py。
```

### 最近文件

记录最近读取或修改过的文件，方便后续继续引用。

### 情节笔记

记录会话中发生过的关键事实，例如：

- 某个测试失败的直接原因。
- 某个命令已经运行过。
- 某个实现方案被排除。
- 某个文件摘要已经过期。

### 文件摘要

对重要文件保存摘要和内容哈希。

当文件内容变化时，旧摘要会被识别为不新鲜，减少基于旧代码继续推理的风险。

### 持久主题

适合保存稳定信息，例如：

- 项目运行方式
- 测试命令
- 代码规范
- 用户偏好
- 关键架构约定

### 记忆召回

当用户提出新任务时，RepoPilot 会根据当前问题召回相关记忆。召回会综合：

- 关键词匹配
- 本地语义相似度
- 时间新鲜度
- 记忆强度
- 标签匹配
- 访问次数

### 记忆归档

长期未使用、价值较低或强度衰减的记忆会被归档，避免污染当前上下文。

---

## Skill 扩展

Skill 用于沉淀可复用的项目经验。

推荐目录：

```text
.repopilot/
└── skills/
    └── run-tests/
        └── SKILL.md
```

示例：

```markdown
---
name: run-tests
description: 在本仓库正确运行测试并定位失败用例
keywords: test, pytest, ci
---

当用户要求“跑测试”“修复测试失败”“检查 CI 失败”时使用本技能。

1. 先确认测试命令。
2. 优先运行最小测试范围。
3. 阅读失败 traceback。
4. 判断是实现问题、测试问题还是环境问题。
5. 修改后复跑相关测试。
6. 输出修改原因、影响范围和验证结果。
```

Skill 的加载方式是渐进式的：

1. 启动时只读取 Skill 名称和简介。
2. Agent 判断需要时调用 `use_skill`。
3. Skill 正文进入当前上下文。
4. 后续轮次可以通过记忆召回继续使用。

---

## MCP 扩展

RepoPilot 支持接入 MCP server。

在 `.env` 中配置：

```dotenv
REPOPILOT_MCP_SERVERS={"fs":{"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","."]}}
```

启动后，MCP 工具会注册为：

```text
mcp__<server>__<tool>
```

例如：

```text
mcp__fs__read_file
```

禁用 MCP：

```bash
repopilot --no-mcp
```

建议：

- 只接入可信 MCP server。
- 给 MCP server 最小必要权限。
- 对写操作保持 `--approval ask`。
- 不要把敏感目录暴露给不需要的工具。

---

## 安全机制

RepoPilot 的安全策略集中在路径、命令、审批和脱敏四个方面。

### 路径限制

所有文件操作都会限制在工作区内。

以下路径访问会被拒绝：

```text
../outside.txt
```

指向工作区外部的符号链接也会被拒绝。

### 高风险审批

高风险工具包括：

- `run_shell`
- `write_file`
- `patch_file`
- MCP 外部工具

审批策略：

| 策略    | 行为               |
| ------- | ------------------ |
| `ask`   | 执行前询问确认     |
| `auto`  | 自动执行           |
| `never` | 一律拒绝高风险动作 |

推荐日常使用：

```bash
repopilot --approval ask
```

### shell 环境过滤

运行 shell 命令时，只传入允许的环境变量，避免把敏感变量意外暴露给命令或日志。

### 敏感信息脱敏

RepoPilot 会对常见敏感字段脱敏，例如：

- API key
- token
- secret
- password

也可以手动指定额外脱敏变量：

```bash
repopilot --secret-env-name GITHUB_TOKEN --secret-env-name INTERNAL_API_KEY
```

### 子 Agent 限制

`delegate` 工具派生的子 Agent 默认只用于有限步数的调查任务，不应直接承担高风险写操作。

---

## 运行产物

RepoPilot 会把会话和每次请求的运行产物保存在 `.repopilot/` 下：

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

### `sessions/`

保存可恢复会话，包括：

- session id
- 历史消息
- 工作记忆
- checkpoint
- runtime 配置摘要

### `runs/`

每次用户请求会生成独立运行目录：

- `task_state.json`：任务状态机快照
- `trace.jsonl`：模型输出、工具调用、工具结果等事件流
- `report.json`：运行摘要、错误信息、统计信息和记忆变化

这些文件适合用于：

- 调试模型决策
- 复盘工具调用
- 分析失败任务
- 统计模型表现
- 采集实验指标

---

## 测试

运行全量测试：

```bash
uv run pytest -q
```

运行代码风格检查：

```bash
uv run ruff check .
```

也可以使用标准库单测入口运行部分测试：

```bash
python -m unittest discover tests
```

建议提交前执行：

```bash
uv run pytest -q
uv run ruff check .
```

---

## 评测与实验

项目包含 benchmark、评测器和指标聚合脚本。

### 运行 provider 实验

```bash
python scripts/run_provider_experiments.py
```

### 运行大规模实验

```bash
python scripts/run_large_scale_experiments.py
```

### 收集恢复会话指标

```bash
python scripts/collect_resume_metrics.py
```

评测通常会关注：

- 任务完成率
- 测试通过率
- 平均工具调用步数
- 失败停止原因
- 上下文召回效果
- 记忆噪声影响
- 会话恢复效果
- 安全场景拦截情况

---

## 常见问题

### 1. `repopilot` 命令找不到

先确认已安装项目：

```bash
pip install -e .
```

或者：

```bash
uv sync
```

如果仍无法识别，可尝试：

```bash
python -m RepoPilot
```

如果 module 方式可用但命令不可用，通常是 `pyproject.toml` 中的命令行入口还没有同步，或当前虚拟环境没有激活。

### 2. 模型连接失败

请检查：

- `.env` 是否存在。
- API key 是否填写。
- base URL 是否正确。
- base URL 前后是否有空格、制表符或换行。
- provider 是否和环境变量匹配。
- 当前网络是否能访问模型服务。

尤其注意：复制 URL 时不要把缩进一起复制进去。建议整行删除后手动重新输入。

### 3. 高风险工具不执行

检查审批策略：

```bash
repopilot --approval ask
```

如果使用：

```bash
repopilot --approval never
```

那么运行命令、写文件和补丁修改都会被拒绝。

### 4. 搜索速度慢

建议安装 `ripgrep`。

安装后，`search` 工具会优先使用 `rg`，搜索速度会明显提升。

### 5. MCP server 启动失败

可以先禁用 MCP：

```bash
repopilot --no-mcp
```

再检查：

- Node.js 是否安装。
- `npx` 是否可用。
- `.env` 中的 JSON 是否合法。
- MCP server 命令是否正确。
- 当前目录是否有权限。

### 6. 如何恢复上次任务

使用：

```bash
repopilot --resume latest
```

也可以在 REPL 中输入：

```text
/session
```

查看当前 session 文件路径。

### 7. 文件修改失败，提示 `old_text must occur exactly once`

这是 `patch_file` 的保护机制。

解决方式：

- 让 `old_text` 包含更多上下文。
- 确保目标片段只出现一次。
- 或改用 `write_file` 写入完整文件。

---

## 开发者注意事项

### 统一项目命名

为了让安装、导入和命令行入口一致，建议检查：

```toml
[project]
name = "RepoPilot"

[project.scripts]
repopilot = "RepoPilot.cli:main"

[tool.setuptools.packages.find]
include = ["RepoPilot*"]
```

如果你希望 Python 包名使用小写，也可以把包目录统一调整为：

```text
repopilot/
```

并同步更新：

```toml
[project.scripts]
repopilot = "repopilot.cli:main"

[tool.setuptools.packages.find]
include = ["repopilot*"]
```

两种方式选一种即可，关键是包目录、import 路径、命令入口和测试用例保持一致。

### 发布前检查

建议发布前运行：

```bash
uv run pytest -q
uv run ruff check .
```

检查是否还有历史命名残留：

```bash
rg -n "legacy|old project name|old package name" .
```

检查是否误提交敏感信息：

```bash
rg -n "api_key|token|secret|password|sk-" .
```

### Windows 注意事项

PowerShell 中复制命令时，注意不要把提示符或额外前缀一起复制进去。

例如应输入：

```powershell
git remote add origin git@github.com:your-name/RepoPilot.git
```

不要输入多余的前缀。

---

## 许可证

请根据项目实际情况补充许可证信息。

如果计划开源，建议在仓库根目录添加 `LICENSE` 文件，并在这里写明许可证名称，例如：

```text
MIT License
```

或：

```text
Apache License 2.0
```

---

## 一句话总结

RepoPilot 是一个面向本地代码仓库的命令行智能开发助手，采用扁平模块结构实现模型调用、工具执行、上下文记忆、Skill 扩展、MCP 接入、安全审批和运行审计，适合在真实工程项目中完成持续型代码协作任务。
