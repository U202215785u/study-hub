from fastapi import APIRouter
from ai_client import ai_client

router = APIRouter()

AI_CURATOR_PROMPT = """你是一个资源推荐专家。我会给你用户的搜索需求以及 Bing 实时搜索结果。

你的整个回复就是一份结构化的资源简报。不要输出"好的"、"以下是推荐"等开头语。

## 输出格式

严格按以下报纸格式输出：

# （用一句话概括搜索意图的标题）

> 🔍 全网搜索 | 基于 Bing 实时结果

---

## 需求理解

（一句话概括用户真正想要什么）

---

## 推荐资源

| # | 名称 | 类型 | 说明 |
|:---|:---|:---|:---|
| 1 | [名称](URL) | 教程/工具/文章/视频 | 一句话理由 |
| 2 | [名称](URL) | ... | 一句话理由 |

---

## 补充推荐

（你已知的优质资源但搜索结果未出现，标注「💡 补充」）
| # | 名称 | 类型 | 说明 |
|:---|:---|:---|:---|
| 1 | [名称](URL) | ... | 一句话理由 |

---

## 选荐指南

（2-3 句话：新手从哪开始、进阶看什么、哪些是坑）

## 规则
- 5-10 个推荐，优先免费，付费放最后并注明「💰 付费」
- URL 必须真实可访问，不确定的不要放链接
- 如果搜索结果不足，补充推荐可以多放
- 如果没有任何补充推荐，省略「补充推荐」章节
- 直接输出以上格式的 Markdown，不要任何额外内容"""


async def _bing_search(query: str, max_results: int = 10) -> list[dict]:
    """Bing 搜索，返回 title/href/body 列表。失败返回空列表。"""
    import re
    import httpx
    from urllib.parse import urlencode

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        url = f"https://cn.bing.com/search?{urlencode({'q': query, 'count': max_results})}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return []
            html = resp.text
    except Exception:
        return []

    results = []
    blocks = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)

    for block in blocks[:max_results]:
        title = ""
        href = ""

        h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.DOTALL)
        if h2_match:
            a_match = re.search(
                r'<a[^>]*href="(https?://[^"]*)"[^>]*>(.*?)</a>',
                h2_match.group(1), re.DOTALL
            )
            if a_match:
                href = a_match.group(1)
                title = re.sub(r'<[^>]+>', '', a_match.group(2)).strip()

        if not title:
            a_match = re.search(
                r'<a[^>]*href="(https?://[^"]*)"[^>]*>(.*?)</a>',
                block, re.DOTALL
            )
            if a_match:
                href = a_match.group(1)
                title = re.sub(r'<[^>]+>', '', a_match.group(2)).strip()

        if not (href and title):
            continue

        skip_domains = ['bing.com', 'microsoft.com', 'live.com']
        if any(d in href for d in skip_domains):
            continue

        body = ""
        cap_match = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
        if cap_match:
            body = re.sub(r'<[^>]+>', '', cap_match.group(1)).strip()
            body = re.sub(r'&[a-z]+;', ' ', body)
            body = re.sub(r'&#\d+;', '', body)

        results.append({"title": title, "href": href, "body": body})

    return results


@router.post("/ai-search")
async def ai_search(payload: dict):
    question = (payload.get("question") or "").strip()

    if not question:
        return {"answer": "请输入搜索内容"}

    # Step 1: Bing 实时搜索
    search_results = await _bing_search(question)

    if search_results:
        results_text = "\n\n".join(
            f"[{i+1}] {r['title']}\n    URL: {r['href']}\n    {r['body']}"
            for i, r in enumerate(search_results)
        )
        user_msg = f"搜索需求：{question}\n\nBing 搜索结果：\n\n{results_text}"
    else:
        user_msg = f"搜索需求：{question}\n\n（Bing 搜索失败，请基于你的知识推荐，不确定的链接不要放）"

    messages = [
        {"role": "system", "content": AI_CURATOR_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    answer = await ai_client.chat(messages)

    return {
        "answer": answer,
        "question": question,
        "search_results": search_results,
    }
