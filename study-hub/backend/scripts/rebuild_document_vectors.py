"""Rebuild the derived document vector collection from active SQLite documents."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from database import get_db
from processing.chunker import chunk_text
from processing.vector_store import CHROMA_DIR, VectorStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup-dir", required=True)
    args = parser.parse_args()

    backup = Path(args.backup_dir) / f"chroma-before-document-rebuild-{datetime.now():%Y%m%d-%H%M%S}"
    shutil.copytree(CHROMA_DIR, backup)

    # Delete only the corrupt, derived document collection. Wiki and memory collections stay intact.
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    try:
        client.delete_collection("documents_zh")
    except Exception:
        # Absence is equivalent to an empty derived collection.
        pass

    store = VectorStore()
    conn = get_db()
    rows = conn.execute(
        """
        SELECT d.id, d.title, d.content, d.tags, c.name AS category_name
        FROM documents d
        LEFT JOIN categories c ON c.id = d.category_id
        WHERE d.document_status = 'active'
        ORDER BY d.id
        """
    ).fetchall()
    rebuilt = 0
    for row in rows:
        chunks = chunk_text(row["content"] or "")
        store.add_document(
            row["id"], row["title"], chunks,
            category=row["category_name"] or "", tags=row["tags"] or "",
        )
        conn.execute("UPDATE documents SET chunk_count = ?, updated_at = datetime('now') WHERE id = ?", (len(chunks), row["id"]))
        rebuilt += 1
    conn.commit()
    active_ids = {row["id"] for row in rows}
    indexed = store.collection.get(include=["metadatas"])
    indexed_doc_ids = {meta.get("doc_id") for meta in indexed.get("metadatas", [])}
    if indexed_doc_ids - active_ids:
        raise RuntimeError("rebuild indexed a document that is not active")
    print({"backup": str(backup), "rebuilt_documents": rebuilt, "indexed_documents": len(indexed_doc_ids), "chunks": store.collection.count()})
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
