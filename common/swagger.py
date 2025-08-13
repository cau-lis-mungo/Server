"""
Reusable Swagger / OpenAPI helpers for drf-yasg.

Place this file at: <project_root>/common/swagger.py
Usage example:

    from common.swagger import (
        list_docs, retrieve_docs, create_docs, update_docs, partial_update_docs, destroy_docs,
        PageParam, PageSizeParam, SearchParam, AUTH_HEADER,
        paginated_response,
    )

    class BookViewSet(ModelViewSet):
        @list_docs("List books", params=[PageParam, PageSizeParam, SearchParam],
                   resp=paginated_response(BookSerializer))
        def list(self, request, *args, **kwargs):
            ...

Notes
-----
- These helpers keep view methods clean and your docs consistent.
- You can freely add more common parameters to fit your domain.
"""

from __future__ import annotations
from typing import Optional, Sequence, Union, Type
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.views import get_schema_view
from rest_framework.serializers import Serializer
from rest_framework import permissions

# ---------------------------------------------------------------------------
# Common query parameters (reusable across endpoints)
# ---------------------------------------------------------------------------
PageParam = openapi.Parameter(
    name="page",
    in_=openapi.IN_QUERY,
    description="페이지 번호 (기본 1)",
    type=openapi.TYPE_INTEGER,
)

PageSizeParam = openapi.Parameter(
    name="page_size",
    in_=openapi.IN_QUERY,
    description="페이지 크기 (기본 20)",
    type=openapi.TYPE_INTEGER,
)

SearchParam = openapi.Parameter(
    name="search",
    in_=openapi.IN_QUERY,
    description="검색어",
    type=openapi.TYPE_STRING,
)

UserParam = openapi.Parameter(
    name="user",
    in_=openapi.IN_QUERY,
    description="사용자 ID",
    type=openapi.TYPE_INTEGER,
)

BookParam = openapi.Parameter(
    name="book",
    in_=openapi.IN_QUERY,
    description="도서 ID",
    type=openapi.TYPE_INTEGER,
)

# Authorization header (JWT, etc.) — optional to include in manual_parameters
AUTH_HEADER = openapi.Parameter(
    name="Authorization", # 헤더 이름
    in_=openapi.IN_HEADER, # 위치
    description="JWT Access Token(인증 토큰). 예: Bearer <JWT>", # 설명
    type=openapi.TYPE_STRING, # 데이터 타입
)

# ---------------------------------------------------------------------------
# Common schemas
# ---------------------------------------------------------------------------
ErrorSchema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "detail": openapi.Schema(
            type=openapi.TYPE_STRING, description="에러 메시지"
        )
    },
    required=["detail"],
)


def enum_string(*values: str) -> openapi.Schema:
    """Convenience helper to declare an enum of strings.

    Example:
        status = enum_string("ACTIVE", "EXPIRED")
    """
    return openapi.Schema(type=openapi.TYPE_STRING, enum=list(values))


# Types accepted by helpers
SchemaOrSerializer = Union[openapi.Schema, Type[Serializer], Serializer]
ResponseLike = Union[str, openapi.Response, SchemaOrSerializer]


def _build_responses(
    ok_status: int, ok_resp: Optional[ResponseLike]
) -> dict:
    """Build a standard responses dict with common error shapes.

    - ok_resp can be:
        * Serializer class or instance
        * openapi.Schema
        * openapi.Response
        * simple string description
    """
    responses = {
        400: ErrorSchema,
        401: ErrorSchema,
        403: ErrorSchema,
    }
    if ok_resp is None:
        responses[ok_status] = "OK" if ok_status == 200 else "Success"
    else:
        responses[ok_status] = ok_resp
    return responses


def paginated_response(
    item_serializer: SchemaOrSerializer,
) -> openapi.Schema:
    """Schema for a standard DRF PageNumberPagination envelope.

    Example:
        resp = paginated_response(BookSerializer)
    """
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "count": openapi.Schema(type=openapi.TYPE_INTEGER),
            "next": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
            "previous": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
            "results": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_OBJECT, schema=item_serializer),
            ),
        },
        required=["count", "results"],
    )


