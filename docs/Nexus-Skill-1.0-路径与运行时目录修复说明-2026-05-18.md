# Nexus Skill 1.0 路径与运行时目录修复说明

> 日期：2026-05-18
> 适用对象：`E:\code\Nexus` 当前 `1.0` Skill 发布面
> 用途：记录本次修复的固定目录/固定路径假设问题，并说明新的默认路径策略。

---

## 1. 修复背景

在 `Nexus Skill 1.0` 对外收口后，代码中仍然存在几类会影响宿主运行稳定性的路径假设：

1. 默认数据库路径依赖当前工作目录
2. 默认配置路径绑定仓库源码目录结构
3. projection 默认导出目录依赖当前工作目录
4. 适配层入口依赖 Python 已提前安装 `src` 包路径

这些问题在本地开发环境中不一定暴露，但在宿主集成、插件打包、跨目录调用和不同机器环境下容易导致：

1. 数据库写到意外位置
2. 配置文件找不到
3. projection 文件导出到错误目录
4. 宿主直接从仓库目录加载 skill 时入口导入失败

---

## 2. 本次修复内容

### 2.1 默认数据库路径不再依赖 `cwd`

修复前：

- 默认 `db_path` 为 `data/nexus.db`
- 实际落点依赖调用时的当前工作目录

修复后：

- 默认 `db_path` 改为用户级目录下的稳定路径
- 当前默认策略为：
  - 若设置 `NEXUS_HOME`，使用 `NEXUS_HOME/nexus.db`
  - 否则使用 `~/.nexus/nexus.db`

这意味着：

1. 即使宿主从不同目录启动 Nexus
2. 即使宿主并不在仓库根目录运行

默认数据库路径仍然稳定。

### 2.2 配置文件中的相对数据库路径按配置位置解析

修复前：

- `config/nexus.json` 中的 `db_path` 若写为相对路径
- 其最终落点仍取决于运行时 `cwd`

修复后：

- `load_config()` 会在读取配置文件后解析相对 `db_path`
- 解析基准优先按配置文件所在位置推导
- 对标准 `config/nexus.json` 布局，`data/nexus.db` 会稳定解析到仓库根下的 `data/nexus.db`

这样既保留了当前配置写法，也避免了工作目录漂移。

### 2.3 默认配置路径不再只绑定单一路径

修复前：

- `DEFAULT_CONFIG_PATH` 固定为 `src/nexus/... -> parents[2] -> config/nexus.json`

修复后：

- 默认配置路径采用多候选查找：
  1. `NEXUS_CONFIG`
  2. `cwd/config/nexus.json`
  3. 仓库/源码布局下的 `config/nexus.json`

若候选中存在实际文件，则优先使用存在的那个。

这让 Skill 在不同宿主和不同打包形态下更稳。

### 2.4 projection 默认导出目录不再依赖当前目录

修复前：

- CLI `projection export` 默认输出到相对目录 `projection`
- 导出位置依赖当前工作目录

修复后：

- 若未显式传 `--output`
- 默认输出到数据库文件旁边的 `projection/` 目录

这意味着 projection 输出会跟随实际数据位置，而不是跟随调用位置漂移。

### 2.5 适配层入口增加 `src` 布局导入兜底

修复前：

- `adapters/skill_entry.py` 直接导入 `nexus.skill_entry`
- 当宿主只是把仓库放进 Skill / Plugin 目录，而没有先执行包安装时
- Python 可能找不到 `src/nexus`

修复后：

- `adapters/skill_entry.py` 会先检查仓库下的 `src/`
- 若存在，则把该目录加入 `sys.path`
- 然后再导入 `nexus.skill_entry`

这意味着：

1. 已安装包场景继续兼容
2. 直接仓库挂载场景也能稳定加载入口

### 2.6 对外元数据与文档链接去除机器绑定路径

修复前：

- `README.md` / `README.en.md` 使用本机绝对路径链接
- `.codex-plugin/plugin.json` 使用 `E:/code/Nexus` 作为站点与仓库地址

修复后：

- README 改为相对路径链接
- 插件清单改为仓库相对地址占位

这样做的目标不是定义最终公开仓库 URL，而是先去掉会导致跨机器失真的本机路径绑定。

---

## 3. 当前默认路径策略

### 3.1 数据库路径

优先级如下：

1. CLI 显式传入 `--db-path`
2. 配置文件中的 `db_path`
3. 环境变量 `NEXUS_DB_PATH`
4. `NEXUS_HOME/nexus.db`
5. `~/.nexus/nexus.db`

### 3.2 配置文件路径

优先级如下：

1. 显式传入 `config_path`
2. 环境变量 `NEXUS_CONFIG`
3. `cwd/config/nexus.json`
4. 仓库布局中的 `config/nexus.json`

### 3.3 projection 导出路径

优先级如下：

1. CLI 显式传入 `--output`
2. 数据库文件同级目录下的 `projection/`

### 3.4 skill 入口导入路径

优先级如下：

1. Python 已安装的 `nexus` 包
2. 适配层自动补入的仓库 `src/` 目录

---

## 4. 对宿主接入方的告知

从现在开始，宿主侧应这样理解 `Nexus Skill 1.0`：

1. 不要假设 Nexus 必须从仓库根目录运行
2. 不要假设数据库一定写到当前目录
3. 不要假设 projection 一定导出到当前目录
4. 如果宿主需要完全控制路径，请显式传入配置或 CLI 参数

推荐做法：

1. 明确传入 `config_path`
2. 明确传入 `db_path`
3. 需要固定 projection 落点时显式传入 `--output`
4. 若宿主直接挂载仓库目录，优先调用 `adapters/skill_entry.py`

---

## 5. 兼容性说明

本次修复优先保持以下兼容性：

1. 现有 `config/nexus.json` 仍可继续使用
2. 现有 `projection import/export` 命令不变
3. 现有 `README` 和 `SKILL` 中的公开能力口径不变
4. 已安装包场景与直接仓库挂载场景同时兼容

变化主要体现在默认路径的解释与落点更加稳定。

---

## 6. 一句话结论

本次修复的核心目标不是改功能，而是去掉 `Skill 1.0` 对当前开发目录结构和调用位置的隐式依赖，使其在真实宿主环境中更稳定可用。
