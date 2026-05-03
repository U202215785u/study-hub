"""
文件夹监视器：监听 inbox 目录，新文件自动入库。
"""
import os, time, shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from processing.processors import can_handle, process_path, is_duplicate

INBOX_DIR = os.path.join(os.path.dirname(__file__), "data", "inbox")
PROCESSED_DIR = os.path.join(INBOX_DIR, "processed")
COOLDOWN_SECONDS = 3

os.makedirs(PROCESSED_DIR, exist_ok=True)


class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        time.sleep(COOLDOWN_SECONDS)
        self._process(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        time.sleep(COOLDOWN_SECONDS)
        self._process(event.dest_path)

    def _process(self, path):
        filename = os.path.basename(path)
        ext = os.path.splitext(filename)[1].lower()

        if not can_handle(ext):
            return

        try:
            if not os.path.isfile(path):
                return
            text, ext, content_hash = process_path(path)
            filename = os.path.basename(path)
        except Exception as e:
            print(f"[收件箱] 读取失败: {filename} - {e}")
            self._archive(path, filename)
            return

        if not text.strip():
            print(f"[收件箱] 文件为空: {filename}")
            self._archive(path, filename)
            return

        if is_duplicate(content_hash):
            print(f"[收件箱] 重复内容，跳过: {filename}")
            self._archive(path, filename)
            return

        from database import get_db
        conn = get_db()
        try:
            cur = conn.execute(
                "INSERT INTO documents (title, content, content_type, source, content_hash, char_count) VALUES (?, ?, ?, ?, ?, ?)",
                (filename, text, ext.lstrip("."), "inbox", content_hash, len(text)),
            )
            doc_id = cur.lastrowid
            conn.commit()

            try:
                from processing.chunker import chunk_text
                from processing.vector_store import get_vector_store
                chunks = chunk_text(text)
                vs = get_vector_store()
                vs.add_document(doc_id, filename, chunks)
                conn.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
                conn.commit()
            except Exception as e:
                print(f"[收件箱] 向量化失败: {e}")

            print(f"[收件箱] 已入库: {filename} ({len(text)} 字)")
        except Exception as e:
            print(f"[收件箱] 入库失败: {filename} - {e}")
        finally:
            conn.close()

        self._archive(path, filename)

    def _archive(self, src_path, filename):
        try:
            dst = os.path.join(PROCESSED_DIR, filename)
            if os.path.exists(dst):
                base, ext_ = os.path.splitext(filename)
                dst = os.path.join(PROCESSED_DIR, f"{base}_{int(time.time())}{ext_}")
            shutil.move(src_path, dst)
        except Exception:
            pass


_observer = None


def start_watcher():
    global _observer
    if _observer is not None:
        return
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    _observer = Observer()
    _observer.schedule(InboxHandler(), INBOX_DIR, recursive=False)
    _observer.start()
    print(f"[收件箱] 监视已启动: {INBOX_DIR}")
    print(f"[收件箱] 把任意文件丢进去即自动入库")


def stop_watcher():
    global _observer
    if _observer is not None:
        _observer.stop()
        _observer.join()
        _observer = None
