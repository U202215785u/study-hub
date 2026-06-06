"""Self 文件变更扫描 — 检测 ME.md、DASHBOARD.md 等核心文件的变化。"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from gateway_paths import ROOT
from memory_store import insert_entry


_STATE_PATH = ROOT / ".memory" / "self_change_state.json"
_CORE_FILES = ["ME.md", "DASHBOARD.md", "PRINCIPLES.md", "PREFERENCES.md", "AUTONOMY.md"]


def _load_state() -> dict:
    if not _STATE_PATH.exists():
        return {}
    try:
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state: dict) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _extract_change_summary(old_text: str, new_text: str) -> str:
    """提取变更摘要。"""
    old_lines = set(old_text.split("\n"))
    new_lines = set(new_text.split("\n"))
    added = new_lines - old_lines
    removed = old_lines - new_lines
    
    summary = []
    if added:
        summary.append(f"新增 {len(added)} 行")
    if removed:
        summary.append(f"删除 {len(removed)} 行")
    
    # 提取关键变更
    for line in added:
        if line.strip().startswith("**当前进度**"):
            summary.append(f"当前进度 从「空」变为「{line.split('：', 1)[-1].strip()[:50]}」")
    
    return "；".join(summary) if summary else "骨架 hash 变化"


def scan_self_changes() -> list[str]:
    """扫描 Self 文件变更。"""
    state = _load_state()
    captured_ids = []
    
    for filename in _CORE_FILES:
        path = ROOT / filename
        current_hash = _file_hash(path)
        last_hash = state.get(filename, "")
        
        if current_hash == last_hash or not current_hash:
            continue
        
        old_text = state.get(f"{filename}_content", "")
        new_text = path.read_text(encoding="utf-8") if path.exists() else ""
        
        summary = _extract_change_summary(old_text, new_text)
        
        content = f"Self 文件变更：{filename}\n\n{summary}"
        
        entry_id = insert_entry(
            source="file",
            type="update",
            content=content,
            context={"file": filename, "old_hash": last_hash, "new_hash": current_hash},
            significance="A",
            field="knowledge",
        )
        captured_ids.append(entry_id)
        
        state[filename] = current_hash
        state[f"{filename}_content"] = new_text
    
    _save_state(state)
    return captured_ids
