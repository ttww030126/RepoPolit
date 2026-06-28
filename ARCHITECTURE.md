# mneme 架构说明（ARCHITECTURE）

## 设计目标

把原本扁平的单层包，重构成**职责清晰、依赖单向、便于多人协作**的分层包，同时保持零运行时依赖与可测试性。

## 分层与依赖方向

依赖自上而下单向流动，下层不反向依赖上层：

```
                ┌─────────────┐
                │   cli/      │  接口层：参数解析、REPL、装配入口
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │   core/     │  核心层：控制循环 / 任务状态 / 上下文工程 / 能力装配
                └──────┬──────┘
        ┌──────────────┼───────────────┬──────────────┐
        ▼              ▼               ▼              ▼
   ┌─────────┐   ┌──────────┐    ┌─────────┐    ┌─────────┐
   │ memory/ │   │  tools/  │    │ skills/ │    │  mcp/   │   能力层
   └────┬────┘   └────┬─────┘    └────┬────┘    └────┬────┘
        └─────────────┴───────┬───────┴──────────────┘
                              ▼
        ┌──────────┬──────────┬──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
   │ models/│ │workspace│ │ config/│ │ store/ │ │evaluation│  基础/旁路层
   └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
```

- **接口层 `cli/`**：把命令行参数翻译成「运行现场」，再调用 `core`。不含业务逻辑。
- **核心层 `core/`**：`runtime.Mneme` 是总调度器（感知→决策→行动→记录的控制循环）；`task_state` 是状态机；`context_manager` 做分段预算与裁剪；`enhancements` 负责把 Skill/MCP 等能力装配到 agent 上。
- **能力层**：
  - `memory/`：分层记忆 + 遗忘 + 混合检索 + 自反思（本次升级的重点）。
  - `tools/`：受约束的动作白名单。
  - `skills/`：SKILL.md 渐进式披露。
  - `mcp/`：接入外部 MCP server。
- **基础/旁路层**：`models/`（后端适配）、`workspace/`（仓库快照）、`config/`（.env）、`store/`（工件落盘）、`evaluation/`（基准与指标）。

## 模块映射（重构前 → 重构后）

| 重构前（扁平 `pico/`） | 重构后（分层 `mneme/`） |
|---|---|
| `cli.py` | `cli/app.py` |
| `runtime.py` | `core/runtime.py` |
| `task_state.py` | `core/task_state.py` |
| `context_manager.py` | `core/context_manager.py` |
| `enhancements.py` | `core/enhancements.py` |
| `memory.py` | `memory/layered.py` |
| `memory_decay.py` | `memory/decay.py` |
| `retrieval.py` | `memory/retrieval.py` |
| `reflection.py` | `memory/reflection.py` |
| `models.py` | `models/clients.py` |
| `tools.py` | `tools/registry.py` |
| `skills.py` | `skills/registry.py` |
| `mcp.py` | `mcp/client.py` |
| `workspace.py` | `workspace/context.py` |
| `config.py` | `config/env.py` |
| `run_store.py` | `store/run_store.py` |
| `evaluator.py` | `evaluation/evaluator.py` |
| `metrics.py` | `evaluation/metrics.py` |

## 导入约定

- **跨层一律绝对导入**：`from mneme.memory import LayeredMemory`、`import mneme.tools as toolkit`。这样文件移动不会引发隐式相对路径错乱。
- **每层只暴露 `__init__.py` 里 re-export 的公共 API**，调用方不直接深入到具体文件，降低耦合。
- 顶层 `mneme/__init__.py` 额外暴露最常用的入口（`Mneme`、模型客户端、`main`）以及若干便捷别名（`memory_decay`、`reflection`、`retrieval`）。

## 命名约定（重构后）

| 维度 | 值 |
|---|---|
| 包名 / 命令 | `mneme` |
| 核心类 | `Mneme`（子 agent 别名 `MiniAgent`/`SubAgent`） |
| 状态目录 | `.mneme/`（`sessions/`、`runs/`、`memory/`、`skills/`） |
| 环境变量前缀 | `MNEME_`（保留通用回退名如 `OPENAI_API_KEY`） |

## 为什么这样分

1. **可读性**：新人看目录就能猜到「记忆相关去 `memory/`，工具相关去 `tools/`」。
2. **可演进**：要加知识图谱或真 embedding，只在 `memory/` 里加文件，不动其它层。
3. **可测试**：能力层彼此解耦，单测可以只针对某一层（如 `tests/test_enhancements.py` 只测记忆/技能/MCP）。
4. **可协作**：多人分别负责不同层时冲突更少。
