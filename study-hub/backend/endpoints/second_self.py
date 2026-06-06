"""Second Self API — Self Engine + Memory Store + 文件管理"""
import os, sys, re, json
from datetime import datetime

# 将 second-self 模块加入搜索路径
_SECOND_SELF_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "second-self")
)
if _SECOND_SELF_DIR not in sys.path:
    sys.path.insert(0, _SECOND_SELF_DIR)

from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File, Form
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/second-self", tags=["second-self"])

CORE_FILES = [
    "ME.md", "DASHBOARD.md", "PRINCIPLES.md", "PREFERENCES.md",
    "AUTONOMY.md", "DECISIONS.md", "TASKS.md", "RETRIEVAL_BUDGET.md",
    "ACTION_LOG.md"
]

# ── 延迟导入：避免启动时因路径问题炸掉 ──────────────────────
_self_engine = None
_memory_store = None
_scheduler = None

def _get_self_engine():
    global _self_engine
    if _self_engine is None:
        from self_engine import process, load_self_layer, capture_memories
        _self_engine = (process, load_self_layer, capture_memories)
    return _self_engine

def _get_memory_store():
    global _memory_store
    if _memory_store is None:
        from memory_store import search_memory, ingest, get_stats as mem_stats, insert_entry
        _memory_store = (search_memory, ingest, mem_stats, insert_entry)
    return _memory_store

def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        from scheduler import run_lint as sched_lint
        _scheduler = sched_lint
    return _scheduler


# ── 工具函数 ────────────────────────────────────────────────

def _safe_path(rel_path: str) -> str:
    clean = rel_path.lstrip("/").lstrip("\\")
    abs_path = os.path.abspath(os.path.join(_SECOND_SELF_DIR, clean))
    if os.path.commonpath([abs_path, _SECOND_SELF_DIR]) != _SECOND_SELF_DIR:
        raise HTTPException(403, "路径穿越被拦截")
    return abs_path

def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(404, f"文件不存在: {path}")
    except UnicodeDecodeError:
        with open(path, "r", encoding="gbk", errors="replace") as f:
            return f.read()

def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ═══════════════════════════════════════════════════════════════
# 文件 API
# ═══════════════════════════════════════════════════════════════

@router.get("/api/files")
def list_files():
    result = []
    for name in CORE_FILES:
        fpath = os.path.join(_SECOND_SELF_DIR, name)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            result.append({
                "name": name, "path": name,
                "size": stat.st_size, "updated": stat.st_mtime,
            })
    return result

@router.get("/api/file")
def read_file(path: str = Query(..., description="相对路径")):
    filepath = _safe_path(path)
    if not os.path.isfile(filepath):
        raise HTTPException(404, f"文件不存在: {path}")
    content = _read(filepath)
    return {"path": path, "content": content, "updated": os.path.getmtime(filepath)}

@router.post("/api/file")
def write_file(path: str = Query(..., description="相对路径"), body: dict = Body(...)):
    clean = path.lstrip("/").lstrip("\\")
    if clean.startswith("raw/") or clean.startswith("raw\\"):
        raise HTTPException(403, "raw 目录内容不可变")
    filepath = _safe_path(path)
    content = body.get("content", "")
    _write(filepath, content)
    return {"ok": True, "path": path}


# ═══════════════════════════════════════════════════════════════
# Self Engine API（新）
# ═══════════════════════════════════════════════════════════════

@router.get("/api/self")
def get_self_layer():
    """返回当前 Self 层快照（ME.md + DASHBOARD.md 解析结果）"""
    try:
        _, load_self_layer, _ = _get_self_engine()
        return load_self_layer()
    except Exception as e:
        raise HTTPException(500, f"加载 Self 层失败: {str(e)}")

