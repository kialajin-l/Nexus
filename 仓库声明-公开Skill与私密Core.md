# Nexus 仓库声明：公开 Skill 与私密 Core

日期：2026-05-18

## 当前结论

`E:\code\Nexus` 当前定位为：

- `Nexus Skill / Plugin` 的公开仓
- 面向外部使用、宿主接入、社区流转

`Nexus Core` 当前定位为：

- 私密主研发仓
- 本地迁移落点：`E:\code\Nexus-Core`

## 为什么这样调整

此前公开仓同时承载了：

1. 早期 Skill 结构
2. 后续 `nexus-mvp` Core 研发工作区

这会导致两个问题：

1. 外部用户难以判断公开入口到底是什么
2. Core 研发与公开分发目标长期混杂

因此从现在开始做职责拆分：

1. 公开仓负责 Skill / Plugin 入口与社区化
2. 私密仓负责 Core 能力演进与 2.0 主线开发

## 当前仓库应如何理解

### 公开仓负责

1. `SKILL.md`
2. Skill / Plugin 对外说明
3. 宿主接入入口
4. KXP 等共享格式的对外接入
5. 社区使用、共享、扩充相关文档

### 私密 Core 负责

1. 记忆引擎
2. extract / retrieve / inject / feedback / maintain
3. exchange / KXP 底层实现
4. host adapter / host runner
5. 真实宿主事件约定
6. 2.0 后续演进

## 当前约束

1. 公开仓不再作为 Core 唯一实现源头
2. 公开仓不应再长期维护第二份 Core 运行时
3. 若后续需要对外暴露能力，应优先通过 Skill / Plugin 封装，而不是把 Core 开发结构直接暴露到公开仓

## 后续远端操作

1. 保持当前 GitHub 公开仓作为 `Nexus Skill / Plugin` 仓
2. 新建 GitHub 私密仓作为 `Nexus Core` 仓
3. 将 `E:\code\Nexus-Core` 作为私密仓初始工作区
4. 后续对外 README、Release、社区入口都以 Skill 仓口径发布
