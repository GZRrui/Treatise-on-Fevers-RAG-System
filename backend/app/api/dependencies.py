from fastapi import Request

from backend.app.application.index_service import IndexService
from backend.app.application.qa_service import QAService
from backend.app.application.search_service import SearchService
from backend.app.container import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    return request.app.state.container


def get_qa_service(request: Request) -> QAService:
    return get_container(request).require_qa_service()


def get_index_service(request: Request) -> IndexService:
    return get_container(request).require_index_service()


def get_search_service(request: Request) -> SearchService:
    return get_container(request).require_search_service()
