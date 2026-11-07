import pytest
from fastapi.testclient import TestClient

import database
import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    with TestClient(main.app) as test_client:
        yield test_client


def test_history_returns_only_the_latest_check(client, monkeypatch):
    def fake_check_url(url):
        return {"url": url, "status_code": 200, "duration_ms": 25, "error": None}

    monkeypatch.setattr(main, "check_url", fake_check_url)

    first = client.post("/checks", json={"url": "https://example.com/first"})
    second = client.post("/checks", json={"url": "https://example.com/second"})

    assert first.status_code == second.status_code == 200
    assert first.json()["id"] != second.json()["id"]

    history = client.get("/checks", params={"limit": 1})
    assert history.status_code == 200
    entries = history.json()
    assert len(entries) == 1
    assert entries[0]["id"] == second.json()["id"]
    assert entries[0]["url"] == "https://example.com/second"


def test_unreachable_site_is_saved_in_history(client, monkeypatch):
    def fake_check_url(url):
        return {
            "url": url,
            "status_code": None,
            "duration_ms": 5000,
            "error": "timed out",
        }

    monkeypatch.setattr(main, "check_url", fake_check_url)

    check = client.post("/checks", json={"url": "https://example.com/"})
    assert check.status_code == 200

    history = client.get("/checks")
    assert history.status_code == 200
    entries = history.json()
    assert len(entries) == 1
    assert entries[0]["id"] == check.json()["id"]
    assert entries[0]["status_code"] is None
    assert entries[0]["error"] == "timed out"


@pytest.mark.parametrize("limit", [0, 101])
def test_history_rejects_invalid_limit(client, limit):
    response = client.get("/checks", params={"limit": limit})
    assert response.status_code == 422
