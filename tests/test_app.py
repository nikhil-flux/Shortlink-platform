import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest  # noqa: E402
from main import MemoryStore, create_app  # noqa: E402


@pytest.fixture
def client():
    return create_app(MemoryStore()).test_client()


def test_health(client):
    assert client.get("/healthz").json == {"status": "ok"}


def test_ready(client):
    assert client.get("/readyz").status_code == 200


def test_shorten_and_redirect(client):
    res = client.post("/api/shorten", json={"url": "https://example.com/page"})
    assert res.status_code == 201
    code = res.json["code"]
    follow = client.get(f"/{code}")
    assert follow.status_code == 302
    assert follow.headers["Location"] == "https://example.com/page"


@pytest.mark.parametrize("bad", [None, "", "ftp://x.com", "not-a-url", "javascript:alert(1)"])
def test_rejects_invalid_urls(client, bad):
    assert client.post("/api/shorten", json={"url": bad}).status_code == 400


def test_unknown_code_404(client):
    assert client.get("/nope123").status_code == 404


def test_metrics_exposed(client):
    client.post("/api/shorten", json={"url": "https://example.com"})
    body = client.get("/metrics").data.decode()
    assert "shortlink_created_total" in body
