"""
步骤4: 检索链路封装
- 用户 query 向量化
- Top-k 召回相关条文
- 相似度排序
- 返回格式化结果
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor

from config import TOP_K, SIMILARITY_THRESHOLD


@dataclass
class RetrievedArticle:
    """检索结果 dataclass"""
    id: int
    standard_id: int
    chapter: str
    section: str
    category: str
    text: str
    score: float
    formulas: List[str]


class Retriever:
    """《伤寒论》条文检索器"""

    def __init__(
        self,
        index: Any,
        top_k: int = TOP_K,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
    ):
        """
        初始化检索器

        Args:
            index: LlamaIndex 向量索引 或 IndexProxy
            top_k: 召回数量
            similarity_threshold: 相似度阈值
        """
        self.index = index
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        # 检查是否是 IndexProxy（使用持久化索引）
        if hasattr(index, '_loader'):
            self._use_proxy = True
        else:
            self._use_proxy = False
            # 配置检索器
            self.retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=top_k * 2,  # 多召回一些，后面过滤
            )

            # 配置后处理器
            self.postprocessor = SimilarityPostprocessor(
                similarity_cutoff=similarity_threshold,
            )

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[RetrievedArticle]:
        """
        检索相关条文

        Args:
            query: 用户查询

        Returns:
            检索结果列表
        """
        effective_top_k = top_k or self.top_k

        # 如果使用 IndexProxy，直接调用
        if self._use_proxy:
            raw_results = self.index.retrieve(
                query,
                effective_top_k,
                self.similarity_threshold,
            )
            return [
                RetrievedArticle(
                    id=r["id"],
                    standard_id=r["standard_id"],
                    chapter=r["chapter"],
                    section=r["section"],
                    category=r["category"],
                    text=r["text"],
                    score=r["score"],
                    formulas=r["formulas"],
                )
                for r in raw_results
            ]

        # 执行检索
        retriever = self.retriever
        if effective_top_k != self.top_k:
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=effective_top_k * 2,
            )
        nodes = retriever.retrieve(query)

        # 过滤和转换结果
        results = []
        for node in nodes:
            # 检查相似度阈值
            if node.score < self.similarity_threshold:
                continue

            # 解析元数据
            metadata = node.metadata or {}

            # 提取条文文本（去除章节前缀）
            full_text = node.text
            text = self._extract_article_text(full_text)

            # 解析方剂
            formulas_str = metadata.get("formulas", "")
            formulas = [f.strip() for f in formulas_str.split(",") if f.strip()]

            # 构建检索结果
            result = RetrievedArticle(
                id=int(metadata.get("id", 0)),
                standard_id=int(metadata.get("standard_id", 0)),
                chapter=metadata.get("chapter", ""),
                section=metadata.get("section", ""),
                category=metadata.get("category", ""),
                text=text,
                score=node.score,
                formulas=formulas,
            )
            results.append(result)

            # 控制返回数量
            if len(results) >= effective_top_k:
                break

        return results

    def _extract_article_text(self, full_text: str) -> str:
        """从完整文本中提取条文正文"""
        # 格式: "【辨太阳病脉证并治上】第1条\n\n条文正文..."
        lines = full_text.split("\n")
        # 跳过第一行标题，返回正文
        if len(lines) >= 2:
            return "\n".join(lines[2:]).strip()
        return full_text

    def retrieve_as_dict(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        检索并返回字典格式结果

        Args:
            query: 用户查询

        Returns:
            字典格式的检索结果
        """
        results = self.retrieve(query, top_k=top_k)
        return self.to_dict(results)

    @staticmethod
    def to_dict(results: List[RetrievedArticle]) -> List[Dict[str, Any]]:
        return [
            {
                "id": r.id,
                "standard_id": r.standard_id,
                "chapter": r.chapter,
                "section": r.section,
                "category": r.category,
                "text": r.text,
                "score": round(r.score, 4),
                "formulas": r.formulas,
            }
            for r in results
        ]

    def format_results(self, results: List[RetrievedArticle]) -> str:
        """
        格式化检索结果为可读文本

        Args:
            results: 检索结果列表

        Returns:
            格式化后的文本
        """
        if not results:
            return "未找到相关条文"

        output = []
        output.append("=" * 60)
        output.append(f"检索到 {len(results)} 条相关条文:\n")

        for i, result in enumerate(results, 1):
            output.append(f"【{i}】{result.chapter} 第{result.standard_id}条")
            output.append(f"    相似度: {result.score:.4f}")
            if result.formulas:
                output.append(f"    涉及方剂: {', '.join(result.formulas)}")
            output.append(f"    条文内容: {result.text}")
            output.append("")

        return "\n".join(output)

    def get_context_for_llm(self, results: List[RetrievedArticle]) -> str:
        """
        构建用于 LLM 的上下文

        Args:
            results: 检索结果列表

        Returns:
            上下文字符串
        """
        if not results:
            return "未在《伤寒论》中找到相关信息。"

        context_parts = []
        for result in results:
            part = f"【{result.chapter} 第{result.standard_id}条】\n{result.text}"
            if result.formulas:
                part += f"\n（方剂: {', '.join(result.formulas)}）"
            context_parts.append(part)

        return "\n\n---\n\n".join(context_parts)


# 独立运行入口
if __name__ == "__main__":
    from indexer import Indexer
    from data_loader import DataLoader

    # 1. 加载数据并构建索引
    loader = DataLoader()
    try:
        clean_data = loader.load_clean_data()
    except FileNotFoundError:
        clean_data = loader.process()

    indexer = Indexer()
    try:
        index = indexer.get_index()
    except ValueError:
        index = indexer.build_index(clean_data, force_rebuild=True)

    # 2. 创建检索器
    retriever = Retriever(index, top_k=5, similarity_threshold=0.6)

    # 3. 测试检索
    test_queries = [
        "太阳病的主要症状是什么？",
        "桂枝汤的组成是什么？",
        "什么是少阳病？",
    ]

    print("=" * 60)
    print("检索链路测试")
    print("=" * 60)

    for query in test_queries:
        print(f"\n🔍 查询: {query}")
        results = retriever.retrieve(query)
        print(retriever.format_results(results))
