from datetime import UTC, datetime, timedelta
from typing import Any

from app.postiz.client import PostizClient
from app.postiz.schemas import PostizPost
from app.posts.schemas import (
    CreatedPost,
    CreatePostRequest,
    CreatePostResponse,
    PostListResponse,
    PostSummary,
)

DEFAULT_RANGE_DAYS = 30


async def list_posts(
    client: PostizClient,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> PostListResponse:
    """List posts in a date range.

    Postiz makes both bounds mandatory, so when the caller omits them we pick a
    window rather than sending an invalid request.
    """
    end = end_date or datetime.now(UTC)
    start = start_date or (end - timedelta(days=DEFAULT_RANGE_DAYS))

    result = await client.list_posts(start, end)
    return PostListResponse(posts=[_to_summary(post) for post in result.posts])


async def create_post(client: PostizClient, request: CreatePostRequest) -> CreatePostResponse:
    created = await client.create_post(_build_postiz_payload(request))
    return CreatePostResponse(
        posts=[CreatedPost.model_validate(item) for item in created],
    )


def _build_postiz_payload(request: CreatePostRequest) -> dict[str, Any]:
    """Translate our request into the payload Postiz documents for POST /posts.

    Postiz requires type, date, shortLink and tags on every request, and each
    integration id becomes its own entry in `posts`.
    """
    publish_at = request.scheduled_at or datetime.now(UTC)
    return {
        "type": "schedule" if request.scheduled_at else "now",
        "date": _iso_utc(publish_at),
        "shortLink": False,
        "tags": [],
        "posts": [
            {
                "integration": {"id": integration_id},
                "value": [{"content": request.content, "image": []}],
                "settings": request.settings,
            }
            for integration_id in request.integration_ids
        ],
    }


def _to_summary(post: PostizPost) -> PostSummary:
    integration = post.integration
    return PostSummary(
        id=post.id,
        content=post.content,
        publish_date=post.publish_date,
        state=post.state,
        release_url=post.release_url,
        integration_id=integration.id if integration else None,
        integration_name=integration.name if integration else None,
    )


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
