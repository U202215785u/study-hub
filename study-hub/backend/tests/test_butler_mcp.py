import asyncio
import json
from pathlib import Path


def test_mcp_exposes_all_butler_lifecycle_groups():
    from butler.mcp_tools import butler_tool_names

    names = set(butler_tool_names())
    assert {
        "butler_open_case",
        "butler_next_action",
        "butler_assign",
        "butler_record_attempt",
        "butler_request_approval",
        "butler_record_validation",
        "butler_complete_case",
        "butler_create_memory_draft",
        "butler_recommend_experts",
        "butler_recommend_chain",
        "butler_accept_task_card",
        "butler_report_execution_result",
        "butler_start_case",
        "butler_finalize_case",
        "butler_set_mode",
    } <= names


def test_existing_mcp_server_registers_butler_tools_without_removing_legacy_tools():
    import mcp_server

    names = {tool.name for tool in asyncio.run(mcp_server.list_tools())}

    assert "search_knowledge_base" in names
    assert "butler_open_case" in names


def test_open_case_mcp_response_contains_case_id_and_next_action():
    from butler.mcp_tools import call_butler_tool

    content = asyncio.run(
        call_butler_tool(
            "butler_open_case", {"task_type": "bug", "description": "保存失败"}
        )
    )

    payload = json.loads(content[0].text)
    assert payload["case_id"]
    assert payload["next_action"]["kind"] == "locate_context"


def test_start_case_mcp_uses_simple_path_without_a_second_next_action_call():
    from butler.mcp_tools import call_butler_tool

    content = asyncio.run(
        call_butler_tool(
            "butler_start_case", {"description": "修复保存按钮状态"}
        )
    )

    payload = json.loads(content[0].text)
    assert payload["result"]["mode"] == "simple"
    assert payload["result"]["status"] == "implementing"
    assert payload["next_action"]["kind"] == "finalize_case"


def test_finalize_case_mcp_returns_completed_case():
    from butler.mcp_tools import call_butler_tool

    started = asyncio.run(
        call_butler_tool("butler_start_case", {"description": "修复保存按钮状态"})
    )
    case_id = json.loads(started[0].text)["case_id"]
    content = asyncio.run(
        call_butler_tool(
            "butler_finalize_case",
            {
                "case_id": case_id,
                "summary": "修复保存后的状态刷新",
                "files": ["frontend/src/views/Home.vue"],
                "audit": {key: "passed" for key in ("null", "boundary", "error", "impact", "regression", "pattern")},
                "validation": {"passed": True, "evidence": "回归测试通过"},
            },
        )
    )

    payload = json.loads(content[0].text)
    assert payload["result"]["status"] == "completed"


def test_set_mode_mcp_changes_only_the_requested_case():
    from butler.mcp_tools import call_butler_tool

    started = asyncio.run(
        call_butler_tool("butler_start_case", {"description": "显式切换复杂逻辑"})
    )
    case_id = json.loads(started[0].text)["case_id"]
    content = asyncio.run(
        call_butler_tool("butler_set_mode", {"case_id": case_id, "mode": "complex"})
    )

    assert json.loads(content[0].text)["result"]["mode"] == "complex"


def test_mcp_approval_can_be_requested_from_simple_implementation():
    from butler.mcp_tools import call_butler_tool

    started = asyncio.run(
        call_butler_tool("butler_start_case", {"description": "启动本机任务板服务"})
    )
    started_payload = json.loads(started[0].text)
    case_id = started_payload["case_id"]

    requested = asyncio.run(
        call_butler_tool(
            "butler_request_approval",
            {
                "case_id": case_id,
                "risk_kind": "local_service",
                "summary": "启动本机任务板服务并验证快捷方式",
            },
        )
    )
    approval_payload = json.loads(requested[0].text)
    approval_id = approval_payload["result"]["id"]

    resolved = asyncio.run(
        call_butler_tool(
            "butler_resolve_approval",
            {"approval_id": approval_id, "approved": True, "response": "允许"},
        )
    )
    assert json.loads(resolved[0].text)["result"]["status"] == "approved"

    begun = asyncio.run(call_butler_tool("butler_begin_implementation", {"case_id": case_id}))
    assert json.loads(begun[0].text)["result"]["status"] == "implementing"


def test_mcp_returns_a_readable_error_without_a_stack_trace():
    from butler.mcp_tools import call_butler_tool

    content = asyncio.run(call_butler_tool("butler_no_such_action", {}))

    payload = json.loads(content[0].text)
    assert payload["status"] == "error"
    assert "Traceback" not in payload["reason"]


def test_mcp_normal_task_errors_are_explicitly_fail_open_but_approval_errors_are_fail_closed():
    from butler.mcp_tools import call_butler_tool

    ordinary = asyncio.run(call_butler_tool("butler_open_case", {"task_type": "???", "description": ""}))
    protected = asyncio.run(call_butler_tool("butler_request_approval", {}))

    ordinary_payload = json.loads(ordinary[0].text)
    protected_payload = json.loads(protected[0].text)
    assert ordinary_payload["policy"] == "fail_open"
    assert ordinary_payload["continue"]
    assert protected_payload["policy"] == "fail_closed"


def test_mcp_recommends_experts_and_exposes_task_card_handoff_actions():
    from butler.mcp_tools import call_butler_tool

    opened = asyncio.run(
        call_butler_tool(
            "butler_open_case",
            {"task_type": "investigate", "description": "火山引擎 ASR 返回 200 但识别失败"},
        )
    )
    case_id = json.loads(opened[0].text)["case_id"]
    recommended = asyncio.run(call_butler_tool("butler_recommend_experts", {"case_id": case_id}))

    assert json.loads(recommended[0].text)["result"]["experts"] == ["automation-expert"]


def test_canonical_butler_skill_requires_a_runtime_case_before_project_work():
    workspace = Path(__file__).resolve().parents[3]
    content = (workspace / ".claude" / "skills" / "butler" / "SKILL.md").read_text(encoding="utf-8")

    assert "butler_open_case" in content
    assert "butler_next_action" in content
    assert "butler_create_task_card" in content
    assert "butler_get_task_card" in content
    assert "butler_record_validation" in content
