"""CRM360 Pagination and Sorting Helper.

Provides standardized pagination {items, total, skip, limit} and whitelist-based sorting
across all models with backward-compatible raw list support.
"""
from typing import Generic, TypeVar, List, Optional, Any, Dict
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import Query
from sqlalchemy import asc, desc

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int


def paginate_query(
    query: Query,
    model: Any,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "asc",
    allowed_sort_fields: Optional[List[str]] = None,
    default_sort_field: str = "id",
    default_sort_dir: str = "desc",
    paginate: bool = True,
    raw: bool = False,
) -> Any:
    """
    Applies sorting and pagination to a SQLAlchemy query.
    If paginate=False or raw=True, returns a flat List.
    Otherwise returns a dict with items, total, skip, limit.
    """
    # 1. Sorting with whitelist validation
    if sort_by:
        if allowed_sort_fields and sort_by not in allowed_sort_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort field '{sort_by}'. Allowed sort fields: {', '.join(allowed_sort_fields)}"
            )
        col = getattr(model, sort_by, None)
        if col is not None:
            order_clause = desc(col) if (sort_dir and sort_dir.lower() == "desc") else asc(col)
            query = query.order_by(order_clause)
    elif default_sort_field:
        col = getattr(model, default_sort_field, None)
        if col is not None:
            order_clause = desc(col) if default_sort_dir.lower() == "desc" else asc(col)
            query = query.order_by(order_clause)

    # 2. Check if raw list is requested
    if not paginate or raw:
        if limit is not None and limit > 0:
            query = query.offset(skip).limit(limit)
        elif skip > 0:
            query = query.offset(skip)
        return query.all()

    # 3. Standard paginated response
    total = query.count()
    if limit is not None and limit > 0:
        items = query.offset(skip).limit(limit).all()
    elif skip > 0:
        items = query.offset(skip).all()
    else:
        items = query.all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
