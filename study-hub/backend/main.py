import os, sys, subprocess, platform, asyncio
from contextlib import asynccontextmanager
from pathlib import Path

# 自动加载 .env 文件
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import re

from database import init_db
from endpoints.upload import router as upload_router
from endpoints.rag import router as rag_router
from endpoints.review import router as review_router
from endpoints.categories import router as categories_router
from endpoints.automation import router as automation_router
from endpoints.content_parser import router as content_parser_router
from endpoints.wiki import router as wiki_router
from endpoints.workstation_search import router as workstation_search_router
from endpoints.brainstorm import router as brainstorm_router
from endpoints.admin import router as admin_router
from endpoints.memory import router as memory_router
from endpoints.images import router as images_router
from endpoints.second_self import router as second_self_router
from endpoints.workflow import router as workflow_router
from endpoints.ddl import router as ddl_router
from endpoints.sop import router as sop_router
from endpoints.creator import router as creator_router
from endpoints.skills import router as skills_router
from endpoints.journal import router as journal_router
from endpoints.operations import router as operations_router
from endpoints.settings import router as settings_router
from endpoints.workbench import router as workbench_router
from endpoints.heatmap import router as heatmap_router

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
INBOX_DIR = os.path.join(os.path.dirname(__file__), "data", "inbox")
LEARNING_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mods", "learning")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时校验并清理僵尸 PID 文件（DEC-023）
    _sanitize_pid_file()
    init_db()
    from watcher import start_watcher
    start_watcher()
    # 启动文件注入器定时任务
    asyncio.create_task(_file_injector_loop())
    # 校验外部依赖（ffmpeg / Claude Code）
    _verify_startup_deps()
    # 恢复未完成的任务 + 孤儿 .md 文件（防止重启丢失）
    # 注：暂时异步化以避免阻塞启动
    asyncio.create_task(_async_recover_automation_state())
    # 启动网页变更监控定时任务（每 6 小时）
    asyncio.create_task(_url_monitor_loop())
    yield
    from watcher import stop_watcher
    stop_watcher()


async def _url_monitor_loop():
    """网页变更监控定时任务：每 6 小时检查一次监控的 URL"""
    import logging
    logger = logging.getLogger("studyhub")
    # 首次启动延迟 10 分钟
    await asyncio.sleep(600)
    while True:
        try:
            from endpoints.admin import check_monitored_urls
            result = check_monitored_urls()
            if result.get("changed", 0) > 0:
                logger.info(f"[url_monitor] 检测到 {result['changed']} 个网页有变更")
            else:
                logger.info(f"[url_monitor] 检查了 {result.get('checked', 0)} 个 URL，无变更")
        except Exception as e:
            logger.error(f"[url_monitor] 定时任务异常: {e}")
        await asyncio.sleep(21600)  # 6 小时


async def _file_injector_loop():
    """文件注入器定时任务：每5分钟检查并更新记忆文件"""
    import logging
    logger = logging.getLogger("studyhub")
    # 首次启动延迟30秒，避免与启动过程竞争
    await asyncio.sleep(30)
    while True:
        try:
            from core.file_injector import generate_memory_files
            result = generate_memory_files()
            if result.get("errors"):
                logger.warning(f"[file_injector] 部分文件生成失败: {result['errors']}")
            else:
                logger.info(f"[file_injector] 记忆文件已更新: {result['stats']}")
        except Exception as e:
            logger.error(f"[file_injector] 定时任务异常: {e}")
        await asyncio.sleep(300)  # 5分钟


def _sanitize_pid_file():
    """启动时检查 PID 文件：如果指向的进程已死或端口不匹配，清理之。(ISS-018)"""
    pid_file = os.path.join(os.path.dirname(__file__), "data", "server.pid")
    if not os.path.exists(pid_file):
        return
    try:
        with open(pid_file, "r") as f:
            pid_str = f.read().strip()
        pid = int(pid_str)
    except (ValueError, OSError):
        os.remove(pid_file)
        return

    # 检查进程是否还活着
    proc_alive = False
    try:
        import psutil
        proc_alive = psutil.pid_exists(pid)
    except ImportError:
        try:
            os.kill(pid, 0)
            proc_alive = True
        except (OSError, ProcessLookupError):
            proc_alive = False

    if not proc_alive:
        os.remove(pid_file)
        print(f"[startup] 清理僵尸 PID 文件 (PID={pid} 已不存在)")
        return

    # 进程存在，校验端口是否真的是我们的服务
    # 使用 "localhost" 而非 "127.0.0.1"，兼容绑定 0.0.0.0 的情况 (ISS-018)
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", 8741))
        sock.close()
        if result != 0:
            # 端口未监听，说明 PID 文件对应的是其他进程
            os.remove(pid_file)
            print(f"[startup] 清理无效 PID 文件 (PID={pid} 未监听 8741)")
    except Exception:
        pass


