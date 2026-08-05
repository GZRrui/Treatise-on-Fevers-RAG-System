from typing import List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Optional[str] = None


class ArticleSource(BaseModel):
    id: int
    standard_id: int
    chapter: str
    section: str
    category: str
    text: str
    score: float
    formulas: List[str] = Field(default_factory=list)


class QAData(BaseModel):
    answer: str
    query: str
    sources: List[ArticleSource] = Field(default_factory=list)
    source_count: int = 0


class QAResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: QAData


class SearchData(BaseModel):
    query: str
    total: int
    results: List[ArticleSource]


class SearchResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: SearchData


class IndexBuildData(BaseModel):
    exists: bool
    vector_count: int = 0
    storage_path: str = ""


class IndexBuildResponse(BaseModel):
    code: int = 200
    message: str
    data: IndexBuildData


class IndexStatusResponse(BaseModel):
    exists: bool
    vector_count: int = 0
    storage_path: str = ""
    embedding_model: str = ""
    embedding_dim: int = 0
    status: str = ""
