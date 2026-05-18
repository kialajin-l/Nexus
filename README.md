<div align="center">
  <img src="assets/readme/nexus-banner.svg" alt="Nexus banner" width="100%" />
</div>

> This is a Vibe Coding project: Built with AI, for AI-augmented development.

![License](https://img.shields.io/badge/License-MIT-F2C94C)
![Version](https://img.shields.io/badge/Version-v1.0.0-2D9CDB)
![Python](https://img.shields.io/badge/Python-%3E%3D3.10-27AE60)

[English](README.en.md) | **中文**

## Nexus 是什么

`Nexus Skill / Plugin 1.0` 是一个面向 Agent 宿主的长期记忆 Skill。

它不是让每个用户先搭一套固定本地模型环境、再把 Nexus 当成独立 Core 项目来运行的产品。更合理的理解方式是：

> 把它放进宿主可发现的 Skill / Plugin 目录  
> 由宿主决定何时调用长期记忆能力  
> 由 Nexus 负责记忆提取、检索、注入、反馈、维护与 Markdown 投影

当前公开主线是：

`extract -> store -> search -> inject -> feedback -> stats -> maintain -> projection export/import`

## 核心能力

<div align="center">
  <img src="assets/readme/memory-flow.svg" alt="Nexus memory flow" width="100%" />
</div>

Nexus 1.0 当前对外公开八类能力：

1. `extract`
   从对话、任务上下文、文档片段中提取长期记忆。
2. `search`
   在新任务开始时检索相关记忆。
3. `inject`
   把相关记忆整理成可注入当前上下文的内容。
4. `feedback`
   对记忆执行接受、忽略、纠正、删除反馈。
5. `stats`
   查看当前记忆规模与状态。
6. `maintain`
   执行记忆维护，避免长期堆积失控。
7. `projection export`
   导出本地 Markdown 记忆文件，供用户查看和修改。
8. `projection import`
   把用户修改后的 Markdown 重新导入记忆库。

<div align="center">
  <img src="assets/readme/capability-cards.svg" alt="Nexus capability overview" width="100%" />
</div>

## 安装与接入

### 1. 作为 Skill 安装

Nexus 1.0 的主要安装形态应当是：

1. 下载仓库
2. 放入宿主可发现的 Skill / Plugin 目录
3. 让宿主读取 `SKILL.md`

对宿主最重要的文件通常是：

1. `SKILL.md`
2. `config/nexus.json`
3. `src/nexus/`
4. `adapters/skill_entry.py`

### 2. 最小配置

编辑 [config/nexus.json](config/nexus.json)：

```json
{
  "db_path": "data/nexus.db",
  "log_level": "INFO"
}
```

这份最小配置只表达两件事：

1. 记忆数据库放在哪里
2. 日志级别是什么

它符合 Skill 形态的公开边界，不再把某个固定本地模型方案写成产品前提。

### 3. 宿主已有 LLM 能力时

如果宿主本身已经提供模型能力，Nexus 应优先复用宿主能力。

这意味着：

1. 不应要求所有用户安装 Ollama
2. 不应把 `qwen3:4b` 写成默认前提
3. 不应要求所有用户下载独立 embedding 模型

对于 Codex、Claude Code、Hermes 这类宿主，合理口径是：**宿主优先，Nexus 复用宿主**。

### 4. 本地或远程 backend 只是可选适配

当宿主没有提供模型 backend 时，接入方才需要自行补上可选适配方案，例如：

1. 本地 Ollama
2. OpenAI-compatible API
3. 宿主注入的其他模型服务

这些都可以支持，但它们不应被写成 Nexus Skill 1.0 的唯一默认方案。

## Agent Skill 使用方式

### Codex 类宿主

把本仓放入可发现的 Skill / Plugin 目录，让宿主读取 `SKILL.md`，并在需要长期记忆时调用 Nexus 入口。

### Claude Code 类宿主

把 Nexus 作为长期记忆 Skill 挂入工作流，由宿主在合适节点触发 `extract / search / inject / feedback / stats / maintain / projection`。

### Hermes 类宿主

把 Nexus 当作外部长期记忆插件接入，由 Hermes 决定何时触发记忆提取、检索、注入、反馈和 Markdown 投影导入导出。

## 公开入口

当前 Skill 1.0 的统一入口包括：

1. `SKILL.md`
2. `adapters/skill_entry.py`
3. `src/nexus/skill_entry.py`
4. `src/nexus/cli.py`

当前公开稳定对象包括：

1. `MemoryCoprocessor`
2. `Config`
3. `MemoryRecord`
4. `MemoryType`
5. `MemoryStatus`
6. `ScoredMemory`
7. `ProjectionConfig`
8. `ProjectionMode`
9. `MemoryRiskLevel`

## Markdown 投影层

1. `projection export`
   把当前记忆导出为本地 Markdown 文件。
2. `projection import`
   把用户修改后的 Markdown 导回本地记忆库。

Skill 1.0 默认采用更宽松的用户侧策略，重点是：

1. 用户可见
2. 用户可编辑
3. 用户改完可导回
4. 不直接继承 Core 的高风控默认限制

## 快速示例

公开示例位于 [examples/quickstart_1_0.py](examples/quickstart_1_0.py)。

这个示例展示的是 Skill 1.0 的公开工作流，包括：

1. extract
2. search
3. inject
4. feedback
5. stats
6. projection export
7. projection import

示例使用 mock 组件验证流程，不把固定本地模型环境写成使用前提。

## 当前不包含什么

以下内容不属于当前 1.0 主公开面：

1. `exchange`
2. `host adapter / host runner / event runner`
3. `host events / host contract`
4. `service`
5. host 示例脚本
6. 协议预验收脚本
7. `tests`
8. `lab`

旧版 `anchor / compress / guard / pipeline / ruleforge` 只保留为历史材料，不再作为公开主线接口。

## 与 Nexus Core 的关系

Nexus Skill / Plugin 1.0 以 `Nexus Core 1.0` 的稳定能力为底座，但本仓对外强调的是 Skill 入口，而不是 Core 内部研发结构。

当前公开重点只有一件事：把长期记忆能力整理成清晰、统一、可安装、可理解的 Skill。

## 2.0 方向

未来 `2.0` 可以继续扩展，但不属于当前主公开面：

1. 更丰富的宿主接入方式
2. 更稳定的长期运行记忆工作流
3. 更清晰的插件化安装体验
4. 更强的跨环境协作能力

## License

MIT
