import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

STUDY_HUB_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = STUDY_HUB_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import database


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _run_powershell(script, *args, timeout=45):
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            *map(str, args),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _wait_for_health(port, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=1
            ) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise AssertionError(f"service on port {port} did not become healthy")


def _make_script_sandbox(tmp_path):
    backend_dir = tmp_path / "copy with spaces" / "backend"
    backend_dir.mkdir(parents=True)
    for name in ("start-background.ps1", "stop-background.ps1"):
        shutil.copy2(BACKEND_DIR / name, backend_dir / name)
    (backend_dir / "main.py").write_text(
        """
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"status": "ok"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass

HTTPServer(("127.0.0.1", int(os.environ["PORT"])), Handler).serve_forever()
""".lstrip(),
        encoding="utf-8",
    )
    return backend_dir


def test_init_db_repairs_an_existing_empty_database(tmp_path, monkeypatch):
    db_path = tmp_path / "study_hub.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
    assert db_path.stat().st_size > 0

    monkeypatch.setattr(database, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    database.init_db()

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"categories", "documents"} <= tables


def test_readme_recommends_the_real_windows_entrypoints():
    readme = (STUDY_HUB_DIR / "README.md").read_text(encoding="utf-8")
    windows_section = readme.split("### Windows（推荐）", 1)[1].split(
        "### macOS / Linux", 1
    )[0]
    assert (STUDY_HUB_DIR / "后台启动.bat").is_file()
    assert (STUDY_HUB_DIR / "后台停止.bat").is_file()
    assert "`后台启动.bat`" in windows_section
    assert "`后台停止.bat`" in windows_section
    assert "start.bat" not in windows_section
    assert "start.ps1" not in windows_section


def test_windows_scripts_avoid_known_unsafe_process_patterns():
    start_script = (BACKEND_DIR / "start-background.ps1").read_text(encoding="utf-8")
    stop_script = (BACKEND_DIR / "stop-background.ps1").read_text(encoding="utf-8")
    combined = start_script + stop_script

    assert "venv" not in combined.lower()
    assert "$!" not in combined
    assert "%!" not in combined
    assert '*main.py*' not in combined
    assert "Test-StudyHubProcess" in combined


def test_start_and_stop_work_from_a_path_with_spaces(tmp_path):
    backend_dir = _make_script_sandbox(tmp_path)
    start_script = backend_dir / "start-background.ps1"
    stop_script = backend_dir / "stop-background.ps1"
    pid_file = backend_dir / "data" / "server.pid"
    port = _free_port()
    process_id = None
    pid_file.parent.mkdir()
    pid_file.write_text("%!", encoding="utf-8")

    try:
        started = _run_powershell(start_script, "-Port", port)
        assert started.returncode == 0, started.stdout + started.stderr
        assert pid_file.read_text(encoding="utf-8").strip().isdigit()
        process_id = int(pid_file.read_text(encoding="utf-8").strip())
        _wait_for_health(port)

        restarted = _run_powershell(start_script, "-Port", port)
        assert restarted.returncode == 0, restarted.stdout + restarted.stderr
        restarted_process_id = int(pid_file.read_text(encoding="utf-8").strip())
        assert restarted_process_id != process_id
        process_id = restarted_process_id
        _wait_for_health(port)

        stopped = _run_powershell(stop_script, "-Port", port)
        assert stopped.returncode == 0, stopped.stdout + stopped.stderr
        assert not pid_file.exists()
        with socket.socket() as sock:
            assert sock.connect_ex(("127.0.0.1", port)) != 0
    finally:
        if process_id:
            subprocess.run(
                ["taskkill.exe", "/PID", str(process_id), "/T", "/F"],
                capture_output=True,
            )


def test_stop_does_not_kill_an_unrelated_listener(tmp_path):
    backend_dir = _make_script_sandbox(tmp_path)
    stop_script = backend_dir / "stop-background.ps1"
    pid_file = backend_dir / "data" / "server.pid"
    pid_file.parent.mkdir()
    port = _free_port()
    unrelated = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pid_file.write_text(str(unrelated.pid), encoding="utf-8")

    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        else:
            raise AssertionError("unrelated test listener did not start")

        stopped = _run_powershell(stop_script, "-Port", port)
        assert stopped.returncode == 0, stopped.stdout + stopped.stderr
        assert unrelated.poll() is None
        assert not pid_file.exists()
    finally:
        unrelated.terminate()
        try:
            unrelated.wait(timeout=5)
        except subprocess.TimeoutExpired:
            unrelated.kill()
