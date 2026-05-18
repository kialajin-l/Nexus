"""RuleForge 规则引擎 — Python 原型

核心思路：通过声明式规则约束 AI 在信息获取和传递时的准确性，
而非控制用户行为。每条规则由条件（RuleCondition）和动作（RuleAction）组成，
支持权重自适应学习。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── 数据类 ───────────────────────────────────────────────────────────────────


@dataclass
class RuleCondition:
    """规则触发条件，基于坐标空间中的各维度进行匹配。"""

    discipline: Optional[str] = None
    abstraction: Optional[str] = None
    temporality: Optional[str] = None
    scale: Optional[str] = None
    exclude_cross_discipline: bool = False
    exclude_disciplines: List[str] = field(default_factory=list)

    def matches(self, coords: Dict[str, Any], is_cross_discipline: bool = False) -> bool:
        """检查给定坐标是否满足此条件。

        Args:
            coords: 坐标字典，键为维度名（discipline, abstraction, temporality, scale）。
            is_cross_discipline: 当前条目是否跨学科。

        Returns:
            True 表示条件匹配，规则应被触发。
        """
        # 跨学科排除检查
        if self.exclude_cross_discipline and is_cross_discipline:
            return False

        # 学科排除列表检查
        if self.exclude_disciplines:
            current_discipline = coords.get("discipline", "")
            if current_discipline in self.exclude_disciplines:
                return False

        # 逐维度匹配（None 表示不约束该维度）
        if self.discipline is not None:
            if coords.get("discipline") != self.discipline:
                return False
        if self.abstraction is not None:
            if coords.get("abstraction") != self.abstraction:
                return False
        if self.temporality is not None:
            if coords.get("temporality") != self.temporality:
                return False
        if self.scale is not None:
            if coords.get("scale") != self.scale:
                return False

        return True


@dataclass
class RuleAction:
    """规则动作：对指定维度的值进行钳位修正。"""

    dimension: str
    clamp_min: float
    clamp_max: float
    target: Optional[float] = None

    def apply(self, value: float) -> float:
        """将 value 钳位到 [clamp_min, clamp_max] 范围内。

        Args:
            value: 原始值。

        Returns:
            修正后的值。
        """
        return max(self.clamp_min, min(self.clamp_max, value))


@dataclass
class Rule:
    """一条完整的规则定义。"""

    id: str
    name: str
    condition: RuleCondition
    action: RuleAction
    weight: float = 1.0
    priority: int = 1
    enabled: bool = True
    description: str = ""


@dataclass
class RuleResult:
    """单条规则的评估结果。"""

    rule_id: str
    triggered: bool
    dimension: str
    original: float
    corrected: float
    weight: float
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "triggered": self.triggered,
            "dimension": self.dimension,
            "original": self.original,
            "corrected": self.corrected,
            "weight": self.weight,
            "reason": self.reason,
        }


# ─── 默认规则 ─────────────────────────────────────────────────────────────────

DEFAULT_RULES: List[Rule] = [
    Rule(
        id="R1",
        name="instance_abstraction_clamp",
        condition=RuleCondition(abstraction="instance"),
        action=RuleAction(dimension="d2", clamp_min=0.00, clamp_max=0.10),
        weight=1.0,
        priority=1,
        description="实例层抽象度应保持在极低区间 [0.00, 0.10]",
    ),
    Rule(
        id="R2",
        name="method_abstraction_clamp",
        condition=RuleCondition(abstraction="method"),
        action=RuleAction(dimension="d2", clamp_min=0.20, clamp_max=0.30),
        weight=1.0,
        priority=1,
        description="方法层抽象度应保持在中低区间 [0.20, 0.30]",
    ),
    Rule(
        id="R3",
        name="theory_abstraction_clamp",
        condition=RuleCondition(abstraction="theory"),
        action=RuleAction(dimension="d2", clamp_min=0.45, clamp_max=0.55),
        weight=1.0,
        priority=1,
        description="理论层抽象度应保持在中高区间 [0.45, 0.55]",
    ),
    Rule(
        id="R4",
        name="cs_discipline_cross_exclusion",
        condition=RuleCondition(discipline="CS", exclude_cross_discipline=True),
        action=RuleAction(dimension="d1", clamp_min=0.20, clamp_max=0.30),
        weight=1.0,
        priority=2,
        description="计算机学科（非跨学科）的 d1 维度钳位 [0.20, 0.30]",
    ),
]


# ─── 引擎 ─────────────────────────────────────────────────────────────────────


class RuleForge:
    """规则约束引擎。

    评估坐标空间中的条目，根据规则进行修正，并支持权重自适应学习。
    """

    def __init__(
        self,
        rules: Optional[List[Rule]] = None,
        learning_rate: float = 0.2,
        min_weight: float = 0.3,
    ):
        self.rules: List[Rule] = rules if rules is not None else list(DEFAULT_RULES)
        self.learning_rate = learning_rate
        self.min_weight = min_weight
        self._eval_count = 0
        self._trigger_count = 0

    # ── 评估 ──────────────────────────────────────────────────────────────

    def evaluate(
        self,
        coords: Dict[str, Any],
        labels: Optional[Dict[str, Any]] = None,
        is_cross_discipline: bool = False,
    ) -> List[RuleResult]:
        """评估所有已启用规则对给定坐标的作用。

        Args:
            coords: 坐标字典，如 {"discipline": "CS", "abstraction": "instance", ...}。
            labels: 可选的标签信息（预留扩展）。
            is_cross_discipline: 是否跨学科。

        Returns:
            所有规则的评估结果列表。
        """
        self._eval_count += 1
        results: List[RuleResult] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            triggered = rule.condition.matches(coords, is_cross_discipline)
            dimension = rule.action.dimension
            original = coords.get(dimension, 0.0)
            if not isinstance(original, (int, float)):
                original = 0.0

            if triggered:
                self._trigger_count += 1
                corrected = rule.action.apply(float(original))
                reason = f"规则 {rule.id} 触发：{rule.description}"
            else:
                corrected = float(original)
                reason = f"规则 {rule.id} 未触发"

            results.append(
                RuleResult(
                    rule_id=rule.id,
                    triggered=triggered,
                    dimension=dimension,
                    original=float(original),
                    corrected=corrected,
                    weight=rule.weight,
                    reason=reason,
                )
            )

        return results

    # ── 修正应用 ──────────────────────────────────────────────────────────

    def apply_corrections(
        self, coords: Dict[str, Any], rule_results: List[RuleResult]
    ) -> Dict[str, Any]:
        """根据规则结果对坐标进行修正。

        同一维度被多条规则触发时，按权重加权平均。

        Args:
            coords: 原始坐标字典。
            rule_results: evaluate() 返回的结果列表。

        Returns:
            修正后的坐标字典（副本，不修改原始数据）。
        """
        corrected = dict(coords)

        # 按维度分组已触发的修正
        dimension_corrections: Dict[str, List[tuple]] = {}  # dim → [(corrected_val, weight)]
        for r in rule_results:
            if not r.triggered:
                continue
            dim = r.dimension
            if dim not in dimension_corrections:
                dimension_corrections[dim] = []
            dimension_corrections[dim].append((r.corrected, r.weight))

        # 加权平均合并
        for dim, corrections in dimension_corrections.items():
            total_weight = sum(w for _, w in corrections)
            if total_weight <= 0:
                continue
            weighted_sum = sum(v * w for v, w in corrections)
            corrected[dim] = weighted_sum / total_weight

        return corrected

    # ── 权重自适应 ────────────────────────────────────────────────────────

    def adapt_weights(
        self, rule_results: List[RuleResult], feedback: Dict[str, float]
    ) -> None:
        """权重自适应（EXP-006）

        W(t+1) = W(t) + η × feedback

        Args:
            rule_results: 上一轮规则结果（当前未使用，保留接口）
            feedback: {rule_id: +0.1 (正确修正) / -0.1 (错误修正)}
        """
        for rule in self.rules:
            if rule.id in feedback:
                fb = feedback[rule.id]
                rule.weight += self.learning_rate * fb
                rule.weight = max(0.0, min(1.0, rule.weight)) 
