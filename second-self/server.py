"""Second Self 本地服务器 — 零依赖，Python 3 内置库即可运行

HTTP 路由壳。业务逻辑委托给：
- markdown_io.py  — 文件读写
- memory_store.py — 记忆检索与录入
- self_engine.py  — Self Engine 决策管道
- scheduler.py    — Lint 检查
- gateway_paths.py — 路径常量与安全
"""
import base64
import http.server
import json
import urllib.parse

from gateway_paths import ROOT
from markdown_io import read_file, write_file, list_core_files
from memory_store import search_memory, ingest, get_stats as memory_stats
from scheduler import run_lint
from self_engine import process as self_engine_process, load_self_layer, capture_memories
from agent_loop import chat_sync, build_system_prompt

PORT = 8420


class APIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ── HTTP 路由 ────────────────────────────────────────────

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/files":
            self._handle_list_files()
        elif parsed.path == "/api/self":
            self._handle_get_self()
        elif parsed.path == "/api/memory/stats":
            self._handle_memory_stats()
        elif parsed.path == "/hero":
            self.path = "/app/hero.html"
            super().do_GET()
        elif parsed.path.startswith("/api/file"):
            self._handle_read_file(parsed.query)
        elif parsed.path.startswith("/api/memory"):
            self._handle_search_memory(parsed.query)
        elif parsed.path in ("/", ""):
            self.path = "/app/index.html"
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self._read_body(length)) if length > 0 else {}

        if parsed.path == "/api/decide":
            self._handle_decide(body)
        elif parsed.path == "/api/chat":
            self._handle_chat(body)
        elif parsed.path == "/api/chat/stream":
            self._handle_chat_stream(body)
        elif parsed.path.startswith("/api/file"):
            self._handle_write_file(parsed.query, body)
        elif parsed.path == "/api/lint":
            self._handle_lint()
        elif parsed.path == "/api/ingest":
            self._handle_ingest(body)
        elif parsed.path == "/api/ingest/enhanced":
            self._handle_ingest_enhanced(body)
        elif parsed.path == "/api/self/scan-changes":
            self._handle_scan_self_changes()
        elif parsed.path == "/api/pending-captures":
            self._handle_get_pending_captures()
        elif parsed.path == "/api/pending-captures/confirm":
            self._handle_confirm_pending(body)
        elif parsed.path == "/api/project/scan":
            self._handle_scan_project()
        elif parsed.path == "/api/social/ingest":
            self._handle_social_ingest(body)
        elif parsed.path == "/api/chat/distill":
            self._handle_chat_distill(body)
        elif parsed.path == "/api/chat/batch-distill":
            self._handle_chat_batch_distill(body)
        else:
            self._json({"error": "unknown endpoint"}, 404)

    # ── 请求处理（委托给模块）─────────────────────────────────

    def _handle_list_files(self):
        try:
            files = list_core_files()
            self._json(files)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_read_file(self, query):
        params = urllib.parse.parse_qs(query)
        path = params.get("path", [None])[0]
        if not path:
            return self._json({"error": "missing path"}, 400)

        try:
            result = read_file(path)
            self._json(result)
        except FileNotFoundError:
            self._json({"error": "file not found"}, 404)
        except ValueError:
            self._json({"error": "path traversal blocked"}, 403)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_write_file(self, query, body):
        params = urllib.parse.parse_qs(query)
        path = params.get("path", [None])[0]
        content = body.get("content", "")
        if not path:
            return self._json({"error": "missing path"}, 400)

        try:
            write_file(path, content)
            self._json({"ok": True, "path": path})
        except PermissionError:
            self._json({"error": "raw is immutable"}, 403)
        except ValueError:
            self._json({"error": "path traversal blocked"}, 403)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_search_memory(self, query):
        params = urllib.parse.parse_qs(query)
        q = params.get("q", [""])[0]
        k = int(params.get("k", [5])[0])

        try:
            result = search_memory(q, k)
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_lint(self):
        try:
            result = run_lint()
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_ingest(self, body):
        content = body.get("content", "")
        domain = body.get("domain", "ai-learning")
        title = body.get("title", "未命名")

        try:
            from pipeline_manual import ingest_enhanced
            result = ingest_enhanced(content=content, domain=domain, title=title)
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_ingest_enhanced(self, body):
        content = body.get("content", "")
        domain = body.get("domain", "ai-learning")
        title = body.get("title", "未命名")
        user_note = body.get("user_note", "")

        try:
            from pipeline_manual import ingest_enhanced
            result = ingest_enhanced(content=content, domain=domain, title=title, user_note=user_note)
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_scan_self_changes(self):
        try:
            from pipeline_self_change import scan_self_changes
            captured_ids = scan_self_changes()
            self._json({"ok": True, "captured_ids": captured_ids, "count": len(captured_ids)})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_get_pending_captures(self):
        try:
            from pipeline_dialogue import get_pending_captures
            self._json({"ok": True, "pending": get_pending_captures()})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_confirm_pending(self, body):
        index = body.get("index")
        approve = body.get("approve", True)
        if index is None or not isinstance(index, int):
            return self._json({"error": "missing or invalid index"}, 400)

        try:
            from pipeline_dialogue import confirm_pending
            result = confirm_pending(index, approve)
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_scan_project(self):
        try:
            from pipeline_project_watch import scan_project_changes
            captured_ids = scan_project_changes()
            self._json({"ok": True, "captured_ids": captured_ids, "count": len(captured_ids)})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_social_ingest(self, body):
        url = body.get("url", "").strip()
        user_note = body.get("user_note", "")
        if not url:
            return self._json({"error": "missing url"}, 400)

        try:
            from pipeline_social_mcp import ingest_social
            result = ingest_social(url, user_note)
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_chat_distill(self, body):
        chat_text = body.get("chat_text", "").strip()
        context_hint = body.get("context_hint", "")
        if not chat_text:
            return self._json({"error": "missing chat_text"}, 400)

        try:
            from pipeline_chat_manual import distill_chat
            result = distill_chat(chat_text, context_hint)
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_chat_batch_distill(self, body):
        """批量导入聊天记录。

        Body: {
            "file_base64": "base64编码的txt内容",
            "context_hint": "工作群",
            "my_aliases": "L,我的名字"
        }
        """
        file_b64 = body.get("file_base64", "")
        context_hint = body.get("context_hint", "")
        my_aliases = body.get("my_aliases", "")
        if not file_b64:
            return self._json({"error": "missing file_base64"}, 400)

        try:
            chat_text = base64.b64decode(file_b64).decode("utf-8", errors="replace")
        except Exception as e:
            return self._json({"error": f"解码失败: {str(e)}"}, 400)

        if not chat_text.strip():
            return self._json({"error": "文件内容为空"}, 400)

        aliases = [a.strip() for a in my_aliases.split(",") if a.strip()] or None

        try:
            from pipeline_chat_manual import batch_distill_from_export
            result = batch_distill_from_export(chat_text, context_hint, aliases)
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_get_self(self):
        """返回当前 Self 层快照。"""
        try:
            snapshot = load_self_layer()
            self._json(snapshot)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_memory_stats(self):
        """返回记忆存储统计。"""
        try:
            stats = memory_stats()
            self._json(stats)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_decide(self, body):
        """Self Engine 决策管道：输入消息，输出决策结果 + AgentContext。

        POST /api/decide
        Body: {"message": "用户消息文本"}
        """
        message = body.get("message", "")
        if not message:
            return self._json({"error": "missing message"}, 400)

        try:
            result = self_engine_process(message)
            # 确保 memory_field 包含在响应中
            memory_field = result.get("context", {}).get("memory_field", {})
            if isinstance(memory_field, dict):
                result["memory_field"] = memory_field
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_chat(self, body):
        """完整对话：Self Engine + Agent Loop → LLM 回复。

        POST /api/chat
        Body: {"message": "用户消息文本"}
        Response: {"reply": "LLM回复", "decision": {...}, "field_type": "..."}
        """
        message = body.get("message", "")
        if not message:
            return self._json({"error": "missing message"}, 400)

        try:
            # 1. Self Engine 分析（包含记忆场构建）
            result = self_engine_process(message)
            context = result.get("context", {})
            decision = result.get("decision", {})

            # 2. Agent Loop 调 LLM（使用场感知的 System Prompt）
            reply = chat_sync(context, message)

            # 3. 自动记忆捕获
            try:
                capture_memories(message, decision, reply)
            except Exception:
                pass  # 记忆捕获失败不影响主流程

            # 提取记忆场结构用于前端可视化
            memory_field = result.get("context", {}).get("memory_field", {})
            self._json({
                "reply": reply,
                "decision": decision,
                "snapshot": result.get("snapshot", {}),
                "field_type": decision.get("field_type", "通用场"),
                "emotional_state": decision.get("emotional_state", "neutral"),
                "memory_field": memory_field if isinstance(memory_field, dict) else None,
            })
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_chat_stream(self, body):
        """流式对话：SSE 格式，逐字返回（本地服务器模拟实现）。

        POST /api/chat/stream
        Body: {"message": "用户消息文本"}
        """
        message = body.get("message", "")
        if not message:
            return self._json({"error": "missing message"}, 400)

        try:
            # 1. Self Engine 分析
            result = self_engine_process(message)
            context = result.get("context", {})
            decision = result.get("decision", {})

            # 2. 先获取完整回复（本地服务器用同步方式）
            reply = chat_sync(context, message)

            # 3. 自动记忆捕获
            try:
                capture_memories(message, decision, reply)
            except Exception:
                pass

            # 4. SSE 流式输出
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            # 先发送决策 + 记忆场
            memory_field = result.get("context", {}).get("memory_field", {})
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
            self.wfile.write(f"data: {json.dumps({'decision': decision_payload, 'memory_field': memory_field if isinstance(memory_field, dict) else None})}\n\n".encode("utf-8"))

            # 逐字发送回复（模拟真实流式）
            import time
            chunk_size = 3  # 每块 3 个字符
            for i in range(0, len(reply), chunk_size):
                chunk = reply[i:i + chunk_size]
                self.wfile.write(f"data: {json.dumps({'token': chunk})}\n\n".encode("utf-8"))
                time.sleep(0.03)  # 30ms 间隔，模拟打字效果

            self.wfile.write(b"data: [DONE]\n\n")

        except Exception as e:
            self._json({"error": str(e)}, 500)

    # ── HTTP 工具方法 ────────────────────────────────────────

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_body(self, n):
        return self.rfile.read(n).decode("utf-8")

    def log_message(self, format, *args):
        pass  # 静默


if __name__ == "__main__":
    print(f"  Second Self 正在运行 → http://localhost:{PORT}")
    print(f"  按 Ctrl+C 停止")
    server = http.server.HTTPServer(("127.0.0.1", PORT), APIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  已停止")
