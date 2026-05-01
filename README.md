# Nexus

> 🧠 A **Vibe Coding** project: Built with AI, for AI-augmented development.

![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Version](https://img.shields.io/badge/Version-1.0.0-green.svg)

**Nexus** 是一个 AI 助手记忆增强 Skill，让 AI 拥有跨会话的持久记忆。它从对话中自动提取结构化知识（锚点），以结构化方式组织存储，在需要时精准检索，同时通过幻觉防御机制确保 AI 回答的可靠性。

核心理念：**AI 幻觉的本质是思维层没有锚点锚定。先锚定，再联想。**

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔗 **锚点提取** | 从对话中自动提取事实、决策、偏好、规则等结构化知识 |
| 📦 **三层压缩** | 文本去冗 → 锚点提取 → 锚点精炼，最小化 token 消耗 |
| 🛡️ **幻觉防御** | 意图识别 + 幻觉检测 + 多路径执行，将 AI 幻觉从"锚点锚向错误"中解救 |
| 💾 **本地存储** | 纯本地 JSON 存储，零依赖，隐私安全 |

---

## 🏗️ 架构概览

Nexus 采用单 Skill 自包含设计，解压即用：

```
nexus/
├── SKILL.md              # 使用说明与触发命令
├── config/
│   └── nexus.json        # 配置文件（存储路径、参数）
├── src/
│   ├── __init__.py
│   ├── anchor.py         # 锚点定义 + 存储 + 质量计算
│   ├── compressor.py     # 三层压缩引擎
│   └── guard.py          # 幻觉防御（意图识别/检测/多路径）
└── data/                 # 默认数据目录
    ├── anchors.json      # 锚点数据（机器可读）
    └── sessions/         # 会话记录
```

### 三大模块

| 模块 | 职责 | 核心类 |
|------|------|--------|
| **Anchor** | 锚点的定义、存储、检索、质量计算 | `Anchor`, `AnchorStore` |
| **Compressor** | 对话历史的三层压缩，减少 token 消耗 | `Compressor`, `CompressionReport` |
| **Guard** | 意图识别、幻觉检测、多路径执行分析 | `Guard`, `IntentAnalysis`, `HallucinationReport` |

---

## 📦 安装

### 方式一：作为 Skill 安装（推荐）

将 `nexus/` 目录放入你的 Agent 的 Skill 目录即可。解压即用，零配置。

```
your-agent/
└── skills/
    └── nexus/            ← 放这里
        ├── SKILL.md
        ├── config/
        ├── src/
        └── data/
```

首次使用时，Agent 会提示数据存储地址，并告知如何更改。

### 方式二：Python 库集成

```python
from src.anchor import Anchor, AnchorStore, AnchorType
from src.compress import Compressor
from src.guard import Guard

# 初始化存储
store = AnchorStore("data/anchors.json")

# 创建锚点
anchor = Anchor(
    type=AnchorType.FACT,
    content="Python 发布于 1991 年",
    source="对话",
    confidence=1.0,
)
store.save(anchor)

# 压缩对话
compressor = Compressor(store)
report = compressor.compress("用户：Python 哪年发布的？\nAI：1991年。")

# 幻觉检测
guard = Guard(store)
report = guard.detect_hallucination("Python 是 1991 年发布的，由 Guido 创建。")
```

---

## 🚀 快速开始

### 触发命令

在 Agent 对话中使用以下命令：

| 命令 | 功能 |
|------|------|
| `nexus add <内容>` | 手动添加一个锚点 |
| `nexus search <关键词>` | 搜索锚点 |
| `nexus compress` | 压缩当前对话上下文 |
| `nexus guard <文本>` | 检测文本幻觉风险 |
| `nexus stats` | 查看锚点统计信息 |

### 自动触发

Nexus 在以下场景自动工作：

- **对话中出现确定性知识**（事实、日期、数字）→ 自动提取为锚点
- **用户做出选择或决策** → 自动记录为决策锚点
- **检测到 AI 回答可能包含幻觉** → 自动提示风险

---

## 🔧 配置

配置文件位于 `config/nexus.json`：

```json
{
  "version": "1.0.0",
  "store": {
    "anchors_path": "data/anchors.json",
    "sessions_dir": "data/sessions"
  },
  "anchor": {
    "types": ["fact", "decision", "preference", "rule", "project"],
    "max_anchors": 10000
  }
}
```

### 数据存储路径

- **默认位置**：`{skill_dir}/data/anchors.json`
- **首次使用提示**：Agent 会在首次触发时通知数据存放地址
- **自定义路径**：修改 `config/nexus.json` 中的 `store.anchors_path`

---

## 🗺️ 路线图

### v1.0 — 通用 Skill（当前版本）

- [x] 锚点提取与存储
- [x] 三层压缩引擎
- [x] 幻觉防御系统
- [ ] 首次使用提示
- [ ] Obsidian Markdown 输出

### v2.0 — 跨终端记忆共享

跨设备知识同步，让 AI 记忆不再困在单一设备上。

---

## 🤝 相关项目

| 项目 | 说明 |
|------|------|
| [RuleForge](https://github.com/kialajin-l/RuleForge) | 智能规则引擎，自动识别最佳实践并转化为可执行规则 |
| [NightShift](https://github.com/kialajin-l/NightShift) | AI 桌面操作系统，Nexus 的宿主应用 |

---

## 📄 License

MIT License

---

> **Nexus** — 让 AI 拥有记忆，让知识不再遗忘。
