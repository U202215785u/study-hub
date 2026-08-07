"""MCP adapter for the persistent Butler runtime."""

from __future__ import annotations

import json
from threading import Lock

from mcp.types import TextContent, Tool

from database import get_db

from .models import ButlerStateError
from .runtime import ButlerRuntime
from .storage import initialize_butler_schema

_schema_ready = False
_schema_lock = Lock()

def _connection():
    """Provide a connection; bootstrap the additive schema once per process."""
    global _schema_ready
    conn = get_db()
    if not _schema_ready:
        with _schema_lock:
            if not _schema_ready:
                initialize_butler_schema(conn)
                _schema_ready = True
    return conn


def _runtime() -> ButlerRuntime:
    return ButlerRuntime(_connection)


_TOOL_SPECS = (
    ("butler_start_case", "开始一个 Butler 任务；默认走 simple，只有用户明确指定 complex 才进入完整协作链。", {"description": {"type": "string"}, "mode": {"type": "string", "enum": ["simple", "complex"]}, "task_type": {"type": "string"}, "feature_code": {"type": "string"}, "title": {"type": "string"}}, ("description",)),
    ("butler_finalize_case", "在一个事务中记录改动、六项审查、原始问题验证并按结果收尾。", {"case_id": {"type": "string"}, "summary": {"type": "string"}, "files": {"type": "array", "items": {"type": "string"}}, "audit": {"type": "object"}, "validation": {"type": "object"}}, ("case_id", "summary", "files", "audit", "validation")),
    ("butler_set_mode", "按用户明确选择切换当前未终止任务的处理模式。", {"case_id": {"type": "string"}, "mode": {"type": "string", "enum": ["simple", "complex"]}}, ("case_id", "mode")),
    ("butler_open_case", "登记一个项目问题、改动或检查任务。任务类型可留空或使用自然语言，管家会归类。", {"task_type": {"type": "string", "description": "可选；支持排查、调查、研究等自然语言。"}, "description": {"type": "string"}, "feature_code": {"type": "string"}, "title": {"type": "string"}}, ("description",)),
    ("butler_get_case", "读取一项管家任务的当前记录。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_list_cases", "列出尚未归档的管家任务。", {"include_archived": {"type": "boolean"}}, ()),
    ("butler_events", "读取一项任务的过程记录。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_evidence", "读取一项任务的验证和报告证据。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_next_action", "查看当前任务唯一允许的下一步。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_record_context", "记录或补充已查到的项目记忆和领域知识。", {"case_id": {"type": "string"}, "project_index_hits": {"type": "array", "items": {"type": "string"}}, "owner_files": {"type": "array", "items": {"type": "string"}}, "memory_summary": {"type": "array", "items": {"type": "string"}}, "memory_sources": {"type": "array", "items": {"type": "string"}}, "memory_freshness": {"type": "string"}, "location_notes": {"type": "array", "items": {"type": "string"}}}, ("case_id",)),
    ("butler_create_task_card", "根据已定位的任务和项目记忆生成可交给执行 Agent 的五行任务卡。", {"case_id": {"type": "string"}, "scope": {"type": "string"}, "acceptance": {"type": "string"}}, ("case_id",)),
    ("butler_get_task_card", "读取当前任务已经生成的任务卡。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_accept_task_card", "让一个执行 Agent 认领已生成的任务卡。不会自动创建会话。", {"case_id": {"type": "string"}, "agent": {"type": "string"}}, ("case_id", "agent")),
    ("butler_report_execution_result", "回收认领任务卡的执行结果；不会替代审查和验证。", {"case_id": {"type": "string"}, "agent": {"type": "string"}, "outcome": {"type": "string"}, "summary": {"type": "string"}, "evidence": {"type": "string"}, "files": {"type": "array", "items": {"type": "string"}}}, ("case_id", "agent", "outcome", "summary")),
    ("butler_recommend_experts", "按任务描述给出可采纳的领域专家建议，不自动分派。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_recommend_chain", "按任务类型给出可采纳的处理链建议，不自动启动 Agent。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_assign", "分派当前处理角色和所需领域专家。", {"case_id": {"type": "string"}, "role": {"type": "string"}, "experts": {"type": "array", "items": {"type": "string"}}}, ("case_id", "role")),
    ("butler_record_attempt", "记录一次有结果的调查或修复尝试。", {"case_id": {"type": "string"}, "action": {"type": "string"}, "result": {"type": "string"}, "learned": {"type": "string"}}, ("case_id", "action", "result", "learned")),
    ("butler_request_approval", "登记需要用户确认的受保护操作。", {"case_id": {"type": "string"}, "risk_kind": {"type": "string"}, "summary": {"type": "string"}}, ("case_id", "risk_kind", "summary")),
    ("butler_resolve_approval", "记录用户对受保护操作的确认或拒绝。", {"approval_id": {"type": "string"}, "approved": {"type": "boolean"}, "response": {"type": "string"}}, ("approval_id", "approved")),
    ("butler_begin_implementation", "在所有确认完成后开始实施。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_resume_case", "按用户明确的新方向恢复已停止的任务。", {"case_id": {"type": "string"}, "direction": {"type": "string"}}, ("case_id", "direction")),
    ("butler_block_case", "因明确原因停止当前任务。", {"case_id": {"type": "string"}, "reason": {"type": "string"}}, ("case_id", "reason")),
    ("butler_cancel_case", "按用户决定取消当前任务。", {"case_id": {"type": "string"}, "reason": {"type": "string"}}, ("case_id", "reason")),
    ("butler_record_change", "记录实际改动及其涉及文件，交给审查。", {"case_id": {"type": "string"}, "summary": {"type": "string"}, "files": {"type": "array", "items": {"type": "string"}}}, ("case_id", "summary", "files")),
    ("butler_record_audit", "记录六项审查清单的结果。", {"case_id": {"type": "string"}, "verdict": {"type": "string"}, "checklist": {"type": "object"}}, ("case_id", "verdict", "checklist")),
    ("butler_record_validation", "记录对用户原始现象的验证。", {"case_id": {"type": "string"}, "passed": {"type": "boolean"}, "evidence": {"type": "string"}}, ("case_id", "passed", "evidence")),
    ("butler_record_report", "记录研究、体检、部署或记忆更新的报告证据。", {"case_id": {"type": "string"}, "summary": {"type": "string"}, "evidence_type": {"type": "string"}, "location": {"type": "string"}}, ("case_id", "summary", "evidence_type")),
    ("butler_complete_case", "结束已完成验证的任务。", {"case_id": {"type": "string"}}, ("case_id",)),
    ("butler_create_memory_draft", "生成等待用户确认的项目记忆草稿，不会写入文件。", {"case_id": {"type": "string"}, "target_path": {"type": "string"}, "content": {"type": "string"}}, ("case_id", "target_path", "content")),
    ("butler_list_memory_drafts", "查看任务的记忆草稿。", {"case_id": {"type": "string"}}, ()),
    ("butler_resolve_memory_draft", "记录用户对记忆草稿的确认或拒绝；确认后仍需明确写入操作。", {"draft_id": {"type": "string"}, "approved": {"type": "boolean"}, "response": {"type": "string"}}, ("draft_id", "approved")),
)