@router.post("/api/decide")
def decide(body: dict = Body(...)):
    """Self Engine 决策管道：输入消息，输出决策结果 + AgentContext"""
    message = body.get("message", "")
    if not message:
        raise HTTPException(400, "缺少 message 字段")
    try:
        process, _, _ = _get_self_engine()
        return process(message)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"决策引擎错误: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# Agent Loop API — LLM 对话
# ═══════════════════════════════════════════════════════════════

@router.post("/api/chat")
async def chat(body: dict = Body(...)):
    """完整对话管道：Self Engine → Agent Loop → LLM 回应"""
    message = body.get("message", "")
    if not message.strip():
        raise HTTPException(400, "缺少 message 字段")

    try:
        # 1. Self Engine 管道
        process, _, _ = _get_self_engine()
        engine_result = process(message)
        context = engine_result.get("context", {})

        # 2. Agent Loop → LLM
        from agent_loop import chat as llm_chat
        reply = await llm_chat(context, message)

        # 3. 自动捕获记忆
        decision = engine_result.get("decision", {})
        from agent_loop import chat_sync  # noqa: F811
        try:
            from self_engine import capture_memories
            capture_memories(message, decision, reply)
        except Exception:
            pass

        return {
            "reply": reply,
            "decision": decision,
            "context": {
                "priority": decision.get("priority"),
                "linked_project": decision.get("linked_project"),
                "anti_pattern": decision.get("anti_pattern_risk", {}).get("detected"),
                "autonomy": decision.get("autonomy_level", {}).get("level"),
            },
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"对话错误: {str(e)}")


@router.post("/api/chat/stream")
async def chat_stream(body: dict = Body(...)):
    """流式对话管道：SSE 格式，逐 token 返回。

    事件格式：
      data: {"decision": {...}}          # 第一条：决策分析
      data: {"token": "字"}               # 后续：逐字流式
      data: [DONE]                        # 结束标记
    """
    message = body.get("message", "")
    if not message.strip():
        raise HTTPException(400, "缺少 message 字段")

    try:
        # 1. Self Engine
        process, _, _ = _get_self_engine()
        engine_result = process(message)
        context = engine_result.get("context", {})
        decision = engine_result.get("decision", {})

        # 2. 流式 LLM
        from agent_loop import chat_stream as llm_stream

        async def generate():
            # 先发送决策数据
            decision_payload = {
                "priority": decision.get("priority"),
                "linked_project": decision.get("linked_project"),
                "anti_pattern_risk": decision.get("anti_pattern_risk", {}),
                "autonomy_level": {
                    "level": decision.get("autonomy_level", {}).get("level"),
                    "reason": decision.get("autonomy_level", {}).get("reason"),
                },
                "suggested_next_step": decision.get("suggested_next_step"),
                "principle_matches": decision.get("principle_matches", []),
            }
            yield f"data: {json.dumps({'decision': decision_payload})}\n\n"

            # 再发送 token 流
            async for token in llm_stream(context, message):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"流式对话错误: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# Memory Store API
# ═══════════════════════════════════════════════════════════════

@router.get("/api/memory/stats")
def memory_stats():
    """返回记忆存储统计信息"""
    try:
        _, _, mem_stats, _ = _get_memory_store()
        return mem_stats()
    except Exception:
        return {"total": 0, "active": 0, "dormant": 0}

