# Nexus Skill / Plugin 1.0

## 这是什么

这是 `Nexus Skill / Plugin 1.0` 的公开 Skill 入口。  
它以 `Nexus Core 1.0` 为能力底座，当前只聚焦长期记忆主能力。

对外主线是：

`extract -> store -> retrieve -> inject -> feedback -> maintain`

## 适用场景

当宿主或 Agent 需要以下能力时使用本 Skill：

- 从对话、文档片段、任务上下文中提取长期记忆
- 在新任务中检索和注入相关记忆
- 对已存记忆做接受、忽略、纠正、删除反馈
- 查看记忆统计
- 执行记忆维护

## 核心公开能力

- `extract`
- `search`
- `inject`
- `feedback`
- `stats`
- `maintain`

公开稳定对象：

- `MemoryCoprocessor`
- `Config`
- `MemoryRecord`
- `MemoryType`
- `MemoryStatus`
- `ScoredMemory`

## 安装 / 接入

### Python 包

```bash
pip install -e .[ollama]
```

或：

```bash
pip install -e .[openai]
```

### 配置

编辑：

- `config/nexus.json`

最小字段：

- `db_path`
- `llm_provider`
- `llm_model`
- `llm_base_url`
- `llm_api_key`
- `embedding_model`
- `embedding_dimension`
- `log_level`

## 入口文件

- Skill 文档：`SKILL.md`
- 运行时包：`src/nexus/`
- Skill adapter：`src/nexus/skill_entry.py`
- CLI：`src/nexus/cli.py`
- 示例：`examples/quickstart_1_0.py`

## 使用方式

### CLI

```bash
nexus version
nexus --project demo --mock extract --text "We decided to use PostgreSQL."
nexus --project demo --mock search "database choice"
nexus --project demo --mock inject "What database should we use?"
nexus --project demo feedback mem_x accepted
nexus --project demo list
nexus --project demo stats
nexus --project demo maintain
```

### Python

```python
from nexus import Config, MemoryCoprocessor

config = Config.from_env()

with MemoryCoprocessor(project="demo", db_path="data/nexus.db", config=config) as coprocessor:
    coprocessor.extract("We decided to use PostgreSQL.")
    memories = coprocessor.retrieve("database choice")
    injected = coprocessor.inject("What database should we use?")
```

## 边界

本 Skill 当前不把以下内容作为主公开能力：

- `host adapter / host runner / host events / host contract`
- `event runner`
- `service`
- 跨环境互操作协议细节
- 更底层的宿主协同约定
- 宿主事件协议
- `tests`
- `lab`

旧版 `anchor / compress / guard / pipeline / ruleforge` 只可作为历史说明，不再作为对外主入口。
