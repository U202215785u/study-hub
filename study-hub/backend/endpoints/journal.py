from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import json

import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
from database import get_db

router = APIRouter()


class JournalEntryCreate(BaseModel):
    date: str
    content: str
    mood: str = "neutral"
    tags: List[str] = []
    weather: str = ""
    location: str = ""
    sticker: str = ""


class JournalEntryUpdate(BaseModel):
    content: Optional[str] = None
    mood: Optional[str] = None
    tags: Optional[List[str]] = None
    weather: Optional[str] = None
    location: Optional[str] = None
    sticker: Optional[str] = None


class JournalEntryOut(BaseModel):
    id: int
    date: str
    content: str
    mood: str
    tags: List[str]
    weather: str
    location: str
    sticker: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


def _row_to_dict(row):
    d = dict(row)
    d["tags"] = json.loads(d.get("tags") or "[]")
    return d


@router.get("/journal/entries")
def list_entries(year: int = 0, month: int = 0, tag: str = "", mood: str = ""):
    conn = get_db()
    sql = "SELECT * FROM journal_entries WHERE 1=1"
    params = []

    if year:
        sql += " AND strftime('%Y', date) = ?"
        params.append(str(year))
    if month:
        sql += " AND strftime('%m', date) = ?"
        params.append(f"{month:02d}")
    if tag:
        sql += " AND tags LIKE ?"
        params.append(f'%"{tag}"%')
    if mood:
        sql += " AND mood = ?"
        params.append(mood)

    sql += " ORDER BY date DESC, created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


@router.get("/journal/entries/{entry_id}")
def get_entry(entry_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM journal_entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": "日记不存在"}
    return _row_to_dict(row)


@router.get("/journal/today")
def get_today():
    today = date.today().isoformat()
    conn = get_db()
    row = conn.execute("SELECT * FROM journal_entries WHERE date = ?", (today,)).fetchone()
    conn.close()
    if not row:
        return {"date": today, "content": "", "mood": "neutral", "tags": [], "weather": "", "location": "", "sticker": ""}
    return _row_to_dict(row)


@router.post("/journal/entries")
def create_entry(payload: JournalEntryCreate):
    conn = get_db()
    # 同一天只能有一篇日记，存在则更新
    existing = conn.execute("SELECT id FROM journal_entries WHERE date = ?", (payload.date,)).fetchone()
    tags_json = json.dumps(payload.tags, ensure_ascii=False)
    now = datetime.now().isoformat()

    if existing:
        conn.execute(
            """UPDATE journal_entries
               SET content = ?, mood = ?, tags = ?, weather = ?, location = ?, sticker = ?, updated_at = ?
               WHERE id = ?""",
            (payload.content, payload.mood, tags_json, payload.weather, payload.location, payload.sticker, now, existing["id"]),
        )
        conn.commit()
        entry_id = existing["id"]
    else:
        cur = conn.execute(
            """INSERT INTO journal_entries (date, content, mood, tags, weather, location, sticker, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (payload.date, payload.content, payload.mood, tags_json, payload.weather, payload.location, payload.sticker, now, now),
        )
        conn.commit()
        entry_id = cur.lastrowid

    row = conn.execute("SELECT * FROM journal_entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


@router.put("/journal/entries/{entry_id}")
def update_entry(entry_id: int, payload: JournalEntryUpdate):
    conn = get_db()
    existing = conn.execute("SELECT * FROM journal_entries WHERE id = ?", (entry_id,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "日记不存在"}

    content = payload.content if payload.content is not None else existing["content"]
    mood = payload.mood if payload.mood is not None else existing["mood"]
    tags = json.dumps(payload.tags if payload.tags is not None else json.loads(existing["tags"] or "[]"), ensure_ascii=False)
    weather = payload.weather if payload.weather is not None else existing["weather"]
    location = payload.location if payload.location is not None else existing["location"]
    sticker = payload.sticker if payload.sticker is not None else existing["sticker"]
    now = datetime.now().isoformat()

    conn.execute(
        """UPDATE journal_entries
           SET content = ?, mood = ?, tags = ?, weather = ?, location = ?, sticker = ?, updated_at = ?
           WHERE id = ?""",
        (content, mood, tags, weather, location, sticker, now, entry_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM journal_entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


@router.delete("/journal/entries/{entry_id}")
def delete_entry(entry_id: int):
    conn = get_db()
    conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.get("/journal/stats")
def get_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]
    streak = 0
    # 计算连续写日记天数
    rows = conn.execute("SELECT date FROM journal_entries ORDER BY date DESC").fetchall()
    conn.close()

    if rows:
        from datetime import timedelta
        current = date.fromisoformat(rows[0]["date"])
        today = date.today()
        # 如果最新日记不是今天或昨天， streak 从 0 开始
        if (today - current).days > 1:
            streak = 0
        else:
            streak = 1
            prev = current
            for r in rows[1:]:
                d = date.fromisoformat(r["date"])
                if (prev - d).days == 1:
                    streak += 1
                    prev = d
                else:
                    break

    return {"total": total, "streak": streak}


@router.get("/journal/tags")
def list_tags():
    conn = get_db()
    rows = conn.execute("SELECT tags FROM journal_entries").fetchall()
    conn.close()
    tags = set()
    for r in rows:
        for t in json.loads(r["tags"] or "[]"):
            tags.add(t)
    return sorted(tags)
