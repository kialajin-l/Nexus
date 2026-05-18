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

### 1. 作为 Skill 安装

这个仓库的公开主用途是 Agent Skill / Plugin，而不是独立的 runtime 示例工程。

接入时保留以下关键文件：

- `SKILL.md`
- `config/nexus.json`
- `src/nexus/`
- `adapters/`

如果宿主以 Python 环境加载 Skill，请先安装依赖：

```bash
pip install -e .[ollama]
```

或：

```bash
pip install -e .[openai]
```

### 2. 配置 Skill

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

这份配置决定 Skill 在宿主内如何连接记忆库、LLM 和 embedding 后端。

### 3. 让宿主读取 Skill 入口

宿主侧应优先读取：

- [SKILL.md](E:/code/Nexus/SKILL.md)

并把 Nexus 作为一个长期记忆 Skill 使用，而不是把它当作单独的产品 CLI。

当前 Skill 的主能力是：

- `extract`
- `search`
- `inject`
- `feedback`
- `stats`
- `maintain`

### 4. 在宿主中接入

对于支持 Skill / Plugin 目录的 Agent 宿主，推荐做法是：

1. 把本仓放入宿主可发现的 Skill / Plugin 目录
2. 让宿主读取 `SKILL.md`
3. 让宿主在需要长期记忆时调用 Nexus 的统一运行时入口

当前统一入口包括：

- `src/nexus/skill_entry.py`
- `adapters/skill_entry.py`

这意味着宿主可以把 Nexus 当成“长期记忆能力插件”接入，而不是直接暴露底层实现细节。

### 5. 当前适配理解

以目前 1.0 的公开面来看：

- 对 Codex 类宿主：读取 `SKILL.md`，在需要时调用 Nexus Skill 入口
- 对 Claude Code 类宿主：读取 `SKILL.md`，把 Nexus 当作长期记忆 Skill 挂入工作流
- 对 Hermes 类宿主：把 Nexus 当作外部记忆插件接入，由宿主决定何时触发记忆提取、检索与注入

如果后续继续完善，README 会优先补充宿主接入说明，而不是扩写底层 runtime 用法。

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
