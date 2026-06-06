"""
SOP Evolution: analyze wiki pages and match them to SOP blocks/chains.
Replaces the old evolution_pipeline.py which patched AI SKILL.md files.
"""
import json
import re
from database import get_db
from ai_client import ai_client


SOP_ANALYSIS_SYSTEM = """你是一个工作流规范化分析师。你的任务是将 Wiki 知识库中的页面与用户的 SOP（标准操作流程）进行匹配。

## 你的两种核心任务

### 任务 A：匹配已有 SOP
检查 Wiki 页面是否与**已有链路**相关：
- **new_block**：Wiki 描述了一个独立的工作步骤，可以新建为 Block，后续由用户手动加入链路。
- **insert_into_chain**：Wiki 内容明确应插入到某条已有链路中作为新环节。
- **merge_into_block**：Wiki 内容应合并到已有 Block 中，丰富其内容。
- **enrich_block**：Wiki 为已有 Block 提供了补充细节或参考案例。

### 任务 B：提取新 SOP 流程（重要！优先判断）
检查 Wiki 页面本身是否描述了一条**完整的多步骤工作流程**：
- 页面标题或内容包含类似"完整流程""从XX到XX""X步""指南""路线图""方法论"等特征
- 页面内包含多个有先后顺序的操作步骤
- 例如："AI编程从零到一人公司" "内容创作从选题到爆款" "FIRE提前退休指南" "Vibe Coding实战指南"
- 如果是 → 使用 **extract_chain**，将整条流程拆成 steps 数组

判断优先级：先看是否属于任务B（完整流程提取），再看是否属于任务A（匹配已有）。

## 建议类型

- **new_block**：Wiki 页面本身就是一个独立的工作环节。提供完整的 Markdown 操作内容。
- **merge_into_block**：Wiki 页面的内容应该合并到已有 Block 中，作为补充说明。
- **insert_into_chain**：Wiki 内容 + 现有链 = 建议在链的特定位置插入新环节。
- **enrich_block**：Wiki 页面为已有 Block 提供了更多细节或参考。

## 输出格式（严格 JSON 数组）

如果没有有价值的建议，返回空数组 []。有建议时：

```json
[
  {
    "suggestion_type": "new_block",
    "suggested_title": "环节名称",
    "suggested_content": "完整的 Markdown 操作步骤、要点、注意事项…",
    "rationale": "为什么建议创建这个环节",
    "tags": ["标签1", "标签2"],
    "wiki_page_id": 123
  },
  {
    "suggestion_type": "insert_into_chain",
    "chain_id": 1,
    "suggested_title": "环节名称",
    "suggested_content": "环节的完整 Markdown 内容…",
    "rationale": "为什么应该插入到这个链路中",
    "tags": ["标签1"],
    "wiki_page_id": 124
  },
  {
    "suggestion_type": "merge_into_block",
    "block_id": 5,
    "suggested_content": "要追加到目标 Block 的补充内容（Markdown）…",
    "rationale": "为什么应该合并",
    "wiki_page_id": 125
  },
  {
    "suggestion_type": "enrich_block",
    "block_id": 3,
    "suggested_content": "要追加的细节、案例或参考资料…",
    "rationale": "为什么这些内容能丰富目标 Block",
    "wiki_page_id": 126
  },
  {
    "suggestion_type": "extract_chain",
    "suggested_title": "链路名称（如：内容创作完整流程）",
    "chain_description": "这条链路涵盖什么",
    "steps": [
      {"title": "第一步名称", "content": "这一步的详细 Markdown 操作内容…"},
      {"title": "第二步名称", "content": "这一步的详细 Markdown 操作内容…"}
    ],
    "rationale": "这个 Wiki 页面描述了一条完整的 X 步工作流程，应该提取为一整条 SOP 链路",
    "tags": ["标签1"],
    "wiki_page_id": 127
  }
]
```

注意：
- suggested_content / steps[].content 必须是完整、可用的 Markdown 内容。
- rationale 说清楚建议的理由。
- 只提出真正有价值的建议。如果 Wiki 页面与现有工作流无关，不要强行匹配。
- 对于 insert_into_chain，不需要指定具体插入位置，系统会自动追加到链末尾。
- 对于 extract_chain，steps 数组必须按先后顺序排列，每个 step 包含独立的 title 和 content。
- extract_chain 用于"Wiki 本身就是一个 SOP 流程"的情况——如一篇题为"XXX完整流程"的文章，里面自然包含多步骤。"""


SOP_ANALYSIS_USER = """## 待匹配的 Wiki 页面

{wiki_pages_summary}

---

## 现有 SOP 环节 (Blocks)

{blocks_summary}

---

## 现有 SOP 链路 (Chains)

{chains_summary}

---

请分析以上 Wiki 页面，判断哪些可以转化为 SOP 环节或匹配到现有链路中。"""


