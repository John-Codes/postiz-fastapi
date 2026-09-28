import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.postiz.errors import PostizError
from app.postiz.schemas import PostizPostsResponse

logger = logging.getLogger(__name__)


class PostizClient:
    """Thin HTTP client for the Postiz public API.

    Knows about endpoints, headers and payload shapes. Knows nothing about
    FastAPI, business rules or scheduling policy.
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        # Postiz expects the raw key here. Prefixing it with "Bearer" is the
        # single most common cause of a 401 against this API.
        self._headers = {"Authorization": api_key}
        self._client = httpx.AsyncClient(
            base_url=self._base_url, headers=self._headers, timeout=timeout
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def is_connected(self) -> bool:
        response = await self._request("GET", "/is-connected")
        return bool(response.json().get("connected"))

    async def list_posts(self, start_date: datetime, end_date: datetime) -> PostizPostsResponse:
        """Postiz requires both bounds, so there are no defaults here."""
        response = await self._request(
            "GET",
            "/posts",
            params={"startDate": _iso_utc(start_date), "endDate": _iso_utc(end_date)},
        )
        return PostizPostsResponse.model_validate(response.json())

    async def create_post(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        response = await self._request("POST", "/posts", json=payload)
        return response.json()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            # str(exc) can embed the full request URL, which is fine (it holds no
            # secret) but not the headers, which do.
            logger.warning("Postiz request failed: %s: %s", method, type(exc).__name__)
            raise PostizError(503, "Could not reach the Postiz API") from exc

        if response.is_success:
            return response

        raise PostizError(response.status_code, _error_detail(response))


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"Postiz returned HTTP {response.status_code}"

    message = body.get("msg") or body.get("message")
    if isinstance(message, list):
        message = "; ".join(str(item) for item in message)
    if isinstance(message, str) and message:
        return f"Postiz returned HTTP {response.status_code}: {message}"
    return f"Postiz returned HTTP {response.status_code}"
