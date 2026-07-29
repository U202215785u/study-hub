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


def _pid_file(backend_dir, port):
    name = "server.pid" if port == 8741 else f"server.{port}.pid"
    return backend_dir / "data" / name


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
        encoding="utf-8",
        errors="replace",
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
    for name in (
        "start-background.ps1",
        "stop-background.ps1",
        "startup_runner.py",
    ):
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


def test_windows_launchers_only_delegate_to_canonical_scripts():
    launchers = {
        STUDY_HUB_DIR / "后台启动.bat": "backend\\start-background.ps1",
        STUDY_HUB_DIR / "后台停止.bat": "backend\\stop-background.ps1",
        STUDY_HUB_DIR / "启动.bat": "后台启动.bat",
        STUDY_HUB_DIR / "start-background.ps1": "backend\\start-background.ps1",
        STUDY_HUB_DIR / "start-direct.ps1": "backend\\start-background.ps1",
        STUDY_HUB_DIR / "start_server.ps1": "backend\\start-background.ps1",
        STUDY_HUB_DIR / "start-temp.bat": "backend\\start-background.ps1",
        STUDY_HUB_DIR / "stop-background.ps1": "backend\\stop-background.ps1",
        BACKEND_DIR / "start.bat": "start-background.ps1",
        BACKEND_DIR / "后台启动.bat": "start-background.ps1",
        BACKEND_DIR / "后台停止.bat": "stop-background.ps1",
    }

    for launcher, target in launchers.items():
        content = launcher.read_text(encoding="utf-8").lower()
        assert target.lower() in content
        assert "venv" not in content
        assert "main.py" not in content
        assert "python.exe" not in content


def test_desktop_launcher_calls_the_canonical_service_then_opens_the_page():
    launcher = STUDY_HUB_DIR / "打开 Study Hub.bat"

    assert launcher.is_file()
    content = launcher.read_text(encoding="utf-8").lower()
    assert "backend\\start-background.ps1" in content
    assert "后台启动.bat" not in content
    assert "http://127.0.0.1:8741/" in content
    assert "start \"\"" in content


def test_stale_second_port_pid_does_not_kill_first_instance(tmp_path):
    backend_dir = _make_script_sandbox(tmp_path)
    start_script = backend_dir / "start-background.ps1"
    stop_script = backend_dir / "stop-background.ps1"
    first_port = _free_port()
    second_port = _free_port()

    try:
        first = _run_powershell(start_script, "-Port", first_port)
        assert first.returncode == 0, first.stdout + first.stderr
        _wait_for_health(first_port)
        first_pid = _pid_file(backend_dir, first_port).read_text(
            encoding="utf-8"
        )

        stale_pid_file = _pid_file(backend_dir, second_port)
        stale_pid_file.write_text(first_pid, encoding="utf-8")
        second = _run_powershell(start_script, "-Port", second_port)

        assert second.returncode == 0, second.stdout + second.stderr
        _wait_for_health(first_port, timeout=3)
        _wait_for_health(second_port, timeout=3)
    finally:
        _run_powershell(stop_script, "-Port", first_port, timeout=15)
        _run_powershell(stop_script, "-Port", second_port, timeout=15)


def test_start_and_stop_work_from_a_path_with_spaces(tmp_path):
    backend_dir = _make_script_sandbox(tmp_path)
    start_script = backend_dir / "start-background.ps1"
    stop_script = backend_dir / "stop-background.ps1"
    port = _free_port()
    pid_file = _pid_file(backend_dir, port)
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
        _run_powershell(stop_script, "-Port", port, timeout=15)
        if process_id:
            subprocess.run(
                ["taskkill.exe", "/PID", str(process_id), "/T", "/F"],
                capture_output=True,
            )


def test_stop_does_not_kill_an_unrelated_listener(tmp_path):
    backend_dir = _make_script_sandbox(tmp_path)
    stop_script = backend_dir / "stop-background.ps1"
    port = _free_port()
    pid_file = _pid_file(backend_dir, port)
    pid_file.parent.mkdir()
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


def test_start_failure_reports_fresh_process_output(tmp_path):
    backend_dir = _make_script_sandbox(tmp_path)
    start_script = backend_dir / "start-background.ps1"
    data_dir = backend_dir / "data"
    data_dir.mkdir()
    (data_dir / "app.log").write_text("STALE_APP_LOG\n", encoding="utf-8")
    (backend_dir / "main.py").write_text(
        """
import sys

print("FRESH_STARTUP_STDOUT", flush=True)
print("FRESH_IMPORT_FAILURE", file=sys.stderr, flush=True)
raise RuntimeError("import-time crash")
""".lstrip(),
        encoding="utf-8",
    )

    result = _run_powershell(start_script, "-Port", _free_port())
    output = result.stdout + result.stderr

    assert result.returncode == 4
    assert "FRESH_STARTUP_STDOUT" in (
        data_dir / "startup.stdout.log"
    ).read_text(encoding="utf-8")
    assert "FRESH_IMPORT_FAILURE" in (
        data_dir / "startup.stderr.log"
    ).read_text(encoding="utf-8")
    assert "FRESH_IMPORT_FAILURE" in output
    assert "STALE_APP_LOG" not in output


def test_failed_second_port_keeps_first_instance_running(tmp_path):
    backend_dir = _make_script_sandbox(tmp_path)
    start_script = backend_dir / "start-background.ps1"
    stop_script = backend_dir / "stop-background.ps1"
    first_port = _free_port()
    second_port = _free_port()

    try:
        first = _run_powershell(start_script, "-Port", first_port)
        assert first.returncode == 0, first.stdout + first.stderr
        _wait_for_health(first_port)

        (backend_dir / "main.py").write_text(
            "raise RuntimeError('SECOND_PORT_FAILURE')\n",
            encoding="utf-8",
        )
        second = _run_powershell(start_script, "-Port", second_port)

        assert second.returncode == 4, second.stdout + second.stderr
        _wait_for_health(first_port, timeout=3)
    finally:
        _run_powershell(stop_script, "-Port", first_port, timeout=15)
        _run_powershell(stop_script, "-Port", second_port, timeout=15)


def test_stop_checks_listener_after_stale_owned_pid(tmp_path):
    backend_dir = _make_script_sandbox(tmp_path)
    stop_script = backend_dir / "stop-background.ps1"
    main_py = backend_dir / "main.py"
    port = _free_port()
    pid_file = _pid_file(backend_dir, port)
    pid_file.parent.mkdir()
    main_py.write_text(
        """
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

if os.environ["MODE"] == "sleep":
    while True:
        time.sleep(1)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"status": "ok"}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass

HTTPServer(("127.0.0.1", int(os.environ["PORT"])), Handler).serve_forever()
""".lstrip(),
        encoding="utf-8",
    )
    sleeper = subprocess.Popen(
        [sys.executable, "-u", str(main_py)],
        cwd=backend_dir,
        env=dict(os.environ, MODE="sleep", PORT=str(port)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    listener = subprocess.Popen(
        [sys.executable, "-u", str(main_py)],
        cwd=backend_dir,
        env=dict(os.environ, MODE="serve", PORT=str(port)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pid_file.write_text(str(sleeper.pid), encoding="utf-8")

    try:
        _wait_for_health(port)
        stopped = _run_powershell(stop_script, "-Port", port, timeout=15)
        assert stopped.returncode == 0, stopped.stdout + stopped.stderr
        with socket.socket() as sock:
            assert sock.connect_ex(("127.0.0.1", port)) != 0
    finally:
        for process in (sleeper, listener):
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
