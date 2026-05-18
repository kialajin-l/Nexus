"""
Nexus Pipeline — 端到端整合流水线

流程：用户输入 → Nexus Refiner → Gate Controller → [RuleForge] → 最终输出
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.refiner import Refiner, RefinerResult
from src.gate import GateController, GateAction, GateResult
from src.ruleforge import RuleForge, RuleResult


@dataclass
class PipelineResult:
    """流水线完整结果"""
    user_input: str = ""
    refiner: Optional[RefinerResult] = None
    gate: Optional[GateResult] = None
    rule_results: List[RuleResult] = field(default_factory=list)
    coordinates: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    rules_applied: int = 0
    corrections_made: int = 0

    def to_dict(self) -> dict:
        return {
            "user_input": self.user_input,
            "coordinates": self.coordinates,
            "metadata": {
                "refiner_confidence": self.refiner.confidence if self.refiner else 0,
                "gate_action": self.gate.action.value if self.gate else "unknown",
                "rules_applied": self.rules_applied,
                "corrections_made": self.corrections_made,
            },
            "refiner": self.refiner.to_dict() if self.refiner else None,
            "gate": self.gate.to_dict() if self.gate else None,
            "rule_results": [r.to_dict() for r in self.rule_results],
        }


class Pipeline:
    """
    Nexus + RuleForge 整合流水线

    三阶段处理：
    1. Nexus Refiner: 模糊输入 → 结构化 4D 标签
    2. Gate Controller: 置信度判断 → 是否需要规则
    3. RuleForge: 精细条件匹配 → 坐标修正
    """

    def __init__(
        self,
        refiner: Optional[Refiner] = None,
        gate: Optional[GateController] = None,
        ruleforge: Optional[RuleForge] = None,
    ):
        self.refiner = refiner or Refiner()
        self.gate = gate or GateController()
        self.ruleforge = ruleforge or RuleForge()

    def process(
        self,
        user_input: str,
        refiner_response: Optional[dict] = None,
    ) -> PipelineResult:
        """
        端到端处理

        Args:
            user_input: 用户原始输入
            refiner_response: 精炼器的 LLM 响应 JSON
                              如果为 None，返回 prompt 让外部调用 LLM 后再传回

        Returns:
            PipelineResult: 完整处理结果
        """
        result = PipelineResult(user_input=user_input)

        # 阶段 1：精炼
        if refiner_response is not None:
            result.refiner = self.refiner.parse_response(refiner_response)
        else:
            prompt = self.refiner.build_prompt(user_input)
            result.refiner = RefinerResult(reasoning=f"[PENDING_LLM] {prompt}")
            return result

        # 阶段 2：门控
        result.gate = self.gate.evaluate(
            confidence=result.refiner.confidence,
            discipline=result.refiner.discipline,
            is_cross_discipline=result.refiner.is_cross_discipline,
            matched_disciplines=result.refiner.matched_disciplines,
        )

        # 阶段 3：规则修正（仅在门控允许时）
        if result.gate.action != GateAction.DIRECT:
            labels = {
                "discipline": result.refiner.discipline,
                "abstraction": result.refiner.abstraction,
                "temporality": result.refiner.temporality,
                "scale": result.refiner.scale,
            }
            coords = {
                "d1": result.refiner.coordinates[0],
                "d2": result.refiner.coordinates[1],
                "d3": result.refiner.coordinates[2],
                "d4": result.refiner.coordinates[3],
            }

            result.rule_results = self.ruleforge.evaluate(
                coords=coords,
                labels=labels,
                is_cross_discipline=result.refiner.is_cross_discipline,
            )

            corrected = self.ruleforge.apply_corrections(coords, result.rule_results)
            result.coordinates = [corrected["d1"], corrected["d2"], corrected["d3"], corrected["d4"]]
            result.rules_applied = sum(1 for r in result.rule_results if r.triggered)
            result.corrections_made = sum(
                1 for r in result.rule_results
                if r.triggered and abs(r.original - r.corrected) > 0.001
            )
        else:
            result.coordinates = result.refiner.coordinates.copy()

        return result

    def get_stats(self) -> dict:
        return {
            "refiner": "active",
            "gate": {"threshold": self.gate.threshold},
            "ruleforge": self.ruleforge.get_stats(),
        }
