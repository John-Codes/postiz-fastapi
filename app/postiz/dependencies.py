from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.config.settings import Settings, get_settings
from app.postiz.client import PostizClient

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_postiz_client(settings: SettingsDep) -> AsyncIterator[PostizClient]:
    """One client per request, closed when the request ends.

    Kept as a dependency rather than a module global so tests can override it
    and so no HTTP connection pool outlives a request.
    """
    if not settings.is_postiz_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Postiz is not configured. Set POSTIZ_API_KEY in .env.",
        )

    client = PostizClient(
        base_url=settings.postiz_api_url,
        api_key=settings.postiz_api_key,
        timeout=settings.postiz_timeout_seconds,
    )
    try:
        yield client
    finally:
        await client.close()
