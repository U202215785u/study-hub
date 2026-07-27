"""Agent Loop — 调用 LLM 生成回复。

支持多个 LLM 提供商（按优先级，自动回退）：
1. OPENAI_API_KEY + OPENAI_API_BASE（默认 https://api.openai.com/v1）
2. DASHSCOPE_API_KEY（阿里云 DashScope / 通义千问）
3. GRSAI_API_KEY + GRSAI_BASE（GrsAi Nano Banana 2）

模型优先级同上，单请求超时 15 秒，失败自动切换下一个 provider。
"""
import os
from pathlib import Path
from typing import Any, List, Tuple


def _load_env():
    """加载 .env 文件到环境变量。"""
    env_paths = [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / "study-hub" / ".env",
        Path(__file__).parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass
            break


_load_env()


def _get_providers() -> List[Tuple[Any, str]]:
    """获取所有可用的 LLM provider 列表，按优先级排序。
    
    返回 [(client, model), ...]
    """
    try:
        from openai import OpenAI
    except ImportError:
        return []

    providers = []
    timeout = 15.0  # 单个请求超时 15 秒

    # 优先级 1：OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        try:
            client = OpenAI(api_key=openai_key, base_url=base_url, timeout=timeout)
            providers.append((client, model, "OpenAI"))
        except Exception:
            pass

    # 优先级 2：DashScope（阿里云通义千问，OpenAI 兼容）
    dashscope_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if dashscope_key:
        model = os.environ.get("DASHSCOPE_MODEL", "qwen-turbo")
        try:
            client = OpenAI(
                api_key=dashscope_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                timeout=timeout,
            )
            providers.append((client, model, "DashScope"))
        except Exception:
            pass

    # 优先级 3：GRSAI
    grsai_key = os.environ.get("GRSAI_API_KEY", "")
    if grsai_key:
        base_url = os.environ.get("GRSAI_BASE", "")
        if base_url and not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
        model = os.environ.get("GRSAI_MODEL", "nano-banana-2")
        try:
            client = OpenAI(api_key=grsai_key, base_url=base_url, timeout=timeout)
            providers.append((client, model, "GRSAI"))
        except Exception:
            pass

    return providers


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
    """同步调用 LLM，支持多 provider 自动回退。"""
    providers = _get_providers()
    if not providers:
        return "[LLM 客户端未就绪。请配置 OPENAI_API_KEY、DASHSCOPE_API_KEY 或 GRSAI_API_KEY 环境变量。]"

    system_prompt = build_system_prompt(context)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    last_error = ""
    for client, model, name in providers:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            content = response.choices[0].message.content or ""
            # 成功时记录使用的 provider（调试用）
            return content
        except Exception as e:
            last_error = f"[{name} 失败: {str(e)}]"
            continue

    return f"[所有 LLM provider 均调用失败] {last_error}"


def chat(context: dict, message: str) -> str:
    """异步调用 LLM（兼容接口）。"""
    return chat_sync(context, message)
