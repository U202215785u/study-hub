import os, uuid
from fastapi import APIRouter
from pydantic import BaseModel
import httpx
from database import get_db

router = APIRouter()

# GrsAi 配置
GRSAI_BASE = os.getenv("GRSAI_BASE", "https://grsai.dakka.com.cn")
GRSAI_API_KEY = os.getenv("GRSAI_API_KEY", "")
GRSAI_MODEL = os.getenv("GRSAI_MODEL", "nano-banana-2")

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "images")
os.makedirs(IMAGES_DIR, exist_ok=True)


class GenerateCoverRequest(BaseModel):
    page_id: int | None = None
    title: str = ""
    content: str = ""
    prompt: str = ""


@router.post("/images/generate-cover")
async def generate_cover(req: GenerateCoverRequest):
    if not GRSAI_API_KEY:
        return {"error": "GrsAi API Key 未配置，请在 .env 中设置 GRSAI_API_KEY"}

    if req.prompt:
        prompt = req.prompt
    else:
        prompt = (
            f'Create a modern, clean cover image for an article titled "{req.title}". '
            f'The article is about: {req.content[:500]}. '
            f'Style: minimalist, elegant, suitable for a technical blog cover. '
            f'Use soft gradients, abstract shapes, or subtle illustrations. '
            f'No text in the image.'
        )

    # 1. 提交生图任务
    submit_url = f"{GRSAI_BASE.rstrip('/')}/v1/draw/nano-banana"
    headers = {
        "Authorization": f"Bearer {GRSAI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": GRSAI_MODEL,
        "prompt": prompt,
        "aspectRatio": "16:9",
        "urls": [],
        "webHook": "-1"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(submit_url, headers=headers, json=body)
        if resp.status_code != 200:
            return {"error": f"提交生图任务失败 ({resp.status_code}): {resp.text[:500]}"}
        task_data = resp.json()

    task_id = task_data.get("data", {}).get("id") or task_data.get("id")
    if not task_id:
        return {"error": f"未获取到任务 ID: {task_data}"}

    # 2. 轮询查询结果（最多 60 秒）
    result_url = f"{GRSAI_BASE.rstrip('/')}/v1/draw/result"
    image_url = None
    for _ in range(30):
        async with httpx.AsyncClient(timeout=10) as qclient:
            qresp = await qclient.post(result_url, headers=headers, json={"id": task_id})
            if qresp.status_code == 200:
                qdata = qresp.json()
                d = qdata.get("data", {})
                progress = d.get("progress", 0)
                status = d.get("status", "")
                if progress == 100 or status.lower() == "succeeded":
                    results = d.get("results", [])
                    if results:
                        image_url = results[0].get("url")
                    break
                elif status.lower() == "failed":
                    return {"error": f"生图任务失败: {d.get('failure_reason', '未知错误')}"}
        await __import__("asyncio").sleep(2)

    if not image_url:
        return {"error": "生图任务超时，请稍后重试"}

    # 3. 下载图片到本地
    async with httpx.AsyncClient(timeout=30) as dclient:
        dresp = await dclient.get(image_url)
        if dresp.status_code != 200:
            return {"error": f"下载图片失败 ({dresp.status_code})"}
        img_bytes = dresp.content

    filename = f"cover_{uuid.uuid4().hex[:12]}.png"
    filepath = os.path.join(IMAGES_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(img_bytes)

    local_url = f"/images/{filename}"

    # 4. 如果指定了 page_id，自动更新 wiki_pages.cover_image
    if req.page_id:
        conn = get_db()
        conn.execute("UPDATE wiki_pages SET cover_image = ? WHERE id = ?", (local_url, req.page_id))
        conn.commit()
        conn.close()

    return {"url": local_url, "prompt": prompt}