async def _async_recover_automation_state():
    """异步版：避免阻塞 lifespan 启动。"""
    await asyncio.sleep(3)  # 等数据库和文件系统就绪
    try:
        from endpoints.automation import recover_tasks_on_startup
        recover_tasks_on_startup()
    except Exception as e:
        import logging
        logger = logging.getLogger("studyhub")
        logger.warning(f"[startup] 自动化任务恢复失败: {e}")


def _recover_automation_state():
    """启动时恢复自动化任务队列 + 孤儿 .md 文件。"""
    try:
        from endpoints.automation import recover_tasks_on_startup
        recover_tasks_on_startup()
    except Exception as e:
        import logging
        logger = logging.getLogger("studyhub")
        logger.warning(f"[startup] 自动化任务恢复失败: {e}")


def _verify_startup_deps():
    """启动时校验外部依赖可用性，输出警告到控制台和日志。"""
    import logging
    logger = logging.getLogger("studyhub")

    try:
        from endpoints.automation import verify_external_deps
        report = verify_external_deps()
    except Exception as e:
        logger.warning(f"[startup] 无法校验外部依赖: {e}")
        return

    warnings = []
    for name, info in report.items():
        if info.get("warning"):
            warnings.append(f"  ⚠ {name}: {info['warning']}")
        else:
            print(f"[startup] {name}: {info['path']} [OK]")

    if warnings:
        print("\n".join(warnings))
        for w in warnings:
            logger.warning(f"[startup] {w}")

app = FastAPI(title="学习中枢 API", lifespan=lifespan)

class StripApiPrefixMiddleware(BaseHTTPMiddleware):
    """把 /api/xxx 重写为 /xxx，兼容 Vite 开发代理和生产部署两种模式。"""
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/mods"):
            request.scope["path"] = request.url.path[4:]
        return await call_next(request)

app.add_middleware(StripApiPrefixMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # 允许所有来源（开发环境）
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误", "detail": str(exc)},
    )

app.include_router(upload_router)
app.include_router(rag_router)
app.include_router(review_router)
app.include_router(categories_router)
app.include_router(automation_router)
app.include_router(content_parser_router)
app.include_router(wiki_router)
app.include_router(workstation_search_router)
app.include_router(brainstorm_router)
app.include_router(admin_router)
app.include_router(memory_router)
app.include_router(images_router)
app.include_router(second_self_router)
app.include_router(workflow_router)
app.include_router(ddl_router)
app.include_router(sop_router)
app.include_router(creator_router)
app.include_router(skills_router)
app.include_router(journal_router)
app.include_router(operations_router)
app.include_router(settings_router)
app.include_router(workbench_router)
app.include_router(heatmap_router)

def _extract_plan_meta(path: str) -> dict:
    title = ""
    desc = ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        lines = []

    for line in lines:
        s = line.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            break
        elif s.startswith("## ") and not title:
            title = s[3:].strip()

    if not title:
        title = Path(path).stem.replace("-", " ").replace("_", " ")

    found_heading = bool(title)
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            found_heading = True
            continue
        if found_heading and s and not s.startswith("```") and not s.startswith("|") and not s.startswith("---"):
            desc = s
            break

    return {"title": title, "desc": desc[:180]}


@app.get("/learning/plans")
def list_learning_plans():
    plans = []
    if not os.path.isdir(LEARNING_DIR):
        return plans
    for entry in sorted(os.listdir(LEARNING_DIR)):
        if not entry.endswith(".md"):
            continue
        full = os.path.join(LEARNING_DIR, entry)
        if not os.path.isfile(full):
            continue
        meta = _extract_plan_meta(full)
        plans.append({
            "id": entry[:-3],
            "file": entry,
            "title": meta["title"],
            "desc": meta["desc"],
        })
    return plans


