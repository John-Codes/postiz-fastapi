from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.main import app
from app.postiz.dependencies import get_postiz_client


class FakePostizClient:
    """Stands in for PostizClient so tests never touch Docker or the network."""

    def __init__(self) -> None:
        self.posts: list[dict] = []
        self.created: list[dict] = []
        self.create_response: list[dict] = []
        self.error: Exception | None = None
        self.list_posts_calls: list[tuple[object, object]] = []

    async def list_posts(self, start_date, end_date) -> object:
        from app.postiz.schemas import PostizPostsResponse

        self.list_posts_calls.append((start_date, end_date))
        if self.error is not None:
            raise self.error
        return PostizPostsResponse.model_validate({"posts": self.posts})

    async def create_post(self, payload: dict) -> list[dict]:
        self.created.append(payload)
        if self.error is not None:
            raise self.error
        return self.create_response

    async def close(self) -> None:
        pass


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_postiz() -> Iterator[FakePostizClient]:
    """Replace the Postiz client dependency for the duration of one test.

    Without this, a test would call the real Postiz over the network, which
    would make the suite depend on Docker and burn the 30 requests/hour budget.
    """
    fake = FakePostizClient()
    app.dependency_overrides[get_postiz_client] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
