from dataclasses import dataclass
from enum import StrEnum


class IndexState(StrEnum):
    MISSING = "missing"
    READY = "ready"
    CORRUPT = "corrupt"


@dataclass(frozen=True)
class IndexStatus:
    state: IndexState
    vector_count: int = 0
    storage_uri: str = ""
    embedding_model: str = ""
    embedding_dimension: int = 0
    detail: str = ""

    @property
    def exists(self) -> bool:
        return self.state is IndexState.READY
