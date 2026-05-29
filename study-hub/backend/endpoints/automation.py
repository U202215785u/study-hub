import os, sys, json, subprocess, re, tempfile, time, requests, uuid, threading, hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
from fastapi import APIRouter
from database import get_db
from processing.chunker import chunk_text
from processing.vector_store import get_vector_store
from social_parsers import BilibiliParser, XiaohongshuParser, QwenASR, HEADERS_BILIBILI
from douyin_mcp_server.server import DouyinProcessor

router = APIRouter()

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SUMMARIES_DIR = os.path.join(PROJECT_DIR, "douyin-summaries")
BILIBILI_DIR = os.path.join(PROJECT_DIR, "bilibili-summaries")
XHS_DIR = os.path.join(PROJECT_DIR, "xiaohongshu-summaries")
CLAUDE_CMD = r"C:\Users\Administrator\AppData\Roaming\npm\claude.cmd"

MODULES = {
    "douyin-summary": {
        "name": "抖音摘要", "icon": "📹", "output_dir": SUMMARIES_DIR,
        "source_tag": "douyin-summary", "engine": "deep",
    },
    "bilibili-summary": {
        "name": "B站解析", "icon": "📺", "output_dir": BILIBILI_DIR,
        "source_tag": "bilibili-summary", "engine": "deep",
    },
    "xiaohongshu-summary": {
        "name": "小红书解析", "icon": "📕", "output_dir": XHS_DIR,
        "source_tag": "xiaohongshu-summary", "engine": "deep",
    },
}


# ====== Data extraction (native) ======

def _extract_bilibili_raw(user_input: str) -> dict:
    info = BilibiliParser.get_video_info(user_input)
    raw = {
        "platform": "B站", "type": "视频",
        "url": f"https://www.bilibili.com/video/{info['bvid']}",
        "title": info["title"], "author": info["owner"]["name"],
        "description": info.get("description", ""),
        "duration": f"{info['duration'] // 60}分{info['duration'] % 60}秒",
        "category": info.get("tname", ""), "cover": info.get("cover", ""),
        "stats": {
            "播放": info["stat"]["view"], "弹幕": info["stat"]["danmaku"],
            "点赞": info["stat"]["like"], "硬币": info["stat"]["coin"],
            "收藏": info["stat"]["favorite"], "分享": info["stat"]["share"],
            "评论": info["stat"]["reply"],
        },
    }
    if info.get("cid_list") and len(info["cid_list"]) > 1:
        raw["pages"] = [{"page": p["page"], "title": p["part"]} for p in info["cid_list"]]

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if api_key:
        try:
            audio_url, _ = BilibiliParser.get_audio_url(user_input)
            asr = QwenASR(api_key)
            tmp_path = os.path.join(tempfile.gettempdir(), f"bilibili_asr_{info['bvid']}.m4a")
            try:
                audio_resp = requests.get(audio_url, headers=HEADERS_BILIBILI, timeout=60)
                audio_resp.raise_for_status()
                with open(tmp_path, "wb") as f:
                    f.write(audio_resp.content)
                result = asr.recognize(tmp_path, language="zh")
                os.remove(tmp_path)
            except Exception:
                result = asr.recognize(audio_url, language="zh")
            if result["success"] and result["text"]:
                raw["asr_text"] = result["text"]
            elif result["success"] and not result["text"]:
                raw["asr_error"] = "视频无语音或语音过短，无法识别"
            else:
                raw["asr_error"] = result.get("error", "识别失败")
                if "overdue" in raw["asr_error"].lower() or "access denied" in raw["asr_error"].lower():
                    raw["asr_error"] += "（阿里云百炼账号欠费，请充值后重试）"
        except Exception as e:
            raw["asr_error"] = str(e)
    else:
        raw["asr_error"] = "DASHSCOPE_API_KEY 未配置，请在 .env 中设置"
    return raw


