import json
from copy import deepcopy
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database import get_db


router = APIRouter(tags=["heatmap"])

SOURCE_IDS = ("tasks", "documents", "queue")
QUEUE_STATUSES = ("pending", "extracting", "summarizing", "importing", "done")
RANGE_COLUMNS = {90: 13, 196: 28, 365: 53}
QUEUE_RETENTION_DAYS = 7
QUEUE_RETENTION_LIMIT = 200
GRID_FIELDS = [
    {"key": "range_days", "type": "select", "options": [90, 196, 365], "default": 196},
    {"key": "sources", "type": "multiselect", "options": list(SOURCE_IDS), "default": list(SOURCE_IDS)},
    {"key": "palette", "type": "select", "options": ["lime-orange-purple"], "default": "lime-orange-purple"},
    {"key": "scale", "type": "select", "options": ["threshold"], "default": "threshold"},
    {"key": "cell_shape", "type": "select", "options": ["square", "rounded"], "default": "square"},
    {"key": "cell_gap", "type": "number", "min": 0, "max": 12, "step": 1, "default": 5},
    {"key": "cell_radius", "type": "number", "min": 0, "max": 8, "step": 1, "default": 0, "depends_on": {"key": "cell_shape", "equals": "rounded"}},
    {"key": "cell_opacity", "type": "number", "min": 20, "max": 100, "step": 5, "default": 100},
    {"key": "show_legend", "type": "boolean", "default": True},
    {"key": "show_date_labels", "type": "boolean", "default": False},
    {"key": "week_starts_on", "type": "select", "options": [0, 1], "default": 1},
]
GRID_FIELD_MAP = {field["key"]: field for field in GRID_FIELDS}
GRID_SCHEMA = {"version": "grid-v1", "layout": {"rows": 7, "columns_by_range": {str(days): columns for days, columns in RANGE_COLUMNS.items()}}, "fields": GRID_FIELDS}


def _defaults():
    return {field["key"]: deepcopy(field["default"]) for field in GRID_FIELDS}


def _catalog():
    return {"default_style_id": "grid", "styles": [
        {"id": "grid", "name": "方格", "status": "available", "renderer": "grid", "settings_schema": GRID_SCHEMA},
        {"id": "calendar", "name": "日历", "status": "reserved", "renderer": None, "settings_schema": None},
        {"id": "circular", "name": "环形", "status": "reserved", "renderer": None, "settings_schema": None},
        {"id": "flow", "name": "流动", "status": "reserved", "renderer": None, "settings_schema": None},
    ]}


def _normalize(settings):
    if not isinstance(settings, dict):
        raise HTTPException(422, "settings must be an object")
    unknown = set(settings) - set(GRID_FIELD_MAP)
    if unknown:
        raise HTTPException(422, f"unknown heatmap settings: {', '.join(sorted(unknown))}")
    result = {**_defaults(), **settings}
    for field in GRID_FIELDS:
        key, value = field["key"], result[field["key"]]
        if field["type"] == "select" and value not in field["options"]:
            raise HTTPException(422, f"{key} must be one of {field['options']}")
        if field["type"] == "multiselect":
            if not isinstance(value, list) or not value or any(item not in field["options"] for item in value) or len(set(value)) != len(value):
                raise HTTPException(422, f"{key} must contain unique known option ids")
        if field["type"] == "number":
            minimum, maximum, step = field["min"], field["max"], field["step"]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value or not minimum <= value <= maximum or (int(value) - minimum) % step:
                raise HTTPException(422, f"{key} must match catalog range and step")
            result[key] = int(value)
        if field["type"] == "boolean" and not isinstance(value, bool):
            raise HTTPException(422, f"{key} must be boolean")
    if result["cell_shape"] == "square":
        result["cell_radius"] = 0
    return result


def _preferences(conn):
    row = conn.execute("SELECT style_id, settings_json, updated_at FROM heatmap_preferences WHERE id = 1").fetchone()
    if not row:
        return {"style_id": "grid", "settings": _defaults(), "updated_at": None}
    try:
        settings = _normalize(json.loads(row["settings_json"] or "{}"))
    except (ValueError, TypeError, HTTPException):
        settings = _defaults()
    return {"style_id": row["style_id"] if row["style_id"] == "grid" else "grid", "settings": settings, "updated_at": row["updated_at"]}


class PreferencesPayload(BaseModel):
    style_id: str = Field(min_length=1)
    settings: dict = Field(default_factory=dict)


