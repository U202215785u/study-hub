import os

# 优先使用 HuggingFace 镜像（国内网络环境）
if not os.getenv("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import chromadb
from chromadb.config import Settings

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")

# 模型维度映射表
MODEL_DIMENSIONS = {
    "BAAI/bge-small-zh-v1.5": 512,
    "BAAI/bge-large-zh-v1.5": 1024,
    "all-MiniLM-L6-v2": 384,
}

# 从环境变量读取 fallback 策略：strict = 模型失败时报错；auto = 回退到 API
EMBEDDING_FALLBACK = os.getenv("EMBEDDING_FALLBACK", "strict").lower()


class VectorStore:
    def __init__(self):
        os.makedirs(CHROMA_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        # 使用版本化集合名：中文模型用 1024 维，与旧英文 384 维集合隔离
        self.collection = self._get_or_create_collection_with_meta("documents_zh")
        self.wiki_collection = self._get_or_create_collection_with_meta("wiki_pages")
        self.memory_collection = self._get_or_create_collection_with_meta("memories")
        self._embed_fn = None
        self._use_api = False
        self._current_model = None

    def _get_or_create_collection_with_meta(self, name: str):
        """获取或创建集合，并检查/记录 embedding 模型元数据"""
        collection = self.client.get_or_create_collection(name)
        # 尝试读取已记录的模型信息
        existing_meta = collection.metadata or {}
        recorded_model = existing_meta.get("embedding_model")
        recorded_dim = existing_meta.get("embedding_dim")

        if recorded_model:
            print(f"[{name}] 集合已绑定 embedding 模型: {recorded_model} (dim={recorded_dim})")
        else:
            # 新集合，首次初始化时记录当前模型
            model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
            dim = MODEL_DIMENSIONS.get(model_name, 512)
            collection.modify(metadata={
                "embedding_model": model_name,
                "embedding_dim": dim,
            })
            print(f"[{name}] 新集合，绑定 embedding 模型: {model_name} (dim={dim})")
        return collection

    def _get_collection_model(self, collection) -> str:
        """获取集合绑定的 embedding 模型名"""
        meta = collection.metadata or {}
        return meta.get("embedding_model", os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"))

    def _check_dimension_consistency(self, collection, embeddings: list[list[float]]):
        """检查向量维度与集合记录是否一致"""
        meta = collection.metadata or {}
        recorded_dim = meta.get("embedding_dim")
        if recorded_dim is None or not embeddings:
            return
        actual_dim = len(embeddings[0])
        if actual_dim != recorded_dim:
            print(f"⚠️  维度不一致警告: 集合期望 {recorded_dim} 维，实际得到 {actual_dim} 维")

    @property
    def embed_fn(self):
        if self._embed_fn is None:
            # 优先使用中文优化模型 BGE-large-zh-v1.5（1024维，中文效果远超英文模型）
            # 如需轻量模型可设置环境变量 EMBEDDING_MODEL=all-MiniLM-L6-v2
            model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
            try:
                from sentence_transformers import SentenceTransformer
                self._embed_fn = SentenceTransformer(model_name)
                self._use_api = False
                self._current_model = model_name
                print(f"Embedding: 使用本地模型 {model_name}")
            except Exception as e:
                print(f"本地 embedding 模型 {model_name} 加载失败: {e}")
                if EMBEDDING_FALLBACK == "strict":
                    raise RuntimeError(
                        f"本地 embedding 模型 {model_name} 加载失败，"
                        f"且 EMBEDDING_FALLBACK=strict，禁止回退到 API。"
                        f"请安装模型或设置 EMBEDDING_FALLBACK=auto"
                    )
                # 回退到轻量英文模型
                try:
                    from sentence_transformers import SentenceTransformer
                    self._embed_fn = SentenceTransformer("all-MiniLM-L6-v2")
                    self._use_api = False
                    self._current_model = "all-MiniLM-L6-v2"
                    print("Embedding: 回退到本地模型 all-MiniLM-L6-v2")
                except Exception:
                    print("本地 embedding 模型全部加载失败，回退到 API embedding")
                    self._embed_fn = None
                    self._use_api = True
                    self._current_model = "api"
        return self._embed_fn

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if self._use_api or self.embed_fn is None:
            return self._api_embed(texts)
        try:
            embeddings = self.embed_fn.encode(texts, show_progress_bar=False).tolist()
            return embeddings
        except Exception as e:
            print(f"本地 embedding 失败: {e}")
            if EMBEDDING_FALLBACK == "strict":
                raise RuntimeError(f"本地 embedding 失败且 EMBEDDING_FALLBACK=strict: {e}")
            print("回退到 API")
            self._use_api = True
            self._current_model = "api"
            return self._api_embed(texts)

    def _api_embed(self, texts: list[str]) -> list[list[float]]:
        from ai_client import ai_client
        import asyncio, concurrent.futures
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(ai_client.embed(texts))
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, ai_client.embed(texts)).result()

    def _api_embed(self, texts: list[str]) -> list[list[float]]:
        from ai_client import ai_client
        import asyncio, concurrent.futures
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(ai_client.embed(texts))
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, ai_client.embed(texts)).result()

    def add_document(self, doc_id: int, title: str, chunks: list[str], category: str = "", tags: str = ""):
        if not chunks:
            return
        embeddings = self._get_embeddings(chunks)
        self._check_dimension_consistency(self.collection, embeddings)
        ids = [f"doc{doc_id}_chunk{i}" for i in range(len(chunks))]
        metadatas = [{
            "doc_id": doc_id,
            "title": title,
            "chunk_idx": i,
            "category": category,
            "tags": tags,
        } for i in range(len(chunks))]

        existing = self.collection.get(where={"doc_id": doc_id})
        if existing and existing["ids"]:
            self.collection.delete(ids=existing["ids"])

        self.collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

    def query(self, question: str, top_k: int = 5, category: str = "") -> list[dict]:
        q_embedding = self._get_embeddings([question])
        kwargs = {"query_embeddings": q_embedding, "n_results": top_k}
        if category:
            kwargs["where"] = {"category": category}
        results = self.collection.query(**kwargs)
        out = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                out.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })
        return out

    def count(self) -> int:
        return self.collection.count()

    # —— Wiki 页面索引 ——

    def index_wiki_page(self, page_id: int, title: str, content: str, category: str = "", tags: str = ""):
        """将 Wiki 页面全文嵌入后存入向量库"""
        text = f"{title}\n\n{content}"
        embedding = self._get_embeddings([text])
        self._check_dimension_consistency(self.wiki_collection, embedding)
        doc_id = f"wiki_{page_id}"
        metadata = {"page_id": page_id, "title": title, "category": category, "tags": tags}

        existing = self.wiki_collection.get(ids=[doc_id])
        if existing and existing["ids"]:
            self.wiki_collection.update(ids=[doc_id], embeddings=embedding, documents=[text], metadatas=[metadata])
        else:
            self.wiki_collection.add(ids=[doc_id], embeddings=embedding, documents=[text], metadatas=[metadata])

    def remove_wiki_page(self, page_id: int):
        """从向量库中删除指定 Wiki 页面"""
        doc_id = f"wiki_{page_id}"
        try:
            self.wiki_collection.delete(ids=[doc_id])
        except Exception:
            pass

    def search_wiki(self, query: str, top_k: int = 10) -> list[dict]:
        """语义搜索 Wiki 页面"""
        if self.wiki_collection.count() == 0:
            return []
        q_embedding = self._get_embeddings([query])
        results = self.wiki_collection.query(query_embeddings=q_embedding, n_results=top_k)
        out = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                full_text = results["documents"][0][i] if results["documents"] else ""
                score = results["distances"][0][i] if results.get("distances") else None
                snippet = full_text[:200] if full_text else ""
                out.append({
                    "page_id": meta.get("page_id"),
                    "title": meta.get("title", ""),
                    "snippet": snippet,
                    "score": score,
                    "category": meta.get("category", ""),
                    "tags": meta.get("tags", ""),
                })
        return out

    # —— 统一搜索（RRF 融合） ——

    def unified_search(self, query: str, top_k: int = 5) -> list[dict]:
        """统一搜索：同时查 memories + documents + wiki_pages，RRF 融合排序"""
        q_embedding = self._get_embeddings([query])

        # 从三个 collection 分别查询
        collections = [
            ("memory", self.memory_collection),
            ("document", self.collection),
            ("wiki", self.wiki_collection),
        ]

        all_results = []
        for source, coll in collections:
            if coll.count() == 0:
                continue
            try:
                results = coll.query(query_embeddings=q_embedding, n_results=top_k * 2)
                if results and results["ids"] and results["ids"][0]:
                    for i, doc_id in enumerate(results["ids"][0]):
                        meta = results["metadatas"][0][i] if results["metadatas"] else {}
                        content = results["documents"][0][i] if results["documents"] else ""
                        all_results.append({
                            "id": doc_id,
                            "source": source,
                            "content": content[:300] if content else "",
                            "metadata": meta,
                            "rank": i + 1,  # 用于 RRF
                        })
            except Exception as e:
                print(f"[unified_search] {source} 查询失败: {e}")
                continue

        if not all_results:
            return []

        # RRF 融合排序 (k=60)
        RRF_K = 60
        scores = {}
        for r in all_results:
            key = (r["source"], r["id"])
            if key not in scores:
                scores[key] = {**r, "rrf_score": 0}
            scores[key]["rrf_score"] += 1 / (RRF_K + r["rank"])

        # 按 RRF 分数排序，取 top_k
        ranked = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)
        return ranked[:top_k]

    def get_embedding_status(self) -> dict:
        """返回各 collection 的 embedding 状态"""
        status = {}
        for name, coll in [
            ("documents_zh", self.collection),
            ("wiki_pages", self.wiki_collection),
            ("memories", self.memory_collection),
        ]:
            meta = coll.metadata or {}
            status[name] = {
                "model": meta.get("embedding_model", "unknown"),
                "dim": meta.get("embedding_dim", "unknown"),
                "count": coll.count(),
            }
        status["current_model"] = self._current_model or "unknown"
        status["fallback_mode"] = EMBEDDING_FALLBACK
        return status


_store = None

def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
