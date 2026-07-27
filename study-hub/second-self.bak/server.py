"""Second Self 本地服务器 — FastAPI"""
import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from gateway_paths import ROOT, safe_path
from memory_store import insert_entry, search_memory, get_entry, get_stats
from memory_causal import process_entry, causal_search, print_causal_report
from self_engine import load_self_layer, run_decision_engine, retrieve_memories

app = FastAPI(title="Second Self Gateway", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# 模型
# ═══════════════════════════════════════════════════════════════

class IngestRequest(BaseModel):
    content: str
    source: str = "chat"
    type: str = "fact"
    context: dict = {}
    field: str = "knowledge"


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


# ═══════════════════════════════════════════════════════════════
# 路由
# ═══════════════════════════════════════════════════════════════

@app.get("/")
def index():
    """返回前端页面。"""
    index_path = ROOT / "app" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"status": "ok", "version": "2.1"}


@app.get("/api/stats")
def api_stats():
    """系统统计。"""
    return get_stats()


@app.get("/api/files")
def api_files(path: str = ""):
    """列出文件。"""
    target = safe_path(path) if path else ROOT
    files = []
    for p in target.iterdir():
        if p.name.startswith("."):
            continue
        files.append({
            "name": p.name,
            "type": "dir" if p.is_dir() else "file",
            "path": str(p.relative_to(ROOT)).replace("\\", "/"),
        })
    return {"files": files}


@app.get("/api/file")
def api_file_read(path: str):
    """读取文件。"""
    try:
        target = safe_path(path)
        if not target.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return {"content": target.read_text(encoding="utf-8")}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/file")
def api_file_write(path: str, content: str):
    """写入文件。"""
    try:
        target = safe_path(path)
        if str(target).startswith(str(ROOT / "raw")):
            raise HTTPException(status_code=403, detail="raw/ is immutable")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/memory")
def api_memory_search(q: str = Query(...), k: int = 5, use_causal: bool = True):
    """搜索记忆。"""
    return search_memory(q, k=k, use_causal=use_causal)


@app.post("/api/memory")
def api_memory_ingest(req: IngestRequest):
    """插入记忆。"""
    entry_id = insert_entry(
        source=req.source,
        type=req.type,
        content=req.content,
        context=req.context,
        field=req.field,
    )
    return {"success": True, "entry_id": entry_id}


@app.get("/api/memory/{entry_id}")
def api_memory_get(entry_id: str):
    """获取单条记忆。"""
    entry = get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    """聊天接口（简化版）。"""
    message = req.message
    
    # 加载 Self 层
    snapshot = load_self_layer()
    
    # 检索记忆
    memories_result = retrieve_memories(message, k=5, snapshot=snapshot, message_text=message)
    memories = memories_result.get("candidates", memories_result.get("results", []))
    
    # 决策引擎
    decision = run_decision_engine(message, snapshot, memories)
    
    # 自动捕获
    if decision.get("should_capture_memory"):
        try:
            insert_entry(
                source="chat",
                type="capture",
                content=message,
                context={
                    "priority": decision.get("priority"),
                    "linked_project": decision.get("linked_project"),
                },
            )
        except Exception:
            pass
    
    return {
        "message": message,
        "decision": decision,
        "memories": memories[:5],
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


@app.get("/api/causal")
def api_causal_search(q: str = Query(...), k: int = 5):
    """因果检索。"""
    return causal_search(q, k=k)


@app.get("/api/causal/report")
def api_causal_report():
    """因果报告。"""
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    print_causal_report()
    sys.stdout = old_stdout
    return {"report": buffer.getvalue()}


# ═══════════════════════════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8741))
    uvicorn.run(app, host="0.0.0.0", port=port)