@router.get("/heatmap/catalog")
def catalog():
    return _catalog()


@router.get("/heatmap/preferences")
def preferences():
    conn = get_db()
    try:
        return _preferences(conn)
    finally:
        conn.close()


@router.put("/heatmap/preferences")
def save_preferences(payload: PreferencesPayload):
    if payload.style_id != "grid":
        raise HTTPException(422, "only the grid heatmap style is available")
    settings = _normalize(payload.settings)
    conn = get_db()
    try:
        conn.execute("INSERT INTO heatmap_preferences (id, style_id, settings_json, updated_at) VALUES (1, ?, ?, CURRENT_TIMESTAMP) ON CONFLICT(id) DO UPDATE SET style_id=excluded.style_id, settings_json=excluded.settings_json, updated_at=CURRENT_TIMESTAMP", (payload.style_id, json.dumps(settings, ensure_ascii=False)))
        conn.commit()
        return _preferences(conn)
    finally:
        conn.close()


def _date(value):
    try:
        return date.fromisoformat(value) if value else date.today()
    except ValueError as error:
        raise HTTPException(422, "end_date must be YYYY-MM-DD") from error


def _counts(conn, source, start, end):
    if source == "tasks":
        rows = conn.execute("SELECT substr(COALESCE(updated_at, created_at), 1, 10) day, COUNT(*) count FROM ddl_tasks WHERE substr(COALESCE(updated_at, created_at), 1, 10) BETWEEN ? AND ? GROUP BY day", (start.isoformat(), end.isoformat())).fetchall()
    elif source == "documents":
        rows = conn.execute("SELECT substr(created_at, 1, 10) day, COUNT(*) count FROM documents WHERE substr(created_at, 1, 10) BETWEEN ? AND ? GROUP BY day", (start.isoformat(), end.isoformat())).fetchall()
    else:
        window_start = max(start, end - timedelta(days=QUEUE_RETENTION_DAYS - 1))
        placeholders = ",".join("?" for _ in QUEUE_STATUSES)
        rows = conn.execute(f"SELECT substr(created_at,1,10) day, COUNT(*) count FROM (SELECT created_at FROM task_queue WHERE status IN ({placeholders}) AND substr(created_at,1,10) BETWEEN ? AND ? ORDER BY created_at DESC LIMIT ?) GROUP BY day", (*QUEUE_STATUSES, window_start.isoformat(), end.isoformat(), QUEUE_RETENTION_LIMIT)).fetchall()
    return {row["day"]: int(row["count"]) for row in rows if row["day"]}


@router.get("/heatmap/data")
def data(range_days: int = Query(196), sources: str = Query("tasks,documents,queue"), metric: str = Query("records"), end_date: str = Query(""), week_starts_on: int = Query(1)):
    if range_days not in RANGE_COLUMNS or metric != "records" or week_starts_on not in (0, 1):
        raise HTTPException(422, "invalid heatmap query")
    selected = [item.strip() for item in sources.split(",") if item.strip()]
    if not selected or any(item not in SOURCE_IDS for item in selected) or len(set(selected)) != len(selected):
        raise HTTPException(422, "sources must contain unique known source ids")
    end, start = _date(end_date), None
    start = end - timedelta(days=range_days - 1)
    conn = get_db()
    try:
        per_source = {source: _counts(conn, source, start, end) for source in selected}
    finally:
        conn.close()
    dates = [(start + timedelta(days=index)).isoformat() for index in range(range_days)]
    cells = [{"date": day, "count": sum(per_source[source].get(day, 0) for source in selected), "level": min(sum(per_source[source].get(day, 0) for source in selected), 5), "source_counts": {source: per_source[source].get(day, 0) for source in selected}} for day in dates]
    leading = (start.weekday() - week_starts_on) % 7
    slots = RANGE_COLUMNS[range_days] * 7
    if leading + range_days > slots:
        leading = 0
    return {"metric": "records", "range": {"start": start.isoformat(), "end": end.isoformat(), "days": range_days}, "cells": cells, "summary": {"total": sum(cell["count"] for cell in cells), "active_days": sum(bool(cell["count"]) for cell in cells), "source_counts": {source: sum(per_source[source].values()) for source in selected}}, "grid": {"rows": 7, "columns": RANGE_COLUMNS[range_days], "slot_count": slots, "leading_empty_slots": leading, "trailing_empty_slots": slots - leading - range_days}}
