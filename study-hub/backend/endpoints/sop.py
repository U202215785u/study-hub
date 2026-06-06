"""
SOP 规范化模块 — Blocks, Chains, Suggestions, Evolution.
"""
import json
from fastapi import APIRouter
from database import get_db

router = APIRouter()

# ═══════════════════════════════════════════
# Blocks CRUD
# ═══════════════════════════════════════════

@router.get("/sop/blocks")
def list_blocks(search: str = None, tag: str = None):
    conn = get_db()
    query = "SELECT * FROM sop_blocks WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR content LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
    if tag:
        query += " AND tags LIKE ?"
        params.append(f'%"{tag}"%')
    query += " ORDER BY updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/sop/blocks/{block_id}")
def get_block(block_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM sop_blocks WHERE id = ?", (block_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": "Block not found"}
    return dict(row)


@router.post("/sop/blocks")
def create_block(payload: dict):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO sop_blocks (title, description, content, tags, source_wiki_page_id, source_type)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            payload.get("title", ""),
            payload.get("description", ""),
            payload.get("content", ""),
            json.dumps(payload.get("tags", []), ensure_ascii=False),
            payload.get("source_wiki_page_id"),
            payload.get("source_type", "manual"),
        ),
    )
    conn.commit()
    block_id = cur.lastrowid
    row = conn.execute("SELECT * FROM sop_blocks WHERE id = ?", (block_id,)).fetchone()
    conn.close()
    return dict(row)


