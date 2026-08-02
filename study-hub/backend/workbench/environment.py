"""Read-only, redacted information for the Study-Hub workbench."""

from __future__ import annotations

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ROADMAP_FILE_CANDIDATES = (
    Path("project-memory") / "未来规划.md",
    Path("docs") / "roadmap.md",
)
_README_PLANNING_RE = re.compile(r"规划|roadmap|plan|milestone", re.IGNORECASE)


def _relative_path(path: Path, project_root: Path) -> str:
    return path.relative_to(project_root).as_posix()


def _default_health(project_root: Path) -> dict[str, Any]:
    checks = {
        "project": {
            "status": "ok" if project_root.is_dir() else "error",
        },
        "backend": {
            "status": "ok" if (project_root / "study-hub" / "backend").is_dir() else "error",
        },
    }
    status = "ok" if all(item["status"] == "ok" for item in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


def _normalise_health(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"status": "error", "checks": {}, "error": "health_check_invalid"}
    status = value.get("status")
    if status not in {"ok", "degraded", "error"}:
        status = "error"
    raw_checks = value.get("checks", {})
    checks: dict[str, dict[str, str]] = {}
    if isinstance(raw_checks, dict):
        for name, detail in raw_checks.items():
            safe_name = name if isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", name) else "unknown"
            check_status = detail.get("status") if isinstance(detail, dict) else None
            checks[safe_name] = {
                "status": check_status if check_status in {"ok", "degraded", "error"} else "error"
            }
    result: dict[str, Any] = {"status": status, "checks": checks}
    if value.get("error"):
        result["error"] = "health_check_failed"
    return result


def get_environment_info(
    project_root: Path | None = None,
    health_checker: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return runtime facts that are safe to expose to a local workbench."""

    root = Path(project_root or PROJECT_ROOT).resolve()
    try:
        health = _normalise_health(
            health_checker() if health_checker is not None else _default_health(root)
        )
    except Exception:
        health = {"status": "error", "checks": {}, "error": "health_check_failed"}

    return {
        "status": health["status"],
        "runtime": {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "implementation": platform.python_implementation(),
        },
        "health": health,
        "paths": {
            "project_root": ".",
            "backend": _relative_path(root / "study-hub" / "backend", root),
        },
    }


def _roadmap_metadata(path: Path, project_root: Path, content: str, source: str) -> dict[str, Any]:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {
            "status": "error",
            "missing": False,
            "content": None,
            "source": source,
            "relative_path": _relative_path(path, project_root),
            "mtime": None,
            "updated_at": None,
            "error": "stat_failed",
        }
    return {
        "status": "available",
        "missing": False,
        "content": content,
        "source": source,
        "relative_path": _relative_path(path, project_root),
        "mtime": mtime,
        "updated_at": datetime.fromtimestamp(mtime, timezone.utc).isoformat(),
        "error": None,
    }


def _read_readme_planning(path: Path, project_root: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except (OSError, UnicodeError):
        return {
            "status": "error",
            "missing": False,
            "content": None,
            "source": "README.md",
            "relative_path": _relative_path(path, project_root),
            "mtime": None,
            "updated_at": None,
            "error": "read_failed",
        }

    heading_index = None
    heading_text = ""
    heading_level = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match and _README_PLANNING_RE.search(match.group(2)):
            heading_index = index
            heading_text = match.group(2)
            heading_level = len(match.group(1))
            break
    if heading_index is None:
        return None

    end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s+", lines[index])
        if match and len(match.group(1)) <= heading_level:
            end = index
            break
    content = "".join(lines[heading_index:end]).rstrip("\n") + "\n"
    return _roadmap_metadata(path, project_root, content, f"README.md#{heading_text}")


def get_roadmap(project_root: Path | None = None) -> dict[str, Any]:
    """Read the highest-priority available Markdown planning source."""

    root = Path(project_root or PROJECT_ROOT).resolve()
    for relative_path in _ROADMAP_FILE_CANDIDATES:
        path = root / relative_path
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
            return _roadmap_metadata(path, root, content, relative_path.as_posix())
        except (OSError, UnicodeError):
            return {
                "status": "error",
                "missing": False,
                "content": None,
                "source": relative_path.as_posix(),
                "relative_path": relative_path.as_posix(),
                "mtime": None,
                "updated_at": None,
                "error": "read_failed",
            }

    readme_result = _read_readme_planning(root / "README.md", root)
    if readme_result is not None:
        return readme_result

    return {
        "status": "missing",
        "missing": True,
        "content": None,
        "source": None,
        "relative_path": None,
        "mtime": None,
        "updated_at": None,
        "error": None,
    }


# Explicit aliases make the read-only service easy to mount or reuse.
read_environment = get_environment_info
read_roadmap = get_roadmap
