import os, sys, json, subprocess, re, tempfile, time, requests, uuid, threading, hashlib, base64
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
from fastapi import APIRouter
from database import get_db
from processing.chunker import chunk_text
from processing.vector_store import get_vector_store
from social_parsers import BilibiliParser, XiaohongshuParser, QwenASR, HEADERS_BILIBILI
# douyin_mcp_server 模块可能未安装，延迟导入
try:
    from douyin_mcp_server.server import DouyinProcessor
except ImportError:
    DouyinProcessor = None

router = APIRouter()

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SUMMARIES_DIR = os.path.join(PROJECT_DIR, "douyin-summaries")
BILIBILI_DIR = os.path.join(PROJECT_DIR, "bilibili-summaries")
XHS_DIR = os.path.join(PROJECT_DIR, "xiaohongshu-summaries")
CLAUDE_CMD = r"C:\Users\Administrator\AppData\Roaming\npm\claude.cmd"

# ffmpeg 路径自动检测（避免 MinGW/MSYS nohup 等隔离环境丢失 PATH）
def _find_ffmpeg() -> str:
    """在已知位置搜索 ffmpeg.exe，找不到则回退到 'ffmpeg'（靠 PATH）。"""
    import shutil
    candidates = [
        # WinGet 安装
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
        # Chocolatey 安装
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        # 手动安装常见路径
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    # 回退：尝试 shutil.which 在 PATH 中搜索
    found = shutil.which("ffmpeg")
    return found if found else "ffmpeg"

FFMPEG_CMD = _find_ffmpeg()


def verify_external_deps() -> dict:
    """启动时校验外部依赖（ffmpeg / claude 等），返回状态报告。

    调用方（如 main.py lifespan）应在启动时调用此函数并将结果打印到日志。
    如果依赖不可用，此处只报告警告，不阻止启动——
    因为用户可能在使用不需要该依赖的功能。
    """
    import subprocess as sp
    report: dict[str, dict] = {}

    # 1. ffmpeg
    ffmpeg_found = os.path.isfile(FFMPEG_CMD) if FFMPEG_CMD != "ffmpeg" else False
    ffmpeg_works = False
    try:
        result = sp.run(
            [FFMPEG_CMD, "-version"],
            capture_output=True, text=True, timeout=10,
        )
        ffmpeg_works = (result.returncode == 0)
    except Exception:
        pass

    report["ffmpeg"] = {
        "path": FFMPEG_CMD,
        "found_on_disk": ffmpeg_found or ffmpeg_works,
        "executable": ffmpeg_works,
        "warning": None if ffmpeg_works else (
            f"ffmpeg 不可用（路径: {FFMPEG_CMD}）。"
            f"抖音/B站/小红书语音提取将失败。"
            f"请安装 ffmpeg 或更新 automation.py 中 _find_ffmpeg() 的搜索路径。"
        ),
    }

    # 2. Claude Code CLI
    claude_ok = os.path.isfile(CLAUDE_CMD)
    if not claude_ok:
        # 尝试 which
        import shutil
        alt = shutil.which("claude") or shutil.which("claude.cmd")
        if alt:
            claude_ok = True
    report["claude"] = {
        "path": CLAUDE_CMD,
        "found_on_disk": claude_ok,
        "warning": None if claude_ok else (
            f"Claude Code CLI 未找到（路径: {CLAUDE_CMD}）。"
            f"深度总结功能将不可用。"
            f"请安装 Claude Code 并确认路径。"
        ),
    }

    return report

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

    # 检测 API Key 无效错误
    if "invalid api-key" in raw.get("asr_error", "").lower():
        raw["asr_api_key_invalid"] = True

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

    # 补充视频时长（如有）
    if info.get("video_url") and info.get("video_duration"):
        try:
            vd = float(info["video_duration"])
            raw["duration"] = f"{int(vd) // 60}分{int(vd) % 60}秒"
        except (ValueError, TypeError):
            pass

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

    # 检测 API Key 无效错误
    if "invalid api-key" in raw.get("asr_error", "").lower():
        raw["asr_api_key_invalid"] = True

    return raw


def _preprocess_douyin_input(user_input: str) -> str:
    """预处理抖音输入：从口令/分享文本中提取有效链接。

    抖音分享口令可能包含以下格式：
    - 标准 URL: https://v.douyin.com/xxxxx
    - 无协议短链: v.douyin.com/xxxxx
    - 图集链接: www.iesdouyin.com/share/note/xxxxx
    本函数会把无协议的短链补全为 https:// 格式。
    """
    text = user_input.strip()
    # 1. 如果已经包含标准 http(s) URL，直接返回
    if re.search(r'https?://', text):
        return text
    # 2. 提取 v.douyin.com/xxxxx 短链并补全协议
    m = re.search(r'v\.douyin\.com/[a-zA-Z0-9]+', text)
    if m:
        return 'https://' + m.group(0)
    # 3. 提取 iesdouyin.com 链接并补全协议
    m = re.search(r'www\.iesdouyin\.com/share/(?:video|note)/\d+', text)
    if m:
        return 'https://' + m.group(0)
    # 4. 兜底：原样返回，让下游抛出更具体的错误
    return text




# ====== 火山引擎 ASR（豆包语音，无 60s/10MB 限制）======

_VOLC_ENDPOINT = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"


_VOLC_RESOURCE_IDS = [
    "volc.bigasr.auc_turbo",    # 极速版
    "volc.seedasr.auc1",        # 2.0
    "volc.bigasr.auc1",         # 1.0
    "volc.bigasr.auc_idle5",    # 闲时版
]


def _volcengine_asr(audio_path: str) -> dict:
    """使用火山引擎 BigModel ASR 转写音频，自动探测可用资源。"""
    import requests as req
    app_key = os.getenv("VOLC_APP_KEY", "").strip()
    access_key = os.getenv("VOLC_ACCESS_KEY", "").strip()
    resource_id = os.getenv("VOLC_RESOURCE_ID", "").strip()

    if not app_key or not access_key:
        return {"success": False, "text": "", "error": "火山引擎 ASR 未配置，请在 .env 中设置 VOLC_APP_KEY 和 VOLC_ACCESS_KEY"}

    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 探测可用的资源 ID
    rids = [resource_id] if resource_id else []
    rids += [r for r in _VOLC_RESOURCE_IDS if r not in rids]

    last_error = ""
    for rid in rids:
        headers = {
            "X-Api-App-Key": app_key,
            "X-Api-Access-Key": access_key,
            "X-Api-Resource-Id": rid,
            "X-Api-Request-Id": str(uuid.uuid4()),
            "X-Api-Sequence": "-1",
            "Content-Type": "application/json",
        }
        body = {
            "user": {"uid": app_key},
            "audio": {"data": audio_b64},
            "request": {"model_name": "bigmodel", "enable_punc": True, "enable_itn": True},
        }
        try:
            resp = req.post(_VOLC_ENDPOINT, headers=headers, json=body, timeout=120)
            status_code = resp.headers.get("X-Api-Status-Code", "")
            if status_code == "20000000":
                result = resp.json().get("result", {})
                text = result.get("text", "") or ""
                if not text:
                    utterances = result.get("utterances", [])
                    text = "".join(u.get("text", "") for u in utterances)
                return {"success": True, "text": text, "language": None, "usage": None,
                        "request_id": resp.headers.get("X-Api-Request-Id", ""),
                        "resource_id_used": rid}
            try:
                last_error = resp.json().get("header", {}).get("message", str(resp.status_code))
            except Exception:
                last_error = resp.text[:200]
            if "not allowed" not in last_error.lower() and "not granted" not in last_error.lower():
                break  # 非权限错误，不继续试
        except Exception as e:
            last_error = str(e)

    return {"success": False, "text": "", "error": f"火山引擎 ASR 失败: {last_error}"}


def _extract_douyin_raw(user_input: str) -> dict:
    """用 DouyinProcessor 解析抖音视频，提取元数据 + ASR 文本。

    ASR 优先火山引擎（无 60s/10MB 限制），回退 DashScope（55s trim）。
    """
    if DouyinProcessor is None:
        return {
            "platform": "抖音", "type": "视频",
            "url": user_input,
            "title": "抖音解析暂不可用",
            "asr_error": "douyin_mcp_server 模块未安装，抖音解析功能暂不可用。请安装该模块或联系管理员。"
        }
    processor = DouyinProcessor("")
    cleaned_input = _preprocess_douyin_input(user_input)
    info = processor.parse_share_url(cleaned_input)

    raw = {
        "platform": "抖音", "type": "视频",
        "url": f"https://www.douyin.com/video/{info['video_id']}",
        "title": info["title"],
        "video_id": info["video_id"],
    }

    # 检测 ASR 引擎：火山引擎优先，否则 DashScope
    use_volc = bool(os.getenv("VOLC_APP_KEY", "").strip())
    if not use_volc and not os.getenv("DASHSCOPE_API_KEY"):
        raw["asr_error"] = "DASHSCOPE_API_KEY 或 VOLC_APP_KEY 未配置，请在 .env 中设置"
        return raw

    asr = QwenASR(os.getenv("DASHSCOPE_API_KEY", "")) if not use_volc else None
    video_url = info["url"]
    tmp_video = tmp_audio = None

    try:
        import ffmpeg as ffmpeg_mod
        tmp_video = os.path.join(tempfile.gettempdir(), f"douyin_{info['video_id']}.mp4")
        tmp_audio = os.path.join(tempfile.gettempdir(), f"douyin_{info['video_id']}.mp3")

        # 下载视频
        resp = requests.get(video_url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15'
        }, timeout=120)
        resp.raise_for_status()

        # 校验下载内容是否为有效视频（防止反爬页面 / 过期链接）
        content_type = resp.headers.get("Content-Type", "")
        content_start = resp.content[:200]
        content_len = len(resp.content)
        if content_len < 1024:
            raw["asr_error"] = (
                f"视频下载失败：返回数据过小（{content_len} 字节），可能是链接已过期。"
                "请尝试重新复制分享链接后重试。"
            )
            return raw
        if "text/html" in content_type or content_start.startswith(b"<!DOCTYPE") or content_start.startswith(b"<html"):
            raw["asr_error"] = (
                "视频下载失败：服务器返回了网页而非视频文件。"
                "可能是视频链接已过期、被屏蔽，或抖音限制了访问。"
                "请尝试重新复制分享链接后重试。"
            )
            return raw

        with open(tmp_video, "wb") as f:
            f.write(resp.content)

        # ffmpeg 提取音频
        if use_volc:
            # 火山引擎：2h/100MB 限制，无需截断
            ffmpeg_mod.input(tmp_video).output(
                tmp_audio, vn=None, acodec="libmp3lame", audio_bitrate="64k"
            ).run(cmd=FFMPEG_CMD, capture_stdout=True, capture_stderr=True, overwrite_output=True)
            result = _volcengine_asr(tmp_audio)
        else:
            # DashScope flash：60s/10MB 限制，截取前 55 秒
            ffmpeg_mod.input(tmp_video).output(
                tmp_audio, vn=None, acodec="libmp3lame", audio_bitrate="64k",
                **{"t": "55"}
            ).run(cmd=FFMPEG_CMD, capture_stdout=True, capture_stderr=True, overwrite_output=True)
            result = asr.recognize(tmp_audio, language="zh")

        if result["success"] and result["text"]:
            raw["asr_text"] = result["text"]
        elif result["success"] and not result["text"]:
            raw["asr_error"] = "视频无语音或语音过短，无法识别"
        else:
            raw["asr_error"] = result.get("error", "识别失败")
            if "overdue" in raw["asr_error"].lower() or "access denied" in raw["asr_error"].lower():
                raw["asr_error"] += "（阿里云百炼账号欠费，请充值后重试）"

    except FileNotFoundError as e:
        raw["asr_error"] = f"ffmpeg 未找到（{e}）。请安装 ffmpeg 并确保其在系统 PATH 中，或重启后端以刷新 PATH。"
    except Exception as e:
        error_msg = str(e)
        # 提取 ffmpeg 详细错误信息
        if hasattr(e, 'stderr') and e.stderr:
            stderr_text = e.stderr.decode('utf-8', errors='replace')
            for line in stderr_text.split('\n'):
                line_lower = line.lower()
                if 'error:' in line_lower or 'invalid' in line_lower or 'no such file' in line_lower:
                    error_msg = line.strip()
                    break
            # 识别特定错误类型，给出可操作的提示
            if "invalid data found when processing input" in stderr_text.lower():
                error_msg = (
                    "下载的视频文件无效（非视频数据或已损坏）。"
                    "请尝试重新复制抖音分享链接后重试。"
                )
        raw["asr_error"] = f"语音提取失败：{error_msg}"

    finally:
        # 确保临时文件始终被清理
        for p in [tmp_video, tmp_audio]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    # 检测 API Key 无效错误
    if "invalid api-key" in raw.get("asr_error", "").lower():
        raw["asr_api_key_invalid"] = True

    return raw


