#!/usr/bin/env python3
"""
社媒平台解析器 —— B站 / 小红书 / 通用ASR

提供给 study-hub MCP Server 调用，不依赖 FastMCP。
"""

import os, re, json, requests, tempfile
from pathlib import Path
from typing import Optional
import dashscope


HEADERS_MOBILE = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
}

HEADERS_BILIBILI = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
}

HEADERS_XHS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Referer': 'https://www.xiaohongshu.com',
}

DEFAULT_ASR_MODEL = "qwen3-asr-flash"


# ====== 通用 ASR ======

class QwenASR:
    """Qwen-3-ASR-Flash 语音识别器"""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_ASR_MODEL):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY")
        self.model = model
        dashscope.api_key = self.api_key

    def recognize(self, audio_input, context=None, language=None, enable_lid=True, enable_itn=False) -> dict:
        try:
            if isinstance(audio_input, Path):
                audio_input = str(audio_input)
            if os.path.exists(str(audio_input)):
                audio_input = f"file://{os.path.abspath(str(audio_input))}"

            messages = [
                {"role": "system", "content": [{"text": context or ""}]},
                {"role": "user", "content": [{"audio": audio_input}]},
            ]
            asr_options = {"enable_lid": enable_lid, "enable_itn": enable_itn}
            if language:
                asr_options["language"] = language

            response = dashscope.MultiModalConversation.call(
                api_key=self.api_key, model=self.model,
                messages=messages, result_format="message", asr_options=asr_options,
            )
            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.message}")

            result = {"success": True, "text": "", "language": None,
                      "usage": response.usage, "request_id": response.request_id}
            if response.output and response.output.choices:
                choice = response.output.choices[0]
                if choice.message and choice.message.content:
                    result["text"] = choice.message.content[0].get("text", "")
                try:
                    annotations = choice.message.annotations
                    if annotations:
                        for a in annotations:
                            if a.get("type") == "audio_info":
                                result["language"] = a.get("language")
                except (KeyError, AttributeError):
                    pass
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "text": "", "language": None}


# ====== B站解析器 ======

