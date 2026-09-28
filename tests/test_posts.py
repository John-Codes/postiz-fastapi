from fastapi.testclient import TestClient

from app.postiz.errors import PostizError
from tests.conftest import FakePostizClient


def test_list_posts_returns_posts(client: TestClient, fake_postiz: FakePostizClient) -> None:
    fake_postiz.posts = [
        {
            "id": "post-1",
            "content": "Hello world",
            "state": "QUEUE",
            "publishDate": "2026-09-30T10:00:00.000Z",
            "integration": {"id": "int-1", "name": "My Threads"},
        }
    ]

    response = client.get("/api/posts")

    assert response.status_code == 200
    assert response.json() == {
        "posts": [
            {
                "id": "post-1",
                "content": "Hello world",
                "publishDate": "2026-09-30T10:00:00Z",
                "state": "QUEUE",
                "releaseURL": None,
                "integration_id": "int-1",
                "integration_name": "My Threads",
            }
        ]
    }


def test_list_posts_defaults_to_a_30_day_window(
    client: TestClient, fake_postiz: FakePostizClient
) -> None:
    client.get("/api/posts")

    assert len(fake_postiz.list_posts_calls) == 1
    start, end = fake_postiz.list_posts_calls[0]
    assert (end - start).days == 30


def test_list_posts_forwards_explicit_range(
    client: TestClient, fake_postiz: FakePostizClient
) -> None:
    client.get("/api/posts?startDate=2026-09-01T00:00:00Z&endDate=2026-09-30T00:00:00Z")

    start, end = fake_postiz.list_posts_calls[0]
    assert start.isoformat().startswith("2026-09-01")
    assert end.isoformat().startswith("2026-09-30")


def test_list_posts_empty_is_ok(client: TestClient, fake_postiz: FakePostizClient) -> None:
    assert client.get("/api/posts").json() == {"posts": []}


def test_postiz_error_becomes_502(client: TestClient, fake_postiz: FakePostizClient) -> None:
    fake_postiz.error = PostizError(401, "Postiz returned HTTP 401: Invalid API key")

    response = client.get("/api/posts")

    assert response.status_code == 502
    assert "Invalid API key" in response.json()["detail"]


def test_postiz_unreachable_becomes_503(client: TestClient, fake_postiz: FakePostizClient) -> None:
    fake_postiz.error = PostizError(503, "Could not reach the Postiz API")

    assert client.get("/api/posts").status_code == 503


def test_error_response_never_leaks_the_api_key(
    client: TestClient, fake_postiz: FakePostizClient
) -> None:
    fake_postiz.error = PostizError(401, "Postiz returned HTTP 401: Invalid API key")

    body = client.get("/api/posts").text

    assert "Authorization" not in body
    assert "api_key" not in body.lower()
