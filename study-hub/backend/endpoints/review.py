import json
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException
from database import get_db
from ai_client import AIServiceError, ai_client
from processing.vector_store import get_vector_store

router = APIRouter()

REVIEW_SYSTEM_PROMPT = """你是一位学习导师。用户会提供今天的学习笔记（可能很随意），你需要完成三件事：

1. **润色总结**：将用户的笔记整理成一篇通顺、有条理的学习总结。保留所有关键信息，补充逻辑连接。
2. **学习建议**：指出用户学习中可能存在的盲区、需要巩固的知识点，或可以进一步深入的方向。给出 2-3 条具体建议。
3. **关联推荐**：如果用户的知识库中有相关内容，推荐用户对照阅读。

输出格式（严格 JSON）：
{
  "polished": "润色后的总结",
  "suggestions": ["建议1", "建议2", "建议3"],
  "related": ["关联推荐1", "关联推荐2"]
}"""


@router.post("/review/polish")
async def polish_review(payload: dict):
    raw_text = (payload.get("raw_text") or "").strip()
    date_str = (payload.get("date") or date.today().isoformat())

    if not raw_text:
        return {"error": "请输入笔记内容"}

    # 搜索知识库相关内容
    kb_context = ""
    related_docs = []
    try:
        vs = get_vector_store()
        if vs.count() > 0:
            results = vs.query(raw_text, top_k=3)
            if results:
                kb_parts = []
                for r in results:
                    title = r["metadata"].get("title", "未知")
                    kb_parts.append(f"[{title}]\n{r['content']}")
                    if title not in related_docs:
                        related_docs.append(title)
                kb_context = "\n\n".join(kb_parts)
    except Exception:
        pass

    context_block = f"知识库相关内容：\n\n{kb_context}" if kb_context else "知识库中暂无相关内容。"

    messages = [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": f"用户今天的笔记：\n\n{raw_text}\n\n{context_block}\n\n请按 JSON 格式输出。"},
    ]

    try:
        answer = await ai_client.chat(messages, temperature=0.7, max_tokens=2048)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # 解析 AI 返回的 JSON
    try:
        # 尝试提取 JSON
        json_start = answer.find("{")
        json_end = answer.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            result = json.loads(answer[json_start:json_end])
        else:
            result = {"polished": answer, "suggestions": [], "related": related_docs}
    except json.JSONDecodeError:
        result = {"polished": answer, "suggestions": [], "related": related_docs}

    polished = result.get("polished", answer)
    suggestions = result.get("suggestions", [])
    related = result.get("related", related_docs)

    # 存入数据库
    conn = get_db()
    conn.execute(
        "INSERT INTO daily_reviews (date, raw_text, polished, suggestions, related_docs) VALUES (?, ?, ?, ?, ?)",
        (date_str, raw_text, polished, json.dumps(suggestions, ensure_ascii=False), json.dumps(related, ensure_ascii=False)),
    )
    conn.commit()

    review_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    # --- 进化系统钩子 ---
    evolution_info = None
    try:
        from evolution_pipeline import analyze_evolution
        evolution_info = await analyze_evolution(
            new_pages=[],
            updated_pages=[],
            contradictions=[],
            review_summary=polished,
            source_event_type="review_polish",
            source_event_id=review_id,
        )
        if evolution_info.get("low_risk_applied", 0) > 0:
            print(f"[Evolution] Review polish: {evolution_info['low_risk_applied']} low-risk patches applied")
    except Exception as e:
        print(f"[Evolution] Review hook failed (non-fatal): {e}")

    response = {
        "id": review_id,
        "polished": polished,
        "suggestions": suggestions,
        "related_docs": related,
    }
    if evolution_info:
        response["evolution"] = {
            "low_risk_applied": evolution_info["low_risk_applied"],
            "snapshot_id": evolution_info["snapshot_id"],
        }
    return response


@router.get("/review/list")
def list_reviews():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, date, raw_text, polished, created_at FROM daily_reviews ORDER BY date DESC, created_at DESC LIMIT 60"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/review/weekly")
async def weekly_report():
    conn = get_db()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    rows = conn.execute(
        "SELECT date, raw_text, polished FROM daily_reviews WHERE date >= ? ORDER BY date ASC",
        (week_ago,),
    ).fetchall()
    conn.close()

    if not rows:
        return {"report": "本周暂无复盘记录。"}

    entries = "\n\n---\n\n".join(
        f"日期: {r['date']}\n笔记: {r['raw_text']}\n润色: {r['polished'] or ''}"
        for r in rows
    )

    weekly_prompt = """你是一位学习导师。根据用户本周的每日复盘，生成一篇结构化的周报。

你的整个回复就是一份完整的周报。不要输出"好的"、"以下是周报"等开头语。

## 输出格式

严格按以下报纸格式输出：

# 📋 本周学习周报

> 复盘周期：本周 | 复盘天数：N 天

---

## 学习概览

（一段话概括本周学习主题和整体状态）

---

## 主要收获

| # | 日期 | 收获要点 |
|:---|:---|:---|
| 1 | 日期 | 一句话概括当天收获 |
| ... | ... | ... |

---

## 薄弱环节

- 具体薄弱点1
- 具体薄弱点2
- ...

---

## 下周建议

| 优先级 | 建议 | 理由 |
|:---|:---|:---|
| 🔴 高 | 建议1 | 为什么紧迫 |
| 🟡 中 | 建议2 | 为什么重要 |
| 🟢 低 | 建议3 | 为什么值得做 |

---

## 一周金句

> （从本周复盘中提炼一句话最有价值的认知）

直接输出以上格式的 Markdown，不要任何额外内容。"""

    messages = [
        {"role": "system", "content": weekly_prompt},
        {"role": "user", "content": f"本周复盘记录：\n\n{entries}\n\n请生成周报。"},
    ]

    report = await ai_client.chat(messages, temperature=0.7, max_tokens=2048)
    return {"report": report}