@router.put("/sop/blocks/{block_id}")
def update_block(block_id: int, payload: dict):
    conn = get_db()
    row = conn.execute("SELECT * FROM sop_blocks WHERE id = ?", (block_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Block not found"}

    fields = {}
    for key in ("title", "description", "content", "source_wiki_page_id"):
        if key in payload:
            fields[key] = payload[key]
    if "tags" in payload:
        fields["tags"] = json.dumps(payload["tags"], ensure_ascii=False)
    if fields:
        fields["updated_at"] = None  # will use CURRENT_TIMESTAMP via below
        sets = ", ".join(f"{k} = ?" for k in fields.keys())
        vals = list(fields.values())
        # restore updated_at to actual CURRENT_TIMESTAMP
        sets = sets.replace("updated_at = ?", "updated_at = CURRENT_TIMESTAMP")
        vals = [v for k, v in zip(fields.keys(), vals) if k != "updated_at"]
        conn.execute(f"UPDATE sop_blocks SET {sets} WHERE id = ?", vals + [block_id])
        conn.commit()
    conn.close()
    return {"status": "ok"}


@router.delete("/sop/blocks/{block_id}")
def delete_block(block_id: int):
    conn = get_db()
    conn.execute("DELETE FROM sop_blocks WHERE id = ?", (block_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ═══════════════════════════════════════════
# Chains CRUD
# ═══════════════════════════════════════════

@router.get("/sop/chains")
def list_chains():
    conn = get_db()
    rows = conn.execute(
        """SELECT c.*, COUNT(cb.id) as block_count
           FROM sop_chains c
           LEFT JOIN sop_chain_blocks cb ON cb.chain_id = c.id
           GROUP BY c.id
           ORDER BY c.updated_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/sop/chains/{chain_id}")
def get_chain(chain_id: int):
    conn = get_db()
    chain = conn.execute("SELECT * FROM sop_chains WHERE id = ?", (chain_id,)).fetchone()
    if not chain:
        conn.close()
        return {"error": "Chain not found"}

    junctions = conn.execute(
        """SELECT cb.id as cb_id, cb.sort_order, cb.parent_id, cb.branch_label,
                  b.id, b.title, b.description, b.content, b.tags,
                  b.source_wiki_page_id, b.source_type, b.created_at, b.updated_at
           FROM sop_chain_blocks cb
           JOIN sop_blocks b ON cb.block_id = b.id
           WHERE cb.chain_id = ?
           ORDER BY cb.sort_order""",
        (chain_id,),
    ).fetchall()
    conn.close()

    blocks = []
    for j in junctions:
        jd = dict(j)
        block = {
            "cb_id": jd["cb_id"],
            "sort_order": jd["sort_order"],
            "parent_id": jd["parent_id"],
            "branch_label": jd["branch_label"],
            "block": {
                "id": jd["id"],
                "title": jd["title"],
                "description": jd["description"],
                "content": jd["content"],
                "tags": jd["tags"],
                "source_wiki_page_id": jd["source_wiki_page_id"],
                "source_type": jd["source_type"],
                "created_at": jd["created_at"],
                "updated_at": jd["updated_at"],
            },
        }
        blocks.append(block)

    result = dict(chain)
    result["blocks"] = blocks
    return result


@router.post("/sop/chains")
def create_chain(payload: dict):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO sop_chains (name, description) VALUES (?, ?)",
        (payload.get("name", ""), payload.get("description", "")),
    )
    chain_id = cur.lastrowid

    # optionally add initial blocks
    block_ids = payload.get("block_ids", [])
    for i, item in enumerate(block_ids):
        if isinstance(item, dict):
            bid = item["block_id"]
            order = item.get("sort_order", i)
        else:
            bid = int(item)
            order = i
        conn.execute(
            "INSERT INTO sop_chain_blocks (chain_id, block_id, sort_order) VALUES (?, ?, ?)",
            (chain_id, bid, order),
        )
    conn.commit()

    row = conn.execute("SELECT * FROM sop_chains WHERE id = ?", (chain_id,)).fetchone()
    conn.close()
    return dict(row)


@router.put("/sop/chains/{chain_id}")
def update_chain(chain_id: int, payload: dict):
    conn = get_db()
    row = conn.execute("SELECT * FROM sop_chains WHERE id = ?", (chain_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Chain not found"}

    fields = {}
    for key in ("name", "description"):
        if key in payload:
            fields[key] = payload[key]
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values())
        conn.execute(
            f"UPDATE sop_chains SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            vals + [chain_id],
        )
        conn.commit()
    conn.close()
    return {"status": "ok"}


@router.delete("/sop/chains/{chain_id}")
def delete_chain(chain_id: int):
    conn = get_db()
    conn.execute("DELETE FROM sop_chains WHERE id = ?", (chain_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ═══════════════════════════════════════════
# Chain Block Management
# ═══════════════════════════════════════════

@router.post("/sop/chains/{chain_id}/blocks")
def add_block_to_chain(chain_id: int, payload: dict):
    conn = get_db()
    chain = conn.execute("SELECT id FROM sop_chains WHERE id = ?", (chain_id,)).fetchone()
    if not chain:
        conn.close()
        return {"error": "Chain not found"}

    block_id = payload.get("block_id")
    if not block_id:
        conn.close()
        return {"error": "block_id is required"}

    # auto-assign sort_order if not provided
    sort_order = payload.get("sort_order")
    if sort_order is None:
        max_order = conn.execute(
            "SELECT MAX(sort_order) FROM sop_chain_blocks WHERE chain_id = ?", (chain_id,)
        ).fetchone()[0]
        sort_order = (max_order or 0) + 1

    cur = conn.execute(
        """INSERT INTO sop_chain_blocks (chain_id, block_id, sort_order, parent_id, branch_label)
           VALUES (?, ?, ?, ?, ?)""",
        (
            chain_id, block_id, sort_order,
            payload.get("parent_id"), payload.get("branch_label", ""),
        ),
    )
    conn.commit()
    cb_id = cur.lastrowid
    row = conn.execute("SELECT * FROM sop_chain_blocks WHERE id = ?", (cb_id,)).fetchone()
    conn.close()
    return dict(row)


@router.put("/sop/chains/{chain_id}/blocks/{cb_id}")
def update_chain_block(chain_id: int, cb_id: int, payload: dict):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM sop_chain_blocks WHERE id = ? AND chain_id = ?", (cb_id, chain_id)
    ).fetchone()
    if not row:
        conn.close()
        return {"error": "Chain block not found"}

    fields = {}
    for key in ("sort_order", "parent_id", "branch_label"):
        if key in payload:
            fields[key] = payload[key]
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values())
        conn.execute(
            f"UPDATE sop_chain_blocks SET {sets} WHERE id = ?", vals + [cb_id]
        )
        conn.commit()
    conn.close()
    return {"status": "ok"}


@router.delete("/sop/chains/{chain_id}/blocks/{cb_id}")
def remove_block_from_chain(chain_id: int, cb_id: int):
    conn = get_db()
    conn.execute(
        "DELETE FROM sop_chain_blocks WHERE id = ? AND chain_id = ?", (cb_id, chain_id)
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.put("/sop/chains/{chain_id}/reorder")
def reorder_chain_blocks(chain_id: int, payload: dict):
    """Batch reorder: {order: [{cb_id, sort_order}, ...]}"""
    conn = get_db()
    order = payload.get("order", [])
    for item in order:
        conn.execute(
            "UPDATE sop_chain_blocks SET sort_order = ? WHERE id = ? AND chain_id = ?",
            (item["sort_order"], item["cb_id"], chain_id),
        )
    conn.commit()
    conn.close()
    return {"status": "ok"}


# ═══════════════════════════════════════════
# Suggestions
# ═══════════════════════════════════════════

@router.get("/sop/suggestions")
def list_suggestions(status: str = "pending", suggestion_type: str = None, limit: int = 50):
    conn = get_db()
    query = "SELECT * FROM sop_suggestions WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if suggestion_type:
        query += " AND suggestion_type = ?"
        params.append(suggestion_type)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/sop/suggestions/{sug_id}")
def get_suggestion(sug_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM sop_suggestions WHERE id = ?", (sug_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": "Suggestion not found"}
    return dict(row)


@router.post("/sop/suggestions/{sug_id}/confirm")
def confirm_suggestion(sug_id: int):
    """Apply the suggestion: create block, merge content, or insert into chain."""
    conn = get_db()
    row = conn.execute("SELECT * FROM sop_suggestions WHERE id = ?", (sug_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Suggestion not found"}
    if row["status"] != "pending":
        conn.close()
        return {"error": f"Suggestion status is '{row['status']}', not 'pending'"}

    stype = row["suggestion_type"]
    action = ""
    result_id = None

    if stype == "new_block":
        cur = conn.execute(
            """INSERT INTO sop_blocks (title, description, content, tags, source_wiki_page_id, source_type)
               VALUES (?, ?, ?, '[]', ?, 'wiki')""",
            (row["suggested_title"], "", row["suggested_content"], row["wiki_page_id"]),
        )
        conn.commit()
        result_id = cur.lastrowid
        action = "created_block"

    elif stype == "merge_into_block":
        if row["block_id"]:
            existing = conn.execute(
                "SELECT content FROM sop_blocks WHERE id = ?", (row["block_id"],)
            ).fetchone()
            if existing:
                new_content = existing["content"].rstrip() + "\n\n" + row["suggested_content"].strip()
                conn.execute(
                    "UPDATE sop_blocks SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_content, row["block_id"]),
                )
                conn.commit()
                result_id = row["block_id"]
                action = "updated_block"

    elif stype == "insert_into_chain":
        if row["chain_id"]:
            # create a new block from suggestion, then insert into chain
            cur = conn.execute(
                """INSERT INTO sop_blocks (title, description, content, tags, source_wiki_page_id, source_type)
                   VALUES (?, ?, ?, '[]', ?, 'wiki')""",
                (row["suggested_title"], "", row["suggested_content"], row["wiki_page_id"]),
            )
            new_block_id = cur.lastrowid

            # determine sort_order
            max_order = conn.execute(
                "SELECT MAX(sort_order) FROM sop_chain_blocks WHERE chain_id = ?",
                (row["chain_id"],),
            ).fetchone()[0]
            sort_order = (max_order or 0) + 1

            conn.execute(
                "INSERT INTO sop_chain_blocks (chain_id, block_id, sort_order) VALUES (?, ?, ?)",
                (row["chain_id"], new_block_id, sort_order),
            )
            conn.commit()
            result_id = new_block_id
            action = "inserted_into_chain"

    elif stype == "enrich_block":
        if row["block_id"]:
            existing = conn.execute(
                "SELECT content FROM sop_blocks WHERE id = ?", (row["block_id"],)
            ).fetchone()
            if existing:
                new_content = existing["content"].rstrip() + "\n\n" + row["suggested_content"].strip()
                conn.execute(
                    "UPDATE sop_blocks SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_content, row["block_id"]),
                )
                conn.commit()
                result_id = row["block_id"]
                action = "updated_block"

    elif stype == "extract_chain":
        # Parse steps JSON from suggested_content
        try:
            steps_data = json.loads(row["suggested_content"])
            steps = steps_data.get("steps", [])
            chain_desc = steps_data.get("chain_description", "")
        except json.JSONDecodeError:
            steps = []
            chain_desc = ""

        if steps:
            # Create chain
            cur = conn.execute(
                "INSERT INTO sop_chains (name, description) VALUES (?, ?)",
                (row["suggested_title"], chain_desc),
            )
            new_chain_id = cur.lastrowid

            # Create blocks for each step and add to chain
            for i, step in enumerate(steps):
                cur = conn.execute(
                    """INSERT INTO sop_blocks (title, description, content, tags, source_wiki_page_id, source_type)
                       VALUES (?, ?, ?, '[]', ?, 'wiki')""",
                    (step.get("title", ""), "", step.get("content", ""), row["wiki_page_id"]),
                )
                block_id = cur.lastrowid
                conn.execute(
                    "INSERT INTO sop_chain_blocks (chain_id, block_id, sort_order) VALUES (?, ?, ?)",
                    (new_chain_id, block_id, i),
                )
            conn.commit()
            result_id = new_chain_id
            action = "created_chain"

    conn.execute(
        "UPDATE sop_suggestions SET status = 'confirmed', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
        (sug_id,),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "action": action, "result_id": result_id}


@router.post("/sop/suggestions/{sug_id}/reject")
def reject_suggestion(sug_id: int, payload: dict = None):
    conn = get_db()
    row = conn.execute("SELECT * FROM sop_suggestions WHERE id = ?", (sug_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Suggestion not found"}
    if row["status"] != "pending":
        conn.close()
        return {"error": f"Suggestion status is '{row['status']}', not 'pending'"}

    reason = (payload or {}).get("reason", "")
    conn.execute(
        "UPDATE sop_suggestions SET status = 'rejected', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
        (sug_id,),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "suggestion_id": sug_id, "rejected": True}


# ═══════════════════════════════════════════
# Evolution / Wiki Matching
# ═══════════════════════════════════════════

@router.post("/sop/evolution/analyze")
async def trigger_analysis(payload: dict = None):
    """Trigger AI analysis: match wiki pages to SOP blocks/chains."""
    from sop_evolution import analyze_wiki_for_sop

    wiki_page_ids = (payload or {}).get("wiki_page_ids")
    force = (payload or {}).get("force", False)
    limit = (payload or {}).get("limit", 100)

    result = await analyze_wiki_for_sop(wiki_page_ids=wiki_page_ids, force=force, limit=limit)
    result["status"] = "ok"
    return result


@router.get("/sop/wiki-unmatched")
def list_unmatched_wiki():
    """Wiki pages not yet linked to any SOP block or pending suggestion."""
    conn = get_db()
    rows = conn.execute(
        """SELECT w.id as wiki_page_id, w.title, w.slug, w.summary, w.category, w.tags
           FROM wiki_pages w
           WHERE w.id NOT IN (
               SELECT DISTINCT source_wiki_page_id FROM sop_blocks WHERE source_wiki_page_id IS NOT NULL
           )
           AND w.id NOT IN (
               SELECT DISTINCT wiki_page_id FROM sop_suggestions
               WHERE wiki_page_id IS NOT NULL AND status = 'pending'
           )
           ORDER BY w.updated_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
