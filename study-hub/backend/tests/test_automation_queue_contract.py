import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from endpoints.automation import _queue_task_dto
import endpoints.automation as automation


def test_queue_dto_has_machine_progress_and_stable_title_for_each_state():
    for status in ('pending', 'extracting', 'summarizing', 'importing', 'done', 'error'):
        dto = _queue_task_dto({
            'task_id': status,
            'module_id': 'douyin-summary',
            'module_name': 'Douyin summary',
            'status': status,
            'progress': '完成' if status == 'done' else '正在处理',
            'result': None,
        })
        assert dto['task_id'] == status
        assert dto['title'] == 'Douyin summary'
        assert dto['module_name'] == 'Douyin summary'
        assert isinstance(dto['progress'], (int, float))
        assert isinstance(dto['progress_text'], str)

    assert _queue_task_dto({
        'task_id': 'done',
        'module_id': 'douyin-summary',
        'module_name': 'Douyin summary',
        'status': 'done',
        'progress': '完成',
        'result': {'title': 'Finished title'},
    })['title'] == 'Finished title'


def test_queue_dto_exposes_a_stable_code_and_safe_reason_for_failed_parser_tasks():
    dto = _queue_task_dto({
        'task_id': 'failed-parser-task',
        'module_id': 'douyin-summary',
        'module_name': 'Douyin summary',
        'status': 'error',
        'current_step': 'summarize',
        'error': 'Claude request timed out after 480 seconds; token=secret-value',
        'result': None,
    })

    assert dto['error_code'] == 'PARSER-2001'
    assert dto['error'] == 'Claude request timed out after 480 seconds; token=[redacted]'


def test_queue_step_transitions_update_public_status():
    task_id = 'state-transition-test'
    automation._tasks[task_id] = {
        'task_id': task_id,
        'status': 'extracting',
        'steps': [],
    }
    try:
        automation._update_step(task_id, 'summarize', 'running', 'summarizing')
        assert automation._tasks[task_id]['status'] == 'summarizing'

        automation._update_step(task_id, 'import', 'running', 'importing')
        assert automation._tasks[task_id]['status'] == 'importing'
    finally:
        automation._tasks.pop(task_id, None)


def test_worker_records_a_summary_failure_code_and_a_redacted_reason(monkeypatch):
    task_id = f"error-code-contract-{uuid.uuid4().hex}"
    source_key = f"douyin:worker-error-{task_id}"
    monkeypatch.setattr(automation, "_extract_douyin_raw", lambda *_args, **_kwargs: {
        "platform": "Douyin", "title": "Failure contract", "video_id": f"worker-error-{task_id}",
    })
    monkeypatch.setattr(automation, "_run_claude", lambda *_args, **_kwargs: {
        "error": "Summary provider unavailable; token=secret-value",
    })
    monkeypatch.setattr(automation, "_cleanup_tutorial_workspace", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(automation, "_task_to_db", lambda *_args, **_kwargs: None)
    automation._tasks[task_id] = {
        "task_id": task_id,
        "module_id": "douyin-summary",
        "module_name": "Douyin summary",
        "input": f"https://v.douyin.com/{task_id}/",
        "status": "pending",
        "progress": "queued",
        "include_tutorial": False,
    }

    try:
        automation._process_single_task(task_id)
        task = automation._tasks[task_id]
        assert task["status"] == "error"
        assert task["error_code"] == "PARSER-2001"
        assert task["error"] == "Summary provider unavailable; token=[redacted]"
    finally:
        automation._tasks.pop(task_id, None)
        conn = automation.get_db()
        conn.execute("DELETE FROM document_source_claims WHERE source = ? AND source_key = ?", ("douyin-summary", source_key))
        conn.execute("DELETE FROM documents WHERE source_key = ?", (source_key,))
        conn.commit()
        conn.close()


def test_asr_fallback_errors_have_stable_parser_codes():
    assert automation._asr_error_code("火山引擎 ASR 失败: 200") == "PARSER-ASR-2001"
    assert automation._asr_error_code("DASHSCOPE_API_KEY 未配置，请在 .env 中设置") == "PARSER-ASR-1001"
    assert automation._asr_error_code("视频无语音或语音过短，无法识别") == "PARSER-ASR-2004"


def test_douyin_parse_retries_once_after_volcengine_asr_200(monkeypatch):
    attempts = []
    retry_notices = []

    def extract(*args, **kwargs):
        attempts.append((args, kwargs))
        if len(attempts) == 1:
            return {"asr_error": "火山引擎 ASR 失败: 200"}
        return {"asr_text": "第二次识别成功"}

    monkeypatch.setattr(automation, "_extract_douyin_raw", extract)

    raw = automation._extract_douyin_with_asr_200_retry(
        "https://v.douyin.com/example/",
        "retry-task",
        True,
        on_retry=lambda: retry_notices.append("retrying"),
    )

    assert len(attempts) == 2
    assert retry_notices == ["retrying"]
    assert raw["asr_text"] == "第二次识别成功"
    assert raw["asr_auto_retry_attempted"] is True
