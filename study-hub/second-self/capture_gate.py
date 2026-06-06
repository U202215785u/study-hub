"""捕获门 — 判断什么值得记住

不是所有内容都值得进记忆库。捕获门做第一层过滤。
"""
import re
from datetime import datetime


def should_capture(text: str, source: str = "chat") -> tuple[bool, str]:
    """判断文本是否值得捕获。
    
    Returns:
        (should_capture, reason)
    """
    text = text.strip()
    if len(text) < 10:
        return False, "太短"
    
    if len(text) > 5000:
        return False, "太长"
    
    # 过滤常见无意义内容
    noise_patterns = [
        r'^\d+$',  # 纯数字
        r'^[okOK]+$',
        r'^谢谢*$',
        r'^好的*$',
        r'^明白*$',
        r'^哈哈+$',
    ]
    for pattern in noise_patterns:
        if re.match(pattern, text):
            return False, "无意义内容"
    
    # 高价值信号
    value_signals = [
        "决定", "结论", "发现", "学到", "意识到",
        "问题", "方案", "计划", "目标", "原则",
        "因为", "所以", "导致", "结果是",
        "错误", "教训", "经验", "反思",
    ]
    
    for signal in value_signals:
        if signal in text:
            return True, f"包含价值信号: {signal}"
    
    # 知识密度检查
    if _knowledge_density(text) < 0.3:
        return False, "知识密度低"
    
    return True, "通过默认检查"


def _knowledge_density(text: str) -> float:
    """计算文本的知识密度。"""
    # 有信息量的词
    info_words = len(re.findall(r'[\u4e00-\u9fff]{2,}', text))
    info_words += len(re.findall(r'[a-zA-Z]{3,}', text))
    
    total_chars = len(text.strip())
    if total_chars == 0:
        return 0.0
    
    return min(1.0, info_words / (total_chars / 5))


def extract_summary(text: str, max_length: int = 200) -> str:
    """提取摘要。"""
    text = text.strip()
    if len(text) <= max_length:
        return text
    
    # 尝试在第一句结束处截断
    first_sentence = re.split(r'[。！？]', text)[0]
    if len(first_sentence) >= 20:
        return first_sentence[:max_length]
    
    return text[:max_length] + "..."


def classify_content(text: str) -> str:
    """分类内容类型。"""
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["决定", "选择", "选", "要不要", "是否"]):
        return "decision"
    
    if any(w in text_lower for w in ["学到", "发现", "原理", "概念", "方法"]):
        return "knowledge"
    
    if any(w in text_lower for w in ["完成", "做了", "实现", "部署", "发布"]):
        return "action"
    
    if any(w in text_lower for w in ["觉得", "感觉", "认为", "想法", "思考"]):
        return "thought"
    
    return "fact"
