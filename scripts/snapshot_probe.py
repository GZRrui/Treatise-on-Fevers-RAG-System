"""Run inside an archived source tree and emit deterministic API evidence."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import statistics
import sys
import time
from itertools import count
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import UUID

import httpx


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"timestamp", "request_id"}:
                result[key] = "<dynamic>"
            elif key == "storage_path":
                result[key] = "<temporary>/storage/vector_store.json"
            elif key == "answer" and isinstance(item, str):
                result[key] = f"<mock-response:{len(item.split())} tokens>"
            elif key in {"results", "sources"} and isinstance(item, list):
                result[key] = [
                    {"fields": sorted(record)} if isinstance(record, dict) else "<item>"
                    for record in item
                ]
            elif key == "first_event" and isinstance(item, str):
                result[key] = "data: <sources-event>"
            else:
                result[key] = _normalize(item)
        return result
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(round((len(ordered) - 1) * percentile), len(ordered) - 1)
    return round(ordered[index], 3)


def _response(response: httpx.Response) -> dict[str, Any]:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        body: Any = _normalize(response.json())
    elif "text/event-stream" in content_type:
        events = [
            line
            for line in response.text.splitlines()
            if line.startswith("data:")
        ]
        body = {
            "event_count": len(events),
            "first_event": "data: <sources-event>" if events else None,
            "last_event": events[-1][:500] if events else None,
        }
    else:
        body = response.text[:1000]
    return {
        "status": response.status_code,
        "content_type": content_type.split(";", 1)[0],
        "body": body,
    }


def _load_gold(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _index_evidence() -> dict[str, Any]:
    vector_path = Path(os.environ["VECTOR_STORE_PATH"])
    docstore_path = vector_path.parent / "docstore.json"
    vector_data = json.loads(vector_path.read_text(encoding="utf-8"))
    return {
        "status": "isolated-empty-startup-rebuild",
        "vector_count": len(vector_data.get("embedding_dict", {})),
        "vector_store_sha256": hashlib.sha256(vector_path.read_bytes()).hexdigest(),
        "docstore_sha256": hashlib.sha256(docstore_path.read_bytes()).hexdigest(),
    }


async def _quality(
    client: httpx.AsyncClient,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    latencies: list[float] = []
    duplicate_count = 0
    returned_count = 0
    hard_negative_false_positives = 0
    errors = 0

    for case in cases:
        started = time.perf_counter()
        response = await client.post(
            "/api/v1/search",
            json={"query": case["query"], "top_k": 10},
        )
        latencies.append((time.perf_counter() - started) * 1000)
        if response.status_code != 200:
            errors += 1
            retrieved: list[int] = []
        else:
            payload = response.json()["data"]
            retrieved = [int(item["id"]) for item in payload["results"]]
        duplicate_count += len(retrieved) - len(set(retrieved))
        returned_count += len(retrieved)

        if case["kind"] == "hard_negative":
            hard_negative_false_positives += bool(retrieved)
            continue
        relevant = {int(value) for value in case["relevant_ids"]}
        recalls.append(len(relevant & set(retrieved[:5])) / len(relevant))
        reciprocal_ranks.append(
            next(
                (
                    1 / rank
                    for rank, article_id in enumerate(retrieved[:10], start=1)
                    if article_id in relevant
                ),
                0.0,
            )
        )

    hard_negative_count = sum(case["kind"] == "hard_negative" for case in cases)
    return {
        "query_count": len(cases),
        "answerable_count": len(recalls),
        "hard_negative_count": hard_negative_count,
        "recall_at_5": round(statistics.fmean(recalls), 4),
        "mrr_at_10": round(statistics.fmean(reciprocal_ranks), 4),
        "duplicate_result_rate": round(duplicate_count / returned_count, 4)
        if returned_count
        else 0.0,
        "hard_negative_false_positive_rate": round(
            hard_negative_false_positives / hard_negative_count,
            4,
        )
        if hard_negative_count
        else 0.0,
        "error_rate": round(errors / len(cases), 4),
        "latency_ms": {
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        },
    }


async def _probe(snapshot_root: Path, gold_path: Path) -> dict[str, Any]:
    sys.path.insert(0, str(snapshot_root))
    from backend.app.main import create_app

    application = create_app()
    openapi = application.openapi()
    startup_started = time.perf_counter()
    async with application.router.lifespan_context(application):
        startup_ms = (time.perf_counter() - startup_started) * 1000
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://phase0.test",
        ) as client:
            samples = {
                "liveness": _response(await client.get("/health")),
                "readiness": _response(await client.get("/health/ready")),
                "index_status": _response(await client.get("/api/v1/index/status")),
                "qa_invalid": _response(await client.post("/api/v1/qa", json={})),
                "search_top_k_1": _response(
                    await client.post(
                        "/api/v1/search",
                        json={"query": "太阳病", "top_k": 1},
                    )
                ),
                "qa": _response(
                    await client.post(
                        "/api/v1/qa",
                        json={"query": "太阳病", "top_k": 1},
                    )
                ),
                "qa_stream": _response(
                    await client.post(
                        "/api/v1/qa/stream",
                        json={"query": "太阳病", "top_k": 1},
                    )
                ),
            }
            quality = await _quality(client, _load_gold(gold_path))

    return {
        "openapi": openapi,
        "samples": samples,
        "offline_quality": quality,
        "startup": {
            "storage_initially_empty": True,
            "behavior": "implicitly-rebuilds-index",
            "latency_ms": round(startup_ms, 3),
        },
        "index_artifact": _index_evidence(),
    }


async def probe(snapshot_root: Path, gold_path: Path) -> dict[str, Any]:
    identifiers = count(1)
    with patch("uuid.uuid4", side_effect=lambda: UUID(int=next(identifiers))):
        return await _probe(snapshot_root, gold_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_root", type=Path)
    parser.add_argument("gold_path", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = asyncio.run(probe(args.snapshot_root.resolve(), args.gold_path.resolve()))
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
