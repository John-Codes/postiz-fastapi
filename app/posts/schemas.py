from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostSummary(BaseModel):
    """A Postiz post as returned by GET /api/posts."""

    # Response keys are camelCase to match Postiz; allow the snake_case field
    # name too, otherwise PostSummary(publish_date=...) is silently dropped.
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    content: str | None = None
    publish_date: datetime | None = Field(default=None, alias="publishDate")
    state: str | None = None
    release_url: str | None = Field(default=None, alias="releaseURL")
    integration_id: str | None = None
    integration_name: str | None = None


class PostListResponse(BaseModel):
    posts: list[PostSummary] = Field(default_factory=list)