# ====== Deep Summary Prompt ======

def _build_deep_prompt(module_id: str, raw: dict, user_input: str) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    raw_json = json.dumps(raw, ensure_ascii=False, indent=2)

    # 构建来源栏增强信息
    platform = raw.get('platform', '')
    type_ = raw.get('type', '')
    author = raw.get('author', '')
    duration = raw.get('duration', '')
    source_parts = [f"{platform}{type_}"]
    if author:
        source_parts.append(f"@{author}")
    source_line = " · ".join(source_parts)
    if duration:
        source_line += f" | {duration}"

    # 无语音视频标注提示
    no_speech_note = ""
    asr_error = raw.get("asr_error", "")
    if "无语音" in asr_error or "语音过短" in asr_error:
        no_speech_note = (
            "\n【重要】ASR 返回无语音或语音过短，你只有标题和描述可以参考。"
            "请在 `## 内容概要` 段落开头插入以下标注：\n"
            "> ⚠️ 该视频无语音或语音过短，以下内容基于标题和描述推断\n"
            "然后继续基于现有信息生成其余章节。"
        )

    return f"""请根据以下从{platform}提取的原始数据，生成一份结构化的深度总结 Markdown 文档。

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
5. 输出 1~2 条具体行动建议（如"可用此工具做 xxx"、"建议关注该仓库的 releases"）
{no_speech_note}

## 必须严格按照以下格式输出

# {raw.get("title", "未命名")}

> 来源：[{source_line}]({raw.get('url', '')}) | 解析时间：{now_str}

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

## 行动建议

1. ...

## 重要
- 所有链接必须用 WebSearch 验证
- 扩展阅读 3-5 条，标注时效性（截至 {now_str[:7]}）
- 章节标题必须严格按照以上内容，禁止自创标题
- 直接输出以上格式的 Markdown 文档，不要任何额外内容"""


