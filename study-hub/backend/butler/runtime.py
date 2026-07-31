"""State-machine service for persistent Study-Hub Butler cases."""

from __future__ import annotations

from uuid import uuid4

from .catalog import EXTERNAL_EXPERTS, INTERNAL_ROLES
from .models import TASK_TYPES, ButlerStateError, validate_transition
from .storage import append_event, create_task, list_events, list_tasks, read_task, update_task


class ButlerRuntime:
    """Coordinate one task at a time while retaining an auditable history."""

    def __init__(self, connection_factory):
        self._connection_factory = connection_factory

    def _with_connection(self, callback):
        conn = self._connection_factory()
        try:
            result = callback(conn)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _case(self, conn, case_id: str) -> dict:
        case = read_task(conn, case_id)
        if case is None:
            raise ButlerStateError(f"unknown Butler case: {case_id}")
        return case

    def open_case(self, *, task_type: str, description: str, feature_code="", title="") -> dict:
        if task_type not in TASK_TYPES:
            raise ButlerStateError(f"unsupported task type: {task_type}")
        if not description or not description.strip():
            raise ButlerStateError("a case needs a user-reported description")

        def create(conn):
            case = create_task(
                conn,
                {
                    "id": uuid4().hex,
                    "task_type": task_type,
                    "title": title.strip() or description.strip()[:80],
                    "description": description.strip(),
                    "feature_code": feature_code.strip(),
                    "status": "received",
                    "risk_level": "normal",
                    "attempt_count": 0,
                    "current_role": "butler",
                    "current_expert": "",
                    "context": {},
                },
            )
            append_event(conn, case["id"], "received", "已收到用户问题", payload={"description": case["description"]})
            return self._case(conn, case["id"])

        return self._with_connection(create)

    def get_case(self, case_id: str) -> dict:
        return self._with_connection(lambda conn: self._case(conn, case_id))

    def list_cases(self, *, include_archived=False) -> list[dict]:
        return self._with_connection(
            lambda conn: list_tasks(conn, include_archived=include_archived)
        )

    def record_context(self, case_id: str, *, project_index_hits: list[str], owner_files: list[str]) -> dict:
        def record(conn):
            case = self._case(conn, case_id)
            validate_transition(case["status"], "located")
            context = {
                **case["context"],
                "project_index_hits": list(project_index_hits),
                "owner_files": list(owner_files),
            }
            case = update_task(conn, case_id, status="located", context=context)
            append_event(conn, case_id, "context_recorded", "已定位项目记录和领域知识", payload=context)
            return case

        return self._with_connection(record)

    def assign(self, case_id: str, *, role: str, experts: list[str] | tuple[str, ...] = ()) -> dict:
        if role not in INTERNAL_ROLES:
            raise ButlerStateError(f"unknown internal role: {role}")
        unknown = set(experts) - set(EXTERNAL_EXPERTS)
        if unknown:
            raise ButlerStateError(f"unknown experts: {', '.join(sorted(unknown))}")

        def handoff(conn):
            case = self._case(conn, case_id)
            validate_transition(case["status"], "investigating")
            ordered_experts = tuple(dict.fromkeys(experts))
            case = update_task(
                conn,
                case_id,
                status="investigating",
                current_role=role,
                current_expert=",".join(ordered_experts),
            )
            append_event(
                conn,
                case_id,
                "handoff",
                "已分派处理角色和领域专家",
                actor=role,
                payload={"role": role, "experts": ordered_experts},
            )
            return case

        return self._with_connection(handoff)

    def events(self, case_id: str) -> list[dict]:
        return self._with_connection(lambda conn: (self._case(conn, case_id), list_events(conn, case_id))[1])

    def next_action(self, case_id: str) -> dict:
        case = self.get_case(case_id)
        actions = {
            "received": {
                "kind": "locate_context",
                "required": ("project_index_hits", "owner_files"),
                "summary": "先读取项目记录和相关领域知识。",
            },
            "located": {
                "kind": "assign_role",
                "required": ("role",),
                "summary": "选择当前工作阶段，并按需要分派领域专家。",
            },
            "investigating": {
                "kind": "record_attempt",
                "required": ("action", "result", "learned"),
                "summary": "记录一次有证据的调查或最小修复尝试。",
            },
            "blocked": {
                "kind": "await_user_direction",
                "required": (),
                "summary": "任务已停止，等待用户决定是否恢复或换一种方式。",
            },
        }
        return actions.get(
            case["status"],
            {"kind": "inspect_case", "required": (), "summary": "查看当前任务记录后再继续。"},
        )
