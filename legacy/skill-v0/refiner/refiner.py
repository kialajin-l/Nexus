"""Nexus Refiner — 将模糊自然语言转化为结构化 4D 坐标标签

四个维度:
  D1: Discipline     — 学科归属
  D2: Abstraction    — 抽象层次
  D3: Temporality    — 时间属性
  D4: Scale          — 影响范围
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ── 四维枚举 ──────────────────────────────────────────────

class Discipline(str, Enum):
    """学科维度"""
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    MATHEMATICS = "mathematics"
    COMPUTER_SCIENCE = "computer_science"
    ENGINEERING = "engineering"
    MEDICINE = "medicine"
    ECONOMICS = "economics"
    PSYCHOLOGY = "psychology"
    LINGUISTICS = "linguistics"
    PHILOSOPHY = "philosophy"
    SOCIOLOGY = "sociology"
    OTHER = "other"


class Abstraction(str, Enum):
    """抽象层次维度"""
    INSTANCE = "instance"
    METHOD = "method"
    THEORY = "theory"
    CONCEPT = "concept"
    ABSTRACT = "abstract"


class Temporality(str, Enum):
    """时间属性维度"""
    TREND = "trend"
    CURRENT = "current"
    THEORETICAL = "theoretical"
    HISTORICAL = "historical"


class Scale(str, Enum):
    """影响范围维度"""
    PERSONAL = "personal"
    TEAM = "team"
    INDUSTRY = "industry"
    SOCIETY = "society"


# ── 锚点库 ────────────────────────────────────────────────

ANCHOR_LIBRARY: Dict[str, Dict[str, str]] = {
    "discipline": {
        "physics": "牛顿力学、量子力学、热力学、电磁学等物理现象与定律",
        "chemistry": "分子结构、化学反应、有机/无机化学、材料化学",
        "biology": "细胞生物学、遗传学、生态学、进化论、生物化学",
        "mathematics": "代数、几何、拓扑、概率论、数论、分析",
        "computer_science": "算法、数据结构、编程语言、操作系统、网络、AI",
        "engineering": "土木、机械、电气、航空航天、材料工程",
        "medicine": "临床医学、药理学、病理学、公共卫生、外科",
        "economics": "微观经济、宏观经济、金融、博弈论、计量经济",
        "psychology": "认知心理、发展心理、社会心理、临床心理、神经心理",
        "linguistics": "句法学、语义学、语用学、历史语言学、计算语言学",
        "philosophy": "逻辑学、伦理学、认识论、形而上学、美学",
        "sociology": "社会结构、文化研究、组织社会学、社会网络",
    },
    "abstraction": {
        "instance": "具体的、可直接观察的实例或对象（如某段代码、某个实验）",
        "method": "方法、技术、工具或操作流程（如排序算法、实验方法）",
        "theory": "理论框架、模型或系统性解释（如相对论、信息论）",
        "concept": "概念、定义或分类体系（如递归、熵、范式）",
        "abstract": "高度抽象的元理论、哲学思辨或跨领域原理",
    },
    "temporality": {
        "current": "当前正在发生的、当下的状态或实践",
        "historical": "过去的、历史性的事件或发展过程",
        "trend": "趋势性的、正在演变的、面向未来的",
        "theoretical": "超越时间的、纯理论的、假设性的",
    },
    "scale": {
        "personal": "影响个人层面（个人技能、个人决策、个人体验）",
        "team": "影响团队或组织层面（团队协作、项目管理、公司策略）",
        "industry": "影响行业或专业领域（行业标准、技术栈选型、市场格局）",
        "society": "影响社会或全人类层面（政策法规、伦理道德、文明进程）",
    },
}

# ── 跨学科标签 ────────────────────────────────────────────

CROSS_DISCIPLINE_LABELS: Dict[str, List[str]] = {
    "bioinformatics": ["biology", "computer_science"],
    "computational_linguistics": ["linguistics", "computer_science"],
    "mathematical_psychology": ["psychology", "mathematics"],
    "quantum_computing": ["physics", "computer_science"],
    "econophysics": ["economics", "physics"],
    "neuroeconomics": ["economics", "psychology"],
    "computational_biology": ["biology", "computer_science"],
    "mathematical_finance": ["mathematics", "economics"],
}


# ── 精炼器 Prompt ─────────────────────────────────────────

REFINER_PROMPT = """\
你是一个知识精炼器 (Nexus Refiner)。你的任务是将用户的自然语言输入 \
解析为结构化的 4D 知识坐标。

## 四个维度

### D1: Discipline (学科)
{discipline_anchors}

### D2: Abstraction (抽象层次)
{abstraction_anchors}

### D3: Temporality (时间属性)
{temporality_anchors}

### D4: Scale (影响范围)
{scale_anchors}

## 输出要求

请分析以下用户输入，并以 **严格 JSON** 格式返回结果（不要包含 markdown 代码块标记）：

用户输入: "{user_input}"

JSON schema:
{{
  "discipline": "<从上述学科列表中选择最匹配的一个>",
  "abstraction": "<从上述抽象层次列表中选择>",
  "temporality": "<从上述时间属性列表中选择>",
  "scale": "<从上述影响范围列表中选择>",
  "confidence": <0.0 到 1.0 之间的浮点数，表示你对分类的置信度>,
  "reasoning": "<简短说明你的判断依据，50字以内>"
}}

