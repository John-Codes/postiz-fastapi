from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Response keys are camelCase to match Postiz; allow the snake_case field name
# too, otherwise PostSummary(publish_date=...) is silently dropped.
_RESPONSE_CONFIG = ConfigDict(populate_by_name=True)


class PostSummary(BaseModel):
    """A Postiz post as returned by GET /api/posts."""

    model_config = _RESPONSE_CONFIG

    id: str | None = None
    content: str | None = None
    publish_date: datetime | None = Field(default=None, alias="publishDate")
    state: str | None = None
    release_url: str | None = Field(default=None, alias="releaseURL")
    integration_id: str | None = None
    integration_name: str | None = None


class PostListResponse(BaseModel):
    model_config = _RESPONSE_CONFIG

    posts: list[PostSummary] = Field(default_factory=list)


class CreatePostRequest(BaseModel):
    """Our small request shape, translated to Postiz's real payload in service.py.

    `settings` must carry Postiz's `__type` (e.g. "threads"). We cannot infer it:
    the API deliberately does not expose a channel-to-platform mapping, and
    inventing one would break silently.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    content: str = Field(min_length=1)
    integration_ids: list[str] = Field(min_length=1)
    scheduled_at: datetime | None = None
    settings: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_settings_type(self) -> Self:
        if not self.settings.get("__type"):
            raise ValueError('settings must include __type, for example {"__type": "threads"}')
        return self


class CreatedPost(BaseModel):
    model_config = _RESPONSE_CONFIG

    post_id: str | None = Field(default=None, alias="postId")
    integration: str | None = None


class CreatePostResponse(BaseModel):
    model_config = _RESPONSE_CONFIG

    posts: list[CreatedPost] = Field(default_factory=list)
