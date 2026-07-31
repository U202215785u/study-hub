import database
import pytest


def _investigating_case(runtime, task_type, description, role):
    case = runtime.open_case(task_type=task_type, description=description)
    runtime.record_context(case["id"], project_index_hits=[], owner_files=[])
    return runtime.assign(case["id"], role=role)


def _complete_code_case(runtime, case):
    runtime.begin_implementation(case["id"])
    runtime.record_change(case["id"], summary="最小修复", files=["frontend/src/views/Home.vue"])
    runtime.record_audit(
        case["id"], verdict="passed",
        checklist={key: "passed" for key in ("null", "boundary", "error", "impact", "regression", "pattern")},
    )
    runtime.record_validation(case["id"], passed=True, evidence="用户报告的现象不再出现")
    return runtime.complete(case["id"])


def test_bug_flow_keeps_the_debug_repair_audit_and_validation_chain():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _investigating_case(runtime, "bug", "解析工作台的提交按钮点击后无反应", "debugger")
    runtime.assign(case["id"], role="debugger", experts=["frontend-expert", "backend-expert"])
    runtime.record_attempt(case["id"], action="复现并读取请求结果", result="passed", learned="前后两侧都需要排查")

    completed = _complete_code_case(runtime, case)

    assert completed["status"] == "completed"
    assert {"debugger", "implementer", "auditor", "smoke-tester"} <= {
        event["actor"] for event in runtime.events(case["id"])
    }


def test_high_risk_change_stays_awaiting_confirmation_before_implementation():
    from butler.runtime import ButlerRuntime
    from butler.models import ButlerStateError

    runtime = ButlerRuntime(database.get_db)
    case = _investigating_case(runtime, "change", "删除旧的部署数据", "product-manager")
    runtime.assign(case["id"], role="architect", experts=["deploy-expert"])
    approval = runtime.request_approval(case["id"], risk_kind="data", summary="将删除旧的部署数据")

    with pytest.raises(ButlerStateError, match="approval"):
        runtime.begin_implementation(case["id"])
    runtime.resolve_approval(approval["id"], approved=True, response="确认")

    assert _complete_code_case(runtime, case)["status"] == "completed"


def test_research_case_completes_with_a_recorded_report_and_source_evidence():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _investigating_case(runtime, "research", "研究外部自动化方案", "explorer")

    report = runtime.record_report(
        case["id"], summary="比较了三个方案并给出适配结论", evidence_type="research_source", location="https://example.test/plan"
    )

    assert report["status"] == "verifying"
    assert runtime.complete(case["id"])["status"] == "completed"
    assert runtime.events(case["id"])[-1]["type"] == "completed"


def test_health_check_and_deploy_keep_separate_report_and_validation_gates():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    health = _investigating_case(runtime, "health_check", "做一次项目健康检查", "caretaker")
    runtime.record_report(health["id"], summary="六项检查均有结论", evidence_type="health_report")
    assert runtime.complete(health["id"])["status"] == "completed"

    deploy = _investigating_case(runtime, "deploy", "部署后检查核心流程", "smoke-tester")
    runtime.record_report(deploy["id"], summary="环境检查通过", evidence_type="deploy_report")
    runtime.record_validation(deploy["id"], passed=True, evidence="核心流程可用")
    assert runtime.complete(deploy["id"])["status"] == "completed"


def test_memory_update_remains_draft_only_until_a_real_write_is_reported():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _investigating_case(runtime, "memory_update", "记下解析工作台的验证方式", "butler")
    draft = runtime.create_memory_draft(
        case["id"], target_path="project-memory/automation/问题.md", content="验证解析进度"
    )
    runtime.resolve_memory_draft(draft["id"], approved=True, response="确认")
    runtime.record_report(
        case["id"], summary="用户确认后的内容已由执行者写入", evidence_type="memory_write", location=draft["target_path"]
    )

    assert runtime.complete(case["id"])["status"] == "completed"


def test_user_can_cancel_or_block_an_active_case_with_a_human_readable_reason():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    blocked = _investigating_case(runtime, "bug", "保存失败", "debugger")
    assert runtime.block(blocked["id"], reason="等待可复现步骤")["status"] == "blocked"

    cancelled = _investigating_case(runtime, "change", "增加筛选", "product-manager")
    assert runtime.cancel(cancelled["id"], reason="用户暂不继续")["status"] == "cancelled"
