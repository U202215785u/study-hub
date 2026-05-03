"""
Evolution system API endpoints.
"""
import json
from fastapi import APIRouter
from database import get_db
from evolution_pipeline import analyze_evolution
from evolution_files import list_skills, read_skill_file, read_config_files

router = APIRouter()


@router.post("/evolution/analyze")
async def trigger_analysis(payload: dict):
    """
    Trigger evolution analysis manually or from wiki/review hooks.
    Request: {source_event_type, source_event_id, new_pages, updated_pages, contradictions, review_summary}
    """
    new_pages = payload.get("new_pages", [])
    updated_pages = payload.get("updated_pages", [])
    contradictions = payload.get("contradictions", [])
    review_summary = payload.get("review_summary", "")
    source_event_type = payload.get("source_event_type", "manual")
    source_event_id = payload.get("source_event_id", 0)

    result = await analyze_evolution(
        new_pages=new_pages,
        updated_pages=updated_pages,
        contradictions=contradictions,
        review_summary=review_summary,
        source_event_type=source_event_type,
        source_event_id=source_event_id,
    )
    result["status"] = "ok"
    return result


@router.get("/evolution/patches")
def list_patches(status: str = None, risk_level: str = None, limit: int = 50):
    """List skill patches. Optional filters: status, risk_level."""
    conn = get_db()
    query = "SELECT * FROM skill_patches WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if risk_level:
        query += " AND risk_level = ?"
        params.append(risk_level)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/evolution/patches/{patch_id}")
def get_patch(patch_id: int):
    """Get a single patch with full content."""
    conn = get_db()
    row = conn.execute("SELECT * FROM skill_patches WHERE id = ?", (patch_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": "Patch not found"}
    return dict(row)


@router.post("/evolution/patches/{patch_id}/apply")
def apply_patch(patch_id: int):
    """Manually apply a pending patch."""
    from evolution_files import apply_patch_to_skill

    conn = get_db()
    row = conn.execute("SELECT * FROM skill_patches WHERE id = ?", (patch_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Patch not found"}
    if row["status"] != "pending":
        conn.close()
        return {"error": f"Patch status is '{row['status']}', not 'pending'"}

    ok = apply_patch_to_skill(
        row["skill_name"], row["patch_type"],
        row["target_section"] or "", row["patch_content"],
    )
    if ok:
        conn.execute(
            "UPDATE skill_patches SET status = 'applied', applied_at = CURRENT_TIMESTAMP WHERE id = ?",
            (patch_id,),
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "patch_id": patch_id, "applied": True}
    else:
        conn.close()
        return {"error": "Failed to apply patch (skill file not found)"}


@router.post("/evolution/patches/{patch_id}/reject")
def reject_patch(patch_id: int, payload: dict = None):
    """Reject a pending patch."""
    conn = get_db()
    row = conn.execute("SELECT * FROM skill_patches WHERE id = ?", (patch_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Patch not found"}
    if row["status"] != "pending":
        conn.close()
        return {"error": f"Patch status is '{row['status']}', not 'pending'"}

    reason = (payload or {}).get("reason", "")
    conn.execute(
        "UPDATE skill_patches SET status = 'rejected', rejected_at = CURRENT_TIMESTAMP WHERE id = ?",
        (patch_id,),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "patch_id": patch_id, "rejected": True, "reason": reason}


@router.get("/evolution/snapshots")
def list_snapshots(limit: int = 30):
    """List recent system snapshots."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, snapshot_type, snapshot_date, review_summary, evolution_notes, created_at "
        "FROM system_snapshots ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/evolution/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: int):
    """Get a full snapshot."""
    conn = get_db()
    row = conn.execute("SELECT * FROM system_snapshots WHERE id = ?", (snapshot_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": "Snapshot not found"}
    r = dict(row)
    for field in ["skills_json", "config_json", "wiki_stats_json", "patch_ids_applied"]:
        try:
            r[field] = json.loads(r[field]) if r[field] else []
        except json.JSONDecodeError:
            pass
    return r


@router.post("/evolution/snapshots")
def create_manual_snapshot():
    """Create a manual snapshot of the current system state."""
    from evolution_files import (
        list_skills, compute_skill_fingerprint, read_config_files, write_daily_snapshot,
    )

    conn = get_db()
    today = __import__("datetime").date.today().isoformat()

    skills = list_skills()
    skills_json = json.dumps([
        {"skill_name": s["skill_name"], "fingerprint": compute_skill_fingerprint(s["skill_name"]),
         "frontmatter": s["frontmatter"]}
        for s in skills
    ], ensure_ascii=False)

    config_json = json.dumps(read_config_files(), ensure_ascii=False)
    wiki_stats = {}
    try:
        page_count = conn.execute("SELECT COUNT(*) FROM wiki_pages").fetchone()[0]
        link_count = conn.execute("SELECT COUNT(*) FROM wiki_links").fetchone()[0]
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        wiki_stats = {"wiki_page_count": page_count, "wiki_link_count": link_count, "doc_count": doc_count}
    except Exception:
        pass
    wiki_stats_json = json.dumps(wiki_stats, ensure_ascii=False)

    cur = conn.execute(
        """INSERT INTO system_snapshots
           (snapshot_type, snapshot_date, skills_json, config_json, wiki_stats_json, evolution_notes)
           VALUES ('manual', ?, ?, ?, ?, 'Manual snapshot')""",
        (today, skills_json, config_json, wiki_stats_json),
    )
    snapshot_id = cur.lastrowid
    conn.commit()
    conn.close()

    write_daily_snapshot(snapshot_id, today, skills_json, config_json, wiki_stats_json, "", "Manual snapshot")
    return {"status": "ok", "snapshot_id": snapshot_id}


@router.get("/evolution/skills")
def get_skills():
    """List all installed skills."""
    return list_skills()


@router.get("/evolution/skills/{skill_name}")
def get_skill(skill_name: str):
    """Get a single skill's full content."""
    skill = read_skill_file(skill_name)
    if not skill:
        return {"error": f"Skill '{skill_name}' not found"}
    return skill


@router.get("/evolution/config")
def get_config():
    """Get current configuration snapshot."""
    return read_config_files()