@router.get("/api/memory")
def search_memory_api(q: str = Query("", description="搜索关键词"), k: int = Query(5, ge=1, le=30)):
    """关键词搜索记忆（SQLite + 文件双轨）"""
    if not q.strip():
        return {"query": q, "results": [], "stats": {"total": 0, "active": 0, "dormant": 0}}

    query = q.lower().strip()

    # 尝试使用 memory_store 模块的 SQLite 搜索
    try:
        search_fn, _, mem_stats, _ = _get_memory_store()
        return search_fn(query, k)
    except Exception:
        pass

    # Fallback：文件扫描
    results = []
    wiki_dir = os.path.join(_SECOND_SELF_DIR, "wiki")
    if os.path.isdir(wiki_dir):
        for root, _dirs, files in os.walk(wiki_dir):
            for fname in files:
                if not fname.endswith(".md") or fname in ("index.md", "log.md"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    text = _read(fpath).lower()
                    score = text.count(query)
                    if score > 0:
                        rel = os.path.relpath(fpath, _SECOND_SELF_DIR)
                        results.append({
                            "source": rel.replace("\\", "/"), "type": "wiki",
                            "preview": text[:200], "score": score,
                            "entry_id": None, "domain": None, "project": None,
                        })
                except Exception:
                    pass

    for fname in ("DECISIONS.md", "DASHBOARD.md"):
        fpath = os.path.join(_SECOND_SELF_DIR, fname)
        if os.path.isfile(fpath):
            try:
                text = _read(fpath).lower()
                score = text.count(query)
                if score > 0:
                    results.append({
                        "source": fname,
                        "type": "decision" if "DECISION" in fname else "dashboard",
                        "preview": text[:200], "score": score,
                        "entry_id": None, "domain": None, "project": None,
                    })
            except Exception:
                pass

    results.sort(key=lambda r: r["score"], reverse=True)
    return {"query": q, "results": results[:k], "stats": {"total": 0, "active": 0, "dormant": 0}}


# ═══════════════════════════════════════════════════════════════
# Lint + Ingest
# ═══════════════════════════════════════════════════════════════

@router.post("/api/lint")
def run_lint():
    try:
        sched_lint = _get_scheduler()
        return sched_lint()
    except Exception:
        pass

    # Fallback
    dash_path = os.path.join(_SECOND_SELF_DIR, "DASHBOARD.md")
    issues = []
    if os.path.isfile(dash_path):
        text = _read(dash_path)
        now = datetime.now()
        for m in re.finditer(r"上次更新.*?(\d{4}-\d{2}-\d{2})", text):
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d")
                days = (now - dt).days
                issues.append({
                    "type": "project_update", "date": m.group(1),
                    "days_ago": days, "stale": days > 14,
                })
            except ValueError:
                pass
    return {"lint": "fast", "issues": issues, "checked": True}

@router.post("/api/ingest")
def ingest_api(body: dict = Body(...)):
    content = body.get("content", "")
    domain = body.get("domain", "ai-learning")
    title = body.get("title", "未命名")
    if not content.strip():
        raise HTTPException(400, "内容为空")

    # 优先使用增强版手动采集
    try:
        from pipeline_manual import ingest_enhanced
        return ingest_enhanced(content=content, title=title, domain=domain)
    except Exception:
        import traceback
        traceback.print_exc()

    # Fallback：基础 ingest
    date = datetime.now().strftime("%Y-%m-%d")
    try:
        _, ingest_fn, _, _ = _get_memory_store()
        result = ingest_fn(content, domain, title)
        return result
    except Exception:
        pass

    # 最后 fallback
    raw_dir = os.path.join(_SECOND_SELF_DIR, "raw", "articles")
    os.makedirs(raw_dir, exist_ok=True)
    safe_title = title[:30].replace("/", "-").replace("\\", "-")
    raw_file = os.path.join(raw_dir, f"{date}-{safe_title}.md")
    _write(raw_file, content)

    log_dir = os.path.join(_SECOND_SELF_DIR, "wiki")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "log.md")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n## {date} | ingest | {title}\n- domain: {domain}\n")

    rel_raw = os.path.relpath(raw_file, _SECOND_SELF_DIR).replace("\\", "/")
    return {"ok": True, "raw": rel_raw}


@router.post("/api/ingest/enhanced")
def ingest_enhanced_api(body: dict = Body(...)):
    """增强版手动采集：自动标签 + 摘要 + 项目关联 + 相似检测。"""
    content = body.get("content", "")
    domain = body.get("domain", "ai-learning")
    title = body.get("title", "未命名")
    user_note = body.get("user_note", "")
    if not content.strip():
        raise HTTPException(400, "内容为空")

    try:
        from pipeline_manual import ingest_enhanced
        return ingest_enhanced(content=content, title=title, domain=domain, user_note=user_note)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"增强采集失败: {str(e)}")


