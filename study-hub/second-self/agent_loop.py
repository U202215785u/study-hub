"""Agent Loop — LLM 调用 + 流式返回"""
import json
import os
from datetime import datetime

import requests

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")


def chat_completion(messages: list[dict], stream: bool = False, temperature: float = 0.7) -> str:
    """调用 LLM。"""
    if not API_KEY:
        return "[错误] 未配置 API Key"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": stream,
        "temperature": temperature,
    }
    
    try:
        resp = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[错误] {e}"


def stream_completion(messages: list[dict], temperature: float = 0.7):
    """流式调用 LLM。"""
    if not API_KEY:
        yield "[错误] 未配置 API Key"
        return
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
    }
    
    try:
        resp = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
        
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        yield delta["content"]
                except (json.JSONDecodeError, KeyError):
                    pass
    except Exception as e:
        yield f"[错误] {e}"


def build_system_prompt(self_layer: dict, memories: list[dict]) -> str:
    """构建系统提示词。"""
    me = self_layer.get("me", {})
    priorities = me.get("top_priorities", [])
    
    lines = [
        "你是 Second Self，用户的个人 AI 助手。",
        "",
        "## 用户画像",
    ]
    
    identity = me.get("identity", {})
    if identity:
        for k, v in identity.items():
            lines.append(f"- {k}: {v}")
    
    if priorities:
        lines.append("\n## 当前优先级")
        for p in priorities:
            lines.append(f"{p['rank']}. {p['title']}: {p['description']}")
    
    if memories:
        lines.append("\n## 相关记忆")
        for m in memories[:3]:
            content = m.get("content", "") if isinstance(m, dict) else str(m)
            lines.append(f"- {content[:80]}...")
    
    lines.append("\n## 原则")
    lines.append("- 简洁直接，不要过度解释")
    lines.append("- 如果用户问的是技术问题，给出具体代码")
    lines.append("- 主动关联用户的项目和优先级")
    
    return "\n".join(lines)
