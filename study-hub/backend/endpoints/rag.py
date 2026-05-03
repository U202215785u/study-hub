from fastapi import APIRouter
from processing.vector_store import get_vector_store
from ai_client import ai_client
from database import get_db

router = APIRouter()

RAG_SYSTEM_PROMPT = """你是一个知识库助手。请严格基于用户提供的资料来回答问题。

你的整个回复就是一份结构化的知识简报。不要输出"好的"、"以下是回答"等开头语。

## 输出格式

**当找到相关内容时**，严格按以下报纸格式输出：

# （用一句话概括的标题）

> 📚 基于知识库检索 | 匹配文档：N 篇

---

## 核心回答

（用 1-3 段话直接回答问题，信息密度高，不啰嗦）

---

## 关键引用

| # | 来源文档 | 关键内容摘要 |
|:---|:---|:---|
| 1 | 文档名 | 一句话摘要 |
| 2 | 文档名 | 一句话摘要 |

---

## 延伸思考

（1-2 句话：这个答案可能还有哪些值得深入的方向，或知识库中缺失了什么）

**当资料中没有相关信息时**，只输出：

# 未找到相关内容

> 📚 基于知识库检索 | 匹配文档：0 篇

知识库中暂无与该问题相关的内容。建议：上传相关文档后重新搜索。

## 规则
1. 只使用资料中明确出现的信息，不要编造
2. 关键引用表最多列 5 条，按相关度排序
3. 如果只有一个来源文档，关键引用改为单行展示
4. 直接输出以上格式的 Markdown，不要任何额外内容"""


def _get_category_name(category_id) -> str:
    if category_id is None:
        return ""
    conn = get_db()
    row = conn.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()
    conn.close()
    return row["name"] if row else ""


@router.post("/rag/query")
async def rag_query(payload: dict):
    question = (payload.get("question") or "").strip()
    category_id = payload.get("category_id")

    if not question:
        return {"answer": "请输入问题", "sources": []}

    category_name = _get_category_name(category_id)

    vs = get_vector_store()
    chunk_count = vs.count()

    if chunk_count == 0:
        return {"answer": "知识库为空，请先上传文档。", "sources": []}

    results = vs.query(question, top_k=5, category=category_name)
    if not results:
        cat_hint = f"（限定分类: {category_name}）" if category_name else ""
        return {"answer": f"未找到相关内容。{cat_hint}", "sources": []}

    context_parts = []
    sources = []
    seen_titles = set()
    for r in results:
        title = r["metadata"].get("title", "未知文档")
        context_parts.append(f"[来源: {title}]\n{r['content']}")
        if title not in seen_titles:
            sources.append(title)
            seen_titles.add(title)

    context = "\n\n---\n\n".join(context_parts)

    cat_context = f"（限定分类范围: {category_name}）" if category_name else ""
    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": f"参考资料{cat_context}：\n\n{context}\n\n---\n\n问题：{question}"},
    ]

    answer = await ai_client.chat(messages)
    return {"answer": answer, "sources": sources, "category_filter": category_name}
