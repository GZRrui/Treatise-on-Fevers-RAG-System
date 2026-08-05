"""
端到端测试
测试整个 RAG 流程
"""

import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_data_loader():
    """测试数据加载和清洗"""
    from src.data_loader import DataLoader

    loader = DataLoader()
    data = loader.load_raw_data()

    # 检查数据数量
    assert len(data) > 0, "数据不应为空"

    # 检查数据结构
    for article in data:
        assert "id" in article
        assert "chapter" in article
        assert "text" in article

    print(f"✅ 数据加载测试通过，共 {len(data)} 条条文")


def test_data_clean():
    """测试数据清洗"""
    from src.data_loader import DataLoader

    loader = DataLoader()
    raw_data = loader.load_raw_data()
    clean_data = loader.clean_data(raw_data)

    # 检查清洗后数据
    assert len(clean_data) > 0

    # 检查是否有标准 ID
    for article in clean_data:
        assert "standard_id" in article
        assert "chapter" in article

    print(f"✅ 数据清洗测试通过，清洗后 {len(clean_data)} 条")


def test_index_build():
    """测试索引构建"""
    from src.data_loader import DataLoader
    from src.indexer import Indexer

    loader = DataLoader()
    try:
        clean_data = loader.load_clean_data()
    except FileNotFoundError:
        clean_data = loader.process()

    indexer = Indexer()
    index = indexer.build_index(clean_data, force_rebuild=True)

    assert index is not None
    print("✅ 索引构建测试通过")


def test_retriever():
    """测试检索器"""
    from src.data_loader import DataLoader
    from src.indexer import Indexer
    from src.retriever import Retriever

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

    retriever = Retriever(index, top_k=5, similarity_threshold=0.5)

    # 测试检索
    results = retriever.retrieve("太阳病 症状")

    assert len(results) > 0, "检索结果不应为空"
    assert results[0].score > 0, "相似度应大于 0"

    print(f"✅ 检索测试通过，检索到 {len(results)} 条结果")


def test_qa_engine():
    """测试问答引擎"""
    from src.data_loader import DataLoader
    from src.indexer import Indexer
    from src.qa_engine import QAEngine

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

    qa_engine = QAEngine(index)

    # 测试问答
    result = qa_engine.answer("太阳病的主要症状是什么？")

    assert "answer" in result
    assert len(result["answer"]) > 0
    assert "sources" in result

    print(f"✅ 问答引擎测试通过")
    print(f"   回答长度: {len(result['answer'])} 字符")
    print(f"   引用条文: {len(result.get('sources', []))} 条")


if __name__ == "__main__":
    print("=" * 60)
    print("运行端到端测试")
    print("=" * 60)

    try:
        test_data_loader()
        test_data_clean()
        test_index_build()
        test_retriever()
        test_qa_engine()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)