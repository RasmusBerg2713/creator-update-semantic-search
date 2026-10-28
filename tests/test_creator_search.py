import pytest

import creator_search
from creator_search import CreatorSearch, CreatorUpdate


def test_publish_update_sends_domain_metadata(monkeypatch):
    client = CreatorSearch(api_key="test-key")
    monkeypatch.setattr(client, "_embed", lambda text: [0.1, 0.2])
    calls = []
    monkeypatch.setattr(client, "_post", lambda path, payload, attempts=3: calls.append((path, payload)) or {"accepted": True})

    client.publish_update("updates", CreatorUpdate("u-7", "Audio mix", "Normalize dialogue.", "member"))

    path, payload = calls[0]
    assert path == "/v1/vector/upsert"
    assert payload["vectors"][0]["metadata"]["subscriber_tier"] == "member"


def test_delete_collection_sends_collection_name(monkeypatch):
    client = CreatorSearch(api_key="test-key")
    calls = []
    monkeypatch.setattr(client, "_delete", lambda path, payload, attempts=3: calls.append((path, payload)) or {})

    client.delete_collection("updates")

    assert calls == [("/v1/vector/collection/delete", {"collection": "updates"})]


def test_demo_deletes_collection_when_workflow_fails(monkeypatch):
    calls = []

    class RecordingSearch:
        def prepare_collection(self, collection, dimension):
            calls.append(("create", collection))

        def publish_update(self, collection, update):
            calls.append(("upsert", collection))
            raise RuntimeError("query setup failed")

        def delete_collection(self, collection):
            calls.append(("delete", collection))

    monkeypatch.setattr(creator_search, "CreatorSearch", RecordingSearch)

    with pytest.raises(RuntimeError, match="query setup failed"):
        creator_search.demo()

    assert calls == [
        ("create", "creator-updates"),
        ("upsert", "creator-updates"),
        ("delete", "creator-updates"),
    ]
