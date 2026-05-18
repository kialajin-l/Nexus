"""
Nexus Guard · 幻觉防御
意图识别 + 多路径猜想 + 用户选择，将 AI 幻觉从"锚点锚向错误"中解救出来。
"""

from .guard import Guard, IntentAnalysis, HallucinationReport

__all__ = ["Guard", "IntentAnalysis", "HallucinationReport"]
