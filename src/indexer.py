"""
步骤2+3: 分块 + 向量化入库
- 每条条文作为一个独立 Document
- 使用 DashScope Embedding 模型
- 存入 SimpleVectorStore
- 持久化到本地
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.settings import Settings
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.vector_stores.simple import SimpleVectorStore

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    LLM_MODEL,
    VECTOR_STORE_PATH,
    TOP_K,
    SIMILARITY_THRESHOLD,
)
from .model_factory import create_embedding_model, create_llm


class Indexer:
    """《伤寒论》向量索引构建器"""

    def __init__(
        self,
        embedding_model: str = EMBEDDING_MODEL,
        llm_model: str = LLM_MODEL,
        vector_store_path: str = VECTOR_STORE_PATH,
    ):
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.vector_store_path = Path(vector_store_path)

        # 初始化 Embedding 模型
        self.embedding = create_embedding_model(
            model=embedding_model,
            dimension=EMBEDDING_DIM,
        )

        # 初始化 LLM（用于后续问答）
        self.llm = create_llm(model=llm_model)

        # 配置全局设置
        Settings.embed_model = self.embedding
        Settings.llm = self.llm

        self.index: Optional[VectorStoreIndex] = None

    def create_documents(self, data: List[Dict[str, Any]]) -> List[Document]:
        """
        将清洗后的数据转换为 LlamaIndex Document
        每条条文作为一个独立 Document
        """
        documents = []

        for article in data:
            # 构建文档文本
            doc_text = f"【{article['chapter']}】第{article['standard_id']}条\n\n{article['text']}"

            # 构建元数据
            metadata = {
                "id": article.get("id", 0),
                "standard_id": article.get("standard_id", 0),
                "chapter": article.get("chapter", ""),
                "section": article.get("section", ""),
                "category": article.get("category", ""),
                "formulas": ",".join(article.get("formulas", [])),
                "id_range": article.get("id_range", ""),
            }

            # 创建 Document
            doc = Document(
                text=doc_text,
                metadata=metadata,
                id_=f"article_{article.get('id', 0)}",
            )
            documents.append(doc)

        print(f"✅ 成功创建 {len(documents)} 个 Document")
        return documents

    def build_index(self, data: List[Dict[str, Any]], force_rebuild: bool = False) -> VectorStoreIndex:
        """
        构建向量索引

        Args:
            data: 清洗后的条文数据
            force_rebuild: 是否强制重建索引
        """
        print("=" * 50)
        print("步骤2+3: 分块 + 向量化入库")
        print("=" * 50)

        # 检查是否已有索引
        if not force_rebuild and self._index_exists():
            print("📦 检测到已有索引，加载中...")
            return self.load_index()

        # 创建 Documents
        print("\n正在创建文档...")
        documents = self.create_documents(data)

        # 构建索引
        print("\n正在构建向量索引（这可能需要几分钟）...")
        print(f"  - Embedding 模型: {self.embedding_model}")
        print(f"  - 文档数量: {len(documents)}")

        self.index = VectorStoreIndex.from_documents(
            documents,
            show_progress=True,
        )

        # 保存索引
        self.save_index()

        print(f"\n✅ 索引构建完成！")
        print(f"   - 向量维度: {EMBEDDING_DIM}")
        print(f"   - 存储路径: {self.vector_store_path}")

        return self.index

    def _index_exists(self) -> bool:
        """检查索引是否存在"""
        return (
            self.vector_store_path.exists()
            and (self.vector_store_path.parent / "docstore.json").exists()
        )

    def save_index(self) -> None:
        """保存索引到本地"""
        if self.index is None:
            raise ValueError("索引未构建，请先调用 build_index()")

        # 确保目录存在
        self.vector_store_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存向量存储 - 使用 persist() 方法
        persist_path = self.vector_store_path
        self.index.vector_store.persist(persist_path=str(persist_path))

        # 保存文档存储 - 使用 persist() 方法
        docstore_path = self.vector_store_path.parent / "docstore.json"
        self.index.docstore.persist(persist_path=str(docstore_path))

        print(f"   索引已保存至: {self.vector_store_path.parent}")

    def load_index(self) -> VectorStoreIndex:
        """从本地加载索引"""
        from llama_index.core.storage.docstore import SimpleDocumentStore
        from llama_index.core.vector_stores.simple import SimpleVectorStore
        from llama_index.core import Document

        # 加载向量存储
        vector_store = SimpleVectorStore.from_persist_path(str(self.vector_store_path))

        # 加载文档存储
        docstore = SimpleDocumentStore.from_persist_path(
            str(self.vector_store_path.parent / "docstore.json")
        )

        # 获取所有文档ID
        doc_ids = list(docstore.docs.keys())
        if not doc_ids:
            raise ValueError("No documents found in docstore")

        # 将 TextNode 转换为 Document
        documents = []
        for doc_id in doc_ids:
            node = docstore.get_document(doc_id)
            doc = Document(
                text=node.text,
                metadata=node.metadata,
                id_=doc_id,
            )
            documents.append(doc)

        print(f"Loaded {len(documents)} documents from storage")

        # 使用文档和存储上下文构建索引
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
            docstore=docstore,
        )

        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=False,
        )

        print("✅ 索引加载成功！")
        return self.index

    def get_index(self) -> VectorStoreIndex:
        """获取索引（每次启动时快速重建）"""
        if self.index is None:
            # 尝试加载持久化的索引
            from src.index_loader import IndexLoader
            try:
                loader = IndexLoader(str(self.vector_store_path))
                loader.load()
                # 测试检索是否工作
                test_results = loader.retrieve("测试", top_k=1, similarity_threshold=0.0)
                if test_results:
                    print("Index loaded from persisted storage")
                    # 将 loader 包装成可用的索引对象
                    # 创建一个简化的代理对象
                    class IndexProxy:
                        """索引代理 - 使用 IndexLoader"""
                        def __init__(self, loader):
                            self._loader = loader
                            self.index_store = loader.docstore
                            self.vector_store = loader.vector_store

                        def retrieve(self, query, top_k=5, similarity_threshold=0.5):
                            return self._loader.retrieve(query, top_k, similarity_threshold)

                    self.index = IndexProxy(loader)
                    print("Using persisted index (fast startup)")
                    return self.index
            except Exception as e:
                print(f"Failed to load persisted index: {e}")

            # 如果加载失败，快速重建索引
            from src.data_loader import DataLoader
            loader = DataLoader()
            clean_data = loader.load_clean_data()
            print("Rebuilding index...")
            self.index = self.build_index(clean_data, force_rebuild=True)
            return self.index
        return self.index

    def get_index_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        if not self._index_exists():
            return {"exists": False}

        # 尝试读取索引统计信息
        try:
            with open(self.vector_store_path, "r", encoding="utf-8") as f:
                vector_data = json.load(f)

            return {
                "exists": True,
                "vector_count": len(vector_data.get("embedding_dict", {})),
                "storage_path": str(self.vector_store_path),
                "embedding_model": self.embedding_model,
                "embedding_dim": EMBEDDING_DIM,
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}


# 独立运行入口
if __name__ == "__main__":
    from data_loader import DataLoader

    # 1. 加载数据
    loader = DataLoader()
    try:
        clean_data = loader.load_clean_data()
    except FileNotFoundError:
        clean_data = loader.process()

    # 2. 构建索引
    indexer = Indexer()
    indexer.build_index(clean_data, force_rebuild=True)

    # 3. 输出索引信息
    info = indexer.get_index_info()
    print("\n📊 索引信息:")
    for key, value in info.items():
        print(f"  - {key}: {value}")
