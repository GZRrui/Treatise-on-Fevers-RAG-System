"""
步骤6: LLM 调用 + 问答引擎
- 组装检索 → Prompt → LLM → 输出答案
- 支持流式输出
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
import logging

from llama_index.core import VectorStoreIndex
from llama_index.core.llms import ChatMessage, MessageRole

from config import LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from .retriever import Retriever
from .prompt_template import PromptTemplate
from .model_factory import create_llm

logger = logging.getLogger(__name__)


class QAEngine:
    """《伤寒论》问答引擎"""

    def __init__(
        self,
        index: VectorStoreIndex,
        llm_model: str = LLM_MODEL,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
        top_k: int = 5,
        similarity_threshold: float = 0.6,
    ):
        """
        初始化问答引擎

        Args:
            index: LlamaIndex 向量索引
            llm_model: LLM 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            top_k: 检索数量
            similarity_threshold: 相似度阈值
        """
        self.index = index
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        # 初始化 LLM
        self.llm = create_llm(
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 初始化检索器
        self.retriever = Retriever(
            index=index,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        # 初始化 Prompt 模板
        self.prompt_template = PromptTemplate()

    def answer(
        self,
        query: str,
        return_sources: bool = True,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        同步问答

        Args:
            query: 用户问题
            return_sources: 是否返回引用来源

        Returns:
            {
                "answer": str,           # LLM 回答
                "sources": List[Dict],   # 引用的条文
                "query": str,            # 用户问题
            }
        """
        logger.info(f"收到问答请求: {query}")

        # 1. 检索相关条文
        retrieved = self.retriever.retrieve(query, top_k=top_k)
        retrieved_dict = self.retriever.to_dict(retrieved)

        logger.info(f"检索到 {len(retrieved)} 条相关条文")

        # 2. 构建上下文
        context = self.retriever.get_context_for_llm(retrieved)

        # 3. 调用 LLM
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=self.prompt_template.SYSTEM_PROMPT),
            ChatMessage(
                role=MessageRole.USER,
                content=self.prompt_template.QUERY_TEMPLATE.format(
                    context=context,
                    query=query
                )
            ),
        ]

        logger.info("正在调用 LLM...")
        response = self.llm.chat(messages)
        answer = response.message.content

        logger.info("回答生成完成")

        # 5. 构建返回结果
        result = {
            "answer": answer,
            "query": query,
        }

        if return_sources:
            result["sources"] = retrieved_dict
            result["source_count"] = len(retrieved_dict)

        return result

    async def aanswer(
        self,
        query: str,
        return_sources: bool = True,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        异步问答

        Args:
            query: 用户问题
            return_sources: 是否返回引用来源

        Returns:
            问答结果字典
        """
        logger.info(f"收到异步问答请求: {query}")

        # 1. 检索相关条文
        retrieved = await asyncio.to_thread(self.retriever.retrieve, query, top_k)
        retrieved_dict = self.retriever.to_dict(retrieved)

        # 2. 构建上下文
        context = self.retriever.get_context_for_llm(retrieved)

        # 3. 构建消息
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=self.prompt_template.SYSTEM_PROMPT),
            ChatMessage(
                role=MessageRole.USER,
                content=self.prompt_template.QUERY_TEMPLATE.format(
                    context=context,
                    query=query
                )
            ),
        ]

        # 4. 异步调用 LLM
        response = await self.llm.achat(messages)
        answer = response.message.content

        # 5. 构建返回结果
        result = {
            "answer": answer,
            "query": query,
        }

        if return_sources:
            result["sources"] = retrieved_dict
            result["source_count"] = len(retrieved_dict)

        return result

    async def astream_answer(
        self,
        query: str,
        return_sources: bool = True,
        top_k: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式问答

        Args:
            query: 用户问题
            return_sources: 是否返回引用来源

        Yields:
            流式输出片段
        """
        logger.info(f"收到流式问答请求: {query}")

        # 1. 检索相关条文
        retrieved = await asyncio.to_thread(self.retriever.retrieve, query, top_k)
        retrieved_dict = self.retriever.to_dict(retrieved)

        # 首先返回来源信息
        if return_sources:
            yield {
                "type": "sources",
                "data": retrieved_dict,
                "source_count": len(retrieved_dict),
            }

        # 2. 构建上下文
        context = self.retriever.get_context_for_llm(retrieved)

        # 3. 构建消息
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=self.prompt_template.SYSTEM_PROMPT),
            ChatMessage(
                role=MessageRole.USER,
                content=self.prompt_template.QUERY_TEMPLATE.format(
                    context=context,
                    query=query
                )
            ),
        ]

        # 4. 流式调用 LLM
        stream = await self.llm.astream_chat(messages)

        # 5. 流式返回
        full_response = ""
        async for chunk in stream:
            content = chunk.message.content
            if content:
                full_response += content
                yield {
                    "type": "content",
                    "data": content,
                }

        # 返回完整回答
        yield {
            "type": "done",
            "data": full_response,
            "query": query,
        }

    def format_answer(self, result: Dict[str, Any]) -> str:
        """
        格式化回答结果

        Args:
            result: 问答结果

        Returns:
            格式化后的字符串
        """
        output = []
        output.append("=" * 60)
        output.append(f"问题: {result['query']}")
        output.append("=" * 60)
        output.append(f"\n回答:\n{result['answer']}")

        if "sources" in result and result["sources"]:
            output.append("\n" + "-" * 60)
            output.append(f"引用条文 (共 {result['source_count']} 条):")

            for i, source in enumerate(result["sources"], 1):
                output.append(
                    f"\n  [{i}] {source['chapter']} 第{source['standard_id']}条 "
                    f"(相似度: {source['score']:.4f})"
                )
                output.append(f"      {source['text'][:100]}...")

        return "\n".join(output)


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

    # 2. 创建问答引擎
    qa_engine = QAEngine(index)

    # 3. 测试问答
    test_queries = [
        "太阳病的主要症状是什么？",
        "桂枝汤的组成是什么？",
        "什么是少阳病？",
    ]

    print("=" * 60)
    print("问答引擎测试")
    print("=" * 60)

    for query in test_queries:
        print(f"\n❓ 问题: {query}")
        result = qa_engine.answer(query)
        print(qa_engine.format_answer(result))
        print()
