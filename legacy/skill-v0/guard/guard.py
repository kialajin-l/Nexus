"""
Nexus Guard · 幻觉防御

核心理论：
  AI 幻觉的本质是思维层锚点锚向错误。
  防御方式：先锚定，再联想。

三大场景：
  1. 意图识别 — 用户输入模糊指令时，生成多条猜想路径让用户选择
  2. 幻觉检测 — 分析 AI 回答是否存在幻觉风险
  3. 多路径执行 — 复杂任务拆解，为每条路径标注风险和成本

每次用户选择都会生成一个新的决策锚点，逐步建立"用户在什么语境下想要什么"的规则库。
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from ..anchor.anchor import Anchor, AnchorType, AnchorStore


# ── 意图分析结果 ──────────────────────────────────────────

@dataclass
class IntentOption:
    """一个意图选项"""
    label: str = ""           # 意图总结（≤20 字）
    probability: float = 0.0  # 概率 0-1
    plan: str = ""            # 一句话描述执行方案
    risk: str = "低"          # 风险等级：低/中/高


@dataclass
class IntentAnalysis:
    """意图分析结果"""
    raw_input: str = ""
    options: List[IntentOption] = field(default_factory=list)
    recommended: int = 0      # 推荐选项的索引

    def format(self) -> str:
        lines = ["🔍 意图分析\n", "我理解你可能想要：\n"]
        for i, opt in enumerate(self.options):
            marker = " 👈 推荐" if i == self.recommended else ""
            lines.append(
                f"{chr(65 + i)}. {opt.label}（概率 {opt.probability:.0%}）{marker}\n"
                f"   → 计划：{opt.plan}\n"
                f"   → 风险：{opt.risk}\n"
            )
        lines.append("请选择，或者告诉我你真正想要的。")
        return "\n".join(lines)


# ── 幻觉检测结果 ──────────────────────────────────────────

@dataclass
class SentenceCheck:
    """单句检测结果"""
    text: str = ""
    status: str = "✅"       # ✅ 可信 / ⚠️ 存疑 / ❌ 高风险
    reason: str = ""


@dataclass
class HallucinationReport:
    """幻觉检测报告"""
    question: str = ""
    answer: str = ""
    sentences: List[SentenceCheck] = field(default_factory=list)

    @property
    def risk_count(self) -> int:
        return sum(1 for s in self.sentences if s.status == "❌")

    @property
    def warn_count(self) -> int:
        return sum(1 for s in self.sentences if s.status == "⚠️")

    def format(self) -> str:
        lines = [
            "🛡️ 幻觉检测报告\n",
            f"原始问题：{self.question}\n",
            f"AI 回答：{self.answer[:80]}{'...' if len(self.answer) > 80 else ''}\n",
            "逐句分析：\n",
        ]
        for i, s in enumerate(self.sentences, 1):
            lines.append(f"{i}. \"{s.text[:60]}\" {s.status} {s.reason}")
        lines.append("")
        if self.risk_count > 0:
            lines.append(f"⚠️ 发现 {self.risk_count} 个高风险幻觉，建议重新生成。")
        if self.warn_count > 0:
            lines.append(f"💡 {self.warn_count} 个存疑项，建议补充验证。")
        if self.risk_count == 0 and self.warn_count == 0:
            lines.append("✅ 未发现明显幻觉风险。")
        return "\n".join(lines)


# ── Guard 主类 ─────────────────────────────────────────────

class Guard:
    """
    幻觉防御器。

    用法：
        store = AnchorStore("path/to/anchors.json")
        guard = Guard(store)

        # 意图识别
        analysis = guard.analyze_intent("帮我处理一下那个文件")
        print(analysis.format())

        # 记录用户选择 → 生成决策锚点
        guard.record_choice(analysis, choice_index=1)

        # 幻觉检测
        report = guard.detect_hallucination("问题", "AI的回答")
        print(report.format())
    """

    def __init__(self, store: AnchorStore):
        self.store = store

    # ── 场景 1：意图识别 ──────────────────────────────────

    def analyze_intent(self, user_input: str) -> IntentAnalysis:
        """
        分析用户输入的意图，生成多条猜想路径。

        注意：概率分配和方案生成需要 LLM 辅助。
        这里只做结构化占位，真实场景由 Agent 调用 LLM 完成。
        """
        # 检查历史决策锚点，看是否有类似输入的先例
        history = self.store.search(user_input, limit=5)
        decisions = [a for a in history if a.type == AnchorType.DECISION]

        analysis = IntentAnalysis(raw_input=user_input)

        if decisions:
            # 有历史先例，优先推荐之前用户选择过的路径
            last_decision = decisions[-1]
            analysis.options.append(IntentOption(
                label="沿用上次选择",
                probability=0.7,
                plan=last_decision.content,
                risk="低",
            ))
            analysis.options.append(IntentOption(
                label="探索新路径",
                probability=0.3,
                plan="尝试不同的执行方式",
                risk="中",
            ))
            analysis.recommended = 0
        else:
            # 无历史，生成默认选项占位
            analysis.options.append(IntentOption(
                label="直接执行",
                probability=0.5,
                plan="按字面意思理解并执行",
                risk="低",
            ))
            analysis.options.append(IntentOption(
                label="确认意图",
                probability=0.5,
                plan="先向用户确认具体需求再执行",
                risk="低",
            ))
            analysis.recommended = 1

        return analysis

    def record_choice(self, analysis: IntentAnalysis, choice_index: int) -> Anchor:
        """
        记录用户的选择，生成决策锚点。

        每次用户选择 = 一个决策锚点。
        下次遇到类似输入 → 加载历史决策锚点 → 直接走用户偏好的路径。
        """
        if choice_index < 0 or choice_index >= len(analysis.options):
            raise ValueError(f"choice_index {choice_index} 超出范围（0-{len(analysis.options)-1}）")

        chosen = analysis.options[choice_index]
        anchor = Anchor(
            type=AnchorType.DECISION,
            content=f"用户选择了意图「{chosen.label}」：{chosen.plan}",
            source=f"guard:intent:{analysis.raw_input[:50]}",
            confidence=1.0,
            tags=["guard", "decision", "intent"],
        )
        self.store.add(anchor)
        return anchor

    # ── 场景 2：幻觉检测 ──────────────────────────────────

    def detect_hallucination(self, question: str, answer: str) -> HallucinationReport:
        """
        分析 AI 回答是否存在幻觉风险。

        注意：逐句可信度判断需要 LLM 辅助。
        这里只做结构化拆分，真实场景由 Agent 调用 LLM 完成。
        """
        # 按句拆分
        sentences = [s.strip() for s in answer.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n").split("\n") if s.strip()]

        report = HallucinationReport(question=question, answer=answer)

        for sent in sentences:
            # 检查是否有锚点支撑
            anchors = self.store.search(sent, limit=3)
            if anchors:
                best = anchors[0]
                if best.confidence >= 0.8:
                    report.sentences.append(SentenceCheck(text=sent, status="✅", reason="有锚点支撑"))
                else:
                    report.sentences.append(SentenceCheck(text=sent, status="⚠️", reason="锚点置信度不足"))
            else:
                report.sentences.append(SentenceCheck(text=sent, status="⚠️", reason="无锚点支撑，可能是联想"))

        return report

    # ── 场景 3：多路径执行 ────────────────────────────────

    def plan_paths(self, task: str, steps: List[dict]) -> str:
        """
        为复杂任务生成多路径分析。

        steps 格式：[{"name": "步骤名", "paths": [{"desc": "...", "risk": "低/中/高", "tokens": 100}, ...]}, ...]

        返回格式化的路径分析文本。
        """
        lines = [
            f"📋 任务拆解 + 路径分析\n",
            f"任务：{task}\n",
            f"拆解为 {len(steps)} 个步骤：\n",
        ]

        total_tokens = 0
        recommended_path = []

        for i, step in enumerate(steps, 1):
            name = step.get("name", f"步骤 {i}")
            paths = step.get("paths", [])
            lines.append(f"步骤 {i}：{name}")

            best_idx = 0
            best_tokens = float("inf")

            for j, p in enumerate(paths):
                marker = ""
                if p.get("tokens", float("inf")) < best_tokens:
                    best_tokens = p.get("tokens", float("inf"))
                    best_idx = j

            for j, p in enumerate(paths):
                marker = "（推荐）" if j == best_idx else ""
                lines.append(f"  路径 {chr(65+j)}：{p.get('desc', '')}（风险：{p.get('risk', '未知')}）{marker}")

            recommended_path.append(chr(65 + best_idx))
            total_tokens += best_tokens
            lines.append("")

        lines.append(f"推荐方案：{' → '.join(recommended_path)}")
        lines.append(f"预计 token：~{total_tokens}")
        lines.append("\n确认后执行？")

        return "\n".join(lines)
