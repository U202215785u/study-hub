"""
Evolution pipeline: analyze new knowledge, compare against skills,
generate concrete adjustment files (skill patches).
"""
import json
import re
from datetime import date
from database import get_db
from ai_client import ai_client
from evolution_files import (
    list_skills, read_skill_file, write_patch_file,
    apply_patch_to_skill, write_daily_snapshot,
    compute_skill_fingerprint, read_config_files,
)


def classify_risk(text: str) -> str:
    t = text.lower()
    if "risk: high" in t or "风险: 高" in t or '"high"' in t:
        return "high"
    if "risk: low" in t or "风险: 低" in t or '"low"' in t:
        return "low"
    return "medium"


def should_auto_apply(risk_level: str) -> bool:
    return False  # 所有补丁都必须手动确认


SKILL_ANALYSIS_SYSTEM = """你是一个学习系统架构师。你的任务是分析新学到的知识，并将其与现有的 Skills（SKILL.md 文件）进行对比，找出可以改进的地方。

## 分析维度

1. **措辞和格式**：描述是否清晰？术语是否准确？示例是否需要更新？
2. **步骤顺序**：执行流程是否需要调整以更符合新知识？
3. **触发词**：触发短语是否需要扩展以覆盖更多用户表达？
4. **参数量化**：参数说明、默认值、范围是否需要根据新知识调整？
5. **模型选择**：如果有 AI 调用，模型选择是否需要更新？
6. **回退/容错**：是否需要添加额外的错误处理或回退策略？
7. **新增步骤**：是否需要插入新的操作步骤？
8. **模式扩展**：是否需要支持新的语言/框架/模式？

## 风险级别定义

- **low**：措辞调整、格式优化、回退策略添加、触发词扩展（不改变现有行为）
- **medium**：参数修改、模型更换、新增步骤（改变行为但可验证）
- **high**：删除现有步骤、改变核心流程、修改数据模式（可能破坏现有功能）

## 输出格式（严格 JSON 数组）

如果没有改进建议，返回空数组 []。有建议时，每个建议一个对象：

```json
[
  {
    "skill_name": "douyin-summary",
    "risk_level": "low",
    "patch_type": "insert_after",
    "target_section": "### 第二步",
    "patch_content": "新步骤的完整 Markdown 内容...",
    "rationale": "为什么建议这个修改",
    "dimension": "fallback"
  }
]
```

patch_type 可选值: append（追加到文件末尾）、replace（替换 target_section）、insert_after（在 target_section 之后插入）、insert_before（在 target_section 之前插入）

注意：patch_content 必须是完整的、可以直接插入 SKILL.md 的 Markdown 内容。target_section 必须是原文件中实际存在的文本片段。"""


SKILL_ANALYSIS_USER = """## 今天新学到的知识

### 新创建的 Wiki 页面
{new_pages_summary}

### 更新的 Wiki 页面
{updated_pages_summary}

### 发现的矛盾
{contradictions_summary}

### 当日复盘摘要
{review_summary}

---

## 当前 Skills 清单

{skills_inventory}

---

请分析上述新知识，找出可以改进这些 Skills 的地方。对每个建议，给出具体的 patch，并评估风险级别。
只提出真正有价值的改进。如果新知识不相关或已覆盖，返回 []。"""


