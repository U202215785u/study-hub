import os, sys, subprocess, platform
from contextlib import asynccontextmanager
from pathlib import Path

# 自动加载 .env 文件
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from database import init_db
from endpoints.upload import router as upload_router
from endpoints.rag import router as rag_router
from endpoints.review import router as review_router
from endpoints.categories import router as categories_router
from endpoints.automation import router as automation_router
from endpoints.wiki import router as wiki_router
from endpoints.evolution import router as evolution_router
from endpoints.ai_search import router as ai_search_router
from endpoints.brainstorm import router as brainstorm_router

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
INBOX_DIR = os.path.join(os.path.dirname(__file__), "data", "inbox")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from watcher import start_watcher
    start_watcher()
    yield
    from watcher import stop_watcher
    stop_watcher()

app = FastAPI(title="学习中枢 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",
        "http://localhost:8741",
        "http://127.0.0.1:8741",
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
app.include_router(wiki_router)
app.include_router(evolution_router)
app.include_router(ai_search_router)
app.include_router(brainstorm_router)

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

if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8741"))
    uvicorn.run(app, host=host, port=port)
