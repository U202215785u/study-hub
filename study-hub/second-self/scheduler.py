"""定时任务调度器 — 轻量级"""
import json
from datetime import datetime, timedelta
from pathlib import Path

from gateway_paths import ROOT

SCHEDULE_FILE = ROOT / ".memory" / "schedule.json"


def load_schedule() -> dict:
    """加载调度配置。"""
    if SCHEDULE_FILE.exists():
        try:
            return json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_schedule(schedule: dict) -> None:
    """保存调度配置。"""
    SCHEDULE_FILE.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")


def should_run(task_name: str, interval_hours: int = 24) -> bool:
    """检查任务是否应该运行。"""
    schedule = load_schedule()
    last_run = schedule.get(task_name)
    if not last_run:
        return True
    try:
        last = datetime.fromisoformat(last_run)
        return datetime.now() - last > timedelta(hours=interval_hours)
    except ValueError:
        return True


def mark_run(task_name: str) -> None:
    """标记任务已运行。"""
    schedule = load_schedule()
    schedule[task_name] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    save_schedule(schedule)