async def analyze_evolution(
    new_pages: list[dict],
    updated_pages: list[dict],
    contradictions: list[dict],
    review_summary: str = "",
    source_event_type: str = "wiki_compile",
    source_event_id: int = 0,
) -> dict:
    skills = list_skills()
    if not skills:
        return {
            "patches": [], "low_risk_applied": 0,
            "medium_risk_pending": 0, "high_risk_logged": 0,
            "snapshot_id": 0, "message": "No skills installed"
        }

    # Build skills inventory text
    skills_parts = []
    for s in skills:
        skills_parts.append(
            f"### {s['skill_name']}\n"
            f"描述: {s['frontmatter'].get('description', '无')}\n"
            f"触发词: {s['frontmatter'].get('trigger', '无')}\n"
            f"内容摘要: {s['body'][:500]}\n"
        )
    skills_text = "\n".join(skills_parts)

    # Summarize new knowledge
    new_pages_summary = "\n".join(
        f"- [{p.get('title', '')}] {str(p.get('summary', ''))[:200]}"
        for p in new_pages
    ) if new_pages else "（无新页面）"

    updated_pages_summary = "\n".join(
        f"- [{p.get('slug', '')}] {str(p.get('reason', ''))[:200]}"
        for p in updated_pages
    ) if updated_pages else "（无更新）"

    contradictions_summary = "\n".join(
        f"- {c.get('description', c.get('doc_title', ''))}"
        for c in contradictions
    ) if contradictions else "（无矛盾）"

    review_text = review_summary[:1000] if review_summary else "（无当日复盘）"

    messages = [
        {"role": "system", "content": SKILL_ANALYSIS_SYSTEM},
        {"role": "user", "content": SKILL_ANALYSIS_USER.format(
            new_pages_summary=new_pages_summary,
            updated_pages_summary=updated_pages_summary,
            contradictions_summary=contradictions_summary,
            review_summary=review_text,
            skills_inventory=skills_text,
        )},
    ]

    raw = await ai_client.chat(messages, temperature=0.4, max_tokens=4096)
    patches = _parse_patch_json(raw)

    conn = get_db()
    low_applied = 0
    medium_pending = 0
    high_logged = 0
    saved_patches = []

    for p in patches:
        risk = p.get("risk_level", "medium")
        patch_type = p.get("patch_type", "append")
        skill_name = p.get("skill_name", "")
        target_section = p.get("target_section", "")
        patch_content = p.get("patch_content", "")
        rationale = p.get("rationale", "")

        skill = read_skill_file(skill_name)
        if not skill:
            continue

        cur = conn.execute(
            """INSERT INTO skill_patches
               (skill_name, patch_type, target_section, patch_content, rationale,
                source_event_type, source_event_id, risk_level, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (skill_name, patch_type, target_section, patch_content, rationale,
             source_event_type, source_event_id, risk),
        )
        patch_id = cur.lastrowid
        conn.commit()

        file_path = write_patch_file(patch_id, skill_name, patch_type, patch_content)

        if should_auto_apply(risk):
            ok = apply_patch_to_skill(skill_name, patch_type, target_section, patch_content)
            status = "applied" if ok else "pending"
            conn.execute(
                "UPDATE skill_patches SET status = ?, file_path = ?, applied_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, file_path, patch_id),
            )
            conn.commit()
            if ok:
                low_applied += 1
        elif risk == "medium":
            medium_pending += 1
        else:
            high_logged += 1

        saved_patches.append({
            "id": patch_id, "skill_name": skill_name, "risk_level": risk,
            "patch_type": patch_type, "rationale": rationale,
            "status": "applied" if should_auto_apply(risk) else "pending",
            "file_path": file_path,
        })

    # Create daily snapshot
    snapshot_id = _create_snapshot(conn, saved_patches, review_summary, source_event_type)
    conn.close()

    return {
        "patches": saved_patches,
        "low_risk_applied": low_applied,
        "medium_risk_pending": medium_pending,
        "high_risk_logged": high_logged,
        "snapshot_id": snapshot_id,
    }


def _parse_patch_json(raw: str) -> list[dict]:
    raw = raw.strip()
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if m:
        raw = m.group(1).strip()
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "patches" in result:
            return result["patches"]
        return []
    except json.JSONDecodeError:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
    return []


def _create_snapshot(conn, applied_patches: list[dict], review_summary: str, event_type: str) -> int:
    today = date.today().isoformat()

    skills = list_skills()
    skills_data = []
    for s in skills:
        skills_data.append({
            "skill_name": s["skill_name"],
            "fingerprint": compute_skill_fingerprint(s["skill_name"]),
            "frontmatter": s["frontmatter"],
        })
    skills_json = json.dumps(skills_data, ensure_ascii=False)

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

    patch_ids = json.dumps([p["id"] for p in applied_patches])

    cur = conn.execute(
        """INSERT INTO system_snapshots
           (snapshot_type, snapshot_date, skills_json, config_json, wiki_stats_json,
            review_summary, evolution_notes, patch_ids_applied)
           VALUES ('daily', ?, ?, ?, ?, ?, ?, ?)""",
        (today, skills_json, config_json, wiki_stats_json,
         review_summary[:2000] if review_summary else "",
         f"Triggered by: {event_type}",
         patch_ids),
    )
    snapshot_id = cur.lastrowid
    conn.commit()

    write_daily_snapshot(snapshot_id, today, skills_json, config_json, wiki_stats_json,
                         review_summary, f"Triggered by: {event_type}")
    return snapshot_id
