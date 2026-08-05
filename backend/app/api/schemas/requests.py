from typing import Optional

from pydantic import BaseModel, Field


class QARequest(BaseModel):
    query: str = Field(..., description="用户问题", min_length=1, max_length=500)
    top_k: int = Field(default=5, description="检索数量", ge=1, le=20)
    stream: bool = Field(default=False, description="是否流式输出")


class SearchRequest(BaseModel):
    query: str = Field(..., description="检索词", min_length=1, max_length=200)
    top_k: int = Field(default=5, description="返回数量", ge=1, le=20)
    category: Optional[str] = Field(default=None, description="按病证分类筛选")


class BuildIndexRequest(BaseModel):
    force: bool = Field(default=False, description="是否强制重建")
