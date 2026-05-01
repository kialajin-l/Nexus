# Nexus — AI 记忆增强

> 让 AI 拥有跨会话的持久记忆

## 功能

Nexus 从对话中提取结构化知识（锚点），以宇宙坐标模型组织存储，在需要时精准检索，并通过幻觉防御机制确保回答可靠性。

## 触发命令

| 命令 | 功能 |
|------|------|
| `nexus add <内容>` | 手动添加一个锚点 |
| `nexus search <关键词>` | 搜索锚点 |
| `nexus compress` | 压缩当前对话上下文 |
| `nexus guard <文本>` | 检测文本幻觉风险 |
| `nexus stats` | 查看锚点统计信息 |

## 自动触发

以下场景 Nexus 自动工作，无需手动命令：

- 对话中出现确定性知识（事实、日期、数字）→ 自动提取为锚点
- 用户做出选择或决策 → 自动记录为决策锚点
- 检测到 AI 回答可能包含幻觉 → 自动提示风险

## 首次使用

1. 首次触发时，Nexus 会提示数据存储地址（默认 `data/anchors.json`）
2. 如需更改存储路径，编辑 `config/nexus.json` 中的 `store.anchors_path`

## 使用方式

### 手动添加锚点

```
nexus add Python 发布于 1991 年 2 月 20 日
```

### 搜索锚点

```
nexus search Python
```

### 压缩对话

```
nexus compress
```

Nexus 会自动分析当前对话，提取锚点并压缩历史，减少 token 消耗。

### 幻觉检测

```
nexus guard Python 是 1991 年发布的，由 Guido 创建
```

Nexus 会检查文本中的事实是否与已存储的锚点一致，标记潜在幻觉。

### 查看统计

```
nexus stats
```

显示锚点总数、各类型分布、天体分类统计。

## 锚点类型

| 类型 | 说明 | 示例 |
|------|------|------|
| fact | 客观事实 | "Python 发布于 1991 年" |
| decision | 用户决策 | "项目用 TypeScript" |
| preference | 用户偏好 | "喜欢简洁的代码风格" |
| rule | 规则约束 | "提交前必须跑测试" |
| project | 项目信息 | "Nexus v1.0 已发布" |

## 天体分类

锚点按质量自动分类：

- ⭐ **恒星** — 核心知识节点（质量 ≥ 0.7，稳定性 ≥ 0.7）
- 🌍 **行星** — 重要但非核心（质量 ≥ 0.3，稳定性 ≥ 0.5）
- ☄️ **彗星** — 跨域关联（跨域关联 ≥ 3）
- 🪨 **小行星** — 待发展碎片（其他）

## 配置

编辑 `config/nexus.json`：

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

## 注意事项

- 数据纯本地存储，不上传任何外部服务
- 锚点文件为 JSON 格式，可用任何文本编辑器查看
- 建议定期备份 `data/anchors.json`
