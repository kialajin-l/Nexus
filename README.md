<div align="center">
  <img src="assets/readme/nexus-banner.svg" alt="Nexus banner" width="100%" />
</div>

> 这是一个 Vibe Coding project: Built with AI, for AI-augmented development.

![License](https://img.shields.io/badge/License-MIT-F2C94C)
![Version](https://img.shields.io/badge/Version-v1.1.0-2D9CDB)
![Python](https://img.shields.io/badge/Python-%3E%3D3.10-27AE60)

[English](README.en.md) | **中文**

## Nexus 是什么

`Nexus Skill / Plugin 1.1` 是一个面向 Agent 宿主的长期记忆 Skill。

这一版的重点升级只有两个：

1. 支持导出到 Obsidian 友好的 Markdown
2. 支持在安装后优先配置数据库路径和 Obsidian 路径，并检测是否沿用已有数据

## 安装

根据你使用的工具，复制对应命令，在终端里执行：

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

如果上面那种方式不行，也可以手动安装：

1. 克隆仓库
2. 进入仓库目录
3. 执行 `./install.sh <host>`

安装完成后，优先检查并修改：

- `db_path`
- `obsidian_root_path`

默认配置文件在安装后的 Skill 目录里：

- `config/nexus.json`

## 安装后先做什么

首次安装后，建议先确认：

1. SQLite 数据库放在哪里
2. Obsidian 导出目录放在哪里
3. 这些位置是否已经有旧数据可沿用

如果宿主支持命令调用，建议先执行：

```bash
nexus setup --db-path "<db-path>" --obsidian-root "<vault-path>"
```

这个步骤可以帮助判断：

- 数据库文件是否已存在
- Obsidian 目录是否已存在
- 是否已经有可以沿用的内容

## 使用说明

下面这些是用户更容易理解的常见用法。

### 1. 安装与初始化

适合这些场景：

- 安装 Nexus
- 第一次启用
- 设置数据库路径
- 设置 Obsidian 路径
- 检查是否沿用已有数据

示例说法：

- 配置 Nexus
- 设置数据库路径
- 设置 Obsidian 路径
- 检查有没有已有记忆库
- 我想沿用以前的数据库

### 2. 记住信息

适合这些场景：

- 记住一条偏好
- 保存一个决定
- 保存一条规则
- 从当前对话里沉淀长期记忆

示例说法：

- 记住这个偏好
- 保存这次决定
- 把这条规则记下来
- 从这段对话里提取长期记忆

### 3. 查找过去的记忆

适合这些场景：

- 查以前怎么定的
- 搜索过去的偏好
- 查找相关决策
- 找历史规则或事实

示例说法：

- 查一下我之前怎么说的
- 搜一下以前关于数据库的决定
- 找一下之前的偏好
- 看看以前有没有相关记忆

### 4. 在当前任务里引用过去记忆

适合这些场景：

- 回答前先参考以前的偏好
- 在写新方案前带入旧决定
- 给当前任务补充历史上下文

示例说法：

- 先参考以前的规则
- 把相关记忆带到这次任务里
- 给当前任务补充之前的决定

### 5. 修正或删除记忆

适合这些场景：

- 某条记忆不对
- 某条记忆应该忽略
- 某条记忆需要纠正
- 某条记忆需要删除

示例说法：

- 这条记忆是错的
- 忽略这条
- 改一下这条记忆
- 删除这条记忆

### 6. 查看记忆库状态

适合这些场景：

- 查看当前有多少记忆
- 看记忆状态
- 检查记忆库规模

示例说法：

- 看看当前记忆库状态
- 统计一下现在有多少记忆
- 检查一下长期记忆情况

### 7. 整理记忆库

适合这些场景：

- 做一次维护
- 清理长期积累的噪音
- 保持记忆库质量

示例说法：

- 整理一下记忆库
- 做一次记忆维护
- 清理一下长期记忆

### 8. 导出到 Obsidian

适合这些场景：

- 导出 Markdown 到 Obsidian
- 把记忆整理成笔记库
- 给用户一个可读的长期记忆目录

示例说法：

- 导出到 Obsidian
- 把记忆导出成 Markdown
- 生成可放进 Obsidian 的记忆文件

命令示例：

```bash
nexus -p my-project projection export \
  --db-path "<db-path>" \
  --output "<vault-root>" \
  --group-by topic \
  --obsidian-friendly
```

## 提示词说明

当前更适合的用户提示词不是内部能力名，而是常见功能表达。

推荐直接使用这类说法：

- 配置 Nexus
- 设置数据库路径
- 设置 Obsidian 路径
- 检查有没有已有记忆库
- 记住这个偏好
- 保存这次决定
- 查一下我之前怎么说的
- 把相关记忆带到这次任务里
- 这条记忆是错的
- 看看当前记忆库状态
- 整理一下记忆库
- 导出到 Obsidian

## 本地多 Agent 使用方法

Nexus 1.1 支持多个本地 Agent 共用一份长期记忆，但不是自动行为。

要共用，需要做到：

1. 多个宿主显式使用同一个 `db_path`
2. 如需统一导出目录，也使用同一个 `obsidian_root_path`
3. 它们使用兼容的 Nexus 版本和 schema

推荐做法：

1. 先确定一个共享数据库路径
   例如 `D:\\shared\\nexus\\nexus.db`
2. 让 Hermes、Codex、Claude Code 等宿主都指向这个同一个 `db_path`
3. 如需共享同一套导出笔记，也统一 `obsidian_root_path`

可以把它理解成：

- 默认是各自本地私有库
- 想共用时，显式配置成同一个数据库路径

## 1.1 新增能力总结

这一版新增的重点能力是：

1. Obsidian 友好导出
2. 首次安装后的路径配置
3. 已有数据库与已有导出目录的检测
4. 更适合本地多 Agent 共库使用的路径说明

## 当前不包含什么

以下内容不属于当前 1.1 主公开面：

- Obsidian 写回承诺
- `exchange`
- `host adapter / host runner / event runner`
- `host events / host contract`
- `service`
- host 示例脚本
- `tests`
- `lab`

## License

MIT
