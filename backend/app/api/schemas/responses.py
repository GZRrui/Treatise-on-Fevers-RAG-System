
from pydantic import BaseModel, Field

from backend.app.domain.indexing import IndexStatus
from backend.app.domain.qa import AnswerResult
from backend.app.domain.retrieval import ArticleSource as DomainArticleSource
from backend.app.domain.retrieval import SearchResult


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: str | None = None


class ArticleSource(BaseModel):
    id: int
    standard_id: int
    chapter: str
    section: str
    category: str
    text: str
    score: float
    formulas: list[str] = Field(default_factory=list)


class QAData(BaseModel):
    answer: str
    query: str
    sources: list[ArticleSource] = Field(default_factory=list)
    source_count: int = 0


class QAResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: QAData

    @classmethod
    def from_domain(cls, result: AnswerResult) -> "QAResponse":
        return cls(
            data=QAData(
                answer=result.answer,
                query=result.query,
                sources=[_source_from_domain(item) for item in result.sources],
                source_count=result.source_count,
            )
        )


class SearchData(BaseModel):
    query: str
    total: int
    results: list[ArticleSource]


class SearchResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: SearchData

    @classmethod
    def from_domain(cls, result: SearchResult) -> "SearchResponse":
        return cls(
            data=SearchData(
                query=result.query,
                total=result.total,
                results=[_source_from_domain(item) for item in result.items],
            )
        )


class IndexStatusResponse(BaseModel):
    exists: bool
    vector_count: int = 0
    storage_path: str = ""
    embedding_model: str = ""
    embedding_dim: int = 0
    status: str = ""

    @classmethod
    def from_domain(cls, result: IndexStatus) -> "IndexStatusResponse":
        return cls(
            exists=result.exists,
            vector_count=result.vector_count,
            storage_path=result.storage_uri,
            embedding_model=result.embedding_model,
            embedding_dim=result.embedding_dimension,
            status=result.state.value,
        )


def _source_from_domain(source: DomainArticleSource) -> ArticleSource:
    return ArticleSource(
        id=source.id,
        standard_id=source.standard_id,
        chapter=source.chapter,
        section=source.section,
        category=source.category,
        text=source.text,
        score=source.score,
        formulas=list(source.formulas),
    )
