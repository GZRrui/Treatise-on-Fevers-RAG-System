"""Capture the original committed system without modifying the worktree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_REF = "37d2c122cee1956c83d99f64996b4f15976053d4"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "baselines" / "original"
GOLD_PATH = PROJECT_ROOT / "evaluation" / "retrieval_gold.jsonl"


def _run(*args: str, cwd: Path = PROJECT_ROOT) -> bytes:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
    ).stdout


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _tool_version(name: str) -> str:
    executable = shutil.which(name) or shutil.which(f"{name}.cmd")
    if executable is None:
        raise RuntimeError(f"Required runtime executable was not found: {name}")
    output = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    return output.removeprefix("v")


def _extract_archive(archive: Path, destination: Path) -> None:
    root = destination.resolve()
    with zipfile.ZipFile(archive) as source:
        for member in source.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"Unsafe archive path: {member.filename}")
        source.extractall(destination)


def _capture(ref: str) -> tuple[dict[str, Any], str]:
    commit = _run("git", "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    with tempfile.TemporaryDirectory(prefix="ragpp-phase0-") as temporary:
        root = Path(temporary)
        archive = root / "snapshot.zip"
        snapshot = root / "source"
        snapshot.mkdir()
        subprocess.run(
            ["git", "archive", "--format=zip", f"--output={archive}", commit],
            cwd=PROJECT_ROOT,
            check=True,
        )
        _extract_archive(archive, snapshot)

        probe_output = root / "probe.json"
        isolated_storage = root / "storage"
        environment = {
            **os.environ,
            "APP_ENV": "test",
            "RAG_OFFLINE_MODE": "true",
            "DASHSCOPE_API_KEY": "",
            "STORAGE_DIR": str(isolated_storage),
            "VECTOR_STORE_PATH": str(isolated_storage / "vector_store.json"),
            "DATABASE_URL": f"sqlite+aiosqlite:///{root / 'baseline.db'}",
            "DEBUG": "false",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONHASHSEED": "20260805",
        }
        subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "snapshot_probe.py"),
                str(snapshot),
                str(GOLD_PATH),
                str(probe_output),
            ],
            cwd=snapshot,
            env=environment,
            check=True,
        )
        probe = json.loads(probe_output.read_text(encoding="utf-8"))

    openapi_text = json.dumps(probe["openapi"], ensure_ascii=False, indent=2) + "\n"
    samples_text = json.dumps(probe["samples"], ensure_ascii=False, indent=2) + "\n"
    inputs = {
        path: _sha256_bytes(_run("git", "show", f"{commit}:{path}"))
        for path in (
            "requirements.txt",
            "frontend/package-lock.json",
            "data/shanghanlun_raw.json",
            "data/shanghanlun_clean.json",
        )
    }
    manifest = {
        "schema_version": 1,
        "source_commit": commit,
        "runtime": {
            "python": platform.python_version(),
            "node": _tool_version("node"),
            "npm": _tool_version("npm"),
            "provider": "llama-index MockEmbedding/MockLLM",
            "network_enabled": False,
            "random_seed": 20260805,
        },
        "input_sha256": inputs,
        "query_set": {
            "path": "evaluation/retrieval_gold.jsonl",
            "sha256": _sha256_file(GOLD_PATH),
            "case_count": sum(
                bool(line.strip())
                for line in GOLD_PATH.read_text(encoding="utf-8").splitlines()
            ),
        },
        "openapi_sha256": _sha256_bytes(openapi_text.encode("utf-8")),
        "request_samples_sha256": _sha256_bytes(samples_text.encode("utf-8")),
        "index_artifact": probe["index_artifact"],
    }
    quality = {
        "schema_version": 1,
        "source_commit": commit,
        "scope": "deterministic offline baseline; not production model quality",
        "offline_metrics": probe["offline_quality"],
        "startup": probe["startup"],
        "model_call_cost": {"amount": 0, "currency": "CNY", "reason": "Mock providers"},
        "candidate_online_metrics": {
            "provenance": (
                "pre-phase high-order workspace; not original-system acceptance"
            ),
            "recall_at_5": 0.529,
            "mrr_at_10": 0.507,
            "duplicate_result_rate": 0.0,
            "hard_negative_false_positive_rate": 0.20,
        },
        "production_baseline_status": (
            "pending-approved-provider-budget-and-authoritative-dataset"
        ),
    }
    result = {
        "openapi": openapi_text,
        "samples": samples_text,
        "manifest": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        "quality": json.dumps(quality, ensure_ascii=False, indent=2) + "\n",
    }
    return result, commit


def _write(result: dict[str, str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in result.items():
        (OUTPUT_DIR / f"{name}.json").write_text(
            content,
            encoding="utf-8",
            newline="\n",
        )


def _stable_quality(value: str) -> dict[str, Any]:
    quality = cast(dict[str, Any], json.loads(value))
    quality.get("offline_metrics", {}).pop("latency_ms", None)
    quality.get("startup", {}).pop("latency_ms", None)
    return quality


def _check(result: dict[str, str]) -> bool:
    stable_outputs = ("openapi", "samples", "manifest")
    matches = True
    for name in stable_outputs:
        path = OUTPUT_DIR / f"{name}.json"
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == result[name]:
            continue
        matches = False
        print(
            f"Stale {name}.json: expected {_sha256_bytes(result[name].encode())}, "
            f"found {_sha256_bytes(current.encode())}",
            file=sys.stderr,
        )
    quality_path = OUTPUT_DIR / "quality.json"
    try:
        current_quality = _stable_quality(quality_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        current_quality = {}
    expected_quality = _stable_quality(result["quality"])
    if current_quality != expected_quality:
        matches = False
        print("Stale quality.json: deterministic metrics changed", file=sys.stderr)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=ORIGINAL_REF)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    result, commit = _capture(args.ref)
    if args.update:
        _write(result)
        print(f"Updated original-system baseline for {commit}")
        return 0
    if not _check(result):
        print(
            "Original-system baseline is missing or stale; run with --update",
            file=sys.stderr,
        )
        return 1
    print(f"Original-system baseline matches {commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
