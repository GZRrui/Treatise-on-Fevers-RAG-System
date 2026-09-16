"""
交互式问答终端
在终端中与《伤寒论》进行问答
"""

import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("   《伤寒论》RAG 智能问答系统")
    print("=" * 60)
    print("\n你可以问关于《伤寒论》的任何问题，例如：")
    print("  - 太阳病的主要症状是什么？")
    print("  - 桂枝汤的组成是什么？")
    print("  - 什么是少阳病？")
    print("  - 小青龙汤适用于什么症状？")
    print("\n输入 'quit' 或 'exit' 退出程序")
    print("-" * 60 + "\n")

    try:
        # 1. 导入模块
        logger.info("初始化系统...")
        from src.data_loader import DataLoader
        from src.indexer import Indexer
        from src.qa_engine import QAEngine

        # 2. 加载数据
        print("📦 加载数据...")
        loader = DataLoader()
        try:
            clean_data = loader.load_clean_data()
        except FileNotFoundError:
            clean_data = loader.process()

        # 3. 构建/加载索引
        print("🔨 构建向量索引...")
        indexer = Indexer()
        try:
            index = indexer.get_index()
        except ValueError:
            index = indexer.build_index(clean_data, force_rebuild=True)

        # 4. 创建问答引擎
        print("🤖 初始化问答引擎...")
        qa_engine = QAEngine(index)

        print("\n✅ 系统初始化完成！开始问答吧！\n")

        # 5. 交互式问答循环
        while True:
            try:
                query = input("❓ 你: ").strip()

                # 检查退出命令
                if query.lower() in ["quit", "exit", "q", "退出"]:
                    print("\n👋 感谢使用，再见！")
                    break

                # 跳过空输入
                if not query:
                    continue

                # 执行问答
                print("\n🤖 正在思考...")
                result = qa_engine.answer(query)

                # 输出回答
                print("\n📖 回答:")
                print("-" * 60)
                print(result["answer"])

                # 输出来源
                if result.get("sources"):
                    print("\n📚 引用条文:")
                    for i, source in enumerate(result["sources"], 1):
                        print(
                            f"   [{i}] {source['chapter']} "
                            f"第{source['standard_id']}条"
                        )
                        print(f"       {source['text'][:80]}...")

                print("\n" + "-" * 60)

            except KeyboardInterrupt:
                print("\n\n👋 感谢使用，再见！")
                break
            except Exception as e:
                print(f"\n❌ 处理问题失败: {e}")

    except Exception as e:
        logger.error(f"\n❌ 系统初始化失败: {e}")
        print("\n请确保已执行: python scripts/build_index.py 构建索引")
        sys.exit(1)


if __name__ == "__main__":
    main()
