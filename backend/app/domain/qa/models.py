from dataclasses import dataclass
from enum import StrEnum

from backend.app.domain.retrieval import ArticleSource


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    query: str
    sources: tuple[ArticleSource, ...] = ()

    @property
    def source_count(self) -> int:
        return len(self.sources)


class StreamEventType(StrEnum):
    SOURCES = "sources"
    CONTENT = "content"
    END = "end"
    ERROR = "error"


@dataclass(frozen=True)
class StreamEvent:
    type: StreamEventType
    sources: tuple[ArticleSource, ...] = ()
    content: str = ""
    query: str = ""
    message: str = ""