@router.post("/api/self/scan-changes")
def scan_self_changes_api():
    """扫描 Self 核心文件变更，自动生成 update 记忆。"""
    try:
        from pipeline_self_change import scan_self_changes
        captured_ids = scan_self_changes()
        return {"ok": True, "captured_ids": captured_ids, "count": len(captured_ids)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"扫描失败: {str(e)}")


@router.get("/api/pending-captures")
def get_pending_captures_api():
    """获取待确认队列中的低置信度记忆候选。"""
    try:
        from pipeline_dialogue import get_pending_captures
        return {"ok": True, "pending": get_pending_captures()}
    except Exception as e:
        raise HTTPException(500, f"获取待确认队列失败: {str(e)}")


@router.post("/api/pending-captures/confirm")
def confirm_pending_api(body: dict = Body(...)):
    """确认或拒绝待确认队列中的候选。

    Body: {"index": 0, "approve": true}
    """
    index = body.get("index")
    approve = body.get("approve", True)
    if index is None or not isinstance(index, int):
        raise HTTPException(400, "缺少 index 字段或类型错误")

    try:
        from pipeline_dialogue import confirm_pending
        return confirm_pending(index, approve)
    except Exception as e:
        raise HTTPException(500, f"确认失败: {str(e)}")


@router.post("/api/project/scan")
def scan_project_api():
    """扫描 DASHBOARD 项目的骨架变更，生成 milestone 记忆。"""
    try:
        from pipeline_project_watch import scan_project_changes
        captured_ids = scan_project_changes()
        return {"ok": True, "captured_ids": captured_ids, "count": len(captured_ids)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"项目扫描失败: {str(e)}")


@router.post("/api/social/ingest")
def social_ingest_api(body: dict = Body(...)):
    """社交媒体内容蒸馏入库。

    Body: {"url": "https://b23.tv/xxx", "user_note": ""}
    """
    url = body.get("url", "").strip()
    user_note = body.get("user_note", "")
    if not url:
        raise HTTPException(400, "缺少 url 字段")

    try:
        from pipeline_social_mcp import ingest_social
        return ingest_social(url, user_note)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"社交媒体入库失败: {str(e)}")


@router.post("/api/chat/distill")
def chat_distill_api(body: dict = Body(...)):
    """手动聊天蒸馏。

    Body: {"chat_text": "...", "context_hint": "工作群聊"}
    """
    chat_text = body.get("chat_text", "").strip()
    context_hint = body.get("context_hint", "")
    if not chat_text:
        raise HTTPException(400, "缺少 chat_text 字段")

    try:
        from pipeline_chat_manual import distill_chat
        return distill_chat(chat_text, context_hint)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"聊天蒸馏失败: {str(e)}")


@router.post("/api/chat/batch-distill")
async def chat_batch_distill_api(
    file: UploadFile = File(...),
    context_hint: str = Form(""),
    my_aliases: str = Form(""),
):
    """批量导入微信/QQ 聊天记录 txt 文件。

    - file: 聊天记录 txt 文件
    - context_hint: 上下文提示（如"工作群"、"和女朋友的聊天"）
    - my_aliases: L 的昵称，逗号分隔，默认 "L,我"
    """
    try:
        content = await file.read()
        chat_text = content.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(400, f"读取文件失败: {str(e)}")

    if not chat_text.strip():
        raise HTTPException(400, "文件内容为空")

    aliases = [a.strip() for a in my_aliases.split(",") if a.strip()] or None

    try:
        from pipeline_chat_manual import batch_distill_from_export
        return batch_distill_from_export(chat_text, context_hint, aliases)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"批量蒸馏失败: {str(e)}")