注意：
1. discipline 必须是上述列表中的值之一
2. 如果输入明显跨学科，选择最核心的学科，并在 reasoning 中说明
3. confidence 应反映你对分类的确定程度
"""


# ── RefinerResult ─────────────────────────────────────────

@dataclass
class RefinerResult:
    """精炼器输出结果"""
    discipline: str
    abstraction: str
    temporality: str
    scale: str
    coordinates: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    confidence: float = 0.0
    reasoning: str = ""
    is_cross_discipline: bool = False
    matched_disciplines: List[str] = field(default_factory=list)


# ── Refiner ───────────────────────────────────────────────

class Refiner:
    """将模糊自然语言转化为结构化 4D 坐标标签"""

    def build_prompt(self, user_input: str) -> str:
        """构建精炼器 Prompt

        Args:
            user_input: 用户的自然语言输入

        Returns:
            填充完毕的 Prompt 字符串
        """
        def _format_anchors(category: str) -> str:
            anchors = ANCHOR_LIBRARY[category]
            lines = []
            for key, desc in anchors.items():
                lines.append(f"  - **{key}**: {desc}")
            return "\n".join(lines)

        return REFINER_PROMPT.format(
            user_input=user_input,
            discipline_anchors=_format_anchors("discipline"),
            abstraction_anchors=_format_anchors("abstraction"),
            temporality_anchors=_format_anchors("temporality"),
            scale_anchors=_format_anchors("scale"),
        )

    def parse_response(self, response: dict) -> RefinerResult:
        """解析 LLM JSON 响应，计算 4D 坐标

        Args:
            response: LLM 返回的 JSON 字典，包含 discipline/abstraction/
                      temporality/scale/confidence/reasoning

        Returns:
            RefinerResult 实例
        """
        discipline = response.get("discipline", "other")
        abstraction = response.get("abstraction", "concept")
        temporality = response.get("temporality", "current")
        scale = response.get("scale", "personal")
        confidence = float(response.get("confidence", 0.5))
        reasoning = response.get("reasoning", "")

        # 检测跨学科
        is_cross = False
        matched: List[str] = []
        for cross_label, disciplines in CROSS_DISCIPLINE_LABELS.items():
            if discipline in disciplines:
                is_cross = True
                matched = disciplines
                break

        # 计算坐标
        d1 = self._discipline_to_coord(discipline)
        d2 = self._abstraction_to_coord(abstraction)
        d3 = self._temporality_to_coord(temporality)
        d4 = self._scale_to_coord(scale)

        return RefinerResult(
            discipline=discipline,
            abstraction=abstraction,
            temporality=temporality,
            scale=scale,
            coordinates=[d1, d2, d3, d4],
            confidence=confidence,
            reasoning=reasoning,
            is_cross_discipline=is_cross,
            matched_disciplines=matched,
        )

    def _discipline_to_coord(self, discipline: str) -> float:
        """学科标签转 D1 坐标 (0.00 ~ 1.00)

        映射逻辑：按学科的"形式化程度"排列
          physics=0.00 -> biology=0.15 -> cs=0.25 -> engineering=0.35
          -> math=0.50 -> chemistry=0.45 -> medicine=0.55
          -> economics=0.65 -> psychology=0.70 -> linguistics=0.75
          -> sociology=0.85 -> philosophy=1.00
        """
        mapping: Dict[str, float] = {
            "physics": 0.00,
            "biology": 0.15,
            "computer_science": 0.25,
            "engineering": 0.35,
            "chemistry": 0.45,
            "mathematics": 0.50,
            "medicine": 0.55,
            "economics": 0.65,
            "psychology": 0.70,
            "linguistics": 0.75,
            "sociology": 0.85,
            "philosophy": 1.00,
        }
        return mapping.get(discipline, 0.50)

    def _abstraction_to_coord(self, abstraction: str) -> float:
        """抽象层次转 D2 坐标 (0.00 ~ 1.00)

        instance=0.00 -> method=0.25 -> theory=0.50 -> concept=0.75 -> abstract=1.00
        """
        mapping: Dict[str, float] = {
            "instance": 0.00,
            "method": 0.25,
            "theory": 0.50,
            "concept": 0.75,
            "abstract": 1.00,
        }
        return mapping.get(abstraction, 0.50)

    def _temporality_to_coord(self, temporality: str) -> float:
        """时间属性转 D3 坐标 (0.00 ~ 1.00)

        trend=0.00 -> current=0.25 -> theoretical=0.50 -> historical=0.75
        """
        mapping: Dict[str, float] = {
            "trend": 0.00,
            "current": 0.25,
            "theoretical": 0.50,
            "historical": 0.75,
        }
        return mapping.get(temporality, 0.25)

    def _scale_to_coord(self, scale: str) -> float:
        """影响范围转 D4 坐标 (0.00 ~ 1.00)

        personal=0.00 -> team=0.25 -> industry=0.50 -> society=0.75
        """
        mapping: Dict[str, float] = {
            "personal": 0.00,
            "team": 0.25,
            "industry": 0.50,
            "society": 0.75,
        }
        return mapping.get(scale, 0.00)
