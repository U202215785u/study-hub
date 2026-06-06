"""Agent Loop — 调用 LLM 生成回复。

使用 OpenAI 兼容接口，通过环境变量配置：
- OPENAI_API_KEY
- OPENAI_API_BASE（可选，默认 https://api.openai.com/v1）
- OPENAI_MODEL（可选，默认 gpt-4o-mini）
"""
import os
from typing import Any


def _get_client():
    """获取 OpenAI 客户端。"""
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        return OpenAI(api_key=api_key, base_url=base_url)
    except ImportError:
        return None


def build_system_prompt(context: dict) -> str:
    """构建系统提示词。"""
    snapshot = context.get("self_snapshot", {})
    me = snapshot.get("me", {})
    identity = me.get("identity", {})
    
    lines = [
        "你是 Second Self，用户的 AI 分身。",
        f"用户：{identity.get('姓名代号', 'L')}，{identity.get('年龄', '?')}岁，{identity.get('城市', '?')}",
        "",
        "=== 当前记忆场 ===",
    ]
    
    field_prompt = context.get("field_prompt")
    if field_prompt:
        lines.append(field_prompt)
    else:
        memories = context.get("relevant_memories", [])
        for m in memories[:5]:
            lines.append(m.get("content", "")[:200])
    
    decision = context.get("decision", {})
    lines.extend([
        "",
        "=== 决策参考 ===",
        f"优先级：{decision.get('priority', '?')}",
        f"关联项目：{decision.get('linked_project', '无')}",
    ])
    
    return "\n".join(lines)


def chat_sync(context: dict, message: str) -> str:
    """同步调用 LLM。"""
    client = _get_client()
    if not client:
        return "[OpenAI 客户端未安装，请运行: pip install openai]"
    
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    system_prompt = build_system_prompt(context)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        return f"[LLM 调用失败: {str(e)}]"


def chat(context: dict, message: str) -> str:
    """异步调用 LLM（兼容接口）。"""
    return chat_sync(context, message)
