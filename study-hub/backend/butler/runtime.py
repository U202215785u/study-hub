"""State-machine service for persistent Study-Hub Butler cases."""

from __future__ import annotations

from uuid import uuid4

from .catalog import EXTERNAL_EXPERTS, INTERNAL_ROLES
from .models import TASK_TYPES, ButlerStateError, validate_transition
from .storage import (
    append_event,
    create_approval,
    create_evidence,
    create_memory_draft as persist_memory_draft,
    create_task,
    list_events,
    list_evidence,
    list_memory_drafts as persisted_memory_drafts,
    list_tasks,
    pending_approvals,
    read_approval,
    read_memory_draft,
    read_task,
    resolve_approval as persist_approval,
    resolve_memory_draft as persist_memory_draft_resolution,
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
            if case["status"] == "located":
                validate_transition(case["status"], "investigating")
            elif case["status"] != "investigating":
                raise ButlerStateError("roles can only be assigned after context is located")
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

    def evidence(self, case_id: str) -> list[dict]:
        return self._with_connection(lambda conn: (self._case(conn, case_id), list_evidence(conn, case_id))[1])

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

    def block(self, case_id: str, *, reason: str) -> dict:
        if not reason.strip():
            raise ButlerStateError("blocking a case needs a human-readable reason")

        def stop(conn):
            case = self._case(conn, case_id)
            validate_transition(case["status"], "blocked")
            case = update_task(conn, case_id, status="blocked")
            append_event(conn, case_id, "blocked", "任务已停止，等待新的用户决定", payload={"reason": reason.strip()})
            return case

        return self._with_connection(stop)

    def cancel(self, case_id: str, *, reason: str) -> dict:
        if not reason.strip():
            raise ButlerStateError("cancelling a case needs a human-readable reason")

        def stop(conn):
            case = self._case(conn, case_id)
            validate_transition(case["status"], "cancelled")
            case = update_task(conn, case_id, status="cancelled")
            append_event(conn, case_id, "cancelled", "任务已按用户决定取消", payload={"reason": reason.strip()})
            return case

        return self._with_connection(stop)

    def record_report(self, case_id: str, *, summary: str, evidence_type: str, location: str = "") -> dict:
        if not summary.strip() or not evidence_type.strip():
            raise ButlerStateError("a report needs a summary and evidence type")

        def record(conn):
            case = self._case(conn, case_id)
            if case["task_type"] not in {"research", "health_check", "deploy", "memory_update"}:
                raise ButlerStateError("reports can only complete a non-code task")
            if case["status"] != "investigating":
                raise ButlerStateError("a report can only be recorded while investigating")
            if case["task_type"] == "memory_update":
                drafts = persisted_memory_drafts(conn, task_id=case_id)
                if not any(draft["status"] == "approved" for draft in drafts):
                    raise ButlerStateError("memory update needs an approved memory draft before reporting a write")
            validate_transition(case["status"], "verifying")
            evidence = create_evidence(
                conn,
                {
                    "task_id": case_id,
                    "evidence_type": evidence_type.strip(),
                    "summary": summary.strip(),
                    "location": location.strip(),
                },
            )
            context = {**case["context"], "report": {"summary": summary.strip(), "evidence_id": evidence["id"]}}
            case = update_task(conn, case_id, status="verifying", context=context)
            append_event(
                conn,
                case_id,
                "report_recorded",
                "已记录任务报告，等待完成条件核验",
                actor=case["current_role"] or "butler",
                payload={"evidence_id": evidence["id"], "evidence_type": evidence_type.strip(), "location": location.strip()},
            )
            return case

        return self._with_connection(record)

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
            no_code_task = case["task_type"] in {"research", "health_check", "deploy", "memory_update"}
            if no_code_task:
                if "report" not in case["context"]:
                    raise ButlerStateError("a recorded report is required before completion")
                validation = case["context"].get("validation")
                if case["task_type"] == "deploy" and (not validation or not validation.get("passed")):
                    raise ButlerStateError("deployment validation is required before completion")
            else:
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

    def create_memory_draft(self, case_id: str, *, target_path: str, content: str) -> dict:
        if not target_path.strip() or not content.strip():
            raise ButlerStateError("a memory draft needs a target path and proposed content")

        def create(conn):
            self._case(conn, case_id)
            draft = persist_memory_draft(
                conn,
                {
                    "id": uuid4().hex,
                    "task_id": case_id,
                    "target_path": target_path.strip(),
                    "content": content.strip(),
                    "status": "pending",
                },
            )
            append_event(
                conn,
                case_id,
                "memory_draft_created",
                "已生成记忆草稿，等待用户确认后再写入",
                payload={"draft_id": draft["id"], "target_path": draft["target_path"]},
            )
            return draft

        return self._with_connection(create)

    def list_memory_drafts(self, *, case_id: str | None = None) -> list[dict]:
        def list_for_case(conn):
            if case_id is not None:
                self._case(conn, case_id)
            return persisted_memory_drafts(conn, task_id=case_id)

        return self._with_connection(list_for_case)

    def resolve_memory_draft(self, draft_id: str, *, approved: bool, response: str = "") -> dict:
        def resolve(conn):
            draft = read_memory_draft(conn, draft_id)
            if draft is None:
                raise ButlerStateError(f"unknown memory draft: {draft_id}")
            if draft["status"] != "pending":
                raise ButlerStateError("memory draft has already been decided")
            draft = persist_memory_draft_resolution(
                conn, draft_id, approved=approved, response=response
            )
            append_event(
                conn,
                draft["task_id"],
                "memory_draft_resolved",
                "用户已确认记忆草稿，等待明确写入操作" if approved else "用户拒绝写入这份记忆草稿",
                payload={
                    "draft_id": draft_id,
                    "approved": approved,
                    "response": response,
                    "requested_operation": (
                        {"kind": "write_memory", "target_path": draft["target_path"], "content": draft["content"]}
                        if approved else None
                    ),
                },
            )
            return draft

        return self._with_connection(resolve)

    def next_action(self, case_id: str) -> dict:
        case = self.get_case(case_id)
        non_code_task = case["task_type"] in {"research", "health_check", "deploy", "memory_update"}
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
                "kind": "record_report" if non_code_task else "record_attempt",
                "required": ("summary", "evidence_type") if non_code_task else ("action", "result", "learned"),
                "summary": "记录任务报告及其证据。" if non_code_task else "记录一次有证据的调查或最小修复尝试。",
            },
            "awaiting_approval": {
                "kind": "resolve_approval",
                "required": ("approval_id", "approved"),
                "summary": "等待用户确认或拒绝受保护的操作。",
            },
            "implementing": {
                "kind": "record_change",
                "required": ("summary", "files"),
                "summary": "记录实际改动和涉及文件，交给审查。",
            },
            "auditing": {
                "kind": "record_audit",
                "required": ("verdict", "checklist"),
                "summary": "填写六项审查清单后进入验证。",
            },
            "verifying": {
                "kind": "record_validation" if (not non_code_task or case["task_type"] == "deploy") else "complete_case",
                "required": ("passed", "evidence") if (not non_code_task or case["task_type"] == "deploy") else (),
                "summary": "按用户报告的原始现象完成验证。" if (not non_code_task or case["task_type"] == "deploy") else "报告证据已记录，可以结束任务。",
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