# ---------------------------------------------------------------------------
# Action-specific decorators (reusable wrappers around swagger_auto_schema)
# ---------------------------------------------------------------------------

def list_docs(
    summary: str,
    params: Optional[Sequence[openapi.Parameter]] = None,
    resp: Optional[ResponseLike] = None,
    tags: Optional[Sequence[str]] = None,
):
    """Decorator for ViewSet.list (GET collection).

    - Adds common query params and 200/4xx responses.
    - `resp` can be a Serializer (many=True implied by your pagination schema),
      an openapi.Schema, or openapi.Response.
    """
    params = list(params or [])
    responses = _build_responses(200, resp)
    return swagger_auto_schema(
        operation_summary=summary,
        manual_parameters=params,
        responses=responses,
        tags=list(tags or []),
    )


def retrieve_docs(
    summary: str,
    resp: Optional[ResponseLike] = None,
    tags: Optional[Sequence[str]] = None,
):
    """Decorator for ViewSet.retrieve (GET detail)."""
    responses = _build_responses(200, resp)
    # Not found is typical for retrieve
    responses[404] = ErrorSchema
    return swagger_auto_schema(
        operation_summary=summary,
        responses=responses,
        tags=list(tags or []),
    )


def create_docs(
    summary: str,
    req: Optional[SchemaOrSerializer] = None,
    resp: Optional[ResponseLike] = None,
    tags: Optional[Sequence[str]] = None,
    security: Optional[list] = None,
    params: Optional[Sequence[openapi.Parameter]] = None,
):
    """Decorator for ViewSet.create (POST)."""
    responses = _build_responses(201, resp)
    return swagger_auto_schema(
        operation_summary=summary,
        request_body=req,
        responses=responses,
        tags=list(tags or []),
        security=security or [],
        manual_parameters=list(params or []),
    )


def update_docs(
    summary: str,
    req: Optional[SchemaOrSerializer] = None,
    resp: Optional[ResponseLike] = None,
    tags: Optional[Sequence[str]] = None,
    security: Optional[list] = None,
    params: Optional[Sequence[openapi.Parameter]] = None,
):
    """Decorator for ViewSet.update (PUT)."""
    responses = _build_responses(200, resp)
    responses[404] = ErrorSchema
    return swagger_auto_schema(
        operation_summary=summary,
        request_body=req,
        responses=responses,
        tags=list(tags or []),
        security=security or [],
        manual_parameters=list(params or []),
    )


def partial_update_docs(
    summary: str,
    req: Optional[SchemaOrSerializer] = None,
    resp: Optional[ResponseLike] = None,
    tags: Optional[Sequence[str]] = None,
    security: Optional[list] = None,
    params: Optional[Sequence[openapi.Parameter]] = None,
):
    """Decorator for ViewSet.partial_update (PATCH)."""
    responses = _build_responses(200, resp)
    responses[404] = ErrorSchema
    return swagger_auto_schema(
        operation_summary=summary,
        request_body=req,
        responses=responses,
        tags=list(tags or []),
        security=security or [],
        manual_parameters=list(params or []),
    )


def destroy_docs(
    summary: str,
    tags: Optional[Sequence[str]] = None,
    security: Optional[list] = None,
    params: Optional[Sequence[openapi.Parameter]] = None,
):
    """Decorator for ViewSet.destroy (DELETE)."""
    return swagger_auto_schema(
        operation_summary=summary,
        responses={204: "No Content", 401: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema},
        tags=list(tags or []),
        security=security or [],
        manual_parameters=list(params or []),
    )


# ---------------------------------------------------------------------------
# Small helpers for custom endpoints (APIView / @action)
# ---------------------------------------------------------------------------

def ok_response(description: str, schema: Optional[SchemaOrSerializer] = None) -> openapi.Response:
    """Create a standardized 200 OK response wrapper.

    Example:
        responses={200: ok_response("결과", MySerializer)}
    """
    return openapi.Response(description=description, schema=schema)
