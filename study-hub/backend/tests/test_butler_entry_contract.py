from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[3]


def test_workspace_contract_requires_butler_for_project_operations():
    contract = (WORKSPACE / "AGENTS.md").read_text(encoding="utf-8")
    required = (
        "mcp__study_hub__butler_open_case",
        "mcp__study_hub__butler_next_action",
        "mcp__study_hub__butler_record_context",
        "mcp__study_hub__butler_assign",
        "mcp__study_hub__butler_record_attempt",
        "mcp__study_hub__butler_request_approval",
        "mcp__study_hub__butler_record_change",
        "mcp__study_hub__butler_record_audit",
        "mcp__study_hub__butler_record_validation",
        "mcp__study_hub__butler_complete_case",
    )

    assert all(name in contract for name in required)
    assert "纯概念解释" in contract
    assert "用户不需要选择页面" in contract
    assert "尽力登记" in contract
    assert "fail-open" in contract
    assert "高影响操作" in contract


def test_butler_runtime_still_exposes_entry_and_completion_gates():
    from butler.mcp_tools import butler_tool_names

    names = set(butler_tool_names())
    assert {
        "butler_open_case",
        "butler_next_action",
        "butler_request_approval",
        "butler_record_validation",
        "butler_complete_case",
    } <= names