def butler_tool_names() -> tuple[str, ...]:
    return tuple(spec[0] for spec in _TOOL_SPECS)


def butler_tool_definitions() -> list[Tool]:
    return [
        Tool(
            name=name,
            description=description,
            inputSchema={"type": "object", "properties": properties, "required": list(required)},
        )
        for name, description, properties, required in _TOOL_SPECS
    ]


def _result_payload(result, runtime: ButlerRuntime) -> dict:
    payload = {"status": "ok", "result": result}
    if isinstance(result, dict):
        case_id = result.get("id") or result.get("task_id")
        if case_id:
            payload["case_id"] = case_id
            try:
                payload["next_action"] = runtime.next_action(case_id)
            except ButlerStateError:
                pass
    return payload


def _error_payload(name: str, error: Exception) -> dict:
    """Describe whether a caller may continue when Butler itself is unavailable."""
    reason = str(error) or "工具参数不完整或当前任务不能执行这一步"
    protected = name in {"butler_request_approval", "butler_resolve_approval"} or "approval is required" in reason
    if protected:
        return {
            "status": "error",
            "policy": "fail_closed",
            "reason": reason,
            "continue": "这是受保护操作；在获得明确确认前不要继续执行。",
        }
    return {
        "status": "error",
        "policy": "fail_open",
        "reason": reason,
        "continue": "这是普通管家记录问题；可继续进行只读定位或常规排查，并在管家恢复后补录任务和证据。",
        "recovery": "检查参数或稍后重试 butler_open_case / 当前记录工具。",
    }


