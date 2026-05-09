import os

# 优先使用 HuggingFace 镜像（国内网络环境）
if not os.getenv("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import chromadb
from chromadb.config import Settings

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")

class VectorStore:
    def __init__(self):
        os.makedirs(CHROMA_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        # 使用版本化集合名：中文模型用 1024 维，与旧英文 384 维集合隔离
        self.collection = self.client.get_or_create_collection("documents_zh")
        self.wiki_collection = self.client.get_or_create_collection("wiki_pages")
        self._embed_fn = None
        self._use_api = False

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
                print(f"Embedding: 使用本地模型 {model_name}")
            except Exception as e:
                print(f"本地 embedding 模型 {model_name} 加载失败: {e}")
                # 回退到轻量英文模型
                try:
                    from sentence_transformers import SentenceTransformer
                    self._embed_fn = SentenceTransformer("all-MiniLM-L6-v2")
                    self._use_api = False
                    print("Embedding: 回退到本地模型 all-MiniLM-L6-v2")
                except Exception:
                    print("本地 embedding 模型全部加载失败，回退到 API embedding")
                    self._embed_fn = None
                    self._use_api = True
        return self._embed_fn

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if self._use_api or self.embed_fn is None:
            return self._api_embed(texts)
        try:
            return self.embed_fn.encode(texts, show_progress_bar=False).tolist()
        except Exception as e:
            print(f"本地 embedding 失败: {e}，回退到 API")
            self._use_api = True
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

    def add_document(self, doc_id: int, title: str, chunks: list[str], category: str = "", tags: str = ""):
        if not chunks:
            return
        embeddings = self._get_embeddings(chunks)
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


_store = None

def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
