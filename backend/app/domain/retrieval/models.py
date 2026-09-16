from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleSource:
    id: int
    standard_id: int
    chapter: str
    section: str
    category: str
    text: str
    score: float
    formulas: tuple[str, ...] = ()


@dataclass(frozen=True)
class SearchResult:
    query: str
    items: tuple[ArticleSource, ...]

    @property
    def total(self) -> int:
        return len(self.items)
