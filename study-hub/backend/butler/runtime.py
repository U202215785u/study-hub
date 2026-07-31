"""State-machine service for persistent Study-Hub Butler cases."""

from __future__ import annotations

from uuid import uuid4

from .catalog import EXTERNAL_EXPERTS, INTERNAL_ROLES
from .models import TASK_TYPES, ButlerStateError, validate_transition
from .storage import (
    append_event,
    create_approval,
    create_task,
    list_events,
    list_tasks,
    pending_approvals,
    read_approval,
    read_task,
    resolve_approval as persist_approval,
    update_task,
)


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

    def request_approval(self, case_id: str, *, risk_kind: str, summary: str) -> dict:
        if not risk_kind or not summary.strip():
            raise ButlerStateError("approval needs a risk kind and user-readable summary")

        def request(conn):
            case = self._case(conn, case_id)
            validate_transition(case["status"], "awaiting_approval")
            approval = create_approval(
                conn,
                {
                    "id": uuid4().hex,
                    "task_id": case_id,
                    "risk_kind": risk_kind,
                    "summary": summary.strip(),
                    "status": "pending",
                },
            )
            update_task(conn, case_id, status="awaiting_approval", risk_level="protected")
            append_event(
                conn,
                case_id,
                "approval_requested",
                "需要用户确认后才能继续",
                payload={"approval_id": approval["id"], "risk_kind": risk_kind, "summary": summary.strip()},
            )
            return approval

        return self._with_connection(request)

    def resolve_approval(self, approval_id: str, *, approved: bool, response: str = "") -> dict:
        def resolve(conn):
            approval = read_approval(conn, approval_id)
            if approval is None:
                raise ButlerStateError(f"unknown approval: {approval_id}")
            if approval["status"] != "pending":
                raise ButlerStateError("approval has already been decided")
            approval = persist_approval(conn, approval_id, approved=approved, response=response)
            case = self._case(conn, approval["task_id"])
            if not approved:
                validate_transition(case["status"], "blocked")
                update_task(conn, case["id"], status="blocked")
            append_event(
                conn,
                case["id"],
                "approval_resolved",
                "用户已确认" if approved else "用户拒绝了此操作",
                payload={"approval_id": approval_id, "approved": approved, "response": response},
            )
            return approval

        return self._with_connection(resolve)

    def begin_implementation(self, case_id: str) -> dict:
        def begin(conn):
            case = self._case(conn, case_id)
            if pending_approvals(conn, case_id):
                raise ButlerStateError("approval is required before implementation")
            validate_transition(case["status"], "implementing")
            case = update_task(conn, case_id, status="implementing", current_role="implementer")
            append_event(conn, case_id, "implementation_started", "开始执行已批准的改动", actor="implementer")
            return case

        return self._with_connection(begin)

    def record_attempt(self, case_id: str, *, action: str, result: str, learned: str) -> dict:
        if not action.strip() or not result.strip() or not learned.strip():
            raise ButlerStateError("each attempt needs action, result, and learned evidence")

        def record(conn):
            case = self._case(conn, case_id)
            if case["status"] != "investigating":
                raise ButlerStateError("attempts can only be recorded while investigating")
            count = case["attempt_count"] + (1 if result == "failed" else 0)
            target_status = "blocked" if result == "failed" and count >= 3 else "investigating"
            if target_status != case["status"]:
                validate_transition(case["status"], target_status)
            case = update_task(conn, case_id, attempt_count=count, status=target_status)
            append_event(
                conn,
                case_id,
                "attempt_recorded",
                "已记录一次调查或修复尝试",
                actor=case["current_role"] or "debugger",
                payload={"action": action, "result": result, "learned": learned, "attempt_count": count},
            )
            if target_status == "blocked":
                append_event(conn, case_id, "blocked", "连续三次未通过，已停止继续尝试")
            return case

        return self._with_connection(record)

    def resume(self, case_id: str, *, direction: str) -> dict:
        if not direction.strip():
            raise ButlerStateError("resuming a blocked case needs explicit user direction")

        def continue_case(conn):
            case = self._case(conn, case_id)
            validate_transition(case["status"], "investigating")
            context = {**case["context"], "resume_direction": direction.strip()}
            case = update_task(conn, case_id, status="investigating", current_role="debugger", context=context)
            append_event(
                conn,
                case_id,
                "resumed",
                "用户明确要求继续处理",
                payload={"direction": direction.strip()},
            )
            return case

        return self._with_connection(continue_case)

    def record_change(self, case_id: str, *, summary: str, files: list[str]) -> dict:
        if not summary.strip() or not files:
            raise ButlerStateError("a change record needs a summary and changed files")

        def record(conn):
            case = self._case(conn, case_id)
            validate_transition(case["status"], "auditing")
            context = {
                **case["context"],
                "change": {"summary": summary.strip(), "files": list(files)},
            }
            case = update_task(conn, case_id, status="auditing", context=context)
            append_event(
                conn,
                case_id,
                "change_recorded",
                "已记录本次改动，等待审查",
                actor="implementer",
                payload=context["change"],
            )
            return case

        return self._with_connection(record)

    def record_audit(self, case_id: str, *, verdict: str, checklist: dict) -> dict:
        required_checks = {"null", "boundary", "error", "impact", "regression", "pattern"}
        if not required_checks <= set(checklist):
            missing = ", ".join(sorted(required_checks - set(checklist)))
            raise ButlerStateError(f"audit is missing checklist items: {missing}")
        if verdict != "passed":
            raise ButlerStateError("a failed audit must return to investigation instead of verification")

        def record(conn):
            case = self._case(conn, case_id)
            validate_transition(case["status"], "verifying")
            context = {**case["context"], "audit": {"verdict": verdict, "checklist": dict(checklist)}}
            case = update_task(conn, case_id, status="verifying", current_role="smoke-tester", context=context)
            append_event(
                conn,
                case_id,
                "audit_recorded",
                "审查通过，等待按原始问题验证",
                actor="auditor",
                payload=context["audit"],
            )
            return case

        return self._with_connection(record)

    def record_validation(self, case_id: str, *, passed: bool, evidence: str) -> dict:
        if not evidence.strip():
            raise ButlerStateError("validation needs evidence against the original report")

        def record(conn):
            case = self._case(conn, case_id)
            if case["status"] != "verifying":
                raise ButlerStateError("validation can only be recorded while verifying")
            context = {**case["context"], "validation": {"passed": passed, "evidence": evidence.strip()}}
            count = case["attempt_count"] if passed else case["attempt_count"] + 1
            status = "verifying" if passed else ("blocked" if count >= 3 else "investigating")
            case = update_task(conn, case_id, status=status, attempt_count=count, context=context)
            append_event(
                conn,
                case_id,
                "validation_recorded",
                "原始问题验证通过" if passed else "原始问题验证未通过，返回调查",
                actor="smoke-tester",
                payload=context["validation"],
            )
            if not passed:
                append_event(
                    conn,
                    case_id,
                    "attempt_recorded",
                    "验证失败已计入一次尝试",
                    actor="smoke-tester",
                    payload={"action": "validation", "result": "failed", "learned": evidence.strip(), "attempt_count": count},
                )
            if status == "blocked":
                append_event(conn, case_id, "blocked", "连续三次未通过，已停止继续尝试")
            return case

        return self._with_connection(record)

    def complete(self, case_id: str) -> dict:
        def finish(conn):
            case = self._case(conn, case_id)
            if "audit" not in case["context"]:
                raise ButlerStateError("audit is required before completion")
            validation = case["context"].get("validation")
            if not validation or not validation.get("passed"):
                raise ButlerStateError("validation is required before completion")
            validate_transition(case["status"], "completed")
            case = update_task(conn, case_id, status="completed")
            append_event(conn, case_id, "completed", "任务已完成并通过验证")
            return case

        return self._with_connection(finish)

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
