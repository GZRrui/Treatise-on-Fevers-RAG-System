"""
索引加载器 - 修复新版 llama-index 的持久化问题
使用向量存储和文档存储直接进行检索
"""

from typing import List, Dict, Any, Optional
from llama_index.core.vector_stores.simple import SimpleVectorStore
from llama_index.core.vector_stores.types import VectorStoreQuery
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.schema import TextNode
from pathlib import Path

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
)
from .model_factory import create_embedding_model


class IndexLoader:
    """索引加载器 - 直接使用持久化的向量存储"""

    def __init__(
        self,
        vector_store_path: str,
        embedding_model: str = EMBEDDING_MODEL,
        embedding_dim: int = EMBEDDING_DIM,
        embedding: Any = None,
    ):
        self.vector_store_path = Path(vector_store_path)
        self.docstore_path = self.vector_store_path.parent / "docstore.json"

        self.embedding = embedding or create_embedding_model(
            model=embedding_model, dimension=embedding_dim
        )

        self.vector_store: Optional[SimpleVectorStore] = None
        self.docstore: Optional[SimpleDocumentStore] = None

    def load(self):
        """加载向量存储和文档存储"""
        self.vector_store = SimpleVectorStore.from_persist_path(str(self.vector_store_path))
        self.docstore = SimpleDocumentStore.from_persist_path(str(self.docstore_path))
        return self

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        检索相关条文

        Args:
            query: 用户查询
            top_k: 返回数量
            similarity_threshold: 相似度阈值

        Returns:
            检索结果列表
        """
        if not self.vector_store or not self.docstore:
            self.load()

        # 生成查询向量
        query_embedding = self.embedding.get_text_embedding(query)

        # 执行向量搜索
        vector_query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=top_k * 2,  # 多召回一些，后面过滤
        )
        result = self.vector_store.query(vector_query)

        # 处理结果
        results = []
        ids = result.ids or []
        similarities = result.similarities or []

        for i, doc_id in enumerate(ids):
            if i >= len(similarities):
                break

            score = similarities[i]

            # 过滤相似度阈值
            if score < similarity_threshold:
                continue

            # 从文档存储获取文档
            try:
                node = self.docstore.get_document(doc_id)
                metadata = node.metadata or {}

                # 提取条文文本
                text = node.text
                lines = text.split("\n")
                if len(lines) >= 2:
                    article_text = "\n".join(lines[2:]).strip()
                else:
                    article_text = text

                # 解析方剂
                formulas_str = metadata.get("formulas", "")
                formulas = [f.strip() for f in formulas_str.split(",") if f.strip()]

                results.append({
                    "id": int(metadata.get("id", 0)),
                    "standard_id": int(metadata.get("standard_id", 0)),
                    "chapter": metadata.get("chapter", ""),
                    "section": metadata.get("section", ""),
                    "category": metadata.get("category", ""),
                    "text": article_text,
                    "score": round(score, 4),
                    "formulas": formulas,
                })

                if len(results) >= top_k:
                    break

            except Exception as e:
                print(f"Warning: Failed to get document {doc_id}: {e}")
                continue

        return results


# 独立测试
if __name__ == "__main__":
    from config import VECTOR_STORE_PATH

    print("=== Index Loader Test ===")

    loader = IndexLoader(VECTOR_STORE_PATH)
    loader.load()

    test_queries = [
        "太阳病的主要症状是什么？",
        "桂枝汤的组成是什么？",
        "什么是少阳病？",
    ]

    for query in test_queries:
        print(f"\n--- Query: {query} ---")
        results = loader.retrieve(query, top_k=5, similarity_threshold=0.5)
        print(f"Found {len(results)} results")
        for i, r in enumerate(results[:3], 1):
            print(f"  [{i}] {r['chapter']} 第{r['standard_id']}条 (Score: {r['score']:.4f})")
            print(f"      Text: {r['text'][:60]}...")
