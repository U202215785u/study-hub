import pytest


def test_every_existing_butler_task_type_has_a_complete_chain():
    from butler.catalog import TASK_CHAINS

    assert set(TASK_CHAINS) == {
        "bug",
        "change",
        "research",
        "health_check",
        "deploy",
        "memory_update",
    }
    assert TASK_CHAINS["bug"] == (
        "butler",
        "debugger",
        "experts",
        "implementer",
        "auditor",
        "smoke-tester",
    )


def test_frontend_and_backend_symptom_routes_to_both_experts():
    from butler.catalog import resolve_experts

    assert resolve_experts("页面保存后服务返回失败") == (
        "frontend-expert",
        "backend-expert",
    )


def test_terminal_status_has_no_outgoing_transition():
    from butler.models import ButlerStateError, validate_transition

    with pytest.raises(ButlerStateError):
        validate_transition("completed", "implementing")