# ====== ASR failure fallback ======

def _should_fallback_to_meta_card(raw: dict) -> bool:
    """判断是否需要降级为元数据卡片（ASR 致命失败）。"""
    asr_error = raw.get("asr_error", "")
    asr_text = raw.get("asr_text", "")
    # 有有效 ASR 文本，正常生成
    if asr_text and len(asr_text.strip()) > 10:
        return False
    # 无 ASR 错误，正常生成（如小红书图文有 description）
    if not asr_error:
        return False
    # 无语音/语音过短不算致命错误，继续生成但加标注
    if "无语音" in asr_error or "语音过短" in asr_error:
        return False
    # 其他 ASR 错误（API 错误、超时、欠费等）降级
    return True


def _build_meta_card(raw: dict, user_input: str) -> dict:
    """ASR 失败时生成元数据卡片，返回和 _run_claude 兼容的 dict。"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = raw.get("title", "").strip()
    if not title:
        platform = raw.get("platform", "未知")
        vid = raw.get("video_id") or raw.get("bvid") or raw.get("note_id") or ""
        title = f"未知标题（{platform} {vid}）" if vid else f"未知标题（{platform}）"

    platform = raw.get("platform", "")
    type_ = raw.get("type", "")
    url = raw.get("url", "")
    author = raw.get("author", "") or "未知"
    duration = raw.get("duration", "")

    source_parts = [f"{platform}{type_}"]
    if author and author != "未知":
        source_parts.append(f"@{author}")
    source_line = " · ".join(source_parts)
    if duration:
        source_line += f" | {duration}"

    asr_error = raw.get("asr_error", "语音提取失败")
    # 过滤换行符，防止破坏 Markdown 结构
    asr_error = asr_error.replace("\n", " ").replace("\r", " ")
    # 清理过长的错误信息，保留核心
    if len(asr_error) > 200:
        asr_error = asr_error[:200] + "…"

    lines = [
        f"# {title}",
        "",
        f"> 来源：[{source_line}]({url}) | 解析时间：{now_str}",
        "",
        "---",
        "",
        "## 解析状态",
        "",
        f"⚠️ {asr_error}",
        "",
        "---",
        "",
        "## 已知信息",
        "",
    ]

    desc = raw.get("description", "")
    if desc and len(desc.strip()) > 5:
        lines.append(f"- **简介**：{desc.strip()[:300]}")
    lines.append(f"- **平台**：{platform}")
    if author and author != "未知":
        lines.append(f"- **作者**：{author}")
    if raw.get("cover"):
        lines.append(f"- **封面**：{raw['cover']}")
    if raw.get("stats"):
        stats = raw["stats"]
        stats_str = " · ".join([f"{k}: {v}" for k, v in stats.items() if v is not None])
        if stats_str:
            lines.append(f"- **数据**：{stats_str}")

    lines.extend([
        "",
        "---",
        "",
        "> 💡 建议直接观看原视频以获取完整内容。",
    ])

    content = "\n".join(lines)
    return {"content": content, "md_path": ""}


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

MAX_WORKERS = 5
_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
# 细粒度进度步骤定义
STEPS = [
    ("extract_meta", "提取元数据"),
    ("summarize", "AI 总结"),
    ("import", "生成文档"),
]

_tasks: dict[str, dict] = {}  # task_id → {status, module_id, input, result, doc_id, title, error, created_at, steps, current_step}
_lock = threading.Lock()


# ====== Task Queue Persistence (survive backend restart) ======

def _task_to_db(task: dict):
    """将内存中的任务状态写入 SQLite task_queue 表（upsert）。"""
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO task_queue (task_id, module_id, module_name, input_text, input_hash,
                status, progress, error, result_doc_id, result_title,
                steps_json, current_step, api_key_error, api_key_error_msg,
                replace_doc_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(task_id) DO UPDATE SET
                status=excluded.status, progress=excluded.progress,
                error=excluded.error, result_doc_id=excluded.result_doc_id,
                result_title=excluded.result_title, steps_json=excluded.steps_json,
                current_step=excluded.current_step, api_key_error=excluded.api_key_error,
                api_key_error_msg=excluded.api_key_error_msg,
                replace_doc_id=excluded.replace_doc_id, updated_at=datetime('now')
        """, (
            task.get("task_id", ""),
            task.get("module_id", ""),
            task.get("module_name", ""),
            task.get("input", "")[:500],
            hashlib.sha256(task.get("input", "").encode("utf-8", errors="replace")).hexdigest(),
            task.get("status", "pending"),
            task.get("progress", ""),
            task.get("error", ""),
            (task.get("result") or {}).get("doc_id"),
            (task.get("result") or {}).get("title", ""),
            json.dumps(task.get("steps", []), ensure_ascii=False),
            task.get("current_step", ""),
            1 if task.get("api_key_error") else 0,
            task.get("api_key_error_msg", ""),
            task.get("replace_doc_id"),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[task_queue] 持久化任务 {task.get('task_id', '?')} 失败: {e}")


def _load_pending_tasks_from_db() -> list[dict]:
    """启动时从 SQLite 恢复未完成的任务（pending/extracting/summarizing/importing）。"""
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM task_queue WHERE status IN ('pending','extracting','summarizing','importing') "
            "ORDER BY created_at"
        ).fetchall()
        conn.close()
        tasks = []
        for r in rows:
            tasks.append({
                "task_id": r["task_id"],
                "module_id": r["module_id"],
                "module_name": r["module_name"],
                "input": r["input_text"],
                "status": "pending",  # 重启后全部重置为 pending 重新执行
                "progress": "排队中…",
                "error": "",
                "result": {"doc_id": r["result_doc_id"], "title": r["result_title"]} if r["result_doc_id"] else None,
                "created_at": r["created_at"],
                "steps": json.loads(r["steps_json"]) if r["steps_json"] else [],
                "current_step": None,
                "api_key_error": bool(r["api_key_error"]),
                "api_key_error_msg": r["api_key_error_msg"],
                "replace_doc_id": r["replace_doc_id"],
            })
        return tasks
    except Exception as e:
        print(f"[task_queue] 加载待恢复任务失败: {e}")
        return []


