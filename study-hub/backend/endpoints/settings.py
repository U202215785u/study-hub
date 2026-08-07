import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_client import get_ai_config
from database import get_db
from services.secure_settings import delete_secret, load_secret, save_secret, secret_status


router = APIRouter(prefix="/settings", tags=["settings"])
BACKEND_DIR = Path(__file__).resolve().parent.parent


class AISettingsUpdate(BaseModel):
    base_url: str = Field(min_length=8, max_length=500)
    model: str = Field(min_length=1, max_length=200)
    api_key: str | None = Field(default=None, max_length=20_000)


class ModelRouteUpdate(BaseModel):
    model: str = Field(min_length=1, max_length=200)


class ServiceSettingsUpdate(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)


def _directory_size(directory: Path) -> int:
    if not directory.exists():
        return 0
    total = 0
    for path in directory.rglob("*"):
        if path.is_file():
            try:
                total += path.stat().st_size
            except OSError:
                continue
    return total


def _ai_settings():
    config = get_ai_config()
    conn = get_db()
    try:
        key_status = secret_status(conn, "ai.deepseek.api_key")
    finally:
        conn.close()
    return {"provider": "DeepSeek", "base_url": config["api_base"], "model": config["model"], "api_key": key_status}


SETTINGS_CATEGORIES = [
    ("ai", "AI 服务", ["DeepSeek 对话与向量", "DashScope 语音识别", "图像生成"]),
    ("content", "内容解析", ["社媒登录凭证", "解析能力状态"]),
    ("integrations", "发布与集成", ["CapCut", "Postiz", "n8n"]),
    ("connections", "服务连接", ["本地服务", "浏览器扩展"]),
    ("knowledge", "知识与检索", ["向量模型", "索引状态"]),
    ("automation", "自动化与工作流", ["任务队列", "外部工具"]),
    ("workspace", "工作区", ["快捷入口", "AI 启动器", "自定义命令"]),
    ("maintenance", "数据与维护", ["本地存储", "缓存与索引"]),
]


MODEL_ROUTES = [
    {"id": "deepseek_chat", "capability": "聊天与内容生成", "provider": "DeepSeek", "setting": "ai.deepseek.model", "model_env": "DEEPSEEK_MODEL", "default_model": "deepseek-v4-flash", "options": ["deepseek-v4-flash"], "used_by": ["问答", "内容总结", "Wiki", "工作流", "创作助手"]},
    {"id": "grs_image", "capability": "生图", "provider": "GRS AI", "model_env": "GRSAI_MODEL", "default_model": "nano-banana-2", "options": ["nano-banana-2"], "used_by": ["Wiki 封面", "创作项目封面"]},
    {"id": "doubao_asr", "capability": "语音识别", "provider": "豆包语音识别", "model_env": "VOLC_RESOURCE_ID", "default_model": "volc.bigasr.auc_turbo", "options": ["volc.bigasr.auc_turbo", "volc.seedasr.auc1", "volc.bigasr.auc1", "volc.bigasr.auc_idle5"], "used_by": ["抖音导入", "B站导入", "小红书导入", "本地音频"]},
    {"id": "dashscope_asr", "capability": "语音识别备用", "provider": "DashScope", "model_env": "DASHSCOPE_ASR_MODEL", "default_model": "qwen3-asr-flash", "options": ["qwen3-asr-flash"], "used_by": ["豆包不可用时的音频导入"]},
    {"id": "volc_tts", "capability": "语音合成", "provider": "火山引擎", "model_env": "VOLC_TTS_CLUSTER", "default_model": "volcano_tts", "options": ["volcano_tts"], "used_by": ["创作语音"]},
    {"id": "embedding", "capability": "向量检索", "provider": "本地模型", "model_env": "EMBEDDING_MODEL", "default_model": "BAAI/bge-small-zh-v1.5", "options": ["BAAI/bge-small-zh-v1.5", "all-MiniLM-L6-v2"], "used_by": ["文档检索", "Wiki 检索"]},
]


SERVICE_CONFIGS = [
    {
        "id": "grs",
        "provider": "GRS AI",
        "fields": [
            {"id": "base_url", "label": "服务地址", "setting": "ai.grs.base_url", "env": "GRSAI_BASE", "default": "https://grsai.dakka.com.cn", "kind": "url"},
            {"id": "api_key", "label": "密钥", "setting": "ai.grs.api_key", "env": "GRSAI_API_KEY", "default": "", "kind": "secret"},
        ],
    },
    {
        "id": "volc",
        "provider": "火山引擎（豆包语音）",
        "fields": [
            {"id": "app_key", "label": "App Key", "setting": "ai.volc.app_key", "env": "VOLC_APP_KEY", "default": "", "kind": "secret"},
            {"id": "access_key", "label": "Access Key", "setting": "ai.volc.access_key", "env": "VOLC_ACCESS_KEY", "default": "", "kind": "secret"},
        ],
    },
    {
        "id": "dashscope",
        "provider": "DashScope（语音备用）",
        "fields": [
            {"id": "api_key", "label": "密钥", "setting": "ai.dashscope.api_key", "env": "DASHSCOPE_API_KEY", "default": "", "kind": "secret"},
        ],
    },
    {
        "id": "vision_fallback",
        "provider": "OpenAI-compatible vision fallback",
        "fields": [
            {"id": "base_url", "label": "服务地址", "setting": "ai.vision_fallback.base_url", "env": "VISION_FALLBACK_API_BASE", "default": "https://dasuapi.com/v1", "kind": "url"},
            {"id": "model", "label": "模型", "setting": "ai.vision_fallback.model", "env": "VISION_FALLBACK_MODEL", "default": "gpt-5.6-terra", "kind": "text"},
            {"id": "api_key", "label": "密钥", "setting": "ai.vision_fallback.api_key", "env": "VISION_FALLBACK_API_KEY", "default": "", "kind": "secret"},
        ],
    },
]


