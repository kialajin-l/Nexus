# Nexus Coordinate Canonical Specification v1

日期：2026-08-20  
状态：`FROZEN_DESIGN / IMPLEMENTATION_NOT_STARTED`  
任务：`NX-N1-CANONICAL-SPEC`  
Owner：Nexus

## 1. Scope

本规范冻结 Nexus 空间坐标对象的第一版跨仓库语义，供 `Nexus-Core` F1 只读 conformance 使用。它冻结数据语义和失败边界，不代表坐标分配器、空间检索器或 GH²I 已实现。

本规范不改变 Nexus-Core SQLite 主事实源，也不授权 Core 写入坐标、空间节点、边或 GH²I 主索引。

## 2. Version identity

| Field | Value |
|---|---|
| `schema_version` | `nexus-coordinate-v1` |
| `schema_hash` | `sha256:3eb8d772310d06c11a3ed0073ca8f317e1aa0f965819f525f46353220a3b3f8b` |
| `coordinate_dimensions` | `4` |
| `coordinate_range` | 每一维为闭区间 `[0.0, 1.0]` |
| `numeric_precision` | 最多 6 位小数；超出精度拒绝，不自动四舍五入 |
| `time_encoding` | UTC ISO-8601，使用 `Z`，例如 `2026-08-20T00:00:00Z` |

Hash descriptor（UTF-8、无换行）为：

```text
nexus-coordinate-v1|dimensions=4|range=0.0..1.0|precision=6-decimal-places|time=UTC-ISO8601-Z|d1=discipline|d2=abstraction|d3=temporal|d4=scale|node_id=node:<anchor_id>|coordinate_status=proposed,validated,deprecated|unknown_fields=reject|partial_batch=rollback|gh2i=derived-index-only
```

`schema_hash` 是上述 descriptor 的 SHA-256 小写十六进制值；规范正文或实现字段变化时必须提升 schema version 或重新形成 owner decision。

## 3. Coordinate dimensions

坐标按对象字段 `d1` 至 `d4` 表示，顺序不可交换：

| Key | Name | `0.0` anchor | `1.0` anchor |
|---|---|---|---|
| `d1` | Discipline | pure natural science | cross-disciplinary / unclassifiable |
| `d2` | Abstraction | concrete entity | pure abstract / meta-cognition |
| `d3` | Temporal | eternal / foundational | instantaneous / frontier |
| `d4` | Scale | subatomic / code-line level | cosmic / civilizational level |

坐标是可解释的粗定位信号，不是事实置信度、重要性、质量、embedding 或情感分数。`d1` 的高值表示跨学科性，不表示某个固定学科名称；四维数值不能单独推导内容真伪。

## 4. Canonical object

规范化对象必须包含以下字段，未知字段按 fail-closed 处理：

```json
{
  "schema_version": "nexus-coordinate-v1",
  "anchor_id": "anc_example_001",
  "node_id": "node:anc_example_001",
  "coordinates": {"d1": 0.8, "d2": 0.3, "d3": 0.9, "d4": 0.6},
  "coordinate_status": "validated",
  "source_ref": "nexus://coordinate/anc_example_001",
  "created_at": "2026-08-20T00:00:00Z",
  "updated_at": "2026-08-20T00:00:00Z"
}
```

### 4.1 Required field rules

- `anchor_id` 是 Nexus 锚点的稳定主标识，创建后不可因坐标变化而改变。
- `node_id` 为确定性派生标识，格式为 `node:<anchor_id>`；不得由坐标值生成。
- `coordinates` 必须同时包含 `d1`、`d2`、`d3`、`d4`，值必须是有限 JSON number。
- `coordinate_status` 只能为 `proposed`、`validated` 或 `deprecated`。
- `source_ref` 必须指向可追溯的 Nexus 来源；不得包含凭据或原始会话 payload。
- 时间字段必须使用 UTC `Z`；`updated_at` 不得早于 `created_at`。

### 4.2 Null and unknown fields

- 必填字段不得为 `null`。
- 坐标缺失、类型错误、超出范围或超过 6 位小数时拒绝对象。
- v1 不允许未知字段；未来扩展必须提升 schema version 并重新完成 conformance。
- 不允许通过默认值、隐式转换或截断修复非法坐标。

## 5. Stable edge identity

v1 允许描述派生关系，但不要求 Core 存储或写入关系。边对象使用：

```text
edge_id = edge:<source_node_id>:<relation_type>:<target_node_id>
```

`relation_type` 必须是规范化 ASCII token；同一方向、同一类型和同一端点只能生成一个 `edge_id`。边坐标或 GH²I bucket 变化不得改变 `edge_id`。

## 6. GH²I boundary

GH²I v1 只能作为上述 canonical object 的派生空间索引：

1. 从 canonical object 构建；不反向成为 coordinate source-of-truth。
2. 可以独立重建、失效、删除和重新生成；不删除 Nexus 锚点或 Core memory facts。
3. 索引构建失败、损坏或版本不匹配时，查询回退到 canonical source / FlatRetriever 语义。
4. GH²I 的 bucket、hash、gravity score、route、local index 和 cache state 不属于 canonical object。
5. GH²I 不得直接写入 Nexus-Core SQLite、Core graph 或 stable memory 状态。

## 7. Import and compatibility policy

| Input | Result | Core write |
|---|---|---:|
| Valid `nexus-coordinate-v1` object | accepted for read-only conformance | no |
| Missing field / wrong type / range or precision error | rejected with deterministic reason | no |
| Unknown schema version | rejected | no |
| Unknown field | rejected | no |
| Partial batch import | reject whole batch and rollback | no partial write |
| Schema hash drift | defer pending owner decision | no |
| Deprecated coordinate object | observable with deprecated status | no reactivation |

## 8. Admission decision

`NX-N1-CANONICAL-SPEC` is frozen at the design level on 2026-08-20 under the user's explicit authorization. Actual coordinate implementation remains outside this document and must first pass F1 Core conformance.

The corresponding Nexus-Core task is `F1-SPATIAL-INTEROP-CONTRACT-V1-CONFORMANCE`, limited to a read-only adapter, fixture runner and negative tests. No spatial write, GH²I main-index write, graph write, runtime, provider, credential or cross-host capability is authorized.
