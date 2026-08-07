import os
import httpx

from database import get_db
from services.secure_settings import load_secret

# 不可变 — DeepSeek 唯一 AI 服务，禁止切换 Provider
DEFAULT_API_BASE = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-v4-flash"
AI_SERVICE_ERROR_MESSAGE = "AI service temporarily unavailable. Check AI settings."
VISION_FALLBACK_API_BASE = "https://dasuapi.com/v1"
VISION_FALLBACK_MODEL = "gpt-5.6-terra"
VISION_SERVICE_ERROR_MESSAGE = "Image analysis is temporarily unavailable. Check AI settings."


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


def get_vision_fallback_config():
    conn = get_db()
    try:
        return {
            "api_base": load_secret(conn, "ai.vision_fallback.base_url") or os.getenv("VISION_FALLBACK_API_BASE", VISION_FALLBACK_API_BASE),
            "api_key": load_secret(conn, "ai.vision_fallback.api_key") or os.getenv("VISION_FALLBACK_API_KEY", ""),
            "model": load_secret(conn, "ai.vision_fallback.model") or os.getenv("VISION_FALLBACK_MODEL", VISION_FALLBACK_MODEL),
        }
    finally:
        conn.close()


class AIServiceError(RuntimeError):
    """Safe, user-facing AI failure without upstream response details."""

    def __init__(self, *_args):
        super().__init__(AI_SERVICE_ERROR_MESSAGE)


class VisionServiceError(RuntimeError):
    def __init__(self):
        super().__init__(VISION_SERVICE_ERROR_MESSAGE)


class RecoverableVisionError(RuntimeError):
    pass


class AIClient:
    async def chat(self, messages, temperature=0.7, max_tokens=2048):
        config = get_ai_config()
        if not config["api_key"]:
            raise AIServiceError(AI_SERVICE_ERROR_MESSAGE)
        url = f"{config['api_base'].rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
        body = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise AIServiceError(AI_SERVICE_ERROR_MESSAGE) from exc
        if not 200 <= resp.status_code < 300:
            raise AIServiceError(AI_SERVICE_ERROR_MESSAGE)
        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIServiceError(AI_SERVICE_ERROR_MESSAGE) from exc

    async def embed(self, texts: list[str]) -> list[list[float]]:
        config = get_ai_config()
        if not config["api_key"]:
            raise AIServiceError(AI_SERVICE_ERROR_MESSAGE)
        url = f"{config['api_base'].rstrip('/')}/embeddings"
        headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
        body = {
            "model": config["model"],
            "input": texts,
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise AIServiceError(AI_SERVICE_ERROR_MESSAGE) from exc
        if not 200 <= resp.status_code < 300:
            raise AIServiceError(AI_SERVICE_ERROR_MESSAGE)
        try:
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
        except (ValueError, KeyError, TypeError) as exc:
            raise AIServiceError(AI_SERVICE_ERROR_MESSAGE) from exc

    @staticmethod
    def _vision_messages(image_data_urls: list[str], context: str) -> list[dict]:
        return [{"role": "user", "content": [
            {"type": "text", "text": context.strip()},
            *({"type": "image_url", "image_url": {"url": url}} for url in image_data_urls),
        ]}]

    async def _vision_chat(self, config: dict, image_data_urls: list[str], context: str) -> str:
        if not config.get("api_key"):
            raise RecoverableVisionError()
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(
                    f"{config['api_base'].rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
                    json={"model": config["model"], "messages": self._vision_messages(image_data_urls, context), "temperature": 0.2, "max_tokens": 1200},
                )
        except httpx.HTTPError as exc:
            raise RecoverableVisionError() from exc
        if response.status_code in (400, 408, 429) or response.status_code >= 500:
            raise RecoverableVisionError()
        if not 200 <= response.status_code < 300:
            raise VisionServiceError()
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise RecoverableVisionError() from exc
        if not isinstance(content, str) or not content.strip():
            raise RecoverableVisionError()
        return content.strip()

    async def describe_images(self, image_data_urls: list[str], context: str) -> str:
        if not image_data_urls:
            raise VisionServiceError()
        try:
            return await self._vision_chat(get_ai_config(), image_data_urls, context)
        except RecoverableVisionError:
            try:
                return await self._vision_chat(get_vision_fallback_config(), image_data_urls, context)
            except (RecoverableVisionError, VisionServiceError) as exc:
                raise VisionServiceError() from exc


ai_client = AIClient()
