"""
Nexus 锚点系统
从对话中提取结构化锚点（事实、决策、偏好、规则），存储为 JSON。
锚点是三维知识模型的底层（现实层），用于跨会话记忆和幻觉防御。
"""

from .anchor import Anchor, AnchorType, CelestialType, AnchorStore, compute_mass, classify_celestial

__all__ = ["Anchor", "AnchorType", "CelestialType", "AnchorStore", "compute_mass", "classify_celestial"]