async def analyze_wiki_for_sop(wiki_page_ids: list[int] = None, force: bool = False, limit: int = 100) -> dict:
    """
    Analyze wiki pages and generate SOP suggestions.

    Args:
        wiki_page_ids: Optional list of wiki page IDs to analyze. If None, analyzes all unmatched pages.
        force: If True, re-analyze even already-matched pages.

    Returns:
        {suggestions_created: N, types: {new_block: M, ...}}
    """
    conn = get_db()

    # Collect wiki pages to analyze
    if wiki_page_ids:
        placeholders = ",".join("?" * len(wiki_page_ids))
        wiki_rows = conn.execute(
            f"SELECT id, title, slug, summary, content, tags, category FROM wiki_pages WHERE id IN ({placeholders})",
            wiki_page_ids,
        ).fetchall()
    elif force:
        wiki_rows = conn.execute(
            "SELECT id, title, slug, summary, content, tags, category FROM wiki_pages ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    else:
        # Unmatched: not linked to any block and not in a pending suggestion
        wiki_rows = conn.execute(
            """SELECT w.id, w.title, w.slug, w.summary, w.content, w.tags, w.category
               FROM wiki_pages w
               WHERE w.id NOT IN (
                   SELECT DISTINCT source_wiki_page_id FROM sop_blocks WHERE source_wiki_page_id IS NOT NULL
               )
               AND w.id NOT IN (
                   SELECT DISTINCT wiki_page_id FROM sop_suggestions
                   WHERE wiki_page_id IS NOT NULL AND status = 'pending'
               )
               ORDER BY w.updated_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()

    if not wiki_rows:
        conn.close()
        return {"suggestions_created": 0, "types": {}, "message": "No wiki pages to analyze"}

    # Build wiki pages summary for AI
    wiki_parts = []
    for w in wiki_rows:
        wiki_parts.append(
            f"### [{w['title']}](id={w['id']})\n"
            f"分类: {w['category'] or '未分类'}\n"
            f"标签: {w['tags'] or '无'}\n"
            f"摘要: {w['summary'][:400] if w['summary'] else '无'}\n"
            f"内容预览: {w['content'][:1200] if w['content'] else '无'}\n"
        )
    wiki_text = "\n---\n".join(wiki_parts)

    # Collect existing blocks
    blocks_rows = conn.execute(
        "SELECT id, title, description, tags FROM sop_blocks ORDER BY updated_at DESC"
    ).fetchall()
    if blocks_rows:
        blocks_parts = []
        for b in blocks_rows:
            blocks_parts.append(
                f"- **[{b['title']}](id={b['id']})**: {b['description'][:120] or '无描述'} "
                f"(标签: {b['tags']})"
            )
        blocks_text = "\n".join(blocks_parts)
    else:
        blocks_text = "（暂无）"

    # Collect existing chains
    chains_rows = conn.execute(
        """SELECT c.id, c.name, c.description,
                  GROUP_CONCAT(b.title, ' → ') as block_sequence
           FROM sop_chains c
           LEFT JOIN sop_chain_blocks cb ON cb.chain_id = c.id
           LEFT JOIN sop_blocks b ON b.id = cb.block_id
           GROUP BY c.id
           ORDER BY c.updated_at DESC"""
    ).fetchall()
    if chains_rows:
        chains_parts = []
        for c in chains_rows:
            seq = c['block_sequence'] or '（空链）'
            chains_parts.append(
                f"- **[{c['name']}](id={c['id']})**: {c['description'][:120] or '无描述'}\n"
                f"  流程: {seq}"
            )
        chains_text = "\n".join(chains_parts)
    else:
        chains_text = "（暂无）"

    conn.close()

    # Call AI
    messages = [
        {"role": "system", "content": SOP_ANALYSIS_SYSTEM},
        {"role": "user", "content": SOP_ANALYSIS_USER.format(
            wiki_pages_summary=wiki_text,
            blocks_summary=blocks_text,
            chains_summary=chains_text,
        )},
    ]

    raw = await ai_client.chat(messages, temperature=0.4, max_tokens=8192)
    suggestions = _parse_suggestion_json(raw)

    # Save suggestions to DB
    conn = get_db()
    saved_count = 0
    type_counts = {}

    for s in suggestions:
        stype = s.get("suggestion_type", "")
        wiki_id = s.get("wiki_page_id")
        block_id = s.get("block_id")
        chain_id = s.get("chain_id")
        title = s.get("suggested_title", "")
        content = s.get("suggested_content", "")
        rationale = s.get("rationale", "")
        tags = json.dumps(s.get("tags", []), ensure_ascii=False)

        if not stype or not wiki_id:
            continue

        # For extract_chain, store steps JSON in suggested_content
        if stype == "extract_chain":
            steps = s.get("steps", [])
            chain_desc = s.get("chain_description", "")
            content = json.dumps({"chain_description": chain_desc, "steps": steps}, ensure_ascii=False)

        conn.execute(
            """INSERT INTO sop_suggestions
               (suggestion_type, wiki_page_id, block_id, chain_id,
                suggested_title, suggested_content, rationale, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (stype, wiki_id, block_id, chain_id, title, content, rationale),
        )
        saved_count += 1
        type_counts[stype] = type_counts.get(stype, 0) + 1

    conn.commit()
    conn.close()

    return {
        "suggestions_created": saved_count,
        "types": type_counts,
        "message": f"Created {saved_count} suggestions" if saved_count else "No suggestions generated",
    }


def _parse_suggestion_json(raw: str) -> list[dict]:
    """Parse AI response into suggestion list. Robust against markdown wrapping."""
    raw = raw.strip()
    # Try extracting JSON from markdown code block
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if m:
        raw = m.group(1).strip()
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "suggestions" in result:
            return result["suggestions"]
        return []
    except json.JSONDecodeError:
        # Try to find JSON array boundaries
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
    return []
