import os
import httpx

from database import get_db
from services.secure_settings import load_secret

# 不可变 — DeepSeek 唯一 AI 服务，禁止切换 Provider
DEFAULT_API_BASE = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-v4-flash"


def get_ai_config():
    conn = get_db()
    try:
        return {
            "api_base": load_secret(conn, "ai.deepseek.base_url") or os.getenv("DEEPSEEK_API_BASE", DEFAULT_API_BASE),
            "api_key": load_secret(conn, "ai.deepseek.api_key") or os.getenv("DEEPSEEK_API_KEY", ""),
            "model": load_secret(conn, "ai.deepseek.model") or os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL),
        }
    finally:
        conn.close()


class AIClient:
    async def chat(self, messages, temperature=0.7, max_tokens=2048):
        config = get_ai_config()
        if not config["api_key"]:
            return "AI service is not configured"
        url = f"{config['api_base'].rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
        body = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                return f"AI API 错误 ({resp.status_code}): {resp.text[:500]}"
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        config = get_ai_config()
        if not config["api_key"]:
            raise RuntimeError("AI service is not configured")
        url = f"{config['api_base'].rstrip('/')}/embeddings"
        headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
        body = {
            "model": config["model"],
            "input": texts,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                raise RuntimeError(f"Embedding API 错误 ({resp.status_code}): {resp.text[:500]}")
            data = resp.json()
            return [item["embedding"] for item in data["data"]]


ai_client = AIClient()