class BilibiliParser:
    """B站视频解析器（无需登录）"""

    @staticmethod
    def extract_bvid(share_text: str) -> str:
        bv = re.search(r'BV[a-zA-Z0-9]{10}', share_text)
        if bv:
            return bv.group(0)

        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
        if not urls:
            raise ValueError("未找到有效的B站链接或BV号")

        url = urls[0]
        if 'b23.tv' in url:
            try:
                r = requests.get(url, headers=HEADERS_BILIBILI, allow_redirects=True, timeout=15)
                url = r.url
            except Exception:
                try:
                    r = requests.get(url, headers=HEADERS_BILIBILI, allow_redirects=False, timeout=10)
                    if r.status_code in (301, 302):
                        url = r.headers.get('Location', url)
                except Exception:
                    pass

        bv = re.search(r'BV[a-zA-Z0-9]{10}', url)
        if bv:
            return bv.group(0)
        raise ValueError("无法提取BV号，请提供完整的B站视频链接或BV号")

    @staticmethod
    def get_video_info(share_text: str) -> dict:
        bvid = BilibiliParser.extract_bvid(share_text)
        resp = requests.get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
                           headers=HEADERS_BILIBILI, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ValueError(f"B站API错误: {data.get('message', '未知')}")

        v = data["data"]
        pages = v.get("pages", [])
        return {
            "bvid": bvid, "aid": v.get("aid", 0),
            "title": v.get("title", ""), "description": v.get("desc", ""),
            "cover": v.get("pic", ""), "duration": v.get("duration", 0),
            "owner": {"name": v.get("owner", {}).get("name", ""),
                      "mid": v.get("owner", {}).get("mid", 0),
                      "face": v.get("owner", {}).get("face", "")},
            "stat": {"view": v.get("stat", {}).get("view", 0),
                     "danmaku": v.get("stat", {}).get("danmaku", 0),
                     "reply": v.get("stat", {}).get("reply", 0),
                     "favorite": v.get("stat", {}).get("favorite", 0),
                     "coin": v.get("stat", {}).get("coin", 0),
                     "share": v.get("stat", {}).get("share", 0),
                     "like": v.get("stat", {}).get("like", 0)},
            "cid_list": [{"page": p.get("page",1), "part": p.get("part",""), "cid": p.get("cid",0)} for p in pages],
            "tname": v.get("tname", ""), "pubdate": v.get("pubdate", 0),
        }

    @staticmethod
    def get_play_url(bvid: str, cid: int, quality: int = 80) -> dict:
        url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&fnval={quality}&fnver=0&fourk=1"
        resp = requests.get(url, headers=HEADERS_BILIBILI, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ValueError(f"获取播放URL失败: {data.get('message', '未知')}")

        pd = data["data"]
        result = {"quality": pd.get("quality", 0), "format": pd.get("format", ""),
                  "timelength": pd.get("timelength", 0)}
        dash = pd.get("dash", {})
        if dash:
            result["dash"] = {"duration": dash.get("duration", 0), "video": [], "audio": []}
            for v in dash.get("video", []):
                result["dash"]["video"].append({
                    "id": v.get("id"), "base_url": v.get("base_url", ""),
                    "backup_url": v.get("backup_url", []),
                    "width": v.get("width"), "height": v.get("height"),
                    "frame_rate": v.get("frame_rate"), "codecs": v.get("codecs"),
                    "bandwidth": v.get("bandwidth"),
                })
            for a in dash.get("audio", []):
                result["dash"]["audio"].append({
                    "id": a.get("id"), "base_url": a.get("base_url", ""),
                    "backup_url": a.get("backup_url", []),
                    "codecs": a.get("codecs"), "bandwidth": a.get("bandwidth"),
                })
        durl = pd.get("durl", [])
        if durl:
            result["durl"] = [{"url": d.get("url", ""), "backup_url": d.get("backup_url", []),
                               "size": d.get("size"), "length": d.get("length")} for d in durl]
        return result

    @staticmethod
    def get_audio_url(share_text: str, cid: Optional[int] = None) -> tuple:
        """返回 (audio_url, video_info_dict)"""
        info = BilibiliParser.get_video_info(share_text)
        if cid is None:
            cids = info.get("cid_list", [])
            if cids:
                cid = cids[0]["cid"]
            else:
                resp = requests.get(f"https://api.bilibili.com/x/player/pagelist?bvid={info['bvid']}",
                                   headers=HEADERS_BILIBILI, timeout=10)
                pd = resp.json()
                if pd.get("code") == 0 and pd.get("data"):
                    cid = pd["data"][0]["cid"]
                else:
                    raise ValueError("无法获取cid")

        play = BilibiliParser.get_play_url(info["bvid"], cid)
        dash = play.get("dash", {})
        if dash and dash.get("audio"):
            best = max(dash["audio"], key=lambda a: a.get("bandwidth", 0))
            audio_url = best.get("base_url") or best.get("backup_url", [""])[0]
            if audio_url:
                return audio_url, info

        durl = play.get("durl", [])
        if durl:
            video_url = durl[0].get("url") or durl[0].get("backup_url", [""])[0]
            if video_url:
                return video_url, info

        raise ValueError("无法获取音频/视频流URL")


# ====== 小红书解析器 ======

class XiaohongshuParser:
    """小红书笔记解析器"""

    @staticmethod
    def extract_note_id(share_text: str) -> str:
        note = re.search(r'/explore/([a-zA-Z0-9]+)', share_text)
        if note:
            return note.group(1)

        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
        if not urls:
            raise ValueError("未找到有效的小红书链接")

        url = urls[0]
        if 'xhslink.com' in url:
            r = requests.get(url, headers=HEADERS_XHS, allow_redirects=True, timeout=15)
            note = re.search(r'/explore/([a-zA-Z0-9]+)', r.url)
            if note:
                return note.group(1)
            note = re.search(r'/explore/([a-zA-Z0-9]+)', r.text)
            if note:
                return note.group(1)
            raise ValueError("无法解析小红书短链接")

        note = re.search(r'/explore/([a-zA-Z0-9]+)', url)
        if note:
            return note.group(1)

        r = requests.get(url, headers=HEADERS_XHS, timeout=15)
        note = re.search(r'/explore/([a-zA-Z0-9]+)', r.url)
        if note:
            return note.group(1)
        raise ValueError("无法提取笔记ID")

    @staticmethod
    def get_note_info(share_text: str) -> dict:
        note_id = XiaohongshuParser.extract_note_id(share_text)
        headers = {**HEADERS_XHS, 'Accept': 'text/html,application/xhtml+xml',
                   'Accept-Language': 'zh-CN,zh;q=0.9', 'Cache-Control': 'no-cache'}
        resp = requests.get(f"https://www.xiaohongshu.com/explore/{note_id}",
                           headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        note_data = {}

        # 从 __INITIAL_STATE__ 提取
        m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
        if m:
            try:
                state = json.loads(m.group(1))
                detail = state.get("note", {}).get("noteDetailMap", {}).get(note_id, {})
                if detail:
                    note = detail.get("note", {})
                    note_data = {
                        "note_id": detail.get("noteId", note_id),
                        "title": note.get("title", ""),
                        "description": note.get("desc", ""),
                        "type": note.get("type", ""),
                        "cover": "", "images": [], "video_url": "",
                        "author": {
                            "name": note.get("user", {}).get("nickname", ""),
                            "id": note.get("user", {}).get("userId", ""),
                            "avatar": note.get("user", {}).get("avatar", ""),
                        },
                        "stat": {
                            "liked": note.get("interactInfo", {}).get("likedCount", 0),
                            "collected": note.get("interactInfo", {}).get("collectedCount", 0),
                            "comment": note.get("interactInfo", {}).get("commentCount", 0),
                            "shared": note.get("interactInfo", {}).get("shareCount", 0),
                        },
                        "tags": [t.get("name", "") for t in note.get("tagList", [])],
                        "create_time": note.get("time", 0),
                        "ip_location": note.get("ipLocation", ""),
                    }
                    for img in note.get("imageList", []):
                        url = img.get("urlDefault") or img.get("url") or img.get("infoList", [{}])[0].get("url", "")
                        if url and not url.startswith("http"):
                            url = "https:" + url
                        if url:
                            note_data["images"].append(url)
                            if not note_data["cover"]:
                                note_data["cover"] = url
                    video = note.get("video", {})
                    if video:
                        media = video.get("media", {})
                        stream = media.get("stream", {})
                        h264 = stream.get("h264", [{}])[0].get("masterUrl", "")
                        h265 = stream.get("h265", [{}])[0].get("masterUrl", "")
                        note_data["video_url"] = h264 or h265
                        note_data["video_duration"] = media.get("videoDuration", 0)
                        cover = video.get("image", {}).get("firstFrameFileid", "")
                        if cover and not cover.startswith("http"):
                            cover = "https:" + cover
                        if cover:
                            note_data["cover"] = cover
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # fallback: meta 标签
        if not note_data:
            og = lambda p: (lambda m: m.group(1) if m else "")(re.search(f'<meta[^>]*name="og:{p}"[^>]*content="([^"]*)"', html))
            note_data = {
                "note_id": note_id,
                "title": og("title"), "description": og("description"),
                "cover": og("image"), "images": [],
                "video_url": og("video"), "author": {}, "stat": {}, "tags": [],
            }

        if not note_data:
            raise ValueError("无法解析笔记信息，可能需要登录Cookie")
        return note_data

    @staticmethod
    def get_video_url(share_text: str) -> tuple:
        """返回 (video_url, note_info_dict)"""
        info = XiaohongshuParser.get_note_info(share_text)
        video_url = info.get("video_url", "")
        if not video_url:
            raise ValueError("该笔记没有视频内容")
        return video_url, info
