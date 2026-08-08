import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database
from endpoints import upload


def test_document_page_reaches_all_active_documents_in_stable_order():
    conn = database.get_db()
    conn.execute("DELETE FROM documents WHERE title LIKE 'pagination-contract-%'")
    for offset in range(53):
        conn.execute(
            "INSERT INTO documents (title, content, source, document_status, created_at) VALUES (?, 'body', 'upload', 'active', ?)",
            (f"pagination-contract-{offset}", "2026-08-01 10:00:00" if offset < 3 else f"2026-08-01 09:{offset:02d}:00"),
        )
    conn.execute("INSERT INTO documents (title, content, source, document_status, created_at) VALUES ('pagination-contract-archived', 'body', 'upload', 'archived_duplicate', '2026-08-02 10:00:00')")
    conn.commit()
    conn.close()

    first = upload.list_document_page(page_size=50)
    second = upload.list_document_page(page_size=50, cursor=first["next_cursor"])
    items = first["items"] + second["items"]

    assert first["total"] == 53
    assert len(items) == len({item["id"] for item in items}) == 53
    assert first["next_cursor"] is not None
    assert second["next_cursor"] is None
    assert [item["title"] for item in first["items"][:3]] == ["pagination-contract-2", "pagination-contract-1", "pagination-contract-0"]


def test_document_page_keeps_the_selected_category_filter():
    conn = database.get_db()
    conn.execute("DELETE FROM documents WHERE title LIKE 'pagination-category-contract-%'")
    conn.execute("INSERT INTO documents (title, content, source, category_id, document_status) VALUES ('pagination-category-contract-match', 'body', 'upload', 991, 'active')")
    conn.execute("INSERT INTO documents (title, content, source, category_id, document_status) VALUES ('pagination-category-contract-other', 'body', 'upload', 992, 'active')")
    conn.commit()
    conn.close()

    page = upload.list_document_page(page_size=50, category_id=991)

    conn = database.get_db()
    conn.execute("DELETE FROM documents WHERE title LIKE 'pagination-category-contract-%'")
    conn.commit()
    conn.close()
    assert page["total"] == 1
    assert [item["title"] for item in page["items"]] == ["pagination-category-contract-match"]
