from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PostizIntegration(BaseModel):
    """The channel a post goes to.

    Every field is optional: the Postiz OpenAPI spec marks none of them as
    required, and `picture` is null for channels without an avatar.
    """

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    provider_identifier: str | None = Field(default=None, alias="providerIdentifier")
    name: str | None = None
    picture: str | None = None


class PostizPost(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    content: str | None = None
    # Platform-specific and deliberately not modelled.
    settings: dict[str, Any] = Field(default_factory=dict)
    publish_date: datetime | None = Field(default=None, alias="publishDate")
    # Null until the post is actually published.
    release_url: str | None = Field(default=None, alias="releaseURL")
    state: str | None = None
    integration: PostizIntegration | None = None


class PostizPostsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    posts: list[PostizPost] = Field(default_factory=list)


class PostizCreatedPost(BaseModel):
    """One element of the array Postiz returns from POST /posts."""

    model_config = ConfigDict(extra="allow")

    post_id: str | None = Field(default=None, alias="postId")
    integration: str | None = None
