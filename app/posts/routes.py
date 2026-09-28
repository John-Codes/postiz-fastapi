from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.postiz.client import PostizClient
from app.postiz.dependencies import get_postiz_client
from app.postiz.errors import PostizError
from app.posts.schemas import CreatePostRequest, CreatePostResponse, PostListResponse
from app.posts.service import create_post, list_posts

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


@router.post("/posts", response_model=CreatePostResponse, status_code=status.HTTP_201_CREATED)
async def write_post(
    request: CreatePostRequest,
    client: Annotated[PostizClient, Depends(get_postiz_client)],
) -> CreatePostResponse:
    """Create or schedule a post. Omit scheduled_at to publish immediately."""
    try:
        return await create_post(client, request)
    except PostizError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.detail) from exc
