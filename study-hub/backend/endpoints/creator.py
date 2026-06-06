"""
新媒体创作工作区 — 服务管理 API
提供自托管服务的状态检测和基础管理
"""

import asyncio
import socket
from typing import List, Dict
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/creator", tags=["creator"])

# ============================================
# 自托管服务配置
# ============================================
DEFAULT_SERVICES = [
    {"id": "postiz", "name": "Postiz", "icon": "📅", "desc": "社媒管理平台", "host": "localhost", "port": 4200, "url": "http://localhost:4200"},
    {"id": "n8n", "name": "n8n", "icon": "⚡", "desc": "自动化工作流", "host": "localhost", "port": 5678, "url": "http://localhost:5678"},
    {"id": "ghost", "name": "Ghost", "icon": "👻", "desc": "博客出版平台", "host": "localhost", "port": 2368, "url": "http://localhost:2368"},
    {"id": "strapi", "name": "Strapi", "icon": "📦", "desc": "Headless CMS", "host": "localhost", "port": 1337, "url": "http://localhost:1337"},
    {"id": "comfyui", "name": "ComfyUI", "icon": "🎭", "desc": "AI 图像生成", "host": "localhost", "port": 8188, "url": "http://localhost:8188"},
    {"id": "invokeai", "name": "InvokeAI", "icon": "🖼️", "desc": "AI 绘画工具", "host": "localhost", "port": 9090, "url": "http://localhost:9090"},
    {"id": "uptime", "name": "Uptime Kuma", "icon": "📊", "desc": "服务监控", "host": "localhost", "port": 3001, "url": "http://localhost:3001"},
]


# ============================================
# 数据模型
# ============================================
class ServiceStatus(BaseModel):
    id: str
    name: str
    icon: str
    desc: str
    url: str
    online: bool
    response_time_ms: float = 0.0


class ServiceListResponse(BaseModel):
    services: List[ServiceStatus]
    total: int
    online_count: int


# ============================================
# 工具函数
# ============================================
def _check_port(host: str, port: int, timeout: float = 2.0) -> tuple[bool, float]:
    """检测端口是否开放，返回 (是否在线, 响应时间ms)"""
    start = asyncio.get_event_loop().time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        elapsed = (asyncio.get_event_loop().time() - start) * 1000
        return result == 0, elapsed
    except Exception:
        return False, 0.0


async def _check_service_async(svc: Dict) -> ServiceStatus:
    """异步检测单个服务状态"""
    loop = asyncio.get_event_loop()
    online, response_time = await loop.run_in_executor(
        None, _check_port, svc["host"], svc["port"]
    )
    return ServiceStatus(
        id=svc["id"],
        name=svc["name"],
        icon=svc["icon"],
        desc=svc["desc"],
        url=svc["url"],
        online=online,
        response_time_ms=round(response_time, 1)
    )


# ============================================
# API 端点
# ============================================
@router.get("/services", response_model=ServiceListResponse)
async def list_services() -> ServiceListResponse:
    """
    获取所有自托管服务的状态列表
    
    通过 TCP 端口检测判断服务是否在线，
    并发检测所有服务以提高响应速度。
    """
    tasks = [_check_service_async(svc) for svc in DEFAULT_SERVICES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    services = []
    for r in results:
        if isinstance(r, Exception):
            continue
        services.append(r)
    
    return ServiceListResponse(
        services=services,
        total=len(services),
        online_count=sum(1 for s in services if s.online)
    )


@router.get("/services/{service_id}", response_model=ServiceStatus)
async def get_service_status(service_id: str) -> ServiceStatus:
    """获取单个服务的详细状态"""
    svc = next((s for s in DEFAULT_SERVICES if s["id"] == service_id), None)
    if not svc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"服务 {service_id} 不存在")
    
    return await _check_service_async(svc)