def get_runtime_setting(setting: str, env: str, default: str = "") -> str:
    """Prefer encrypted user settings, then retain existing environment configuration."""
    conn = get_db()
    try:
        saved = load_secret(conn, setting)
    finally:
        conn.close()
    return saved if saved is not None else os.getenv(env, default)


def _model_route(route: dict) -> dict:
    return {
        "id": route["id"],
        "capability": route["capability"],
        "provider": route["provider"],
        "model": get_runtime_setting(route.get("setting", f"model.route.{route['id']}"), route["model_env"], route["default_model"]),
        "options": route["options"],
        "used_by": route["used_by"],
    }


@router.get("/model-routes")
def get_model_routes():
    return {"routes": [_model_route(route) for route in MODEL_ROUTES]}


@router.put("/model-routes/{route_id}")
def update_model_route(route_id: str, payload: ModelRouteUpdate):
    route = next((item for item in MODEL_ROUTES if item["id"] == route_id), None)
    if route is None or payload.model not in route["options"]:
        raise HTTPException(status_code=422, detail="model must be one of the verified presets for this capability")
    conn = get_db()
    try:
        save_secret(conn, route.get("setting", f"model.route.{route_id}"), payload.model)
    finally:
        conn.close()
    os.environ[route["model_env"]] = payload.model
    return _model_route(route)


@router.get("/services")
def get_service_settings():
    services = []
    conn = get_db()
    try:
        for service in SERVICE_CONFIGS:
            fields = []
            for field in service["fields"]:
                fields.append({
                    "id": field["id"], "label": field["label"], "kind": field["kind"],
                    "configured": secret_status(conn, field["setting"])["configured"] or bool(os.getenv(field["env"], field["default"])),
                })
            services.append({"id": service["id"], "provider": service["provider"], "fields": fields})
    finally:
        conn.close()
    return {"services": services}


@router.put("/services/{service_id}")
def update_service_settings(service_id: str, payload: ServiceSettingsUpdate):
    service = next((item for item in SERVICE_CONFIGS if item["id"] == service_id), None)
    if service is None:
        raise HTTPException(status_code=404, detail="service not found")
    fields = {field["id"]: field for field in service["fields"]}
    if not payload.values or any(name not in fields for name in payload.values):
        raise HTTPException(status_code=422, detail="only known service settings may be changed")
    conn = get_db()
    try:
        for name, value in payload.values.items():
            if not isinstance(value, str) or not value.strip():
                continue
            field = fields[name]
            if field["kind"] == "url" and not value.startswith(("https://", "http://")):
                raise HTTPException(status_code=422, detail="service address must be an HTTP URL")
            save_secret(conn, field["setting"], value)
            os.environ[field["env"]] = value.strip()
    finally:
        conn.close()
    return get_service_settings()


@router.get("/catalog")
def get_settings_catalog():
    return {
        "categories": [
            {"id": category_id, "label": label, "items": items}
            for category_id, label, items in SETTINGS_CATEGORIES
        ]
    }


@router.get("/ai")
def get_ai_settings():
    return _ai_settings()


@router.put("/ai")
def update_ai_settings(payload: AISettingsUpdate):
    if not payload.base_url.startswith(("https://", "http://")):
        raise HTTPException(status_code=422, detail="base_url must be an HTTP URL")
    if payload.model not in MODEL_ROUTES[0]["options"]:
        raise HTTPException(status_code=422, detail="model must be a verified DeepSeek preset")
    conn = get_db()
    try:
        save_secret(conn, "ai.deepseek.base_url", payload.base_url)
        save_secret(conn, "ai.deepseek.model", payload.model)
        if payload.api_key:
            save_secret(conn, "ai.deepseek.api_key", payload.api_key)
    finally:
        conn.close()
    return _ai_settings()


@router.delete("/ai/key")
def delete_ai_key():
    conn = get_db()
    try:
        delete_secret(conn, "ai.deepseek.api_key")
    finally:
        conn.close()
    return _ai_settings()


@router.get("/status")
def get_settings_status():
    ai = _ai_settings()
    data_dir = BACKEND_DIR / "data"
    port = os.getenv("PORT", "8741")
    return {
        "status": "ok",
        "services": {
            "local": {"status": "available", "address": f"http://localhost:{port}"},
            "ai": {"status": "available" if ai["api_key"]["configured"] else "needs_configuration", "configured": ai["api_key"]["configured"], "provider": ai["provider"], "model": ai["model"], "base_url": ai["base_url"]},
            "content": {"status": "available", "label": "内容解析"},
        },
        "storage": {"bytes": _directory_size(data_dir)},
    }
