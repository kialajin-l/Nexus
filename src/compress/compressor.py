"""
上下文压缩器

三层压缩：
  层级 1：文本去冗（合并重复、删除无信息量消息）
  层级 2：锚点提取（结构拆分、形成确定性知识）
  层级 3：锚点精炼（去重合并、质量评估）

核心理论：压缩的层级放得越低，越能有效减少数据传输中产生的错误。
锚点层是"信号"和"噪音"的分界线——在锚点层压缩，压缩的是纯净信号。
"""

import json
import math
import os
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone

from ..anchor.anchor import Anchor, AnchorType, AnchorStore


# ── Token 估算 ────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """
    粗略估算 token 数。
    中文 1 字 ≈ 2 tokens，英文 1 词 ≈ 1.3 tokens。
    """
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - cn_chars
    return int(cn_chars * 2 + other_chars * 0.25)


# ── 压缩报告 ──────────────────────────────────────────────

@dataclass
class CompressionReport:
    """压缩结果报告"""
    original_tokens: int = 0
    level1_tokens: int = 0
    level2_count: int = 0
    level2_tokens: int = 0
    level3_count: int = 0
    level3_tokens: int = 0
    compression_ratio: float = 0.0
    anchors: List[dict] = field(default_factory=list)
    summary: str = ""

    @property
    def savings_percent(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return round((1 - self.level3_tokens / self.original_tokens) * 100, 1)

    def to_dict(self) -> dict:
        return {
            "original_tokens": self.original_tokens,
            "level1_tokens": self.level1_tokens,
            "level2_count": self.level2_count,
            "level2_tokens": self.level2_tokens,
            "level3_count": self.level3_count,
            "level3_tokens": self.level3_tokens,
            "compression_ratio": self.compression_ratio,
            "savings_percent": self.savings_percent,
            "summary": self.summary,
        }

    def format_report(self) -> str:
        return (
            f"📊 压缩报告\n\n"
            f"原始对话：~{self.original_tokens} tokens\n"
            f"层级 1（文本去冗）：~{self.level1_tokens} tokens（节省 "
            f"{self._pct(self.original_tokens, self.level1_tokens)}）\n"
            f"层级 2（锚点提取）：{self.level2_count} 个锚点，~{self.level2_tokens} tokens（节省 "
            f"{self._pct(self.original_tokens, self.level2_tokens)}）\n"
            f"层级 3（锚点精炼）：{self.level3_count} 个锚点，~{self.level3_tokens} tokens（节省 "
            f"{self.savings_percent}%）\n\n"
            f"压缩比：{self.compression_ratio}:1"
        )

    @staticmethod
    def _pct(original: int, compressed: int) -> str:
        if original == 0:
            return "0%"
        return f"{round((1 - compressed / original) * 100, 1)}%"


# ── 压缩器 ────────────────────────────────────────────────

class Compressor:
    """
    三层压缩器。

    用法：
        store = AnchorStore("path/to/anchors.json")
        compressor = Compressor(store)
        report = compressor.compress(dialogue_messages)
        print(report.format_report())
    """

    def __init__(self, store: AnchorStore):
        self.store = store

    def compress(self, messages: List[dict], max_anchors: int = 0) -> CompressionReport:
        """
        执行三层压缩。

        messages 格式：[{"role": "user"|"assistant", "content": "..."}, ...]

        返回 CompressionReport。
        """
        report = CompressionReport()

        # ── 原始 token ──
        full_text = "\n".join(m.get("content", "") for m in messages)
        report.original_tokens = estimate_tokens(full_text)

        # ── 层级 1：文本去冗 ──
        cleaned = self._level1_dedup(messages)
        cleaned_text = "\n".join(cleaned)
        report.level1_tokens = estimate_tokens(cleaned_text)

        # ── 层级 2：锚点提取 ──
        # 注意：真实场景中这一步由 LLM 完成（Agent 读取对话后按锚点格式输出）
        # 这里提供基础的关键词匹配作为 fallback / 离线模式
        anchors = self._level2_extract_anchors(cleaned)
        report.level2_count = len(anchors)
        report.level2_tokens = sum(estimate_tokens(a.get("content", "")) for a in anchors)

        # ── 层级 3：锚点精炼 ──
        refined = self._level3_refine(anchors)
        if max_anchors > 0:
            refined = refined[:max_anchors]
        report.level3_count = len(refined)
        report.level3_tokens = sum(estimate_tokens(a.get("content", "")) for a in refined)
        report.anchors = refined

        # ── 压缩比 ──
        if report.level3_tokens > 0:
            report.compression_ratio = round(report.original_tokens / report.level3_tokens, 1)
        else:
            report.compression_ratio = 0.0

        report.summary = f"从 {len(messages)} 条消息中提取 {len(refined)} 个锚点"
        return report

    # ── 层级 1：文本去冗 ──

    @staticmethod
    def _level1_dedup(messages: List[dict]) -> List[str]:
        """
        文本级压缩：
        - 删除无信息量消息（"好的"、"嗯"、"收到"等）
        - 去重：完全相同的消息只保留第一次
        """
        noise_patterns = {
            "好的", "嗯", "收到", "ok", "OK", "了解", "明白",
            "是的", "对", "可以", "没问题", "谢谢", "感谢",
        }
        cleaned = []
        seen = set()

        for msg in messages:
            content = msg.get("content", "").strip()
            if not content:
                continue
            if content in noise_patterns:
                continue
            key = content[:100]
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(content)

        return cleaned

    # ── 层级 2：锚点提取（关键词 fallback）──

    @staticmethod
    def _level2_extract_anchors(messages: List[str]) -> List[dict]:
        """
        从清洗后的消息中提取锚点结构。
        实际场景中由 LLM 完成，这里是离线 fallback。
        """
        anchors = []
        rules = [
            (["决定", "确定", "选择", "采用", "就用", "定了", "方案"], "decision", 0.8),
            (["不要", "必须", "禁止", "应该", "规则", "不能"], "rule", 0.7),
            (["喜欢", "偏好", "更好", "习惯", "风格", "更喜欢"], "preference", 0.7),
            (["是", "等于", "发布于", "创建于", "包含", "定义为", "位于"], "fact", 0.6),
        ]

        for msg in messages:
            for keywords, anchor_type, confidence in rules:
                if any(k in msg for k in keywords):
                    anchors.append({
                        "type": anchor_type,
                        "content": msg[:200],
                        "confidence": confidence,
                    })
                    break  # 一条消息只归一个类型

        return anchors

    # ── 层级 3：锚点精炼 ──

    @staticmethod
    def _level3_refine(anchors: List[dict]) -> List[dict]:
        """
        精炼锚点：
        - 去重（前 50 字符相同的合并）
        - 排序（按 confidence 降序）
        """
        if not anchors:
            return []

        seen = set()
        unique = []
        for a in anchors:
            key = a.get("content", "")[:50]
            if key not in seen:
                seen.add(key)
                unique.append(a)

        unique.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return unique


# ── 对比工具 ──────────────────────────────────────────────

def compare_traditional_vs_nexus(
    original_tokens: int,
    nexus_tokens: int,
    fidelity: float = 0.85,
) -> str:
    """
    对比传统方式 vs Nexus 方式的 token 消耗。

    fidelity: 信息保真度估算（默认 85%）
    """
    saved = original_tokens - nexus_tokens
    pct = round(saved / original_tokens * 100, 1) if original_tokens > 0 else 0

    return (
        "| 方式 | Token 消耗 | 信息保真度 | 幻觉风险 |\n"
        "|------|-----------|-----------|---------|\n"
        f"| 传统（完整上下文） | ~{original_tokens} | 100% | 高（噪音多） |\n"
        f"| Nexus（锚点压缩） | ~{nexus_tokens} | ~{fidelity*100:.0f}% | 低（纯净信号） |\n"
        f"| 节省 | {pct}% | -{(1-fidelity)*100:.0f}% | 显著降低 |"
    )
