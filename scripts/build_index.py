"""
一键构建向量索引脚本
首次运行时执行此脚本构建索引
"""

import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("=" * 60)
    print("《伤寒论》RAG 问答系统 - 构建向量索引")
    print("=" * 60)

    try:
        # 1. 导入模块
        logger.info("导入模块...")
        from src.data_loader import DataLoader
        from src.indexer import Indexer

        # 2. 加载和清洗数据
        logger.info("\n📦 步骤1: 数据加载与清洗")
        loader = DataLoader()
        try:
            clean_data = loader.load_clean_data()
            logger.info(f"从缓存加载清洗后数据: {len(clean_data)} 条")
        except FileNotFoundError:
            clean_data = loader.process()

        # 3. 构建索引
        logger.info("\n📦 步骤2: 构建向量索引")
        indexer = Indexer()
        indexer.build_index(clean_data, force_rebuild=True)

        # 4. 输出索引信息
        info = indexer.get_index_info()
        logger.info("\n📊 索引信息:")
        for key, value in info.items():
            if key != "error":
                logger.info(f"   {key}: {value}")

        # 5. 完成
        print("\n" + "=" * 60)
        print("✅ 索引构建完成！")
        print("=" * 60)
        print("\n接下来你可以:")
        print("  1. 运行 python scripts/interactive_qa.py 进行交互问答")
        print("  2. 启动后端 API: uvicorn backend.main:app --reload")
        print("  3. 访问 API 文档: http://localhost:8000/docs")

    except Exception as e:
        logger.error(f"\n❌ 索引构建失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
