import os, json
import httpx

DEFAULT_PROVIDER = os.getenv("AI_DEFAULT_PROVIDER", "kimi")

PROVIDER_CONFIGS = {
    "kimi": {
        "api_base": os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1"),
        "api_key": os.getenv("KIMI_API_KEY", ""),
        "model": os.getenv("KIMI_MODEL", "moonshot-v1-8k"),
    },
    "deepseek": {
        "api_base": os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    },
    "doubao": {
        "api_base": os.getenv("DOUBAO_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"),
        "api_key": os.getenv("DOUBAO_API_KEY", ""),
        "model": os.getenv("DOUBAO_MODEL", "doubao-pro-32k"),
    },
    "claude": {
        "api_base": os.getenv("CLAUDE_API_BASE", "https://api.anthropic.com"),
        "api_key": os.getenv("CLAUDE_API_KEY", ""),
        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
    },
}

class AIClient:
    def __init__(self):
        self.providers = {}
        for name, cfg in PROVIDER_CONFIGS.items():
            if cfg["api_key"]:
                self.providers[name] = cfg

    @property
    def default_provider(self):
        if DEFAULT_PROVIDER in self.providers:
            return DEFAULT_PROVIDER
        if self.providers:
            return next(iter(self.providers))
        return None

    def _is_claude(self, provider):
        return provider == "claude"

    async def chat(self, messages, provider=None, temperature=0.7, max_tokens=2048):
        """
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        返回: str
        """
        provider = provider or self.default_provider
        if not provider or provider not in self.providers:
            return "错误：未配置任何 AI 服务。请设置 *_API_KEY 环境变量。"

        cfg = self.providers[provider]

        if self._is_claude(provider):
            return await self._chat_claude(cfg, messages, temperature, max_tokens)
        else:
            return await self._chat_openai_compat(cfg, messages, temperature, max_tokens)

    async def _chat_openai_compat(self, cfg, messages, temperature, max_tokens):
        url = f"{cfg['api_base'].rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        }
        body = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                return f"AI API 错误 ({resp.status_code}): {resp.text[:500]}"
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _chat_claude(self, cfg, messages, temperature, max_tokens):
        url = f"{cfg['api_base'].rstrip('/')}/v1/messages"
        headers = {
            "x-api-key": cfg["api_key"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        # 提取 system 消息
        system = None
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})

        body = {
            "model": cfg["model"],
            "messages": chat_messages,
            "max_tokens": max_tokens,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                return f"Claude API 错误 ({resp.status_code}): {resp.text[:500]}"
            data = resp.json()
            return data["content"][0]["text"]

    def embed(self, texts: list[str], provider=None) -> list[list[float]]:
        """
        文本向量化。使用 OpenAI 兼容的 /embeddings 接口。
        Claude 不支持 embeddings，会自动选择其他可用 provider。
        """
        provider = provider or self.default_provider
        if self._is_claude(provider):
            # Claude 没有 embeddings API，换一个
            for p in self.providers:
                if p != "claude":
                    provider = p
                    break

        if not provider or provider not in self.providers:
            raise RuntimeError("未配置支持 embedding 的 AI 服务")

        cfg = self.providers[provider]
        url = f"{cfg['api_base'].rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        }
        body = {
            "model": cfg.get("embedding_model", cfg["model"]),
            "input": texts,
        }

        with httpx.Client(timeout=120) as client:
            resp = client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                raise RuntimeError(f"Embedding API 错误 ({resp.status_code}): {resp.text[:500]}")
            data = resp.json()
            return [item["embedding"] for item in data["data"]]

    def list_providers(self):
        return list(self.providers.keys())


ai_client = AIClient()