def parse_checklist_md(path: str) -> dict:
    """Parse a markdown file into checklist format.
    Supports:
      - # Title -> plan name
      - ## Topic -> topic group
      - - [ ] / - [x] task -> checklist item
      - - task -> plain item
      - | Task | ... | table rows -> extract task from first column
      - #tag at end of line -> tag
    """
    name = ""
    topics = []
    current_topic = None
    in_table = False

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        lines = []

    def flush_topic():
        nonlocal current_topic
        if current_topic is not None:
            topics.append(current_topic)
            current_topic = None

    def extract_tag(text: str) -> tuple:
        # Extract #tag from end of text
        m = re.search(r"#(\S+)$", text.strip())
        if m:
            return text[:m.start()].strip(), m.group(1)
        return text.strip(), ""

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        # Plan name (only first # heading)
        if stripped.startswith("# ") and not stripped.startswith("## "):
            flush_topic()
            if not name:
                name = stripped[2:].strip()
            continue

        # Topic heading
        if stripped.startswith("## ") or stripped.startswith("### "):
            flush_topic()
            topic_name = stripped[3:].strip() if stripped.startswith("### ") else stripped[3:].strip()
            current_topic = {"topic": topic_name, "items": []}
            continue

        # Table header / separator
        if stripped.startswith("|") and "---" in stripped:
            in_table = True
            continue
        if stripped.startswith("|") and not stripped.startswith("| "):
            in_table = False

        # Table row
        if stripped.startswith("| ") and "|" in stripped[2:]:
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            if len(cells) >= 1 and cells[0] and cells[0] not in ("任务", "Task", "步骤"):
                task_text = cells[0]
                # Check for checkbox emoji or [x] in other columns
                done = any("[x]" in c or "☑" in c or "✅" in c for c in cells[1:])
                task_text, tag = extract_tag(task_text)
                if task_text:
                    item = {"t": task_text, "done": done}
                    if tag:
                        item["tg"] = tag
                    if current_topic is None:
                        current_topic = {"topic": "未分类", "items": []}
                    current_topic["items"].append(item)
            continue

        # Checklist item: - [ ] or - [x]
        if stripped.startswith("- [ ] ") or stripped.startswith("- [x] ") or stripped.startswith("- [X] "):
            if current_topic is None:
                current_topic = {"topic": "未分类", "items": []}
            content = stripped[6:].strip()
            done = stripped.startswith("- [x] ") or stripped.startswith("- [X] ")
            content, tag = extract_tag(content)
            item = {"t": content, "done": done}
            if tag:
                item["tg"] = tag
            current_topic["items"].append(item)
            continue

        # Plain list item: - xxx
        if stripped.startswith("- "):
            if current_topic is None:
                current_topic = {"topic": "未分类", "items": []}
            content = stripped[2:].strip()
            content, tag = extract_tag(content)
            if content:
                item = {"t": content}
                if tag:
                    item["tg"] = tag
                current_topic["items"].append(item)
            continue

    flush_topic()
    return {"name": name or Path(path).stem.replace("-", " ").replace("_", " "), "topics": topics}


@app.get("/learning/checklist/{filename}")
def get_checklist(filename: str):
    if not filename.endswith(".md"):
        filename += ".md"
    # Security: prevent path traversal
    safe_name = os.path.basename(filename)
    path = os.path.join(LEARNING_DIR, safe_name)
    if not os.path.isfile(path):
        return JSONResponse(status_code=404, content={"error": "文件不存在"})
    return parse_checklist_md(path)


@app.get("/inbox/open")
def open_inbox():
    os.makedirs(INBOX_DIR, exist_ok=True)
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["explorer", INBOX_DIR])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", INBOX_DIR])
        else:
            subprocess.Popen(["xdg-open", INBOX_DIR])
        return {"status": "ok", "path": INBOX_DIR}
    except Exception as e:
        return {"error": str(e)}

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "data", "images")
if os.path.isdir(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

TUTORIAL_FRAMES_DIR = os.path.join(os.path.dirname(__file__), "data", "tutorial_frames")
os.makedirs(TUTORIAL_FRAMES_DIR, exist_ok=True)
app.mount("/tutorial-frames", StaticFiles(directory=TUTORIAL_FRAMES_DIR), name="tutorial_frames")

if os.path.isdir(LEARNING_DIR):
    app.mount("/mods/learning", StaticFiles(directory=LEARNING_DIR), name="mods_learning")

if os.path.isdir(FRONTEND_DIR):
    INDEX_PATH = os.path.abspath(os.path.join(FRONTEND_DIR, "index.html")).replace("\\", "/")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        path = full_path
        file_path = os.path.abspath(os.path.join(FRONTEND_DIR, path)).replace("\\", "/")
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(INDEX_PATH, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})

if __name__ == "__main__":
    import uvicorn
    import logging

    # 配置日志：同时输出到控制台和文件
    LOG_DIR = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE = os.path.join(LOG_DIR, "app.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("studyhub")

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8741"))

    logger.info("=" * 50)
    logger.info("🚀 学习中枢 Study Hub 正在启动…")
    logger.info("📍 数据目录: %s", os.path.join(os.path.dirname(__file__), "data"))
    logger.info("📍 日志文件: %s", LOG_FILE)
    logger.info("🌐 服务地址: http://%s:%d", host if host != "0.0.0.0" else "localhost", port)
    logger.info("📋 管理控制台: http://localhost:%d/admin.html", port)
    logger.info("=" * 50)

    uvicorn.run(app, host=host, port=port, log_level="info")
