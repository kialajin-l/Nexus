# Nexus Skill / Plugin 1.0

## 用途

当宿主或 Agent 需要长期记忆能力时，使用本 Skill。

本 Skill 负责的主线只有：

`extract -> search -> inject -> feedback -> stats -> maintain`

它不是一个独立产品说明文件，也不是宿主运行时本身。

## 何时触发

以下场景应触发 Nexus：

1. 需要把当前对话、任务上下文、文档片段沉淀为长期记忆
2. 需要在新任务开始前检索历史偏好、决策、规则、事实
3. 需要把相关记忆注入到当前上下文
4. 需要对记忆做接受、忽略、纠正、删除反馈
5. 需要查看当前记忆状态
6. 需要执行定期维护

## 宿主应如何使用

宿主应把 Nexus 当作“长期记忆 Skill / Plugin”接入，而不是把它当成主应用。

宿主侧最小接入方式：

1. 读取本文件
2. 加载 `config/nexus.json`
3. 在需要长期记忆时调用统一入口：
   - `src/nexus/skill_entry.py`
   - 或 `adapters/skill_entry.py`

## 宿主接入约定

### Codex 类宿主

- 把本仓放入可发现的 Skill / Plugin 目录
- 读取 `SKILL.md`
- 在需要长期记忆时调用 Nexus 入口

### Claude Code 类宿主

- 把本仓作为 Skill 提供给宿主
- 读取 `SKILL.md`
- 在工作流中按需触发长期记忆能力

### Hermes 类宿主

- 把 Nexus 当作外部长期记忆插件
- 由宿主决定何时触发 `extract / search / inject / feedback / stats / maintain`

## 暴露能力

对外只应暴露以下能力语义：

- `extract`
- `search`
- `inject`
- `feedback`
- `stats`
- `maintain`

如宿主需要调用稳定对象，允许依赖：

- `MemoryCoprocessor`
- `Config`
- `MemoryRecord`
- `MemoryType`
- `MemoryStatus`
- `ScoredMemory`

## 不应作为主入口的内容

以下内容当前不应被宿主当成 Skill 1.0 主公开能力：

- 宿主事件层
- 服务化部署层
- 跨环境互操作协议细节
- 实验性目录
- 历史旧版模块

旧版 `anchor / compress / guard / pipeline / ruleforge` 只作为历史材料保留，不再作为主入口。

## 最小原则

宿主可以这样理解 Nexus：

> 需要长期记忆时调用它  
> 不需要时不要让它侵入宿主主流程  
> 它负责记忆能力，不负责替代宿主本身
