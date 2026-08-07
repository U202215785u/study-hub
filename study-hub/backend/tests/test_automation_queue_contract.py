import os
import sys

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
