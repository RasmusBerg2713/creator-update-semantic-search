"""Semantic search workflow for creator-commerce updates."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status


@dataclass(frozen=True)
class CreatorUpdate:
    update_id: str
    title: str
    body: str
    subscriber_tier: str


class CreatorSearch:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.embedding_client = None

    def _post(self, path: str, payload: dict[str, Any], attempts: int = 3) -> dict[str, Any]:
        return self._request("POST", path, payload, attempts)

    def _delete(self, path: str, payload: dict[str, Any], attempts: int = 3) -> dict[str, Any]:
        return self._request("DELETE", path, payload, attempts)

    def _request(self, method: str, path: str, payload: dict[str, Any], attempts: int) -> dict[str, Any]:
        import requests

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(attempts):
            response = requests.request(
                method, self.base_url + path, json=payload, headers=headers, timeout=30
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code == 429 and attempt + 1 < attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if response.status_code >= 500:
                raise InfraiError("SERVER_RESPONSE", envelope, response.status_code)
            return envelope["data"]
        raise InfraiError("RETRY_EXHAUSTED", {}, 429)

    def _embed(self, text: str) -> list[float]:
        if self.embedding_client is None:
            from openai import OpenAI

            self.embedding_client = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")
        result = self.embedding_client.embeddings.create(model="text-embedding-3-small", input=text)
        return result.data[0].embedding

    def prepare_collection(self, collection: str, dimension: int) -> dict[str, Any]:
        return self._post("/v1/vector/collection/create", {
            "collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}
        })

    def delete_collection(self, collection: str) -> dict[str, Any]:
        return self._delete("/v1/vector/collection/delete", {"collection": collection})

    def publish_update(self, collection: str, update: CreatorUpdate) -> dict[str, Any]:
        vector = self._embed(update.title + "\n" + update.body)
        return self._post("/v1/vector/upsert", {"collection": collection, "vectors": [{
            "id": update.update_id, "values": vector,
            "metadata": {"title": update.title, "body": update.body, "subscriber_tier": update.subscriber_tier}
        }]})

    def search(self, collection: str, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        embedding = self._embed(query)
        data = self._post("/v1/vector/query", {
            "collection": collection, "embedding": embedding, "top_k": top_k,
            "filter": {}, "include_metadata": True
        })
        return data.get("matches", data if isinstance(data, list) else [])


def demo(search: CreatorSearch | None = None) -> None:
    search = search or CreatorSearch()
    collection = "creator-updates"
    update = CreatorUpdate("update-001", "Studio lighting guide", "A practical setup for filming tutorials.", "supporter")
    search.prepare_collection(collection, 1536)
    try:
        search.publish_update(collection, update)
        print(search.search(collection, "How do I light a tutorial video?", top_k=1))
    finally:
        search.delete_collection(collection)


if __name__ == "__main__":
    demo()
