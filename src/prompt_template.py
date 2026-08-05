"""
步骤5: Prompt 工程
固定 Prompt 模板，伤寒论专家角色
"""

from typing import List, Dict, Any


class PromptTemplate:
    """《伤寒论》问答 Prompt 模板"""

    # 系统角色设定
    SYSTEM_PROMPT = """你是一位精通《伤寒论》的中医专家。你对《伤寒论》的条文、方剂、病证有深入的研究，能够准确解释经典条文的含义。

请严格遵循以下原则：
1. 只基于提供的条文内容回答，不要编造不存在的条文
2. 引用具体条文编号（如"第X条"）
3. 如条文涉及方剂，请说明方剂组成和用法
4. 用通俗易懂的现代汉语解释古典中医术语
5. 如果条文中没有相关信息，明确说明"《伤寒论》条文中未找到相关信息"
6. 回答应当条理清晰，便于理解"""

    # 用户 Query 模板
    QUERY_TEMPLATE = """## 相关条文
{context}

## 用户问题
{query}

## 回答要求
请根据上述条文内容，回答用户的问题。要求：
1. 严格基于条文内容，不要超出条文范围
2. 引用条文编号
3. 解释关键术语
4. 如涉及方剂，说明组成和适用证候"""

    @classmethod
    def build_prompt(cls, query: str, context: str) -> str:
        """
        构建完整的 Prompt

        Args:
            query: 用户问题
            context: 检索到的条文上下文

        Returns:
            完整的 prompt
        """
        return f"{cls.SYSTEM_PROMPT}\n\n{cls.QUERY_TEMPLATE.format(context=context, query=query)}"

    @classmethod
    def build_context(cls, articles: List[Dict[str, Any]]) -> str:
        """
        构建条文上下文

        Args:
            articles: 检索到的条文列表

        Returns:
            上下文字符串
        """
        if not articles:
            return "未在《伤寒论》中找到相关信息。"

        context_parts = []
        for article in articles:
            chapter = article.get("chapter", "")
            standard_id = article.get("standard_id", 0)
            text = article.get("text", "")
            formulas = article.get("formulas", [])

            part = f"【{chapter} 第{standard_id}条】\n{text}"
            if formulas:
                part += f"\n（涉及方剂: {', '.join(formulas)}）"
            context_parts.append(part)

        return "\n\n---\n\n".join(context_parts)

    @classmethod
    def format_article_reference(cls, articles: List[Dict[str, Any]]) -> str:
        """
        格式化的条文引用列表（用于回复中引用）

        Args:
            articles: 检索到的条文列表

        Returns:
            条文引用列表
        """
        if not articles:
            return ""

        references = []
        for article in articles:
            chapter = article.get("chapter", "")
            standard_id = article.get("standard_id", 0)
            text = article.get("text", "")[:50]  # 截取前50字

            ref = f"- {chapter} 第{standard_id}条：{text}..."
            references.append(ref)

        return "\n".join(references)


# 独立测试
if __name__ == "__main__":
    # 测试数据
    test_articles = [
        {
            "chapter": "辨太阳病脉证并治上",
            "standard_id": 1,
            "text": "太阳之为病，脉浮，头项强痛而恶寒。",
            "formulas": [],
        },
        {
            "chapter": "辨太阳病脉证并治上",
            "standard_id": 12,
            "text": "太阳中风，阳浮而阴弱，阳浮者热自发，...桂枝汤主之。",
            "formulas": ["桂枝汤"],
        },
    ]

    query = "太阳病的主要症状是什么？"
    context = PromptTemplate.build_context(test_articles)
    prompt = PromptTemplate.build_prompt(query, context)

    print("=" * 60)
    print("Prompt 示例")
    print("=" * 60)
    print(prompt)