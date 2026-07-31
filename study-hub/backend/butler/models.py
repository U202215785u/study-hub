"""Shared state-machine rules for Butler coordination tasks."""

TASK_TYPES = frozenset(
    {"bug", "change", "research", "health_check", "deploy", "memory_update"}
)

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


def validate_transition(current: str, target: str) -> None:
    """Reject invalid state transitions before any persistent mutation."""
    if current not in STATUSES:
        raise ButlerStateError(f"unknown current status: {current}")
    if target not in STATUSES:
        raise ButlerStateError(f"unknown target status: {target}")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ButlerStateError(f"cannot transition from {current} to {target}")
