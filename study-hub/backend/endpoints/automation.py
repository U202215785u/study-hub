import os, sys, json, subprocess, re, tempfile, time, requests
from datetime import datetime
from fastapi import APIRouter
from database import get_db
from processing.chunker import chunk_text
from processing.vector_store import get_vector_store

_STUDY_HUB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _STUDY_HUB_DIR not in sys.path:
    sys.path.insert(0, _STUDY_HUB_DIR)

from social_parsers import BilibiliParser, XiaohongshuParser, QwenASR, HEADERS_BILIBILI

router = APIRouter()

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SUMMARIES_DIR = os.path.join(PROJECT_DIR, "douyin-summaries")
BILIBILI_DIR = os.path.join(PROJECT_DIR, "bilibili-summaries")
XHS_DIR = os.path.join(PROJECT_DIR, "xiaohongshu-summaries")
CLAUDE_CMD = r"C:\Users\Administrator\AppData\Roaming\npm\claude.cmd"

MODULES = {
    "douyin-summary": {
        "name": "抖音摘要",
        "icon": "📹",
        "output_dir": SUMMARIES_DIR,
        "source_tag": "douyin-summary",
        "engine": "claude",
        "prompt_template": (
            "请帮我总结这个抖音视频：{input}\n\n"
            "请使用 douyin-summary skill 完成。要求：\n"
            "1. 提取视频中的文字内容\n"
            "2. 识别文中提到的链接/资源\n"
            "3. 扩展相关知识\n"
            "4. 输出结构化 Markdown 文档"
        ),
    },
    "bilibili-summary": {
        "name": "B站解析",
        "icon": "📺",
        "output_dir": BILIBILI_DIR,
        "source_tag": "bilibili-summary",
        "engine": "deep",
    },
    "xiaohongshu-summary": {
        "name": "小红书解析",
        "icon": "📕",
        "output_dir": XHS_DIR,
        "source_tag": "xiaohongshu-summary",
        "engine": "deep",
    },
}


# ====== 数据提取（native） ======

