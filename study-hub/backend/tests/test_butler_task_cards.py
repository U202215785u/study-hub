import asyncio
import json

import database
import pytest


def _located_case(runtime):
    case = runtime.open_case(
        task_type="bug",
        title="解析提交后转圈",
        description="点击提交后页面持续显示加载，用户无法继续。",
        feature_code="PARSER-WORKBENCH",
    )
    return runtime.record_context(
        case["id"],
        project_index_hits=["解析工作台的提交状态由前端请求结果决定"],
        owner_files=[".agents/owners/frontend-owner.md"],
        memory_summary=["此前同类问题需要先核对请求结果"],
        location_notes=["提交按钮的请求状态待查"],
    )


def test_task_card_uses_verified_project_memory_and_keeps_five_compact_lines():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _located_case(runtime)

    card = runtime.create_task_card(
        case["id"],
        scope="只处理提交流程，不改其他页面。",
        acceptance="提交后显示结果或清晰错误，不再无限转圈。",
    )

    assert card["text"] == "\n".join(
        (
            "【任务】解析提交后转圈",
            "【已知】点击提交后页面持续显示加载，用户无法继续。",
            "【定位】功能代号：PARSER-WORKBENCH；项目记忆：此前同类问题需要先核对请求结果；定位记录：解析工作台的提交状态由前端请求结果决定；相关文件：.agents/owners/frontend-owner.md；补充线索：提交按钮的请求状态待查",
            "【范围】只处理提交流程，不改其他页面。",
            "【验收】提交后显示结果或清晰错误，不再无限转圈。",
        )
    )
    assert runtime.get_task_card(case["id"]) == card
    assert runtime.events(case["id"])[-1]["type"] == "task_card_created"


def test_task_card_requires_context_before_handoff():
    from butler.models import ButlerStateError
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = runtime.open_case(task_type="bug", description="保存失败")

    with pytest.raises(ButlerStateError, match="context"):
        runtime.create_task_card(case["id"], scope="只处理保存", acceptance="保存成功或显示错误")


def test_task_card_marks_missing_details_as_pending_instead_of_inventing_them():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = runtime.open_case(task_type="bug", description="保存失败")
    runtime.record_context(case["id"], project_index_hits=[], owner_files=[])

    card = runtime.create_task_card(case["id"])

    assert card["text"].splitlines() == [
        "【任务】保存失败",
        "【已知】保存失败",
        "【定位】待查",
        "【范围】待查",
        "【验收】待查",
    ]


def test_mcp_creates_and_reads_the_persisted_task_card():
    from butler.mcp_tools import call_butler_tool
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _located_case(runtime)

    created = asyncio.run(
        call_butler_tool(
            "butler_create_task_card",
            {
                "case_id": case["id"],
                "scope": "只处理提交流程，不改其他页面。",
                "acceptance": "提交后显示结果或清晰错误，不再无限转圈。",
            },
        )
    )
    created_payload = json.loads(created[0].text)
    read = asyncio.run(call_butler_tool("butler_get_task_card", {"case_id": case["id"]}))
    read_payload = json.loads(read[0].text)

    assert created_payload["result"]["text"].startswith("【任务】解析提交后转圈")
    assert read_payload["result"] == created_payload["result"]


def test_task_card_keeps_a_memory_snapshot_with_sources_and_freshness():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = runtime.open_case(task_type="bug", description="ASR 识别失败")
    runtime.record_context(
        case["id"],
        project_index_hits=["识别服务调用供应商 API"],
        owner_files=["backend/services/asr.py"],
        memory_summary=["HTTP 200 仍需读取业务错误码"],
        memory_sources=["project-memory/automation/asr.md#provider-response"],
        memory_freshness="2026-08-01",
    )
    card = runtime.create_task_card(case["id"], scope="只检查 ASR 响应", acceptance="说明 200 的业务含义")

    runtime.record_context(
        case["id"],
        project_index_hits=["后续新增定位"],
        owner_files=[],
        memory_summary=[],
    )

    assert card["snapshot"]["memory_sources"] == ["project-memory/automation/asr.md#provider-response"]
    assert card["snapshot"]["memory_freshness"] == "2026-08-01"
    assert card["snapshot"]["project_index_hits"] == ["识别服务调用供应商 API"]
    assert runtime.get_task_card(case["id"])["snapshot"] == card["snapshot"]


def test_an_accepted_task_card_collects_a_result_from_the_same_agent():
    from butler.models import ButlerStateError
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _located_case(runtime)
    runtime.create_task_card(case["id"], scope="只检查提交流程", acceptance="给出根因")

    accepted = runtime.accept_task_card(case["id"], agent="asr-debugger")
    with pytest.raises(ButlerStateError, match="accepted"):
        runtime.accept_task_card(case["id"], agent="another-agent")
    report = runtime.report_execution_result(
        case["id"],
        agent="asr-debugger",
        outcome="root_cause_found",
        summary="供应商业务错误码被当成成功处理",
        evidence="响应体包含业务错误字段",
        files=["backend/services/asr.py"],
    )

    assert accepted["agent"] == "asr-debugger"
    assert report["outcome"] == "root_cause_found"
    handoff = runtime.get_case(case["id"])["context"]["task_card_handoff"]
    assert handoff["status"] == "reported"
    assert handoff["result"]["files"] == ["backend/services/asr.py"]