def _extract_xiaohongshu_raw(user_input: str) -> dict:
    info = XiaohongshuParser.get_note_info(user_input)
    note_id = info.get("note_id", "")
    raw = {
        "platform": "小红书", "type": "视频" if info.get("video_url") else "图文",
        "url": f"https://www.xiaohongshu.com/explore/{note_id}",
        "title": info.get("title", "无标题"),
        "author": info.get("author", {}).get("name", ""),
        "description": info.get("description", ""),
        "tags": info.get("tags", []), "location": info.get("ip_location", ""),
        "stats": {
            "点赞": info.get("stat", {}).get("liked", 0),
            "收藏": info.get("stat", {}).get("collected", 0),
            "评论": info.get("stat", {}).get("comment", 0),
            "分享": info.get("stat", {}).get("shared", 0),
        },
        "images": info.get("images", [])[:9],
    }

    if info.get("video_url"):
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if api_key:
            try:
                asr = QwenASR(api_key)
                result = asr.recognize(info["video_url"], language="zh")
                if result["success"] and result["text"]:
                    raw["asr_text"] = result["text"]
                else:
                    raw["asr_error"] = result.get("error", "识别失败")
                    if "overdue" in raw["asr_error"].lower() or "access denied" in raw["asr_error"].lower():
                        raw["asr_error"] += "（阿里云百炼账号欠费，请充值后重试）"
            except Exception as e:
                raw["asr_error"] = str(e)
        else:
            raw["asr_error"] = "DASHSCOPE_API_KEY 未配置，请在 .env 中设置"
    return raw


def _extract_douyin_raw(user_input: str) -> dict:
    """用 DouyinProcessor 解析抖音视频，提取元数据 + ASR 文本。

    ASR 三级降级：
    1. 直接传视频 URL 给 DashScope（快，但限 10MB）
    2. 下载视频 → ffmpeg 提取音频 → ASR 音频文件
    3. 全部失败则记录错误原因
    """
    processor = DouyinProcessor("")
    info = processor.parse_share_url(user_input)

    raw = {
        "platform": "抖音", "type": "视频",
        "url": f"https://www.douyin.com/video/{info['video_id']}",
        "title": info["title"],
        "video_id": info["video_id"],
    }

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raw["asr_error"] = "DASHSCOPE_API_KEY 未配置，请在 .env 中设置"
        return raw

    asr = QwenASR(api_key)
    video_url = info["url"]

    # Level 1: 直接传视频 URL
    result = asr.recognize(video_url, language="zh")
    if result["success"] and result["text"]:
        raw["asr_text"] = result["text"]
        return raw

    # Level 1 失败，记录原因，尝试 Level 2
    l1_error = result.get("error", "识别失败")

    # Level 2: 下载视频 → ffmpeg 提取音频 → ASR
    try:
        import ffmpeg as ffmpeg_mod
        tmp_video = os.path.join(tempfile.gettempdir(), f"douyin_{info['video_id']}.mp4")
        tmp_audio = os.path.join(tempfile.gettempdir(), f"douyin_{info['video_id']}.mp3")

        # 下载视频
        resp = requests.get(video_url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15'
        }, timeout=120)
        resp.raise_for_status()
        with open(tmp_video, "wb") as f:
            f.write(resp.content)

        # ffmpeg 提取音频（64k mp3，压缩到 10MB 以内）
        ffmpeg_mod.input(tmp_video).output(
            tmp_audio, vn=None, acodec="libmp3lame", audio_bitrate="64k"
        ).run(capture_stdout=True, capture_stderr=True, overwrite_output=True)

        # ASR 音频文件
        result = asr.recognize(tmp_audio, language="zh")

        # 清理临时文件
        for p in [tmp_video, tmp_audio]:
            try: os.remove(p)
            except: pass

        if result["success"] and result["text"]:
            raw["asr_text"] = result["text"]
        elif result["success"] and not result["text"]:
            raw["asr_error"] = f"Level 1 失败（{l1_error}）；Level 2 音频提取成功但无有效语音"
        else:
            raw["asr_error"] = f"Level 1 失败（{l1_error}）；Level 2 失败（{result.get('error', '未知')}）"
            if "overdue" in raw["asr_error"].lower() or "access denied" in raw["asr_error"].lower():
                raw["asr_error"] += "（阿里云百炼账号欠费，请充值后重试）"
    except Exception as e:
        raw["asr_error"] = f"Level 1 失败（{l1_error}）；Level 2 异常（{e}）"

    return raw


