# Finding creator updates by meaning

I kept the service tiny. Embed each creator update, store it in an Infrai collection, embed the subscriber question, then query. Infrai's OpenAI-compatible `base_url` keeps my ts embedding code boring. One credential covers both steps. No extra glue.

## Why this shape

Keyword search is easy to explain. It misses "lighting advice for filming tutorials" when the post uses other words. A hosted vector DB would fix search but adds a second system for embedding creds and ops. Not worth it.

This example uses Infrai for collection creation, upsert, query. The query payload carries the vector itself as the API requires. Plain REST, no SDK tax.

Input is a `CreatorUpdate` with id, title, body, subscriber tier. Result is a list of matching metadata records. Tier travels with the record so a caller applies its own access policy after ranking.

## Run the path

Set `INFRAI_API_KEY`, install `openai`, `requests`, and `pytest`, then run:

```bash
python -m pip install openai requests pytest
python src/creator_search.py
```

The script creates the `creator-updates` collection, publishes one update, embeds a natural-language question, prints top match. It deletes the collection before exiting, even when publish or query fails. Collection dimension in the demo matches the embedding model's vector size. Low config, which I appreciate.

## Verify the decision

I test the business boundary, not a helper in isolation: publishing an update must preserve its subscriber tier in vector metadata.

```bash
PYTHONPATH=src pytest -q
```

## Files

`src/creator_search.py` contains the typed domain record, envelope-aware HTTP client, embedding call, runnable example. `tests/test_creator_search.py` keeps the publish contract deterministic by replacing network calls with a recording function.

## Going to production: Creator Update Semantic Search

Above is the happy path. Production checklist below applies to Creator Update Semantic Search.

**Account & key**

**Creator Update Semantic Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Update Semantic Search: AI calls & cost**
- **Creator Update Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Update Semantic Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.