def _extract_bilibili_raw(user_input: str) -> dict:
    """调用 B站 API 提取原始数据，尝试 ASR 语音识别"""
    info = BilibiliParser.get_video_info(user_input)
    raw = {
        "platform": "B站",
        "type": "视频",
        "url": f"https://www.bilibili.com/video/{info['bvid']}",
        "title": info["title"],
        "author": info["owner"]["name"],
        "description": info.get("description", ""),
        "duration": f"{info['duration'] // 60}分{info['duration'] % 60}秒",
        "category": info.get("tname", ""),
        "cover": info.get("cover", ""),
        "stats": {
            "播放": info["stat"]["view"],
            "弹幕": info["stat"]["danmaku"],
            "点赞": info["stat"]["like"],
            "硬币": info["stat"]["coin"],
            "收藏": info["stat"]["favorite"],
            "分享": info["stat"]["share"],
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
            # B站音频URL有防盗链，先下载到本地再识别
            tmp_path = os.path.join(tempfile.gettempdir(), f"bilibili_asr_{info['bvid']}.m4a")
            try:
                audio_resp = requests.get(audio_url, headers=HEADERS_BILIBILI, timeout=60)
                audio_resp.raise_for_status()
                with open(tmp_path, "wb") as f:
                    f.write(audio_resp.content)
                result = asr.recognize(tmp_path, language="zh")
                os.remove(tmp_path)
            except Exception:
                # 下载失败则回退到直接传URL
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
    """调用小红书解析器提取原始数据，视频笔记尝试 ASR"""
    info = XiaohongshuParser.get_note_info(user_input)
    note_id = info.get("note_id", "")
    raw = {
        "platform": "小红书",
        "type": "视频" if info.get("video_url") else "图文",
        "url": f"https://www.xiaohongshu.com/explore/{note_id}",
        "title": info.get("title", "无标题"),
        "author": info.get("author", {}).get("name", ""),
        "description": info.get("description", ""),
        "tags": info.get("tags", []),
        "location": info.get("ip_location", ""),
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


# ====== Deep Summary Prompt 构建 ======

def _build_deep_prompt(module_id: str, raw: dict, user_input: str) -> str:
    """根据平台原始数据构建 deep-summary prompt，格式对齐 douyin-summary skill"""
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

如果 ASR 文本提取失败（存在 asr_error 字段），在核心内容章节如实引用错误原因，例如：
- 欠费 → 「⚠️ 语音提取失败（阿里云百炼账号欠费），以下基于标题和描述重建」
- API Key 未配置 → 「⚠️ 语音提取失败（API Key 未配置），以下基于标题和描述重建」
- 其他错误 → 「⚠️ 语音提取失败（{{错误原因}}），以下基于标题和描述重建」

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


# ====== Claude Code 执行 ======

def _run_claude(prompt: str, output_dir: str, timeout: int = 480) -> dict:
    """通过 claude -p 执行，优先使用 Claude 写入/更新的 .md 文件，否则回退到 stdout"""
    os.makedirs(output_dir, exist_ok=True)
    # 记录执行前最后修改时间，用于检测新增或被覆盖的文件
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

    # 找到执行后修改/新增的 .md 文件（按修改时间倒序）
    md_files = []
    for f in os.listdir(output_dir):
        fp = os.path.join(output_dir, f)
        if f.endswith(".md") and os.path.getmtime(fp) > cutoff:
            md_files.append((os.path.getmtime(fp), fp))
    md_files.sort(reverse=True)

    # 优先使用 Claude 通过 Write 工具生成/更新的文件
    if md_files:
        md_path = md_files[0][1]
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"md_path": md_path, "content": content}

    # 回退：stdout 直接输出
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


# ====== API 端点 ======

@router.get("/automation/modules")
def list_modules():
    return [
        {"id": mid, "name": m["name"], "icon": m["icon"]}
        for mid, m in MODULES.items()
    ]


@router.post("/automation/run")
def run_automation(payload: dict):
    module_id = payload.get("module_id", "")
    user_input = (payload.get("input") or "").strip()

    if module_id not in MODULES:
        return {"error": f"未知模块: {module_id}"}
    if not user_input:
        return {"error": "请输入内容"}
    if len(user_input) > 10000:
        return {"error": "输入内容过长，请限制在 10000 字以内"}

    module = MODULES[module_id]
    engine = module.get("engine", "claude")
    output_dir = module["output_dir"]

    # ---- 数据提取 + Claude 深度格式化 ----
    if engine == "deep":
        try:
            if module_id == "bilibili-summary":
                raw = _extract_bilibili_raw(user_input)
            elif module_id == "xiaohongshu-summary":
                raw = _extract_xiaohongshu_raw(user_input)
            else:
                return {"error": f"未知 deep 模块: {module_id}"}
        except Exception as e:
            return {"error": f"数据提取失败: {str(e)}"}

        prompt = _build_deep_prompt(module_id, raw, user_input)
        result = _run_claude(prompt, output_dir)

    elif engine == "claude":
        # 抖音：直接使用 skill prompt
        prompt = module["prompt_template"].format(input=user_input)
        result = _run_claude(prompt, output_dir, timeout=300)

    else:
        return {"error": f"未知引擎: {engine}"}

    if "error" in result or result.get("status") == "no_output":
        return result

    content = result["content"]
    md_path = result["md_path"]

    # 从内容提取标题
    title = os.path.basename(md_path).replace(".md", "")
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # ---- 入库 + 向量化 ----
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO documents (title, content, content_type, source, char_count) VALUES (?, ?, ?, ?, ?)",
        (title, content, "text", module["source_tag"], len(content)),
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
    return {"status": "done", "doc_id": doc_id, "title": title}
