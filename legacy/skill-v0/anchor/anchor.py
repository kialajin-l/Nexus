"""
锚点核心定义与存储

锚点六元组：(x, m, C, L, τ, σ)
- x: 空间坐标（初始 4 维）
- m: 质量（综合重要性）
- C: 天体类型（恒星/行星/彗星/小行星）
- L: 本地索引
- τ: 创建时间
- σ: 稳定性系数
"""

import json
import math
import os
import uuid
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime, timezone


# ── 锚点类型 ──────────────────────────────────────────────

class AnchorType(str, Enum):
    """锚点的语义类型"""
    FACT = "fact"               # 经过验证的确定性知识
    DECISION = "decision"       # 用户做出的选择
    PREFERENCE = "preference"   # 用户的个人偏好
    RULE = "rule"               # 行为约束
    PROJECT = "project"         # 项目相关信息


class CelestialType(str, Enum):
    """天体分类（宇宙坐标模型）"""
    STAR = "恒星"       # m ≥ 0.7, σ ≥ 0.7
    PLANET = "行星"     # m ≥ 0.3, σ ≥ 0.5
    COMET = "彗星"      # 跨域关联 ≥ 3
    ASTEROID = "小行星" # 其他


# ── 锚点数据类 ────────────────────────────────────────────

@dataclass
class Anchor:
    """一个结构化锚点"""

    # 基础字段（提取时生成）
    id: str = field(default_factory=lambda: f"anchor_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}")
    type: AnchorType = AnchorType.FACT
    content: str = ""
    source: str = ""
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)
    anchors: List[str] = field(default_factory=list)  # 关联的其他锚点 ID

    # 宇宙坐标模型字段
    coordinates: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    mass: float = 0.5           # 质量 m ∈ [0, 1]
    celestial: CelestialType = CelestialType.ASTEROID
    stability: float = 0.5      # σ ∈ [0, 1]
    local_index: dict = field(default_factory=dict)

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        d["celestial"] = self.celestial.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Anchor":
        data = data.copy()
        data["type"] = AnchorType(data["type"])
        data["celestial"] = CelestialType(data["celestial"])
        return cls(**data)


# ── 质量函数 ──────────────────────────────────────────────

def compute_mass(
    access_count: int = 0,
    cite_count: int = 0,
    last_access_hours: float = 0,
    max_access: int = 100,
    max_cite: int = 50,
    alpha: float = 0.4,
    beta: float = 0.3,
    gamma: float = 0.3,
    decay_lambda: float = 0.01,
) -> float:
    """
    m(a) = α·f_access + β·f_cite + γ·f_decay

    f_access = log(1 + access_count) / log(1 + max_access)
    f_cite   = cite_count / max_cite
    f_decay  = e^(-λ · hours_since_last_access)
    """
    f_access = math.log(1 + access_count) / math.log(1 + max_access) if max_access > 0 else 0
    f_cite = min(cite_count / max_cite, 1.0) if max_cite > 0 else 0
    f_decay = math.exp(-decay_lambda * last_access_hours)

    mass = alpha * f_access + beta * f_cite + gamma * f_decay
    return round(min(max(mass, 0.0), 1.0), 4)


def classify_celestial(mass: float, stability: float, cross_domain_count: int = 0) -> CelestialType:
    """
    天体分类规则：
    - 恒星: m ≥ 0.7 且 σ ≥ 0.7
    - 行星: m ≥ 0.3 且 σ ≥ 0.5
    - 彗星: 跨域关联 ≥ 3
    - 小行星: 其他
    """
    if mass >= 0.7 and stability >= 0.7:
        return CelestialType.STAR
    if mass >= 0.3 and stability >= 0.5:
        return CelestialType.PLANET
    if cross_domain_count >= 3:
        return CelestialType.COMET
    return CelestialType.ASTEROID


# ── 锚点存储 ──────────────────────────────────────────────

class AnchorStore:
    """锚点的 JSON 文件存储"""

    def __init__(self, path: str):
        self.path = path
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            self._write({"version": "0.1.0", "updated_at": "", "anchors": []})

    def _read(self) -> dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_all(self) -> List[Anchor]:
        data = self._read()
        return [Anchor.from_dict(a) for a in data.get("anchors", [])]

    def save(self, anchor: Anchor):
        data = self._read()
        data["anchors"].append(anchor.to_dict())
        self._write(data)

    def save_batch(self, anchors: List[Anchor]):
        data = self._read()
        existing_ids = {a["id"] for a in data["anchors"]}
        for anchor in anchors:
            if anchor.id not in existing_ids:
                data["anchors"].append(anchor.to_dict())
                existing_ids.add(anchor.id)
        self._write(data)

    def find_similar(self, content: str, threshold: float = 0.8) -> Optional[Anchor]:
        """简单相似度查找：前 N 字符匹配"""
        prefix = content[:60]
        for anchor in self.load_all():
            if anchor.content[:60] == prefix:
                return anchor
        return None

    def update_confidence(self, anchor_id: str, delta: float = 0.1):
        data = self._read()
        for a in data["anchors"]:
            if a["id"] == anchor_id:
                a["confidence"] = min(1.0, a.get("confidence", 0.5) + delta)
                a["updated_at"] = datetime.now(timezone.utc).isoformat()
                break
        self._write(data)

    @property
    def count(self) -> int:
        return len(self._read().get("anchors", []))

    def stats(self) -> dict:
        data = self._read()
        anchors = data.get("anchors", [])
        types = {}
        for a in anchors:
            t = a.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
        return {"total": len(anchors), "types": types}