async def call_butler_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Dispatch Butler tools and return stable JSON text suitable for MCP clients."""
    args = arguments or {}
    runtime = _runtime()
    try:
        handlers = {
            "butler_start_case": lambda: runtime.start_case(description=args["description"], mode=args.get("mode", "simple"), task_type=args.get("task_type", ""), feature_code=args.get("feature_code", ""), title=args.get("title", "")),
            "butler_finalize_case": lambda: runtime.finalize_case(args["case_id"], summary=args["summary"], files=args["files"], audit=args["audit"], validation=args["validation"]),
            "butler_set_mode": lambda: runtime.set_mode(args["case_id"], mode=args["mode"]),
            "butler_open_case": lambda: runtime.open_case(task_type=args.get("task_type", ""), description=args["description"], feature_code=args.get("feature_code", ""), title=args.get("title", "")),
            "butler_get_case": lambda: runtime.get_case(args["case_id"]),
            "butler_list_cases": lambda: runtime.list_cases(include_archived=args.get("include_archived", False)),
            "butler_events": lambda: runtime.events(args["case_id"]),
            "butler_evidence": lambda: runtime.evidence(args["case_id"]),
            "butler_next_action": lambda: runtime.next_action(args["case_id"]),
            "butler_record_context": lambda: runtime.record_context(args["case_id"], project_index_hits=args.get("project_index_hits", []), owner_files=args.get("owner_files", []), memory_summary=args.get("memory_summary", []), memory_sources=args.get("memory_sources", []), memory_freshness=args.get("memory_freshness", ""), location_notes=args.get("location_notes", [])),
            "butler_create_task_card": lambda: runtime.create_task_card(args["case_id"], scope=args.get("scope", ""), acceptance=args.get("acceptance", "")),
            "butler_get_task_card": lambda: runtime.get_task_card(args["case_id"]),
            "butler_accept_task_card": lambda: runtime.accept_task_card(args["case_id"], agent=args["agent"]),
            "butler_report_execution_result": lambda: runtime.report_execution_result(args["case_id"], agent=args["agent"], outcome=args["outcome"], summary=args["summary"], evidence=args.get("evidence", ""), files=args.get("files", [])),
            "butler_recommend_experts": lambda: runtime.recommend_experts(args["case_id"]),
            "butler_recommend_chain": lambda: runtime.recommend_chain(args["case_id"]),
            "butler_assign": lambda: runtime.assign(args["case_id"], role=args["role"], experts=args.get("experts", [])),
            "butler_record_attempt": lambda: runtime.record_attempt(args["case_id"], action=args["action"], result=args["result"], learned=args["learned"]),
            "butler_request_approval": lambda: runtime.request_approval(args["case_id"], risk_kind=args["risk_kind"], summary=args["summary"]),
            "butler_resolve_approval": lambda: runtime.resolve_approval(args["approval_id"], approved=args["approved"], response=args.get("response", "")),
            "butler_begin_implementation": lambda: runtime.begin_implementation(args["case_id"]),
            "butler_resume_case": lambda: runtime.resume(args["case_id"], direction=args["direction"]),
            "butler_block_case": lambda: runtime.block(args["case_id"], reason=args["reason"]),
            "butler_cancel_case": lambda: runtime.cancel(args["case_id"], reason=args["reason"]),
            "butler_record_change": lambda: runtime.record_change(args["case_id"], summary=args["summary"], files=args["files"]),
            "butler_record_audit": lambda: runtime.record_audit(args["case_id"], verdict=args["verdict"], checklist=args["checklist"]),
            "butler_record_validation": lambda: runtime.record_validation(args["case_id"], passed=args["passed"], evidence=args["evidence"]),
            "butler_record_report": lambda: runtime.record_report(args["case_id"], summary=args["summary"], evidence_type=args["evidence_type"], location=args.get("location", "")),
            "butler_complete_case": lambda: runtime.complete(args["case_id"]),
            "butler_create_memory_draft": lambda: runtime.create_memory_draft(args["case_id"], target_path=args["target_path"], content=args["content"]),
            "butler_list_memory_drafts": lambda: runtime.list_memory_drafts(case_id=args.get("case_id")),
            "butler_resolve_memory_draft": lambda: runtime.resolve_memory_draft(args["draft_id"], approved=args["approved"], response=args.get("response", "")),
        }
        if name not in handlers:
            raise ButlerStateError(f"unknown Butler tool: {name}")
        payload = _result_payload(handlers[name](), runtime)
    except (ButlerStateError, KeyError, TypeError, ValueError) as exc:
        payload = _error_payload(name, exc)
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, default=list))]
