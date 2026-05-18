<div align="center">
  <img src="assets/readme/nexus-banner.svg" alt="Nexus banner" width="100%" />
</div>

> 🧠 这是一个 Vibe Coding project: Built with AI, for AI-augmented development.

![License](https://img.shields.io/badge/License-MIT-F2C94C)
![Version](https://img.shields.io/badge/Version-v1.0.0-2D9CDB)
![Python](https://img.shields.io/badge/Python-%3E%3D3.10-27AE60)

[English](README.en.md) | **中文**

## Nexus 是什么

`Nexus Skill / Plugin 1.0` 是一个面向外部用户发布的长期记忆 Skill / Plugin 入口。

它的目标很直接：让 Agent 和 AI 工作流把有价值的信息沉淀为可检索、可注入、可反馈、可维护的长期记忆，而不是把上下文消耗在一次性对话里。

当前公开主线是：

`extract -> store -> retrieve -> inject -> feedback -> maintain`

## 核心能力

<div align="center">
  <img src="assets/readme/memory-flow.svg" alt="Nexus memory flow" width="100%" />
</div>

Nexus 1.0 当前聚焦六类公开能力：

1. `extract`
   从对话、任务描述、文档片段中提取有价值的长期记忆。
2. `retrieve / search`
   在新任务到来时检索相关记忆。
3. `inject`
   把最相关的记忆整理成可直接注入上下文的内容。
4. `feedback`
   对记忆做接受、忽略、纠正、删除反馈。
5. `stats`
   查看当前记忆规模与状态。
6. `maintain`
   定期维护记忆质量，避免长期堆积失控。

<div align="center">
  <img src="assets/readme/capability-cards.svg" alt="Nexus capability overview" width="100%" />
</div>

## 适合什么场景

- 长任务开发，避免项目上下文每轮都重新解释
- 多轮协作，让偏好、决策和规则沉淀下来
- Agent 工具链，需要在后续任务中复用历史信息
- 本地优先的长期记忆接入，不把公开主入口做成复杂宿主系统

## 快速开始

### 1. 安装

如果你使用 Ollama：

```bash
pip install -e .[ollama]
```

如果你使用 OpenAI 兼容接口：

```bash
pip install -e .[openai]
```

### 2. 配置

编辑 [config/nexus.json](E:/code/Nexus/config/nexus.json)：

```json
{
  "db_path": "data/nexus.db",
  "llm_provider": "ollama",
  "llm_model": "qwen3:4b",
  "llm_base_url": "http://localhost:11434",
  "llm_api_key": "",
  "embedding_model": "nomic-embed-text",
  "embedding_dimension": 768,
  "log_level": "INFO"
}
```

### 3. CLI 示例

```bash
nexus version
nexus --project demo --mock extract --text "We decided to use PostgreSQL."
nexus --project demo --mock search "database choice"
nexus --project demo --mock inject "What database should we use?"
nexus --project demo stats
nexus --project demo maintain
```

`--mock` 用于验证公开入口，不依赖真实 LLM 或 embedding 服务。

### 4. Python 示例

```python
from nexus import Config, MemoryCoprocessor

config = Config.from_env()

with MemoryCoprocessor(project="demo", db_path="data/nexus.db", config=config) as coprocessor:
    coprocessor.extract("We decided to use PostgreSQL.")
    results = coprocessor.retrieve("database choice")
    context = coprocessor.inject("What database should we use?")
    stats = coprocessor.stats()
```

### 5. 公开 quickstart

示例文件：

- [examples/quickstart_1_0.py](E:/code/Nexus/examples/quickstart_1_0.py)

运行：

```bash
python examples/quickstart_1_0.py
```

## 仓库结构

```text
Nexus/
├── README.md
├── README.en.md
├── SKILL.md
├── config/
│   └── nexus.json
├── assets/
│   └── readme/
├── src/
│   └── nexus/
├── adapters/
├── examples/
└── tests/
```

## 当前边界

这版 README 只面向 `Nexus Skill / Plugin 1.0` 的公开能力，不展开更底层的内部设计。

当前重点只有一件事：把长期记忆能力整理成清晰、统一、可安装、可理解的公共入口。

当前不作为 1.0 主公开面的内容包括：

- 宿主事件接入
- 服务化部署形态
- 跨环境互操作细节
- 实验性研究目录与历史验证材料

## 2.0 方向

未来 `2.0` 可以继续扩展，但本仓当前 README 只做高层说明，不提前展开实现细节：

- 更丰富的宿主接入方式
- 更灵活的跨环境记忆协作
- 更稳定的长期运行记忆工作流
- 更清晰的插件化安装与集成体验

## License

MIT
