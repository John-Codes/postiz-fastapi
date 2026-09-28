from fastapi.testclient import TestClient

from tests.conftest import FakePostizClient

VALID_BODY = {
    "content": "Hello from the API",
    "integration_ids": ["int-1"],
    "settings": {"__type": "threads"},
}


def test_create_post_publishes_now_when_unscheduled(
    client: TestClient, fake_postiz: FakePostizClient
) -> None:
    fake_postiz.create_response = [{"postId": "post-1", "integration": "int-1"}]

    response = client.post("/api/posts", json=VALID_BODY)

    assert response.status_code == 201
    assert response.json() == {"posts": [{"postId": "post-1", "integration": "int-1"}]}

    payload = fake_postiz.created[0]
    assert payload["type"] == "now"
    assert payload["shortLink"] is False
    assert payload["tags"] == []


def test_create_post_sends_every_field_postiz_requires(
    client: TestClient, fake_postiz: FakePostizClient
) -> None:
    client.post("/api/posts", json=VALID_BODY)

    payload = fake_postiz.created[0]
    assert set(payload) == {"type", "date", "shortLink", "tags", "posts"}
    assert payload["posts"] == [
        {
            "integration": {"id": "int-1"},
            "value": [{"content": "Hello from the API", "image": []}],
            "settings": {"__type": "threads"},
        }
    ]


def test_create_post_schedules_when_date_given(
    client: TestClient, fake_postiz: FakePostizClient
) -> None:
    client.post("/api/posts", json={**VALID_BODY, "scheduled_at": "2026-10-01T09:30:00Z"})

    payload = fake_postiz.created[0]
    assert payload["type"] == "schedule"
    assert payload["date"] == "2026-10-01T09:30:00.000Z"


def test_create_post_splits_multiple_integrations(
    client: TestClient, fake_postiz: FakePostizClient
) -> None:
    client.post("/api/posts", json={**VALID_BODY, "integration_ids": ["a", "b"]})

    ids = [item["integration"]["id"] for item in fake_postiz.created[0]["posts"]]
    assert ids == ["a", "b"]


def test_create_post_requires_settings_type(client: TestClient) -> None:
    response = client.post("/api/posts", json={**VALID_BODY, "settings": {}})

    assert response.status_code == 422
    assert "__type" in response.text


def test_create_post_requires_at_least_one_integration(client: TestClient) -> None:
    assert client.post("/api/posts", json={**VALID_BODY, "integration_ids": []}).status_code == 422


def test_create_post_rejects_empty_content(client: TestClient) -> None:
    assert client.post("/api/posts", json={**VALID_BODY, "content": ""}).status_code == 422


def test_create_post_rejects_unknown_fields(client: TestClient) -> None:
    response = client.post("/api/posts", json={**VALID_BODY, "platform": "threads"})

    assert response.status_code == 422


def test_create_post_surfaces_postiz_error(
    client: TestClient, fake_postiz: FakePostizClient
) -> None:
    from app.postiz.errors import PostizError

    fake_postiz.error = PostizError(400, "Postiz returned HTTP 400: unknown enum __type")

    response = client.post("/api/posts", json=VALID_BODY)

    assert response.status_code == 502
    assert "unknown enum" in response.json()["detail"]
