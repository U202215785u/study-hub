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


def test_mcp_returns_a_readable_error_without_a_stack_trace():
    from butler.mcp_tools import call_butler_tool

    content = asyncio.run(call_butler_tool("butler_no_such_action", {}))

    payload = json.loads(content[0].text)
    assert payload["status"] == "error"
    assert "Traceback" not in payload["reason"]


def test_canonical_butler_skill_requires_a_runtime_case_before_project_work():
    workspace = Path(__file__).resolve().parents[3]
    content = (workspace / ".claude" / "skills" / "butler" / "SKILL.md").read_text(encoding="utf-8")

    assert "butler_open_case" in content
    assert "butler_next_action" in content
    assert "butler_create_task_card" in content
    assert "butler_get_task_card" in content
    assert "butler_record_validation" in content