# ====== Deep Summary Prompt ======

def _build_deep_prompt(module_id: str, raw: dict, user_input: str) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    raw_json = json.dumps(raw, ensure_ascii=False, indent=2)

    return f"""请根据以下从{raw['platform']}提取的原始数据，生成一份结构化的深度总结 Markdown 文档。

## 原始数据

```json
{raw_json}
```

## 用户原始输入
{user_input}

## 要求

你需要直接输出一份完整的 Markdown 文档，不要输出任何开头语、结尾语或解释说明。你的整个回复就是这份文档本身。

按以下步骤思考，但只输出最终文档：
1. 理解内容（2-3 句话概括核心观点）
2. 提取核心内容（分点展开，配合原文关键句）
3. 识别资源（用 WebSearch 验证链接，以表格列出）
4. 扩展阅读（用 WebSearch 搜索相关主题，3-5 条，优先中文）
5. 一句话思考总结（50 字以内）

如果 ASR 文本提取失败（存在 asr_error 字段），在核心内容章节如实引用错误原因。

## 必须严格按照以下格式输出

# {raw.get("title", "未命名")}

> 来源：[{raw['platform']}{raw.get('type', '')}]({raw.get('url', '')}) | 解析时间：{now_str}

---

## 内容概要

（2-3 句话概括）

---

## 核心内容

### 要点一：（小标题）
（展开说明）

### 要点二：（小标题）
（展开说明）

---

## 提到的资源

| 名称 | 类型 | 地址/说明 |
|:---|:---|:---|
| ... | ... | ... |

---

## 扩展阅读

- **（标题）**（链接） — 一句话说明
- ...

---

## 思考

（一句话总结，50 字以内）

## 重要
- 所有链接必须用 WebSearch 验证
- 扩展阅读 3-5 条，标注时效性（截至 {now_str[:7]}）
- 直接输出以上格式的 Markdown 文档，不要任何额外内容"""


# ====== Claude Code execution ======

