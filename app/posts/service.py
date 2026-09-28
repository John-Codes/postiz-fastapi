from datetime import UTC, datetime, timedelta

from app.postiz.client import PostizClient
from app.postiz.schemas import PostizPost
from app.posts.schemas import PostListResponse, PostSummary

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
