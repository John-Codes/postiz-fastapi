from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.postiz.client import PostizClient
from app.postiz.dependencies import get_postiz_client
from app.postiz.errors import PostizError
from app.posts.schemas import PostListResponse
from app.posts.service import list_posts

router = APIRouter(prefix="/api", tags=["posts"])


@router.get("/posts", response_model=PostListResponse)
async def read_posts(
    client: Annotated[PostizClient, Depends(get_postiz_client)],
    start_date: Annotated[datetime | None, Query(alias="startDate")] = None,
    end_date: Annotated[datetime | None, Query(alias="endDate")] = None,
) -> PostListResponse:
    """List posts. Both bounds default to a 30 day window ending now."""
    try:
        return await list_posts(client, start_date, end_date)
    except PostizError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.detail) from exc
