"""捕获闸门 — 评估记忆是否值得保存。"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gateway_paths import ROOT


@dataclass
class CaptureConfig:
    """捕获配置。"""
    min_significance: str = "auto"  # auto / A / B / C
    dedup_window: int = 7  # 去重窗口（天）
    
    @property
    def projects(self) -> list[dict]:
        """从 DASHBOARD 加载项目列表。"""
        dash_path = ROOT / "DASHBOARD.md"
        if not dash_path.exists():
            return []
        text = dash_path.read_text(encoding="utf-8")
        projects = []
        pattern = r'### 项目\s*\d*\s*[:：]\s*(.+?)\n'
        for match in re.finditer(pattern, text):
            projects.append({"name": match.group(1).strip()})
        return projects


@dataclass
class CaptureDecision:
    """捕获决策结果。"""
    should_capture: bool
    significance: str  # A / B / C / drop
    reason: str
    entry_type: str = "capture"


def evaluate_capture(content: str, source: str, config: CaptureConfig | None = None) -> CaptureDecision:
    """评估内容是否值得捕获。"""
    if config is None:
        config = CaptureConfig()
    
    content_lower = content.lower()
    
    # A 级：决策、原则、身份相关
    a_signals = ["决定", "原则", "优先级", "目标", "里程碑", "复盘"]
    for s in a_signals:
        if s in content_lower:
            return CaptureDecision(True, "A", f"命中 A 级信号「{s}」")
    
    # B 级：项目进展、方法、知识
    b_signals = ["完成", "进度", "方法", "知识", "技巧", "经验"]
    for s in b_signals:
        if s in content_lower:
            return CaptureDecision(True, "B", f"命中 B 级信号「{s}」")
    
    # C 级：一般记录
    if len(content) > 50:
        return CaptureDecision(True, "C", "长度达标，作为一般记录")
    
    return CaptureDecision(False, "drop", "内容过短且无价值信号")
