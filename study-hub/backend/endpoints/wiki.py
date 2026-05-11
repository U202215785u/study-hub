import json, re, os
from fastapi import APIRouter
from database import get_db
from ai_client import ai_client
from processing.vector_store import get_vector_store

router = APIRouter()

WIKI_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "wiki")
os.makedirs(WIKI_DIR, exist_ok=True)

#编译哈希缓存文件，用于增量编译（跳过内容未变更的文档）
COMPILED_HASHES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "compiled_hashes.json")

def _load_compiled_hashes() -> dict:
    if os.path.exists(COMPILED_HASHES_PATH):
        try:
            with open(COMPILED_HASHES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def _save_compiled_hashes(hashes: dict):
    os.makedirs(os.path.dirname(COMPILED_HASHES_PATH), exist_ok=True)
    with open(COMPILED_HASHES_PATH, "w", encoding="utf-8") as f:
        json.dump(hashes, f, ensure_ascii=False)

# —— Karpathy LLM Wiki 编译 prompt ——

COMPILE_SYSTEM = """你是一个知识库编译引擎。你的任务是把原始学习资料编译成结构化、互联的 Wiki 页面。

## 核心理念
- 你不是在做"一次性总结"，而是在**持续维护一个持久化知识库**
- 知识库的价值在于**精准的交叉引用**——页面之间通过 [[wikilink]] 形成知识网络，但**只在有实质关联时才链接**
- **资源完整性**：原始文档中的 URL、工具地址、项目链接、参考文章都是知识库的重要组成部分，必须完整提取

## 关联判断标准
关联必须是**具体且可验证的**，满足以下至少一条才建立链接：
1. 技术栈相同（如都是 React 相关内容）
2. 概念有直接依赖关系（如 A 是 B 的底层原理）
3. 同一问题的不同解法（如两种数据库迁移方案）
以下情况**禁止**关联：
- 仅在抽象层面相似（如"都在讲编程"）
- 只是同属一个大类（如"都是 AI"、"都是前端"）
- 关键词碰巧重合但主题不同

## 内容类型识别
首先判断原始文档的类型，决定页面写作策略：

### tutorial（教程/实战）
页面结构：**目标** → **前置条件** → **操作步骤**（每步一个 ### 标题）→ **预期结果** → **常见问题**
- 步骤必须可执行、可复现
- 代码示例完整，包含必要的 import 和环境说明

### concept（概念/原理）
页面结构：**定义** → **核心原理** → **关键机制** → **代码示例** → **常见误区**
- 用通俗语言解释复杂概念，先直觉后严谨
- 至少给出 1 个实际代码示例

### tool（工具介绍）
页面结构：**简介** → **安装/获取** → **核心功能** → **适用场景** → **同类对比** → **资源链接**
- 必须包含工具的官方地址、GitHub 仓库等外部链接
- 说明这个工具解决了什么问题

### comparison（对比分析）
页面结构：**对比背景** → **对比表格**（Markdown 表格）→ **各方案优劣** → **选择建议**
- 必须有对比表格，维度 ≥ 3 个
- 给出明确的选择建议（什么情况下选 A，什么情况下选 B）

### reference（参考/规范）
页面结构：**定义** → **语法/接口** → **参数说明** → **使用示例** → **注意事项**
- 适合 API 文档、配置参考、语法手册类内容

## 学习路径标注
每个新页面需要标注以下元信息：
- **difficulty**：beginner（零基础可读）/ intermediate（需要一定背景）/ advanced（需要深入理解）
- **prerequisites**：建议先阅读的已有页面 slug 列表（从已有页面列表中选择，可空）
- **next_steps**：读完本页后建议继续阅读的页面 slug 列表（可空）
- 标注原则：宁可少标也不要乱标，不确定就留空

## 外部链接提取
**极其重要**：从原始文档中提取**所有**外部 URL，按类型归类：
- `official`：官方文档、官网
- `github`：GitHub 仓库
- `tool`：工具/产品地址
- `article`：参考文章、博客
- `video`：视频链接
- `other`：其他
每个链接记录 `{url, title, type}`。原始文档中提到的每一个 URL 都不能遗漏。

## 输出格式
你必须输出一个 JSON，包含以下字段：
```json
{
  "new_pages": [
    {
      "title": "页面标题（简洁，5-15字）",
      "slug": "url-friendly-slug",
      "content": "完整的 Markdown 内容（按内容类型的结构写）",
      "summary": "1-2句概述",
      "tags": ["标签1", "标签2"],
      "category": "分类名（2-6字）",
      "content_type": "tutorial | concept | tool | comparison | reference",
      "difficulty": "beginner | intermediate | advanced",
      "prerequisites": ["slug1", "slug2"],
      "next_steps": ["slug3"],
      "external_links": [
        {"url": "https://...", "title": "链接标题", "type": "github"}
      ]
    }
  ],
  "update_pages": [
    {
      "slug": "需要更新的已有页面slug",
      "append_content": "追加到该页面的补充内容（Markdown）",
      "reason": "为什么需要更新（须说明具体关联点）",
      "add_external_links": [
        {"url": "https://...", "title": "...", "type": "github"}
      ]
    }
  ],
  "contradictions": [
    {
      "page_slug": "涉及的页面slug",
      "description": "矛盾点描述",
      "source_a": "来源A的说法",
      "source_b": "来源B的说法"
    }
  ],
  "index_update": "一句话说明本次编译对知识库的影响"
}
```

## 写作规则
1. **[[wikilink]] 宁缺毋滥**：只在满足上述关联标准时才添加 [[slug]] 链接
2. **新页面**：按内容类型对应的结构写，每个页面完整自包含
3. **更新已有页面**：只有讨论**同一具体话题**时才追加。不确定时宁建新页面
4. **update_pages 留空是正常的**
5. **外部链接完整**：文档中出现的每个 URL 都要提取到 external_links，同时在 content 的 "## 📎 相关资源" 小节中列出
6. **中文为主**，专业术语保留英文
7. content 中使用 Markdown 格式：标题用 ##/###，代码用代码块，重要概念用 **加粗**
8. 每个页面 content 末尾必须有 "## 📎 相关资源" 小节（即使只有一个链接）
9. 页面标题使用中文，slug 使用英文或拼音
"""

COMPILE_USER_TEMPLATE = """## 已有 Wiki 页面列表
{existing_pages}

## 需要编译的原始文档

### 文档：{doc_title}
{content}

---

请将以上文档编译为 Wiki 页面。注意：
1. 先判断文档的内容类型，按对应结构编写
2. 提取文档中**所有**外部 URL 到 external_links
3. 标注每页的 difficulty、prerequisites、next_steps
4. 如果内容与已有页面相关，更新已有页面而非创建重复页面"""

# —— slug 工具 ——

def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    return s[:80]

# —— Wiki API ——

@router.post("/wiki/compile")
async def compile_wiki(payload: dict):
    """编译所有或指定文档为 Wiki 页面。支持增量模式：跳过内容未变更的文档。"""
    doc_ids = payload.get("doc_ids", [])
    force = payload.get("force", False)

    compiled_hashes = _load_compiled_hashes()

    conn = get_db()
    if doc_ids:
        placeholders = ",".join("?" for _ in doc_ids)
        docs = conn.execute(
            f"SELECT * FROM documents WHERE id IN ({placeholders}) ORDER BY id",
            doc_ids
        ).fetchall()
    else:
        docs = conn.execute(
            "SELECT d.* FROM documents d WHERE d.id NOT IN "
            "(SELECT CAST(json_each.value AS INTEGER) FROM wiki_pages, json_each(wiki_pages.source_doc_ids) "
            "WHERE CAST(json_each.value AS INTEGER) = d.id) "
            "ORDER BY d.id LIMIT 10"
        ).fetchall()

    # 增量编译：过滤掉内容哈希未变更的文档
    skipped = []
    docs_to_compile = []
    for doc in docs:
        doc_dict = dict(doc)
        doc_hash = doc_dict.get("content_hash", "")
        cached_hash = compiled_hashes.get(str(doc_dict["id"]), "")
        if not force and doc_hash and cached_hash and doc_hash == cached_hash:
            skipped.append({"doc_id": doc_dict["id"], "doc_title": doc_dict["title"]})
        else:
            docs_to_compile.append(doc_dict)

    docs = docs_to_compile
    if skipped:
        print(f"[Wiki] 跳过 {len(skipped)} 个未变更的文档")

    if not docs:
        conn.close()
        return {"status": "no_docs", "message": "没有待编译的文档"}

    existing = conn.execute("SELECT slug, title, summary FROM wiki_pages").fetchall()
    existing_lines = []
    for r in existing:
        existing_lines.append(f"- [[{r['slug']}]] {r['title']}：{r['summary'][:80] if r['summary'] else ''}")
    existing_text = "\n".join(existing_lines) if existing_lines else "（空知识库，这是第一批页面）"

    results = []
    all_contradictions = []
    new_page_summaries = []
    updated_page_summaries = []
    for doc in docs:
        doc_dict = dict(doc)
        content = doc_dict.get("content", "")
        if len(content) > 12000:
            content = content[:12000] + "\n\n…(内容过长，已截断前 12000 字)"

        messages = [
            {"role": "system", "content": COMPILE_SYSTEM},
            {"role": "user", "content": COMPILE_USER_TEMPLATE.format(
                existing_pages=existing_text,
                doc_title=doc_dict["title"],
                content=content,
            )},
        ]

        raw = await ai_client.chat(messages, max_tokens=4096)
        try:
            parsed = _parse_json(raw)
            saved = _save_compile_result(parsed, doc_dict["id"], doc_dict["title"])
            # 记录已编译的哈希（增量缓存）
            doc_hash = doc_dict.get("content_hash", "")
            if doc_hash:
                compiled_hashes[str(doc_dict["id"])] = doc_hash
            results.append({
                "doc_id": doc_dict["id"],
                "doc_title": doc_dict["title"],
                "new_pages": len(saved.get("new_pages", [])),
                "updated_pages": len(saved.get("updated_pages", [])),
                "contradictions": len(saved.get("contradictions", [])),
            })
            # 收集新页面/更新页面摘要供进化分析
            for np in saved.get("new_pages", []):
                new_page_summaries.append({"title": np, "slug": np, "summary": doc_dict["title"]})
            for up in saved.get("updated_pages", []):
                updated_page_summaries.append({"slug": up, "reason": f"来自文档: {doc_dict['title']}"})
            for c in saved.get("contradictions", []):
                if isinstance(c, dict):
                    c["_doc_title"] = doc_dict["title"]
                    all_contradictions.append(c)
                else:
                    all_contradictions.append({"description": str(c), "doc_title": doc_dict["title"]})
        except Exception as e:
            results.append({"doc_id": doc_dict["id"], "doc_title": doc_dict["title"], "error": str(e)})

        # 刷新已有页面列表供下一篇使用
        existing = conn.execute("SELECT slug, title, summary FROM wiki_pages").fetchall()
        existing_lines = []
        for r in existing:
            existing_lines.append(f"- [[{r['slug']}]] {r['title']}：{r['summary'][:80] if r['summary'] else ''}")
        existing_text = "\n".join(existing_lines)

    conn.close()
    _save_compiled_hashes(compiled_hashes)

    # --- 进化系统钩子 ---
    evolution_info = None
    try:
        from evolution_pipeline import analyze_evolution
        evolution_info = await analyze_evolution(
            new_pages=new_page_summaries,
            updated_pages=updated_page_summaries,
            contradictions=all_contradictions,
            review_summary="",
            source_event_type="wiki_compile",
            source_event_id=0,
        )
        print(f"[Evolution] Wiki compile: {evolution_info.get('low_risk_applied', 0)} low-risk applied, "
              f"{evolution_info.get('medium_risk_pending', 0)} medium pending, "
              f"{evolution_info.get('high_risk_logged', 0)} high logged")
    except Exception as e:
        print(f"[Evolution] Wiki hook failed (non-fatal): {e}")

    response = {"status": "done", "results": results, "skipped": skipped}
    if evolution_info:
        response["evolution"] = {
            "low_risk_applied": evolution_info["low_risk_applied"],
            "medium_risk_pending": evolution_info["medium_risk_pending"],
            "high_risk_logged": evolution_info["high_risk_logged"],
            "snapshot_id": evolution_info["snapshot_id"],
        }
    return response


@router.get("/wiki/pages")
def list_wiki_pages(category: str = None, search: str = None):
    conn = get_db()
    if search:
        rows = conn.execute(
            "SELECT id, title, slug, summary, tags, category, content_type, difficulty, "
            "external_links, prerequisites, next_steps, version, char_count, "
            "created_at, updated_at FROM wiki_pages "
            "WHERE title LIKE ? OR content LIKE ? OR summary LIKE ? OR tags LIKE ? "
            "ORDER BY updated_at DESC",
            (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"),
        ).fetchall()
    elif category:
        rows = conn.execute(
            "SELECT id, title, slug, summary, tags, category, content_type, difficulty, "
            "external_links, prerequisites, next_steps, version, char_count, "
            "created_at, updated_at FROM wiki_pages WHERE category = ? ORDER BY updated_at DESC",
            (category,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, slug, summary, tags, category, content_type, difficulty, "
            "external_links, prerequisites, next_steps, version, char_count, "
            "created_at, updated_at FROM wiki_pages ORDER BY updated_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/wiki/pages/{page_id}")
def get_wiki_page(page_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM wiki_pages WHERE id = ?", (page_id,)).fetchone()
    if not row:
        # try slug
        row = conn.execute("SELECT * FROM wiki_pages WHERE slug = ?", (str(page_id),)).fetchone()
    if not row:
        conn.close()
        return {"error": "Wiki 页面不存在"}

    page = dict(row)
    # 获取入链
    in_links = conn.execute(
        "SELECT wp.title, wp.slug FROM wiki_links wl "
        "JOIN wiki_pages wp ON wl.source_page_id = wp.id "
        "WHERE wl.target_page_slug = ?",
        (page["slug"],),
    ).fetchall()
    # 获取出链
    out_links = conn.execute(
        "SELECT * FROM wiki_links WHERE source_page_id = ?", (page["id"],)
    ).fetchall()

    conn.close()
    page["in_links"] = [dict(r) for r in in_links]
    page["out_links"] = [dict(r) for r in out_links]
    return page


@router.get("/wiki/graph")
def get_wiki_graph():
    """返回知识图谱数据：nodes + edges"""
    conn = get_db()
    pages = conn.execute("SELECT id, title, slug, category, tags FROM wiki_pages").fetchall()
    links = conn.execute(
        "SELECT wl.source_page_id, wp.slug as source_slug, wp.title as source_title, "
        "wl.target_page_slug, wl.link_type "
        "FROM wiki_links wl JOIN wiki_pages wp ON wl.source_page_id = wp.id"
    ).fetchall()
    conn.close()

    nodes = []
    for p in pages:
        p = dict(p)
        nodes.append({
            "id": p["slug"],
            "label": p["title"],
            "category": p["category"],
            "tags": json.loads(p["tags"]) if p["tags"] else [],
        })

    edges = []
    seen = set()
    for l in links:
        l = dict(l)
        key = (l["source_slug"], l["target_page_slug"])
        if key not in seen:
            seen.add(key)
            edges.append({
                "source": l["source_slug"],
                "target": l["target_page_slug"],
                "type": l["link_type"],
            })

    return {"nodes": nodes, "edges": edges}


@router.get("/wiki/categories")
def get_wiki_categories():
    conn = get_db()
    rows = conn.execute(
        "SELECT category, COUNT(*) as count FROM wiki_pages "
        "WHERE category != '' GROUP BY category ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.delete("/wiki/pages/{page_id}")
def delete_wiki_page(page_id: int):
    conn = get_db()
    page = conn.execute("SELECT * FROM wiki_pages WHERE id = ?", (page_id,)).fetchone()
    if not page:
        conn.close()
        return {"error": "Wiki 页面不存在"}
    conn.execute("DELETE FROM wiki_links WHERE source_page_id = ?", (page_id,))
    conn.execute("DELETE FROM wiki_pages WHERE id = ?", (page_id,))
    conn.commit()
    get_vector_store().remove_wiki_page(page_id)
    conn.close()
    return {"status": "ok"}


@router.put("/wiki/pages/{page_id}")
def update_wiki_page(page_id: int, payload: dict):
    """手动编辑 Wiki 页面"""
    conn = get_db()
    page = conn.execute("SELECT * FROM wiki_pages WHERE id = ?", (page_id,)).fetchone()
    if not page:
        conn.close()
        return {"error": "Wiki 页面不存在"}

    title = payload.get("title", "").strip()
    content = payload.get("content", "").strip()
    if not title or not content:
        conn.close()
        return {"error": "标题和内容不能为空"}

    category = payload.get("category", "")
    tags = payload.get("tags", [])
    tags_json = json.dumps(tags, ensure_ascii=False)
    content_type = payload.get("content_type", page["content_type"] if isinstance(page, dict) else "")
    difficulty = payload.get("difficulty", page["difficulty"] if isinstance(page, dict) else "")
    ext_links = json.dumps(payload.get("external_links", []), ensure_ascii=False)
    prereqs = json.dumps(payload.get("prerequisites", []), ensure_ascii=False)
    nexts = json.dumps(payload.get("next_steps", []), ensure_ascii=False)

    # Update slug if title changed
    slug = slugify(title)
    if slug != page["slug"]:
        existing = conn.execute("SELECT id FROM wiki_pages WHERE slug = ? AND id != ?", (slug, page_id)).fetchone()
        if existing:
            slug = f"{slug}-{page_id}"

    conn.execute(
        "UPDATE wiki_pages SET title = ?, slug = ?, content = ?, summary = ?, category = ?, tags = ?, "
        "content_type = ?, difficulty = ?, external_links = ?, prerequisites = ?, next_steps = ?, "
        "char_count = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (title, slug, content, payload.get("summary", page["summary"] or ""),
         category, tags_json, content_type, difficulty, ext_links, prereqs, nexts, len(content), page_id),
    )

    # Re-extract wikilinks from updated content
    conn.execute("DELETE FROM wiki_links WHERE source_page_id = ?", (page_id,))
    wikilinks = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
    for target in set(wikilinks):
        target = target.strip()
        conn.execute(
            "INSERT OR IGNORE INTO wiki_links (source_page_id, target_page_slug, link_type) "
            "VALUES (?, ?, 'reference')",
            (page_id, target),
        )

    conn.commit()

    # 更新向量索引
    get_vector_store().index_wiki_page(page_id, title, content, category, tags_json)

    conn.close()
    return {"status": "ok", "slug": slug, "version": page["version"] + 1}


@router.delete("/wiki/pages")
def delete_all_wiki_pages():
    conn = get_db()
    conn.execute("DELETE FROM wiki_links")
    conn.execute("DELETE FROM wiki_pages")
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "所有 Wiki 页面已清除"}


@router.post("/wiki/regenerate")
async def regenerate_wiki():
    """清空 Wiki 并重新编译所有文档"""
    conn = get_db()
    conn.execute("DELETE FROM wiki_links")
    conn.execute("DELETE FROM wiki_pages")
    conn.commit()

    docs = conn.execute("SELECT id FROM documents ORDER BY id").fetchall()
    conn.close()

    if not docs:
        return {"status": "no_docs", "message": "知识库中没有文档"}

    doc_ids = [d["id"] for d in docs]
    return await compile_wiki({"doc_ids": doc_ids, "force": True})


@router.post("/wiki/search")
async def search_wiki(payload: dict):
    """语义搜索 Wiki 页面"""
    query = (payload.get("query") or "").strip()
    if not query:
        return {"results": [], "query": ""}

    top_k = payload.get("top_k", 10)
    vs = get_vector_store()
    results = vs.search_wiki(query, top_k=top_k)

    # Enrich with slug from DB
    if results:
        conn = get_db()
        page_ids = [r["page_id"] for r in results if r.get("page_id")]
        placeholders = ",".join("?" for _ in page_ids)
        rows = conn.execute(
            f"SELECT id, slug, version FROM wiki_pages WHERE id IN ({placeholders})",
            page_ids,
        ).fetchall()
        conn.close()
        slug_map = {r["id"]: r for r in rows}
        for r in results:
            pid = r.get("page_id")
            if pid and pid in slug_map:
                r["slug"] = slug_map[pid]["slug"]
                r["version"] = slug_map[pid]["version"]

    return {"results": results, "query": query}


@router.post("/wiki/reindex")
async def reindex_wiki():
    """重建所有 Wiki 页面的向量索引"""
    conn = get_db()
    pages = conn.execute("SELECT id, title, content, category, tags FROM wiki_pages").fetchall()
    conn.close()

    if not pages:
        return {"status": "no_pages", "message": "没有 Wiki 页面可索引"}

    vs = get_vector_store()
    count = 0
    for p in pages:
        p = dict(p)
        vs.index_wiki_page(p["id"], p["title"], p["content"], p.get("category", ""), p.get("tags", ""))
        count += 1

    return {"status": "ok", "indexed": count}


@router.post("/wiki/learning-paths")
async def generate_learning_paths():
    """分析所有 Wiki 页面，自动生成学习路径"""
    conn = get_db()
    pages = conn.execute(
        "SELECT id, title, slug, summary, category, content_type, difficulty, tags, prerequisites, next_steps "
        "FROM wiki_pages ORDER BY category, difficulty, title"
    ).fetchall()
    conn.close()

    if not pages:
        return {"status": "no_pages", "message": "没有 Wiki 页面"}

    # Build page summary for LLM
    page_list = []
    for p in pages:
        p = dict(p)
        diff = p.get("difficulty", "") or ""
        ctype = p.get("content_type", "") or ""
        cat = p.get("category", "") or ""
        page_list.append(
            f"- [[{p['slug']}]] {p['title']} "
            f"({'入门' if diff == 'beginner' else '进阶' if diff == 'intermediate' else '高级' if diff == 'advanced' else '未知难度'}) "
            f"[{ctype or '未知类型'}] "
            f"分类:{cat} "
            f"摘要:{p.get('summary', '')[:60]}"
        )

    messages = [
        {"role": "system", "content": """你是一个知识库学习路径规划师。分析所有 Wiki 页面，为不同类型的学习者设计学习路径。

## 输出格式
```json
{
  "paths": [
    {
      "title": "路径名称（吸引人，10-20字）",
      "description": "这个路径适合谁，能学到什么",
      "target_audience": "适合人群（如：零基础入门 / 有编程基础 / 进阶提升）",
      "pages": [
        {
          "slug": "页面slug",
          "order": 1,
          "reason": "为什么先学这个（10-20字）"
        }
      ]
    }
  ],
  "hub_page_content": "一个综述页面的 Markdown 内容，作为学习路径的总入口页面，介绍所有路径"
}
```

## 路径设计原则
1. 从易到难：beginner → intermediate → advanced
2. 同一个路径内的页面要有递进关系，不是随机堆砌
3. 每个路径 5-12 个页面，太少没意义，太多吓人
4. 路径之间可以有交叉（同一页面可出现在多个路径）
5. 给每个路径起一个有吸引力的名字，不要叫"XX学习路径"

## 路径类型建议（根据实际页面灵活调整，不要生造不存在的路径）
- 如果有 AI 编程相关内容 → "AI 编程实战之路"
- 如果有 Python 相关内容 → "Python 进阶之路"
- 如果有开发工具相关内容 → "开发者工具链"
- 根据实际内容自由发挥"""},
        {"role": "user", "content": "## 所有 Wiki 页面\n\n" + "\n".join(page_list) +
         "\n\n---\n\n请为这些页面设计 2-4 个学习路径。如果页面太少（< 10个），只设计 1-2 个路径。"},
    ]

    raw = await ai_client.chat(messages, max_tokens=4096)
    parsed = _parse_json(raw)

    # Save paths and hub page
    conn = get_db()
    saved_paths = []
    for path in parsed.get("paths", []):
        path_slugs = json.dumps([p["slug"] for p in path.get("pages", [])], ensure_ascii=False)
        path_title = path.get("title", "")
        path_slug = slugify(path_title)
        path_content = f"# {path_title}\n\n**适合人群**：{path.get('target_audience', '')}\n\n{path.get('description', '')}\n\n## 学习路线\n\n"
        for i, step in enumerate(path.get("pages", []), 1):
            path_content += f"{i}. **[[{step['slug']}]]** — {step.get('reason', '')}\n"
        path_content += "\n\n---\n\n> 此学习路径由 AI 自动生成，基于页面间的依赖关系和难度递进"

        # Upsert
        existing = conn.execute("SELECT id FROM wiki_pages WHERE slug = ?", (path_slug,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE wiki_pages SET title=?, content=?, summary=?, category=?, tags=?, "
                "char_count=?, version=version+1, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (path_title, path_content, path.get("description", ""), "学习路径",
                 json.dumps(["学习路径"], ensure_ascii=False), len(path_content), existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO wiki_pages (title, slug, content, summary, source_doc_ids, tags, category, char_count) "
                "VALUES (?, ?, ?, ?, '[]', ?, ?, ?)",
                (path_title, path_slug, path_content, path.get("description", ""),
                 json.dumps(["学习路径"], ensure_ascii=False), "学习路径", len(path_content)),
            )
        saved_paths.append({"slug": path_slug, "title": path_title, "steps": len(path.get("pages", []))})

    # Save hub page
    hub_content = parsed.get("hub_page_content", "")
    if hub_content:
        hub_slug = "learning-paths"
        hub_title = "📚 学习路径总览"
        existing = conn.execute("SELECT id FROM wiki_pages WHERE slug = ?", (hub_slug,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE wiki_pages SET title=?, content=?, summary=?, category=?, tags=?, "
                "char_count=?, version=version+1, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (hub_title, hub_content, "知识库学习路径总览", "学习路径",
                 json.dumps(["学习路径", "入门指引"], ensure_ascii=False), len(hub_content), existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO wiki_pages (title, slug, content, summary, source_doc_ids, tags, category, char_count) "
                "VALUES (?, ?, ?, ?, '[]', ?, ?, ?)",
                (hub_title, hub_slug, hub_content, "知识库学习路径总览",
                 json.dumps(["学习路径", "入门指引"], ensure_ascii=False), "学习路径", len(hub_content)),
            )
        saved_paths.append({"slug": hub_slug, "title": hub_title, "steps": 0})

    conn.commit()
    conn.close()
    return {"status": "ok", "paths": saved_paths}


@router.post("/wiki/category-overviews")
async def generate_category_overviews():
    """为每个分类生成综述 hub 页面"""
    conn = get_db()
    categories = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM wiki_pages "
        "WHERE category != '' AND category != '学习路径' GROUP BY category HAVING cnt >= 2 ORDER BY cnt DESC"
    ).fetchall()
    conn.close()

    if not categories:
        return {"status": "no_categories", "message": "没有足够页面生成分类综述"}

    results = []
    for cat_row in categories:
        cat = cat_row["category"]
        conn = get_db()
        pages = conn.execute(
            "SELECT title, slug, summary, content_type, difficulty, char_count "
            "FROM wiki_pages WHERE category = ? ORDER BY title", (cat,)
        ).fetchall()
        conn.close()

        page_list = []
        for p in pages:
            p = dict(p)
            page_list.append(
                f"- [[{p['slug']}]] {p['title']} "
                f"({p.get('difficulty', '') or '未知'} / {p.get('content_type', '') or '未知类型'} / {p['char_count']}字) "
                f"{p.get('summary', '')[:80]}"
            )

        messages = [
            {"role": "system", "content": f"""你是知识库分类综述撰写专家。为分类"{cat}"下的所有页面写一个综述 hub 页面。

## 综述页结构
```markdown
# {cat} 知识综述

## 本分类涵盖

（2-3句话概述这个分类涉及哪些主题，适合谁来读）

## 核心概念速览

（用一个 Markdown 表格列出关键概念，每行：概念名 | 简要说明 | 相关页面）

## 推荐阅读顺序

（按从易到难排列本分类下的页面，每个页面一句话说明为什么读）

## 页面索引

（完整列出本分类下所有页面的链接和简介）
```

## 要求
- 把分散的页面串联成有逻辑的知识体系
- 给读者一个清晰的导航，知道先看什么后看什么
- 用 [[slug]] 引用页面"""},
            {"role": "user", "content": f"## 分类：{cat}\n\n" + "\n".join(page_list) +
             "\n\n---\n\n请撰写这个分类的综述 hub 页面。"},
        ]

        raw = await ai_client.chat(messages, max_tokens=2048)
        parsed = raw.strip()
        # Remove markdown code fences if present
        m = re.search(r'```(?:markdown)?\s*([\s\S]*?)```', parsed)
        if m:
            parsed = m.group(1).strip()

        slug = slugify(f"{cat}-综述")
        title = f"📂 {cat} · 知识综述"
        summary = f"{cat} 分类下的知识综述，包含 {len(pages)} 个相关页面"

        conn = get_db()
        existing = conn.execute("SELECT id FROM wiki_pages WHERE slug = ?", (slug,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE wiki_pages SET title=?, content=?, summary=?, category=?, char_count=?, "
                "version=version+1, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (title, parsed, summary, cat, len(parsed), existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO wiki_pages (title, slug, content, summary, source_doc_ids, tags, category, char_count) "
                "VALUES (?, ?, ?, ?, '[]', ?, ?, ?)",
                (title, slug, parsed, summary, json.dumps(["综述", cat], ensure_ascii=False), cat, len(parsed)),
            )
        conn.commit()
        conn.close()
        results.append({"category": cat, "slug": slug, "page_count": len(pages)})

    return {"status": "ok", "overviews": results}


def _parse_json(raw: str) -> dict:
    """从 AI 回复中提取 JSON，兼容各种 LLM 输出格式问题"""
    raw = raw.strip()
    # 移除 markdown 代码块包裹
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if m:
        raw = m.group(1).strip()

    # 尝试直接解析
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 修复常见 LLM JSON 问题：字符串值中含未转义换行
    fixed = re.sub(r'(?<=[^\\])\\(?=[^"\\/bfnrtu])', r'\\\\', raw)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 尝试截断到最后一个完整的顶层键
    # 找到最后一个 "key": 后跟完整值的位置
    try:
        # 尝试用 json.loads 逐行恢复
        for end_char in range(len(raw), 0, -1):
            try:
                return json.loads(raw[:end_char] + ('}' if not raw[:end_char].rstrip().endswith('}') else ''))
            except json.JSONDecodeError:
                continue
    except Exception:
        pass

    # 最终回退：提取能提取的字段
    result = {"new_pages": [], "update_pages": [], "contradictions": [], "index_update": ""}
    try:
        partial = raw[:raw.rfind('}')+1] if '}' in raw else raw
        result = json.loads(partial)
    except Exception:
        pass
    return result


def _save_compile_result(parsed: dict, source_doc_id: int, source_title: str) -> dict:
    conn = get_db()
    updated = []
    new_pages = []

    # 处理新页面
    for p in parsed.get("new_pages", []):
        title = p["title"].strip()
        slug = p.get("slug", "") or slugify(title)
        content = p.get("content", "")
        summary = p.get("summary", "")
        tags = json.dumps(p.get("tags", []), ensure_ascii=False)
        category = p.get("category", "")
        content_type = p.get("content_type", "")
        difficulty = p.get("difficulty", "")
        ext_links = json.dumps(p.get("external_links", []), ensure_ascii=False)
        prereqs = json.dumps(p.get("prerequisites", []), ensure_ascii=False)
        nexts = json.dumps(p.get("next_steps", []), ensure_ascii=False)

        # 检查是否已存在同 slug 页面
        existing = conn.execute("SELECT id FROM wiki_pages WHERE slug = ?", (slug,)).fetchone()
        if existing:
            # 追加内容，合并 external_links
            conn.execute(
                "UPDATE wiki_pages SET content = content || '\n\n---\n\n' || ?, "
                "version = version + 1, char_count = char_count + ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (content, len(content), existing["id"]),
            )
            # 合并新的 external_links 到已有页面
            if ext_links and ext_links != "[]":
                old_links = conn.execute(
                    "SELECT external_links FROM wiki_pages WHERE id = ?", (existing["id"],)
                ).fetchone()
                old = json.loads(old_links["external_links"]) if old_links and old_links["external_links"] else []
                new_list = p.get("external_links", [])
                old_urls = {l["url"] for l in old if "url" in l}
                for link in new_list:
                    if link.get("url") and link["url"] not in old_urls:
                        old.append(link)
                conn.execute("UPDATE wiki_pages SET external_links = ? WHERE id = ?",
                             (json.dumps(old, ensure_ascii=False), existing["id"]))
            updated.append(slug)
        else:
            conn.execute(
                "INSERT INTO wiki_pages (title, slug, content, summary, source_doc_ids, tags, category, "
                "content_type, difficulty, external_links, prerequisites, next_steps, char_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, slug, content, summary, json.dumps([source_doc_id]), tags, category,
                 content_type, difficulty, ext_links, prereqs, nexts, len(content)),
            )
            new_pages.append(slug)

    # 处理更新已有页面
    for u in parsed.get("update_pages", []):
        slug = u.get("slug", "")
        append_content = u.get("append_content", "")
        if slug and append_content:
            existing = conn.execute("SELECT id FROM wiki_pages WHERE slug = ?", (slug,)).fetchone()
            if existing:
                dated = f"\n\n> 更新来源：{source_title}\n\n{append_content}"
                conn.execute(
                    "UPDATE wiki_pages SET content = content || ?, "
                    "version = version + 1, char_count = char_count + ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE slug = ?",
                    (dated, len(dated), slug),
                )
                # 更新 source_doc_ids
                page = conn.execute("SELECT source_doc_ids, external_links FROM wiki_pages WHERE slug = ?", (slug,)).fetchone()
                sids = json.loads(page["source_doc_ids"]) if page["source_doc_ids"] else []
                if source_doc_id not in sids:
                    sids.append(source_doc_id)
                    conn.execute("UPDATE wiki_pages SET source_doc_ids = ? WHERE slug = ?",
                                 (json.dumps(sids), slug))
                # 合并新的 external_links
                add_links = u.get("add_external_links", [])
                if add_links:
                    old_links = json.loads(page["external_links"]) if page["external_links"] else []
                    old_urls = {l["url"] for l in old_links if "url" in l}
                    for link in add_links:
                        if link.get("url") and link["url"] not in old_urls:
                            old_links.append(link)
                    conn.execute("UPDATE wiki_pages SET external_links = ? WHERE slug = ?",
                                 (json.dumps(old_links, ensure_ascii=False), slug))
                updated.append(slug)

    # 处理矛盾
    contradictions = parsed.get("contradictions", [])

    # 提取新页面中的 [[wikilinks]] 写入 wiki_links 表
    for p in parsed.get("new_pages", []):
        slug = p.get("slug", "") or slugify(p["title"])
        content = p.get("content", "")
        wikilinks = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
        page_row = conn.execute("SELECT id FROM wiki_pages WHERE slug = ?", (slug,)).fetchone()
        if page_row:
            for target in set(wikilinks):
                target = target.strip()
                conn.execute(
                    "INSERT OR IGNORE INTO wiki_links (source_page_id, target_page_slug, link_type) "
                    "VALUES (?, ?, 'reference')",
                    (page_row["id"], target),
                )

    conn.commit()

    # 索引新创建和更新的页面到向量库
    vs = get_vector_store()
    for slug in new_pages + updated:
        row = conn.execute(
            "SELECT id, title, content, category, tags FROM wiki_pages WHERE slug = ?", (slug,)
        ).fetchone()
        if row:
            row = dict(row)
            vs.index_wiki_page(row["id"], row["title"], row["content"],
                               row.get("category", ""), row.get("tags", ""))

    conn.close()
    return {"new_pages": new_pages, "updated_pages": updated, "contradictions": contradictions}
