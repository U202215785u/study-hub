"""Back up and reconcile knowledge-base duplicates after explicit approval."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from database import DB_PATH, get_db
from knowledge_reconciliation import archive_duplicates, build_reconciliation_report


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _write_report(report: dict, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"reconciliation-{_timestamp()}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="perform reversible archival")
    parser.add_argument("--approved-report", help="reviewed report JSON containing approved_source_keys")
    args = parser.parse_args()
    if args.apply and not args.approved_report:
        parser.error("--apply requires --approved-report")

    conn = get_db()
    report = build_reconciliation_report(conn)
    data_dir = Path(DB_PATH).parent
    operations_dir = data_dir / "operations"
    result = {"dry_run": not args.apply, "report": report}

    if args.apply:
        approved = json.loads(Path(args.approved_report).read_text(encoding="utf-8"))
        keys = set(approved.get("approved_source_keys", []))
        if not keys:
            parser.error("approved report does not contain approved_source_keys")
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"database integrity check failed: {integrity}")
        backup_dir = data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"study_hub-before-reconciliation-{_timestamp()}.db"
        conn.close()
        shutil.copy2(DB_PATH, backup_path)
        conn = get_db()
        result["backup_path"] = str(backup_path)
        result["manifest"] = archive_duplicates(conn, keys)
        vector_errors = []
        try:
            from processing.vector_store import get_vector_store

            vector_store = get_vector_store()
            for group in result["manifest"]:
                for document_id in group["archived_ids"]:
                    try:
                        existing = vector_store.collection.get(where={"doc_id": document_id})
                        if existing and existing["ids"]:
                            vector_store.collection.delete(ids=existing["ids"])
                    except Exception as exc:
                        vector_errors.append({"document_id": document_id, "error": str(exc)[:500]})
        except Exception as exc:
            vector_errors.append({"document_id": None, "error": str(exc)[:500]})
        if vector_errors:
            result["vector_errors"] = vector_errors

    conn.close()
    report_path = _write_report(result, operations_dir)
    print(json.dumps({"report_path": str(report_path), **result}, ensure_ascii=False))
    return 2 if result.get("vector_errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
