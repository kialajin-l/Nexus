<div align="center">
  <img src="assets/readme/nexus-banner.svg" alt="Nexus banner" width="100%" />
</div>

> 🧠 This is a **Vibe Coding** project: Built with AI, for AI-augmented development.

![License](https://img.shields.io/badge/License-MIT-F2C94C)
![Version](https://img.shields.io/badge/Version-v1.1.0-2D9CDB)
![Python](https://img.shields.io/badge/Python-%3E%3D3.10-27AE60)

[English](README.en.md) | **中文**

**Nexus** 是一个面向 Agent 宿主的长期记忆 Skill——让 AI 助手拥有跨会话的持久记忆能力。

它的核心价值是：**让 Agent 在每次新对话中自动带回之前的决策、偏好和上下文，不再需要用户重复解释背景。**

---

<p align="center">
  <img src="assets/readme/features.png" alt="Nexus Features" width="100%">
</p>

## ✨ 核心功能

### 基础能力

| 功能 | 说明 |
|------|------|
| 🧠 **结构化记忆提取** | 从对话中自动提取事实、决策、偏好、规则、待办，存为结构化锚点 |
| 🔍 **智能记忆检索** | 按关键词、标签、时间、重要性多维度检索，精准召回相关记忆 |
| 💉 **任务前上下文注入** | 新任务开始时自动注入相关历史记忆，减少重复背景说明 |
| 📝 **人工反馈闭环** | 支持接受、忽略、修正、删除记忆，持续提升记忆质量 |
| 📊 **记忆库状态统计** | 查看记忆总量、类型分布、健康度 |
| 🧹 **记忆维护与清理** | 自动去重、过期清理、噪音过滤 |

### v1.1 新增能力

| 功能 | 说明 |
|------|------|
| 📤 **Obsidian 友好导出** | 将记忆库导出为 Markdown 文件，可直接放入 Obsidian 作为笔记浏览 |
| ⚙️ **首次安装路径配置** | 安装后优先配置数据库路径和 Obsidian 导出路径 |
| 🔎 **已有数据检测** | 自动检测是否已有数据库或导出目录，支持沿用旧数据 |
| 🔗 **本地多 Agent 共库** | 多个 Agent（Hermes / Codex / Claude Code 等）可共用同一份记忆库 |

---

<p align="center">
  <img src="assets/readme/architecture.png" alt="Nexus Architecture" width="100%">
</p>

## 🏗️ 架构概览

```
Nexus/
├── src/nexus/           # 🧠 核心模块
│   ├── coprocessor.py   #   记忆协处理器（提取/检索/注入/反馈）
│   ├── config.py        #   配置管理（db_path / obsidian_root_path）
│   ├── prompts/         #   提取与检索提示词模板
│   └── schema.sql       #   SQLite 数据库 Schema
├── adapters/            # 🔌 宿主适配层
│   └── skill_entry.py   #   Skill 入口（供宿主调用）
├── config/              # ⚙️ 配置文件
│   └── nexus.json       #   默认配置
├── data/                # 💾 运行时数据（SQLite 数据库）
├── scripts/             # 🛠️ 辅助脚本
├── tests/               # 🧪 测试
├── install.sh           # 📦 一键安装脚本
└── SKILL.md             # Agent 技能说明
```

---

<p align="center">
  <img src="assets/readme/workflow.png" alt="Nexus Workflow" width="100%">
</p>

## 🚀 快速开始

Nexus 是一个 AI 技能（Skill），安装后直接在对话中使用。**用自然语言告诉 AI 你想要什么就行**。

### 安装

根据你使用的宿主工具，复制对应命令在终端执行：

### Claude Code

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh claude-code
```

### Codex

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh codex
```

### Hermes

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh hermes
```

### OpenClaw

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh openclaw
```

### DeepSeek TUI

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh deepseek
```

如果一键命令不生效，也可以手动安装：克隆仓库 → 进入目录 → 执行 `./install.sh <host>`

### 首次配置

安装完成后，建议先确认两个路径：

1. **SQLite 数据库路径**（记忆存储位置）
2. **Obsidian 导出路径**（可选，用于将记忆导出为 Markdown 笔记）

默认配置文件在安装后的 Skill 目录中：`config/nexus.json`

---

## 💬 使用示例

### 记住信息

> "记住这个偏好：我习惯用深色主题"
> "保存这次决定：数据库用 SQLite 不用 PostgreSQL"
> "把这条规则记下来：代码注释用中文"

### 查找过去的记忆

> "查一下我之前怎么说的数据库选型"
> "搜一下以前关于部署方式的决定"
> "看看之前有没有相关偏好"

### 在当前任务中引用记忆

> "先参考以前的规则再开始写代码"
> "把相关记忆带到这次任务里"

### 修正或删除记忆

> "这条记忆是错的，改一下"
> "忽略这条记忆"
> "删除这条过时的记忆"

### 导出到 Obsidian

> "把记忆导出成 Markdown"
> "导出到 Obsidian 笔记库"

### 查看记忆库状态

> "看看当前记忆库有多少条"
> "统计一下长期记忆情况"

### 整理记忆库

> "整理一下记忆库，清理噪音"
> "做一次记忆维护"

---

## 📖 使用场景速查

| 场景 | 你可以这样说 |
|------|-------------|
| **安装与初始化** | 配置 Nexus、设置数据库路径、设置 Obsidian 路径、检查有没有已有记忆库、我想沿用以前的数据库 |
| **记住信息** | 记住这个偏好、保存这次决定、把这条规则记下来、从这段对话里提取长期记忆 |
| **查找记忆** | 查一下我之前怎么说的、搜一下以前关于数据库的决定、找一下之前的偏好、看看以前有没有相关记忆 |
| **引用记忆** | 先参考以前的规则、把相关记忆带到这次任务里、给当前任务补充之前的决定 |
| **修正或删除** | 这条记忆是错的、忽略这条、改一下这条记忆、删除这条记忆 |
| **查看状态** | 看看当前记忆库状态、统计一下现在有多少记忆、检查一下长期记忆情况 |
| **整理维护** | 整理一下记忆库、做一次记忆维护、清理一下长期记忆 |
| **导出 Obsidian** | 导出到 Obsidian、把记忆导出成 Markdown、生成可放进 Obsidian 的记忆文件 |

---

## 🔗 本地多 Agent 共库

Nexus 1.1 支持多个本地 Agent 共用一份长期记忆，但不是自动行为。

**共用方法：** 让多个宿主显式使用同一个 `db_path` 即可。

```json
// config/nexus.json
{
  "db_path": "D:\shared\nexus\nexus.db"
}
```

- 默认是各自本地私有库
- 想共用时，显式配置成同一个数据库路径
- 如需共享导出笔记，也统一 `obsidian_root_path`

---

## 🗺️ Roadmap

### v1.0 ✅ — MVP 核心
- [x] 结构化记忆提取（事实/决策/偏好/规则/待办）
- [x] 本地 SQLite 存储
- [x] 多维度记忆检索
- [x] 任务前上下文注入
- [x] 人工反馈闭环（接受/忽略/修正/删除）
- [x] 记忆维护与统计

### v1.1 ✅ — Obsidian 导出 + 多 Agent 共库
- [x] Obsidian 友好 Markdown 导出
- [x] 首次安装路径配置与已有数据检测
- [x] 本地多 Agent 共库支持

### v2.0 📋 — 跨终端记忆共享
- [ ] 跨设备记忆同步
- [ ] 社区维护与共享数据
- [ ] 知识包导入/导出

---

## 🤝 贡献

```bash
git clone https://github.com/kialajin-l/Nexus.git
cd Nexus
pip install -e ".[dev]"
pytest
```

---

## P0 组合当前快照（2026-08-02）

Nexus 是独立开源产品，建立在 Nexus-Core 之上，不与 Nexus-Core 合并。
P0 执行索引标识为 `P0-CONTROL-2026-08-02`（由组合级交接文档维护）。

| P0 任务 | 目标 | 状态 |
|---|---|---|
| `NX-N0-ASSET-INVENTORY` | 清点宇宙坐标、锚点、KXP、规则和接口设计源 | 下一任务 |
| `NX-N1-CANONICAL-SPEC` | 将现有设计源整理为单一宇宙坐标 canonical spec | 待执行，当前设计源未冻结 |
| `NX-N2-LOCAL-PRODUCT` | 单用户本地试用组合 | 待执行 |
| `NX-N3-COORDINATE-PROTOTYPE` | 首个坐标查询原型 | 待执行 |
| `NX-N4-SPATIAL-CANDIDATE` | GH²I 派生索引候选与 A/B | 条件路线 |
| `NX-N5-OPEN-RELEASE` | 独立开源产品发布与维护 | 未开始 |
| `NX-N6-DESIGN-COMPLETE` | 宇宙坐标及高级路线最终决策 | 未开始 |

`Universe-Coordinate-Model.md` 当前仍为 `v0-draft`；GH²I 只能作为派生空间索引/可选后端，
不能替换 Nexus-Core 主事实源或主检索链。文档中的精度、延迟和规模数字仍是待验证假设。
Release 1 面向单用户本地试用，不包含生产多宿主、runtime、provider、网络、凭据或稳定写入。

## 📄 许可证

MIT License

## 🙏 致谢

- [Xiaomi miclaw](https://github.com/XiaomiMiClaw) — AI 助手平台
- [Mem0](https://github.com/mem0ai/mem0) — 记忆层设计参考
- [Hermes](https://github.com/hermes-agent) — Agent 运行时架构参考
- [Obsidian](https://obsidian.md) — 知识管理与导出目标

---

## 🌟 Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=kialajin-l/Nexus&type=Date)](https://star-history.com/#kialajin-l/Nexus&Date)
