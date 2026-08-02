"""Shared state-machine rules for Butler coordination tasks."""

TASK_TYPES = frozenset(
    {"bug", "change", "research", "health_check", "deploy", "memory_update"}
)

# These names are intentionally accepted at the boundary.  A user or agent should
# never have to guess the internal canonical value merely to record a case.
TASK_TYPE_ALIASES = {
    "bug": "bug",
    "investigate": "bug",
    "investigation": "bug",
    "diagnose": "bug",
    "diagnosis": "bug",
    "debug": "bug",
    "troubleshoot": "bug",
    "排查": "bug",
    "调查": "bug",
    "诊断": "bug",
    "故障": "bug",
    "异常": "bug",
    "修复": "bug",
    "change": "change",
    "feature": "change",
    "modify": "change",
    "implementation": "change",
    "修改": "change",
    "新增": "change",
    "功能": "change",
    "优化": "change",
    "research": "research",
    "study": "research",
    "研究": "research",
    "调研": "research",
    "health_check": "health_check",
    "health": "health_check",
    "检查": "health_check",
    "体检": "health_check",
    "deploy": "deploy",
    "deployment": "deploy",
    "release": "deploy",
    "部署": "deploy",
    "发布": "deploy",
    "上线": "deploy",
    "memory_update": "memory_update",
    "memory": "memory_update",
    "记忆": "memory_update",
    "知识更新": "memory_update",
}

_DESCRIPTION_TYPE_HINTS = (
    ("memory_update", ("记忆", "知识更新", "项目记忆", "memory")),
    ("deploy", ("部署", "发布", "上线", "deploy", "release")),
    ("research", ("研究", "调研", "方案对比", "research", "study")),
    ("health_check", ("健康检查", "体检", "health check")),
    ("bug", ("报错", "错误", "异常", "失败", "排查", "调查", "诊断", "修复", "asr", "bug", "error", "fail")),
    ("change", ("新增", "修改", "功能", "调整", "优化", "实现", "change", "feature", "modify")),
)

# A no-progress result should be counted consistently even when the source uses
# different terminology for the same outcome.
NO_PROGRESS_RESULTS = frozenset({"failed", "failure", "error", "timeout", "timed_out", "no_progress"})

STATUSES = frozenset(
    {
        "received",
        "located",
        "investigating",
        "awaiting_approval",
        "implementing",
        "auditing",
        "verifying",
        "completed",
        "blocked",
        "cancelled",
        "archived",
    }
)
TERMINAL_STATUSES = frozenset({"completed", "cancelled", "archived"})

ALLOWED_TRANSITIONS = {
    "received": {"located", "blocked", "cancelled"},
    "located": {"investigating", "awaiting_approval", "blocked", "cancelled"},
    "investigating": {"awaiting_approval", "implementing", "verifying", "blocked", "cancelled"},
    "awaiting_approval": {"investigating", "implementing", "blocked", "cancelled"},
    "implementing": {"investigating", "auditing", "blocked", "cancelled"},
    "auditing": {"investigating", "verifying", "blocked", "cancelled"},
    "verifying": {"investigating", "completed", "blocked", "cancelled"},
    "blocked": {"investigating", "implementing", "cancelled", "archived"},
    "completed": set(),
    "cancelled": set(),
    "archived": set(),
}


class ButlerStateError(ValueError):
    """Raised when a caller tries to bypass a Butler task gate."""


def normalize_task_type(task_type: str | None, description: str = "") -> str:
    """Return a canonical task type from a label or the user's own wording."""
    raw_type = (task_type or "").strip().lower()
    if raw_type in TASK_TYPES:
        return raw_type
    if canonical := TASK_TYPE_ALIASES.get(raw_type):
        return canonical

    report = f"{raw_type} {(description or '').strip().lower()}"
    for canonical, hints in _DESCRIPTION_TYPE_HINTS:
        if any(hint in report for hint in hints):
            return canonical

    # A blank type means the caller delegated classification to Butler.  Bugs are
    # the least surprising default for an otherwise unclassified project report.
    if not raw_type:
        return "bug"
    raise ButlerStateError(f"unsupported task type: {task_type}; describe the issue in natural language or use bug/change/research")


def validate_transition(current: str, target: str) -> None:
    """Reject invalid state transitions before any persistent mutation."""
    if current not in STATUSES:
        raise ButlerStateError(f"unknown current status: {current}")
    if target not in STATUSES:
        raise ButlerStateError(f"unknown target status: {target}")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ButlerStateError(f"cannot transition from {current} to {target}")