def _run_claude(prompt: str, output_dir: str, timeout: int = 480) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    cutoff = time.time()

    try:
        result = subprocess.run(
            [CLAUDE_CMD, "-p", "--dangerously-skip-permissions"],
            cwd=PROJECT_DIR, input=prompt, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        result = None
    except FileNotFoundError:
        return {"error": "未找到 claude 命令，请确认 Claude Code 已安装"}

    md_files = []
    for f in os.listdir(output_dir):
        fp = os.path.join(output_dir, f)
        if f.endswith(".md") and os.path.getmtime(fp) > cutoff:
            md_files.append((os.path.getmtime(fp), fp))
    md_files.sort(reverse=True)

    if md_files:
        md_path = md_files[0][1]
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"md_path": md_path, "content": content}

    stdout = (result.stdout or "").strip() if result else ""
    stderr = (result.stderr or "").strip() if result else ""

    if stdout and len(stdout) > 50:
        title_line = ""
        for line in stdout.split("\n"):
            line = line.strip()
            if line.startswith("# ") and not line.startswith("## "):
                title_line = line[2:].strip()
                break
        safe = re.sub(r'[\\/:*?"<>|]', '_', title_line or "summary")[:60]
        md_path = os.path.join(output_dir, f"{safe}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(stdout)
        return {"md_path": md_path, "content": stdout}

    return {
        "status": "no_output",
        "message": "Claude Code 执行完成，但输出内容过短。请检查网络后重试。",
        "stderr": stderr[-500:] if stderr else "",
    }


# ====== Task Queue ======

MAX_WORKERS = 3
_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
# 细粒度进度步骤定义
STEPS = [
    ("extract_meta", "提取元数据"),
    ("download_audio", "下载音频"),
    ("asr", "ASR 识别"),
    ("summarize", "AI 总结"),
    ("import", "生成文档"),
]

_tasks: dict[str, dict] = {}  # task_id → {status, module_id, input, result, doc_id, title, error, created_at, steps, current_step}
_lock = threading.Lock()


def _init_task_steps(task_id: str):
    """初始化任务的细粒度进度步骤。"""
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        task["steps"] = [{"key": k, "label": l, "status": "pending"} for k, l in STEPS]
        task["current_step"] = None


def _update_step(task_id: str, step_key: str, step_status: str, progress_msg: str = None):
    """更新某个步骤的状态。"""
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        task["current_step"] = step_key
        if task.get("steps"):
            for s in task["steps"]:
                if s["key"] == step_key:
                    s["status"] = step_status
        if progress_msg:
            task["progress"] = progress_msg


def _process_single_task(task_id: str):
    """Worker: process one task and store result."""
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        task["status"] = "extracting"

    _init_task_steps(task_id)
    module_id = task["module_id"]
    user_input = task["input"]
    module = MODULES[module_id]
    engine = module.get("engine", "claude")
    output_dir = module["output_dir"]

    try:
        # Step 1: Extract meta
        _update_step(task_id, "extract_meta", "running", "正在提取元数据…")
        if engine == "deep":
            if module_id == "bilibili-summary":
                raw = _extract_bilibili_raw(user_input)
            elif module_id == "xiaohongshu-summary":
                raw = _extract_xiaohongshu_raw(user_input)
            elif module_id == "douyin-summary":
                raw = _extract_douyin_raw(user_input)
            else:
                raise ValueError(f"未知 deep 模块: {module_id}")
        else:
            raw = {"platform": "未知", "type": ""}
        _update_step(task_id, "extract_meta", "done")

        # Step 2: Summarize (includes ASR inside extract for now)
        _update_step(task_id, "summarize", "running", "正在 AI 深度分析…")
        if engine == "deep":
            prompt = _build_deep_prompt(module_id, raw, user_input)
        else:
            prompt = module["prompt_template"].format(input=user_input)

        result = _run_claude(prompt, output_dir, timeout=300 if engine == "claude" else 480)

        if "error" in result:
            raise RuntimeError(result["error"])
        if result.get("status") == "no_output":
            raise RuntimeError(result.get("message", "输出内容过短"))
        _update_step(task_id, "summarize", "done")

        # Step 3: Import
        _update_step(task_id, "import", "running", "正在入库 + 向量化…")
        content = result["content"]
        md_path = result["md_path"]

        title = os.path.basename(md_path).replace(".md", "")
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # 计算内容哈希，用于去重
        content_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

        conn = get_db()
        # 入库前查重：同一来源 + 相同内容视为重复
        dup = conn.execute(
            "SELECT id FROM documents WHERE source = ? AND content_hash = ? LIMIT 1",
            (module["source_tag"], content_hash),
        ).fetchone()
        if dup:
            doc_id = dup["id"]
            conn.close()
            with _lock:
                _tasks[task_id]["status"] = "done"
                _tasks[task_id]["progress"] = "完成（已存在）"
                _tasks[task_id]["result"] = {"doc_id": doc_id, "title": title}
            _update_step(task_id, "import", "done")
            return

        cur = conn.execute(
            "INSERT INTO documents (title, content, content_type, source, char_count, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (title, content, "text", module["source_tag"], len(content), content_hash),
        )
        doc_id = cur.lastrowid
        conn.commit()

        try:
            chunks = chunk_text(content)
            vs = get_vector_store()
            vs.add_document(doc_id, title, chunks)
            conn.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
            conn.commit()
        except Exception as e:
            print(f"向量化失败 (文档 {doc_id}): {e}")

        conn.close()

        with _lock:
            _tasks[task_id]["status"] = "done"
            _tasks[task_id]["progress"] = "完成"
            _tasks[task_id]["result"] = {"doc_id": doc_id, "title": title}
        _update_step(task_id, "import", "done")

    except Exception as e:
        with _lock:
            _tasks[task_id]["status"] = "error"
            _tasks[task_id]["progress"] = "失败"
            _tasks[task_id]["error"] = str(e)
        # 标记当前步骤为失败
        with _lock:
            t = _tasks.get(task_id)
            if t and t.get("current_step"):
                for s in t.get("steps", []):
                    if s["key"] == t["current_step"] and s["status"] == "running":
                        s["status"] = "error"


# ====== API endpoints ======

@router.get("/automation/modules")
def list_modules():
    return [{"id": mid, "name": m["name"], "icon": m["icon"]} for mid, m in MODULES.items()]


@router.post("/automation/run")
def run_automation(payload: dict):
    """同步执行（保持向后兼容）—— 单任务阻塞等待。"""
    module_id = payload.get("module_id", "")
    user_input = (payload.get("input") or "").strip()

    if module_id not in MODULES:
        return {"error": f"未知模块: {module_id}"}
    if not user_input:
        return {"error": "请输入内容"}
    if len(user_input) > 10000:
        return {"error": "输入内容过长，请限制在 10000 字以内"}

    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = {
        "task_id": task_id, "status": "pending", "module_id": module_id,
        "module_name": MODULES[module_id]["name"],
        "input": user_input, "progress": "排队中…",
        "created_at": datetime.now().isoformat(),
    }

    future: Future = _executor.submit(_process_single_task, task_id)
    future.result()  # 阻塞等待

    task = _tasks.get(task_id, {})
    if task.get("status") == "done":
        return {"status": "done", "task_id": task_id, **task.get("result", {})}
    return {"status": "error", "task_id": task_id, "error": task.get("error", "未知错误")}


@router.post("/automation/queue")
def queue_tasks(payload: dict):
    """批量提交任务，立即返回任务 ID 列表。支持多个链接（\\n 分隔或数组）。"""
    module_id = payload.get("module_id", "")
    inputs = payload.get("inputs", [])

    # 支持单个 input 字符串（换行分隔）
    if not inputs:
        single = (payload.get("input") or "").strip()
        if single:
            inputs = [line.strip() for line in single.split("\n") if line.strip()]

    if module_id not in MODULES:
        return {"error": f"未知模块: {module_id}"}
    if not inputs:
        return {"error": "请输入至少一个链接"}

    # 去重：同一批次内相同输入只保留一个（保留顺序）
    seen = set()
    unique_inputs = []
    for inp in inputs:
        normalized = inp.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_inputs.append(normalized)
    inputs = unique_inputs

    tasks_created = []
    for inp in inputs:
        if len(inp) > 10000:
            continue
        task_id = str(uuid.uuid4())[:8]
        with _lock:
            _tasks[task_id] = {
                "task_id": task_id, "status": "pending", "module_id": module_id,
                "module_name": MODULES[module_id]["name"],
                "input": inp[:200], "progress": "排队中…",
                "created_at": datetime.now().isoformat(),
            }
        _executor.submit(_process_single_task, task_id)
        tasks_created.append(task_id)

    return {
        "status": "queued",
        "count": len(tasks_created),
        "task_ids": tasks_created,
        "message": f"已提交 {len(tasks_created)} 个任务，最多 {MAX_WORKERS} 个并行处理",
    }


@router.get("/automation/queue/status")
def queue_status():
    """获取所有任务状态（最近 50 个）。"""
    with _lock:
        all_tasks = list(_tasks.values())

    # 按创建时间倒序，最多 50 个
    all_tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    recent = all_tasks[:50]

    stats = {
        "total": len(recent),
        "pending": sum(1 for t in recent if t["status"] == "pending"),
        "running": sum(1 for t in recent if t["status"] in ("extracting", "summarizing", "importing")),
        "done": sum(1 for t in recent if t["status"] == "done"),
        "error": sum(1 for t in recent if t["status"] == "error"),
        "max_workers": MAX_WORKERS,
    }

    # 精简返回字段
    items = []
    for t in recent:
        items.append({
            "task_id": t["task_id"], "status": t["status"],
            "module_name": t.get("module_name", ""),
            "input": t.get("input", "")[:100],
            "progress": t.get("progress", ""),
            "error": t.get("error", ""),
            "doc_id": (t.get("result") or {}).get("doc_id") if t.get("result") else None,
            "title": (t.get("result") or {}).get("title") if t.get("result") else None,
            "created_at": t.get("created_at", ""),
            "steps": t.get("steps"),
            "current_step": t.get("current_step"),
        })

    return {"stats": stats, "tasks": items}


@router.get("/automation/queue/{task_id}")
def task_status(task_id: str):
    """查询单个任务状态。"""
    task = _tasks.get(task_id)
    if not task:
        return {"error": "任务不存在"}
    return {
        "task_id": task["task_id"], "status": task["status"],
        "module_name": task.get("module_name", ""),
        "input": task.get("input", "")[:200],
        "progress": task.get("progress", ""),
        "error": task.get("error", ""),
        "result": task.get("result"),
        "created_at": task.get("created_at", ""),
        "steps": task.get("steps"),
        "current_step": task.get("current_step"),
    }


@router.delete("/automation/queue/clear")
def clear_completed():
    """清除已完成和失败的任务。"""
    with _lock:
        to_remove = [tid for tid, t in _tasks.items() if t["status"] in ("done", "error")]
        for tid in to_remove:
            del _tasks[tid]
    return {"cleared": len(to_remove)}


# ====== 重解析 & 清理 ======

@router.post("/automation/reparse/{doc_id}")
def reparse_document(doc_id: int):
    """
    重新解析失败的抖音摘要文档。
    提取原始抖音链接 → 删除旧文档 → 重新提交自动化任务。
    """
    import re

    conn = get_db()
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return {"error": "文档不存在"}

    content = doc["content"] or ""
    title = doc["title"] or ""

    # 提取抖音链接
    douyin_match = re.search(r'https?://v\.douyin\.com/[^\s)\]]+', content)
    if not douyin_match:
        douyin_match = re.search(r'https?://www\.douyin\.com/[^\s)\]]+', content)
    if not douyin_match:
        conn.close()
        return {"error": "文档中未找到抖音链接，无法重新解析"}

    original_link = douyin_match.group(0).rstrip('.。，,')
    conn.close()

    # 删除旧文档（含向量库）
    _delete_document_full(doc_id)

    # 提交新任务
    task_id = str(uuid.uuid4())[:8]
    with _lock:
        _tasks[task_id] = {
            "task_id": task_id, "status": "pending", "module_id": "douyin-summary",
            "module_name": "抖音摘要（重新解析）",
            "input": original_link, "progress": "排队中…",
            "created_at": datetime.now().isoformat(),
        }
    _executor.submit(_process_single_task, task_id)

    return {
        "status": "queued",
        "task_id": task_id,
        "message": f"已重新提交解析任务（原文档：{title}），处理中…",
        "original_link": original_link,
    }


@router.get("/automation/reparseable")
def list_reparseable():
    """列出可以重新解析的文档（ASR 失败或内容不完整）。"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, content, source, char_count, created_at FROM documents "
        "WHERE source IN ('douyin-summary', 'bilibili-summary', 'xiaohongshu-summary') "
        "ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    conn.close()

    import re
    result = []
    for r in rows:
        content = r["content"] or ""
        is_failed = "语音提取失败" in content or "⚠️ 语音提取失败" in content
        is_api_fail = "API" in content[:500] and ("不可用" in content[:500] or "欠费" in content[:500])
        is_level3 = "Level 3" in content[:1000] and "基于视频标题" in content[:1000]
        has_link = bool(re.search(r'https?://v\.douyin\.com/[^\s)\]]+', content))

        if is_failed or is_api_fail or is_level3:
            result.append({
                "doc_id": r["id"], "title": r["title"],
                "source": r["source"], "char_count": r["char_count"],
                "created_at": r["created_at"],
                "fail_reason": "API不可用" if is_api_fail else ("ASR失败" if is_failed else "仅标题推断"),
                "has_link": has_link,
            })

    return {"count": len(result), "documents": result}


@router.post("/documents/cleanup")
def cleanup_documents(payload: dict = None):
    """
    批量清理测试文档、重复文档、无意义短文档。
    支持模式：
    - test: 标题含 test/测试 的文档
    - short: 少于 50 字的文档
    - duplicates: 标题重复的文档（保留第一个）
    - all: 以上全部
    """
    if payload is None:
        payload = {}
    mode = payload.get("mode", "all")
    dry_run = payload.get("dry_run", True)  # 默认预演，不实际删除

    conn = get_db()
    to_delete = set()

    # 1. 测试文档
    if mode in ("test", "all"):
        test_rows = conn.execute(
            "SELECT id, title FROM documents WHERE lower(title) LIKE '%test%' OR title LIKE '%测试%' OR title = 'MCP测试'"
        ).fetchall()
        for r in test_rows:
            to_delete.add(r["id"])

    # 2. 短文档（< 50 字，且不是 douyin/bilibili/xiaohongshu 摘要）
    if mode in ("short", "all"):
        short_rows = conn.execute(
            "SELECT id, title, char_count FROM documents WHERE char_count < 50 "
            "AND source NOT IN ('douyin-summary', 'bilibili-summary', 'xiaohongshu-summary')"
        ).fetchall()
        for r in short_rows:
            to_delete.add(r["id"])

    # 3. 重复文档（检测 upload/extension/claude-desktop/inbox 来源）
    if mode in ("duplicates", "all"):
        dup_rows = conn.execute(
            "SELECT id, title, source, created_at FROM documents "
            "WHERE source IN ('upload', 'extension', 'claude-desktop', 'inbox') "
            "ORDER BY title, created_at"
        ).fetchall()
        seen_titles = {}
        for r in dup_rows:
            normalized = r["title"].strip().lower().replace(" ", "").replace("-", "").replace("_", "")
            key = normalized[:40]
            if key in seen_titles:
                to_delete.add(r["id"])
            else:
                seen_titles[key] = r["id"]

    # 4. 摘要文档重复（抖音/B站/小红书，优先按 content_hash，回退到 title）
    if mode in ("duplicates", "all"):
        summary_rows = conn.execute(
            "SELECT id, title, source, created_at, content_hash FROM documents "
            "WHERE source IN ('douyin-summary', 'bilibili-summary', 'xiaohongshu-summary') "
            "ORDER BY created_at"
        ).fetchall()
        seen_hashes = {}
        seen_summary_titles = {}
        for r in summary_rows:
            # 优先使用 content_hash 去重（新记录）
            if r["content_hash"]:
                key = (r["source"], r["content_hash"])
                if key in seen_hashes:
                    to_delete.add(r["id"])
                    continue
                seen_hashes[key] = r["id"]
            else:
                # 旧记录没有 content_hash，回退到 title 归一化去重
                normalized = r["title"].strip().lower().replace(" ", "").replace("-", "").replace("_", "")
                key = (r["source"], normalized[:40])
                if key in seen_summary_titles:
                    to_delete.add(r["id"])
                else:
                    seen_summary_titles[key] = r["id"]

    conn.close()

    if dry_run:
        # 返回将要删除的文档列表
        conn = get_db()
        details = []
        for did in to_delete:
            row = conn.execute("SELECT id, title, source, char_count FROM documents WHERE id = ?", (did,)).fetchone()
            if row:
                details.append({"id": row["id"], "title": row["title"], "source": row["source"], "char_count": row["char_count"]})
        conn.close()
        return {
            "dry_run": True,
            "count": len(to_delete),
            "documents": details,
            "message": f"预演模式：将删除 {len(to_delete)} 个文档。设置 dry_run=false 确认执行。",
        }

    # 实际删除
    deleted_count = 0
    for did in to_delete:
        try:
            _delete_document_full(did)
            deleted_count += 1
        except Exception:
            pass

    return {"dry_run": False, "deleted": deleted_count}


def _delete_document_full(doc_id: int):
    """完整删除文档：SQLite + 向量库。"""
    conn = get_db()
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return

    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    try:
        vs = get_vector_store()
        existing = vs.collection.get(where={"doc_id": doc_id})
        if existing and existing["ids"]:
            vs.collection.delete(ids=existing["ids"])
    except Exception:
        pass
