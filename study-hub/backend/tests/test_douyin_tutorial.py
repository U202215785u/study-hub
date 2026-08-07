import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database
from endpoints import automation


def test_tutorial_option_changes_input_hash():
    assert automation._input_hash("https://v.douyin.com/example", False) != automation._input_hash(
        "https://v.douyin.com/example", True
    )


def test_split_marked_model_output_keeps_summary_and_tutorial_separate():
    content = """# A summary

核心内容

<!-- TUTORIAL_START -->
## 操作步骤

1. 第一步
<!-- TUTORIAL_END -->
"""

    result = automation._split_summary_tutorial(content, include_tutorial=True)

    assert result == {
        "summary": "# A summary\n\n核心内容",
        "tutorial": "## 操作步骤\n\n1. 第一步",
        "status": "ready",
        "reason": "",
    }


def test_tutorial_parse_failure_keeps_summary_available():
    result = automation._split_summary_tutorial("# Summary\n\n仍可阅读", include_tutorial=True)

    assert result["summary"] == "# Summary\n\n仍可阅读"
    assert result["tutorial"] == ""
    assert result["status"] == "failed"


def test_task_persistence_round_trips_include_tutorial():
    task = {
        "task_id": "task-tutorial",
        "module_id": "douyin-summary",
        "module_name": "抖音摘要",
        "input": "https://v.douyin.com/example",
        "include_tutorial": True,
        "status": "pending",
    }

    automation._task_to_db(task)
    row = database.get_db().execute(
        "SELECT include_tutorial, input_hash FROM task_queue WHERE task_id = ?",
        ("task-tutorial",),
    ).fetchone()

    assert row["include_tutorial"] == 1
    assert row["input_hash"] == automation._input_hash(task["input"], True)


def test_parse_options_are_read_as_tutorial_request():
    parse_options = json.dumps({"include_tutorial": True})

    assert automation._include_tutorial_from_options(parse_options) is True


def test_douyin_prompt_requires_single_marked_summary_and_tutorial_output():
    prompt = automation._build_deep_prompt(
        "douyin-summary",
        {"platform": "抖音", "title": "标题", "url": "https://douyin.example", "tutorial_frames": ["/tutorial-frames/task/01.jpg"]},
        "https://v.douyin.com/example",
        include_tutorial=True,
    )

    assert "<!-- TUTORIAL_START -->" in prompt
    assert "<!-- TUTORIAL_END -->" in prompt
    assert "/tutorial-frames/task/01.jpg" in prompt


def test_reparse_preserves_original_tutorial_option(monkeypatch):
    conn = database.get_db()
    cur = conn.execute(
        "INSERT INTO documents (title, content, source, parse_options) VALUES (?, ?, ?, ?)",
        (
            "抖音旧文档",
            "来源：https://v.douyin.com/example",
            "douyin-summary",
            json.dumps({"include_tutorial": True}),
        ),
    )
    doc_id = cur.lastrowid
    conn.commit()
    conn.close()

    submitted = []
    monkeypatch.setattr(automation._executor, "submit", lambda _fn, task_id: submitted.append(task_id))

    result = automation.reparse_document(doc_id)

    assert result["status"] == "queued"
    assert submitted == [result["task_id"]]
    assert automation._tasks[result["task_id"]]["include_tutorial"] is True
