"""因果记忆系统 — 基于因果关系的记忆检索。

核心概念：
- 因果链接：A 导致 B、A 阻止 B 等
- 时序链接：A 在 B 之前/之后
- 实体节点：人、项目、概念等
"""
import json
import re
from datetime import datetime
from typing import Any

from memory_store import _get_db, search_memory, get_entry


def ensure_causal_tables() -> None:
    """确保因果相关表已创建。"""
    # 表已在数据库初始化时创建
    pass


def causal_search(query: str, k: int = 5) -> dict:
    """因果记忆检索。"""
    ensure_causal_tables()
    db = _get_db()
    
    # 关键词种子
    seed_results = search_memory(query, k=10, use_causal=False)
    seeds = seed_results.get("results", [])
    
    if not seeds:
        return {"query": query, "results": [], "chains": [], "stats": {}}
    
    seed_ids = [r.get("entry_id") for r in seeds if r.get("entry_id")]
    
    # 因果链扩展
    causal_results = _expand_causal_chain(seed_ids, depth=2)
    
    # 时序扩展
    temporal_results = _expand_temporal(seed_ids)
    
    # 实体扩展
    entity_results = _expand_by_entities(seed_ids)
    
    # 融合排序
    merged = _merge_results(seeds, causal_results, temporal_results, entity_results)
    
    # 构建因果链展示
    chains = _build_causal_chains(merged[:k])
    
    return {
        "query": query,
        "results": merged[:k],
        "chains": chains,
        "stats": {
            "seeds": len(seeds),
            "causal_expanded": len(causal_results),
            "temporal_expanded": len(temporal_results),
            "entity_expanded": len(entity_results),
        },
    }


def _expand_causal_chain(seed_ids: list[str], depth: int = 2) -> list[dict]:
    """从种子记忆扩展因果链。"""
    db = _get_db()
    results = []
    current_ids = set(seed_ids)
    
    for _ in range(depth):
        if not current_ids:
            break
        placeholders = ",".join("?" * len(current_ids))
        c = db.execute(
            f"SELECT * FROM causal_links WHERE from_entry_id IN ({placeholders}) OR to_entry_id IN ({placeholders})",
            list(current_ids) * 2,
        )
        new_ids = set()
        for row in c.fetchall():
            from_id = row["from_entry_id"]
            to_id = row["to_entry_id"]
            new_ids.add(from_id)
            new_ids.add(to_id)
            entry = get_entry(from_id) or get_entry(to_id)
            if entry:
                entry = dict(entry)
                entry["score"] = 0.7
                entry["causal_link"] = row["link_type"]
                results.append(entry)
        current_ids = new_ids - current_ids
    
    return results


def _expand_temporal(seed_ids: list[str]) -> list[dict]:
    """时序扩展。"""
    db = _get_db()
    results = []
    placeholders = ",".join("?" * len(seed_ids))
    c = db.execute(
        f"SELECT * FROM temporal_links WHERE from_entry_id IN ({placeholders}) OR to_entry_id IN ({placeholders})",
        list(seed_ids) * 2,
    )
    for row in c.fetchall():
        from_id = row["from_entry_id"]
        entry = get_entry(from_id)
        if entry:
            entry = dict(entry)
            entry["score"] = 0.6
            entry["temporal_relation"] = row["relation"]
            results.append(entry)
    return results


def _expand_by_entities(seed_ids: list[str]) -> list[dict]:
    """通过实体关联扩展。"""
    db = _get_db()
    results = []
    
    # 找到种子记忆关联的实体
    placeholders = ",".join("?" * len(seed_ids))
    c = db.execute(
        f"SELECT entity_id FROM entry_entities WHERE entry_id IN ({placeholders})",
        list(seed_ids),
    )
    entity_ids = [r["entity_id"] for r in c.fetchall()]
    
    if not entity_ids:
        return results
    
    # 找到同一实体的其他记忆
    e_placeholders = ",".join("?" * len(entity_ids))
    c = db.execute(
        f"SELECT entry_id FROM entry_entities WHERE entity_id IN ({e_placeholders})",
        entity_ids,
    )
    related_ids = [r["entry_id"] for r in c.fetchall()]
    
    for rid in related_ids:
        if rid in seed_ids:
            continue
        entry = get_entry(rid)
        if entry:
            entry = dict(entry)
            entry["score"] = 0.5
            results.append(entry)
    
    return results


def _merge_results(seeds: list[dict], causal: list[dict], temporal: list[dict], entity: list[dict]) -> list[dict]:
    """融合多路结果。"""
    merged = {}
    for r in seeds + causal + temporal + entity:
        eid = r.get("entry_id", r.get("id", ""))
        if eid not in merged or r.get("score", 0) > merged[eid].get("score", 0):
            merged[eid] = r
    return sorted(merged.values(), key=lambda x: x.get("score", 0), reverse=True)


def _build_causal_chains(results: list[dict]) -> list[dict]:
    """构建因果链展示。"""
    chains = []
    db = _get_db()
    for r in results:
        eid = r.get("entry_id", r.get("id", ""))
        if not eid:
            continue
        c = db.execute(
            "SELECT * FROM causal_links WHERE from_entry_id = ? OR to_entry_id = ?",
            (eid, eid),
        )
        for row in c.fetchall():
            chains.append({
                "from": row["from_entry_id"],
                "to": row["to_entry_id"],
                "type": row["link_type"],
                "confidence": row["confidence"],
            })
    return chains