def _cleanup_done_tasks_from_db():
    """清理数据库中已完成/失败的任务（保留最近 200 条）。"""
    try:
        conn = get_db()
        conn.execute("DELETE FROM task_queue WHERE status IN ('done','error') AND created_at < datetime('now', '-7 days')")
        # 保留最近 200 条
        conn.execute("""
            DELETE FROM task_queue WHERE id NOT IN (
                SELECT id FROM task_queue ORDER BY created_at DESC LIMIT 200
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[task_queue] 清理旧任务失败: {e}")


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
    """Worker: process one task and store result.

    关键改进：
    1. 提取元数据后先占位入库（防止 AI 总结后崩溃丢失配额）
    2. AI 总结完成后更新占位文档
    3. 输入哈希早期去重（避免重复消耗配额）
    """
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

    # 早期去重：基于输入链接的哈希检查是否已处理过
    input_hash = hashlib.sha256(user_input.encode("utf-8", errors="replace")).hexdigest()
    placeholder_doc_id = None  # 占位文档 ID，用于后续更新

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

        # 检查 API Key 无效错误
        if _check_api_key_error(raw):
            with _lock:
                _tasks[task_id]["api_key_error"] = True
                _tasks[task_id]["api_key_error_msg"] = raw.get("asr_error", "API Key 无效")

        _update_step(task_id, "extract_meta", "done")

        # === 占位入库：在昂贵的 AI 总结之前先写入占位记录 ===
        # 这样即使后台在 AI 总结期间重启，也能通过孤儿恢复找回 .md 文件
        placeholder_title = raw.get("title", "") or f"解析中…（{module['name']}）"
        placeholder_content = json.dumps({
            "_placeholder": True,
            "task_id": task_id,
            "input": user_input,
            "raw_meta": {k: v for k, v in raw.items() if k not in ("asr_text",)},
        }, ensure_ascii=False)
        placeholder_hash = hashlib.sha256(placeholder_content.encode("utf-8", errors="replace")).hexdigest()

        try:
            conn = get_db()
            # 检查是否已有相同 input_hash 的占位文档（可能上次崩溃留下的）
            existing = conn.execute(
                "SELECT id FROM documents WHERE content_hash = ? AND source = ? LIMIT 1",
                (placeholder_hash, module["source_tag"]),
            ).fetchone()
            if not existing:
                cur = conn.execute(
                    "INSERT INTO documents (title, content, content_type, source, char_count, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (placeholder_title[:200], placeholder_content, "text", module["source_tag"],
                     len(placeholder_content), placeholder_hash),
                )
                placeholder_doc_id = cur.lastrowid
                conn.commit()
            else:
                placeholder_doc_id = existing["id"]
            conn.close()
            with _lock:
                _tasks[task_id]["placeholder_doc_id"] = placeholder_doc_id
        except Exception as e:
            print(f"[task] 占位入库失败（非致命）: {e}")

        # Step 2: Summarize (includes ASR inside extract for now)
        _update_step(task_id, "summarize", "running", "正在 AI 深度分析…")

        # ASR 致命失败时降级为元数据卡片
        if engine == "deep" and _should_fallback_to_meta_card(raw):
            result = _build_meta_card(raw, user_input)
            _update_step(task_id, "summarize", "done")
        else:
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

        # Step 3: Import / Update placeholder
        _update_step(task_id, "import", "running", "正在入库 + 向量化…")
        content = result["content"]
        md_path = result.get("md_path", "")

        title = os.path.basename(md_path).replace(".md", "") if md_path else ""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # 空标题 fallback
        if not title:
            platform = raw.get("platform", "未知")
            vid = raw.get("video_id") or raw.get("bvid") or raw.get("note_id") or ""
            title = f"未知标题（{platform} {vid}）" if vid else f"未知标题（{platform}）"

        # 计算内容哈希，用于去重
        content_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

        conn = get_db()
        # 入库前查重：同一来源 + 相同内容视为重复
        dup = conn.execute(
            "SELECT id FROM documents WHERE source = ? AND content_hash = ? AND id != ? LIMIT 1",
            (module["source_tag"], content_hash, placeholder_doc_id or -1),
        ).fetchone()
        if dup:
            doc_id = dup["id"]
            # 删除占位文档（已存在更早的完整记录）
            if placeholder_doc_id:
                try:
                    conn.execute("DELETE FROM documents WHERE id = ?", (placeholder_doc_id,))
                    conn.commit()
                except Exception:
                    pass
            conn.close()
            # 删除被替换的旧文档（如果是重新解析任务）
            _delete_replaced_doc(task_id)
            with _lock:
                _tasks[task_id]["status"] = "done"
                _tasks[task_id]["progress"] = "完成（已存在）"
                _tasks[task_id]["result"] = {"doc_id": doc_id, "title": title}
            _update_step(task_id, "import", "done")
            _task_to_db(_tasks[task_id])
            return

        if placeholder_doc_id:
            # 更新占位文档为完整内容
            conn.execute(
                "UPDATE documents SET title = ?, content = ?, char_count = ?, content_hash = ? WHERE id = ?",
                (title[:200], content, len(content), content_hash, placeholder_doc_id),
            )
            conn.commit()
            doc_id = placeholder_doc_id
        else:
            cur = conn.execute(
                "INSERT INTO documents (title, content, content_type, source, char_count, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (title, content, "text", module["source_tag"], len(content), content_hash),
            )
            doc_id = cur.lastrowid
            conn.commit()

        try:
            chunks = chunk_text(content)
            vs = get_vector_store()
            # 如果之前占位文档可能已有向量记录，先清理
            try:
                existing = vs.collection.get(where={"doc_id": doc_id})
                if existing and existing["ids"]:
                    vs.collection.delete(ids=existing["ids"])
            except Exception:
                pass
            vs.add_document(doc_id, title, chunks)
            conn.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
            conn.commit()
        except Exception as e:
            print(f"向量化失败 (文档 {doc_id}): {e}")

        conn.close()

        # 删除被替换的旧文档（如果是重新解析任务）
        _delete_replaced_doc(task_id)

        with _lock:
            _tasks[task_id]["status"] = "done"
            _tasks[task_id]["progress"] = "完成"
            _tasks[task_id]["result"] = {"doc_id": doc_id, "title": title}
        _update_step(task_id, "import", "done")
        _task_to_db(_tasks[task_id])

    except Exception as e:
        error_msg = str(e)
        with _lock:
            _tasks[task_id]["status"] = "error"
            _tasks[task_id]["progress"] = "失败"
            _tasks[task_id]["error"] = error_msg
        # 标记占位文档为错误状态（保留以便排查）
        if placeholder_doc_id:
            try:
                conn = get_db()
                conn.execute(
                    "UPDATE documents SET title = ? WHERE id = ?",
                    (f"[解析失败] {raw.get('title', '未知')}"[:200], placeholder_doc_id),
                )
                conn.commit()
                conn.close()
            except Exception:
                pass
        # 标记当前步骤为失败
        with _lock:
            t = _tasks.get(task_id)
            if t and t.get("current_step"):
                for s in t.get("steps", []):
                    if s["key"] == t["current_step"] and s["status"] == "running":
                        s["status"] = "error"
        _task_to_db(_tasks[task_id])


def _check_api_key_error(raw: dict) -> bool:
    """检查提取结果中是否包含 API Key 无效错误。"""
    return raw.get("asr_api_key_invalid", False) or \
           "invalid api-key" in raw.get("asr_error", "").lower()


def _check_existing_by_input_hash(input_hash: str, module_id: str) -> dict | None:
    """检查是否已有相同 input_hash 的已完成文档或任务，如有则返回 {doc_id, title}。

    检查顺序：
    1. task_queue 中 status='done' 且有 result_doc_id
    2. documents 中匹配 source 且 placeholder JSON 包含相同 input
    """
    module = MODULES.get(module_id)
    if not module:
        return None
    try:
        conn = get_db()
        # 1. 检查 task_queue 中已完成的记录
        row = conn.execute(
            "SELECT result_doc_id, result_title FROM task_queue WHERE input_hash = ? AND status = 'done' AND result_doc_id IS NOT NULL LIMIT 1",
            (input_hash,),
        ).fetchone()
        if row and row["result_doc_id"]:
            conn.close()
            return {"doc_id": row["result_doc_id"], "title": row["result_title"]}

        # 2. 检查 documents 中是否存在（通过 placeholder JSON 中的 input 字段或 content_hash）
        # 搜索该 source 下最近 200 条，检查 placeholder 内容
        docs = conn.execute(
            "SELECT id, title, content FROM documents WHERE source = ? ORDER BY created_at DESC LIMIT 200",
            (module["source_tag"],),
        ).fetchall()
        conn.close()

        for doc in docs:
            try:
                content = doc["content"]
                if content and '"input":"' in content[:500]:
                    data = json.loads(content)
                    if data.get("_placeholder") or data.get("input"):
                        doc_input = data.get("input", "")
                        doc_hash = hashlib.sha256(doc_input.encode("utf-8", errors="replace")).hexdigest()
                        if doc_hash == input_hash:
                            return {"doc_id": doc["id"], "title": doc["title"]}
            except (json.JSONDecodeError, KeyError):
                continue
    except Exception:
        pass
    return None


# ====== 孤儿文件恢复（启动时自动导入） ======

def recover_orphan_summaries() -> dict:
    """启动时扫描摘要目录，把有 .md 文件但未入库的自动导入。

    扫描 douyin-summaries/, bilibili-summaries/, xiaohongshu-summaries/
    对于每个 .md 文件，检查是否已有对应的 DB 记录（通过 title 匹配），
    如果没有则导入并创建文档记录。

    Returns:
        {"recovered": N, "details": [...]}
    """
    recovered = []
    source_map = {
        "douyin-summaries": "douyin-summary",
        "bilibili-summaries": "bilibili-summary",
        "xiaohongshu-summaries": "xiaohongshu-summary",
    }

    for dir_name, source_tag in source_map.items():
        output_dir = os.path.join(PROJECT_DIR, dir_name)
        if not os.path.isdir(output_dir):
            continue

        for fname in os.listdir(output_dir):
            if not fname.endswith(".md"):
                continue
            fp = os.path.join(output_dir, fname)

            try:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()

                if not content or len(content) < 50:
                    continue

                # 提取标题
                title = fname[:-3]  # 默认用文件名
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("# ") and not line.startswith("## "):
                        title = line[2:].strip()
                        break

                # 计算内容哈希
                content_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

                conn = get_db()
                # 检查是否已入库（通过 content_hash 或 title 匹配）
                existing = conn.execute(
                    "SELECT id FROM documents WHERE (content_hash = ?) OR (title = ? AND source = ?) LIMIT 1",
                    (content_hash, title, source_tag),
                ).fetchone()

                if existing:
                    conn.close()
                    continue  # 已入库，跳过

                # 检查是否为占位文档（需要被替换）
                placeholder = conn.execute(
                    "SELECT id FROM documents WHERE source = ? AND content LIKE '%\"_placeholder\": true%' AND title LIKE ? LIMIT 1",
                    (source_tag, f"%{title[:50]}%"),
                ).fetchone()

                if placeholder:
                    # 更新占位文档
                    conn.execute(
                        "UPDATE documents SET title = ?, content = ?, char_count = ?, content_hash = ? WHERE id = ?",
                        (title[:200], content, len(content), content_hash, placeholder["id"]),
                    )
                    doc_id = placeholder["id"]
                else:
                    # 新建文档
                    cur = conn.execute(
                        "INSERT INTO documents (title, content, content_type, source, char_count, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
                        (title[:200], content, "text", source_tag, len(content), content_hash),
                    )
                    doc_id = cur.lastrowid

                conn.commit()

                # 向量化
                try:
                    chunks = chunk_text(content)
                    vs = get_vector_store()
                    vs.add_document(doc_id, title, chunks)
                    conn.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
                    conn.commit()
                except Exception as e:
                    print(f"[orphan_recovery] 向量化失败 (doc {doc_id}): {e}")

                conn.close()
                recovered.append({"doc_id": doc_id, "title": title[:60], "source": source_tag, "file": fname})
                print(f"[orphan_recovery] 已恢复: {fname} → doc #{doc_id}")

            except Exception as e:
                print(f"[orphan_recovery] 恢复失败 {fname}: {e}")

    return {"recovered": len(recovered), "details": recovered}


def recover_tasks_on_startup():
    """启动时恢复未完成的任务 + 孤儿 .md 文件。

    在 main.py 的 lifespan 中调用。
    """
    # 1. 清理数据库中过期任务
    _cleanup_done_tasks_from_db()

    # 2. 恢复孤儿 .md 文件（AI 总结已完成但未入库的）
    orphan_result = recover_orphan_summaries()
    if orphan_result["recovered"] > 0:
        print(f"[startup] 孤儿文件恢复: {orphan_result['recovered']} 个文档已导入")

    # 3. 从 DB 恢复未完成的任务
    pending_tasks = _load_pending_tasks_from_db()
    if pending_tasks:
        recovered_count = 0
        for task in pending_tasks:
            task_id = task["task_id"]
            # 检查是否已有对应的孤儿文档被恢复了（避免重复处理）
            input_hash = hashlib.sha256(task["input"].encode("utf-8", errors="replace")).hexdigest()
            existing = _check_existing_by_input_hash(input_hash, task["module_id"])
            if existing:
                with _lock:
                    task["status"] = "done"
                    task["result"] = existing
                    task["progress"] = "完成（启动恢复）"
                    _tasks[task_id] = task
                _task_to_db(task)
                recovered_count += 1
                continue

            with _lock:
                _tasks[task_id] = task
            _executor.submit(_process_single_task, task_id)
            recovered_count += 1

        print(f"[startup] 任务队列恢复: {recovered_count} 个任务已重新提交（共 {len(pending_tasks)} 个待恢复）")
    else:
        print("[startup] 任务队列: 无待恢复任务")

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

    # 早期去重：检查是否已有相同输入的任务（已完成或进行中）
    input_hash = hashlib.sha256(user_input.encode("utf-8", errors="replace")).hexdigest()
    existing = _check_existing_by_input_hash(input_hash, module_id)
    if existing:
        return {"status": "done", "task_id": "cached", **existing}

    task_id = str(uuid.uuid4())[:8]
    task = {
        "task_id": task_id, "status": "pending", "module_id": module_id,
        "module_name": MODULES[module_id]["name"],
        "input": user_input, "progress": "排队中…",
        "created_at": datetime.now().isoformat(),
    }
    with _lock:
        _tasks[task_id] = task
    _task_to_db(task)

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

    skipped = 0
    tasks_created = []
    for inp in inputs:
        if len(inp) > 10000:
            continue
        # 跨批次去重：检查是否已有相同输入的已完成任务
        input_hash = hashlib.sha256(inp.encode("utf-8", errors="replace")).hexdigest()
        existing = _check_existing_by_input_hash(input_hash, module_id)
        if existing:
            skipped += 1
            continue

        task_id = str(uuid.uuid4())[:8]
        task = {
            "task_id": task_id, "status": "pending", "module_id": module_id,
            "module_name": MODULES[module_id]["name"],
            "input": inp[:500], "progress": "排队中…",
            "created_at": datetime.now().isoformat(),
        }
        with _lock:
            _tasks[task_id] = task
        _task_to_db(task)
        _executor.submit(_process_single_task, task_id)
        tasks_created.append(task_id)

    msg = f"已提交 {len(tasks_created)} 个任务"
    if skipped:
        msg += f"，跳过 {skipped} 个重复链接"

    return {
        "status": "queued",
        "count": len(tasks_created),
        "skipped": skipped,
        "task_ids": tasks_created,
        "message": msg + f"，最多 {MAX_WORKERS} 个并行处理",
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
            "api_key_error": t.get("api_key_error", False),
            "api_key_error_msg": t.get("api_key_error_msg", ""),
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


def _check_api_key_valid() -> tuple[bool, str]:
    """检查 DASHSCOPE_API_KEY 是否有效。返回 (是否有效, 错误信息)"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return False, "DASHSCOPE_API_KEY 未配置"
    try:
        # 用 dashscope 的 API 验证 Key 是否有效
        # 使用一个无效的音频 URL 来触发验证，但捕获 Key 相关的错误
        import dashscope
        response = dashscope.MultiModalConversation.call(
            api_key=api_key,
            model=DEFAULT_ASR_MODEL,
            messages=[
                {"role": "system", "content": [{"text": ""}]},
                {"role": "user", "content": [{"audio": "https://example.com/test.mp3"}]},
            ],
            result_format="message",
        )
        # 如果返回 200，说明 Key 有效
        if response.status_code == 200:
            return True, ""
        # 检查错误信息是否包含 API Key 无效的关键词
        msg = str(response.message).lower() if hasattr(response, 'message') else ""
        if any(k in msg for k in ["invalid api-key", "invalidapikey", "api key invalid", "unauthorized"]):
            return False, f"API Key 无效"
        # 其他错误（如音频下载失败），Key 本身可能是有效的
        return True, ""
    except Exception as e:
        error_str = str(e).lower()
        if any(k in error_str for k in ["invalid api-key", "invalidapikey", "api key invalid", "unauthorized", "access denied"]):
            return False, f"API Key 无效"
        # 网络错误、音频下载失败等，不确定 Key 是否有效，先认为有效让用户尝试
        return True, ""


@router.post("/automation/queue/retry/{task_id}")
def retry_task(task_id: str):
    """
    重新执行失败的任务（主要用于 API Key 更新后重试）。
    如果任务是 API Key 错误导致的失败，会先检查 Key 是否已更新。
    """
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return {"error": "任务不存在"}
        if task["status"] not in ("error",):
            return {"error": "只有失败的任务可以重试"}

    # 如果之前是 API Key 错误，先检查 Key 是否已更新
    if task.get("api_key_error"):
        is_valid, error_msg = _check_api_key_valid()
        if not is_valid:
            return {
                "error": f"API Key 仍然无效，无法重试。请先更新 .env 中的 DASHSCOPE_API_KEY 后重试。\n当前错误: {error_msg}",
                "api_key_invalid": True,
            }

    with _lock:
        # 重置任务状态
        task["status"] = "pending"
        task["progress"] = "排队中…"
        task["error"] = ""
        task["api_key_error"] = False
        task["api_key_error_msg"] = ""
        task["steps"] = []
        task["current_step"] = None

    # 重新提交执行
    _task_to_db(task)
    _executor.submit(_process_single_task, task_id)

    return {"status": "queued", "task_id": task_id, "message": "任务已重新提交"}


@router.delete("/automation/queue/clear")
def clear_completed():
    """清除已完成和失败的任务（内存 + DB）。"""
    with _lock:
        to_remove = [tid for tid, t in _tasks.items() if t["status"] in ("done", "error")]
        for tid in to_remove:
            del _tasks[tid]

    # 同步清理 DB
    if to_remove:
        try:
            conn = get_db()
            placeholders = ",".join("?" for _ in to_remove)
            conn.execute(f"DELETE FROM task_queue WHERE task_id IN ({placeholders})", to_remove)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[task_queue] 清理 DB 任务失败: {e}")

    return {"cleared": len(to_remove)}


# ====== 重解析 & 清理 ======

# 平台链接提取正则映射
_REPARSE_LINK_PATTERNS = {
    "douyin-summary": [
        r'https?://v\.douyin\.com/[^\s)\]]+',
        r'https?://www\.douyin\.com/[^\s)\]]+',
    ],
    "bilibili-summary": [
        r'https?://b23\.tv/[^\s)\]]+',
        r'https?://www\.bilibili\.com/video/[^\s)\]]+',
    ],
    "xiaohongshu-summary": [
        r'https?://xhslink\.com/[^\s)\]]+',
        r'https?://www\.xiaohongshu\.com/explore/[^\s)\]]+',
    ],
}

_REPARSE_MODULE_MAP = {
    "douyin-summary": ("douyin-summary", "抖音摘要（重新识别）"),
    "bilibili-summary": ("bilibili-summary", "B站解析（重新识别）"),
    "xiaohongshu-summary": ("xiaohongshu-summary", "小红书解析（重新识别）"),
}


@router.post("/automation/reparse/{doc_id}")
def reparse_document(doc_id: int):
    """
    重新解析失败的摘要文档（支持抖音/B站/小红书）。
    提取原始链接 → 删除旧文档 → 重新提交自动化任务。
    """
    import re

    try:
        conn = get_db()
        doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not doc:
            conn.close()
            return {"error": "文档不存在"}

        content = doc["content"] or ""
        title = doc["title"] or ""
        source = doc["source"] if "source" in doc.keys() else ""

        # 根据 source 确定平台和提取规则
        patterns = _REPARSE_LINK_PATTERNS.get(source, [])
        module_info = _REPARSE_MODULE_MAP.get(source)

        if not patterns or not module_info:
            conn.close()
            return {"error": f"不支持的文档类型: {source}，无法重新识别"}

        # 提取原始链接
        original_link = None
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                original_link = match.group(0).rstrip('.。，,')
                break

        if not original_link:
            conn.close()
            return {"error": "文档中未找到原始链接，无法重新识别"}

        conn.close()

        # 提交新任务（携带旧文档 ID，等新文档创建成功后再删除旧文档）
        module_id, module_name = module_info
        task_id = str(uuid.uuid4())[:8]
        task = {
            "task_id": task_id, "status": "pending", "module_id": module_id,
            "module_name": module_name,
            "input": original_link, "progress": "排队中…",
            "created_at": datetime.now().isoformat(),
            "replace_doc_id": doc_id,  # 新任务完成后替换此文档
        }
        with _lock:
            _tasks[task_id] = task
        _task_to_db(task)
        _executor.submit(_process_single_task, task_id)

        return {
            "status": "queued",
            "task_id": task_id,
            "message": f"已重新提交识别任务（原文档：{title}），处理中…",
            "original_link": original_link,
        }
    except Exception as e:
        import traceback
        print(f"[ERROR] reparse_document 失败 (doc_id={doc_id}): {e}")
        traceback.print_exc()
        return {"error": f"内部服务器错误: {str(e)}"}


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


def _delete_replaced_doc(task_id: str):
    """如果是重新解析任务，删除被替换的旧文档。"""
    with _lock:
        old_doc_id = _tasks.get(task_id, {}).get("replace_doc_id")
    if old_doc_id:
        try:
            _delete_document_full(old_doc_id)
        except Exception as e:
            print(f"[WARN] 删除被替换旧文档失败 (doc_id={old_doc_id}): {e}")


@router.post("/automation/extract-webpage")
def extract_webpage(payload: dict):
    """
    通用网页正文提取 — 使用 Jina Reader API 作为首选，fallback 到简单抓取。
    输入: {"url": "https://example.com/article"}
    输出: {"title": "...", "content": "...", "url": "..."}
    """
    url = payload.get("url", "").strip()
    if not url:
        return {"error": "缺少 url 参数"}

    # 确保 URL 有协议前缀
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    # 1. 尝试 Jina Reader API
    try:
        jina_url = f"https://r.jina.ai/http://{url.replace('https://', '').replace('http://', '')}"
        resp = requests.get(jina_url, timeout=30, headers={"User-Agent": "Study-Hub/1.0"})
        if resp.status_code == 200:
            text = resp.text.strip()
            # Jina Reader 返回格式：第一行是标题，后面是正文
            lines = text.split("\n", 1)
            title = lines[0].strip() if lines else ""
            content = lines[1].strip() if len(lines) > 1 else text
            if len(content) > 100:
                return {
                    "title": title or "未命名页面",
                    "content": content,
                    "url": url,
                    "source": "jina_reader",
                }
    except Exception as e:
        print(f"[WARN] Jina Reader 失败: {e}")

    # 2. Fallback: 直接抓取
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code == 200:
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.texts = []
                    self.skip = 0
                    self.skip_tags = {"script", "style", "nav", "header", "footer", "aside"}

                def handle_starttag(self, tag, attrs):
                    if tag in self.skip_tags:
                        self.skip += 1

                def handle_endtag(self, tag):
                    if tag in self.skip_tags:
                        self.skip -= 1

                def handle_data(self, data):
                    if self.skip <= 0:
                        self.texts.append(data)

            extractor = TextExtractor()
            extractor.feed(resp.text)
            content = "\n".join(extractor.texts).strip()
            # 提取 title
            title_match = re.search(r"<title[^>]*>(.*?)</title>", resp.text, re.S)
            title = title_match.group(1).strip() if title_match else "未命名页面"
            return {
                "title": title,
                "content": content,
                "url": url,
                "source": "direct_fetch",
            }
    except Exception as e:
        print(f"[WARN] 直接抓取失败: {e}")

    return {"error": "网页提取失败，请检查 URL 是否可访问"}


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
    except Exception as e:
        print(f"[WARN] 删除向量库文档失败 (doc_id={doc_id}): {e}")
        pass
