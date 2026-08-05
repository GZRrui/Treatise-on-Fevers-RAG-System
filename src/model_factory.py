from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.llms.dashscope import DashScope

from config import (
    DASHSCOPE_API_KEY,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    OFFLINE_MODE,
)


def create_embedding_model(
    model: str = EMBEDDING_MODEL,
    dimension: int = EMBEDDING_DIM,
):
    if OFFLINE_MODE:
        return MockEmbedding(embed_dim=dimension)

    return DashScopeEmbedding(
        api_key=DASHSCOPE_API_KEY,
        model=model,
        dimension=dimension,
    )


def create_llm(
    model: str = LLM_MODEL,
    temperature: float = LLM_TEMPERATURE,
    max_tokens: int = LLM_MAX_TOKENS,
):
    if OFFLINE_MODE:
        return MockLLM(max_tokens=max_tokens)

    return DashScope(
        api_key=DASHSCOPE_API_KEY,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
