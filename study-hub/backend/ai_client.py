import os, json
import httpx

# 不可变 — DeepSeek 唯一 AI 服务，禁止切换 Provider
API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
API_KEY = "sk-d703daaf15d343b88dce53a1dd4d32e4"
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")


class AIClient:
    async def chat(self, messages, temperature=0.7, max_tokens=2048):
        url = f"{API_BASE.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": MODEL,
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
        url = f"{API_BASE.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": MODEL,
            "input": texts,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                raise RuntimeError(f"Embedding API 错误 ({resp.status_code}): {resp.text[:500]}")
            data = resp.json()
            return [item["embedding"] for item in data["data"]]


ai_client = AIClient()
