"""调度器 — 定期 Lint 检查。"""
from datetime import datetime
from pathlib import Path

from gateway_paths import ROOT


def run_lint() -> dict:
    """运行 Lint 检查，返回当前状态摘要。"""
    from memory_store import get_stats
    from self_engine import load_self_layer
    
    snapshot = load_self_layer()
    dashboard = snapshot.get("dashboard", {})
    projects = dashboard.get("strategic_projects", [])
    maintenance = dashboard.get("maintenance_items", [])
    mem_stats = get_stats()
    
    # 检查逾期维护项
    overdue = [m for m in maintenance if "逾期" in m.get("deadline", "")]
    
    # 检查 STALLED 项目
    stalled = []
    for p in projects:
        updated = p.get("updated", "")
        if updated:
            try:
                from datetime import datetime
                d = datetime.strptime(updated, "%Y-%m-%d")
                days = (datetime.now() - d).days
                if days > 14:
                    stalled.append(p["name"])
            except (ValueError, TypeError):
                pass
    
    return {
        "status": "ok" if not overdue and not stalled else "warning",
        "overdue_items": len(overdue),
        "stalled_projects": stalled,
        "memory_total": mem_stats["total"],
        "active_projects": len(projects),
        "checked_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
