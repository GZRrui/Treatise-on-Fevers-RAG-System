"""Rebuild and audit the phase-0 dataset baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_RAW = DATA_DIR / "shanghanlun_raw.json"
DEFAULT_CLEAN = DATA_DIR / "shanghanlun_clean.json"
DEFAULT_MANIFEST = DATA_DIR / "dataset-manifest.json"
DEFAULT_POLICY = DATA_DIR / "cleaning-policy.json"
DEFAULT_FORMULAS = DATA_DIR / "formula-annotations.json"
DEFAULT_JSON_REPORT = PROJECT_ROOT / "docs" / "baselines" / "data-integrity.json"
DEFAULT_MARKDOWN_REPORT = PROJECT_ROOT / "docs" / "baselines" / "data-integrity.md"

CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
HORIZONTAL_WHITESPACE = re.compile(r"[ \t]+")
FORMULA_CANDIDATE = re.compile(
    r"([\u4e00-\u9fff]{2,}?(?:汤|散|丸))(?=主之|方[:：]|。)"
)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _load_records(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Expected an array of JSON objects: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clean_text(value: object) -> str:
    text = value if isinstance(value, str) else ""
    return HORIZONTAL_WHITESPACE.sub(
        " ",
        CONTROL_CHARACTERS.sub("", text),
    ).strip()


def rebuild_clean_records(
    raw: list[dict[str, Any]],
    policy: dict[str, Any],
    formula_annotations: dict[str, Any],
) -> list[dict[str, Any]]:
    numbering = policy["chapter_numbering"]
    excluded = policy["excluded_records"]
    result: list[dict[str, Any]] = []
    observed_exclusions: set[str] = set()

    for article in raw:
        article_id = article.get("id")
        exclusion_key = str(article_id)
        if exclusion_key in excluded:
            observed_exclusions.add(exclusion_key)
            continue

        chapter = article.get("chapter")
        if chapter not in numbering:
            raise ValueError(f"No numbering rule for chapter {chapter!r}")
        category = article.get("category")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"Unexpected empty category for article {article_id}")
        text = _clean_text(article.get("text", article.get("section", "")))
        if not text:
            raise ValueError(f"Unexpected empty text for article {article_id}")

        rule = numbering[chapter]
        formulas = formula_annotations.get(exclusion_key, [])
        if (
            not isinstance(formulas, list)
            or len(formulas) != len(set(formulas))
            or not all(isinstance(formula, str) and formula in text for formula in formulas)
        ):
            raise ValueError(f"Invalid formula annotations for article {article_id}")
        result.append(
            {
                "id": article_id,
                "chapter": chapter,
                "section": article.get("section", ""),
                "category": category,
                "text": text,
                "standard_id": rule["standard_id"],
                "id_range": rule["id_range"],
                "formulas": formulas,
            }
        )

    unapplied = set(excluded) - observed_exclusions
    if unapplied:
        raise ValueError(f"Policy exclusions are absent from raw data: {sorted(unapplied)}")
    unknown_annotations = set(formula_annotations) - {str(record["id"]) for record in result}
    if unknown_annotations:
        raise ValueError(f"Formula annotations reference absent IDs: {sorted(unknown_annotations)}")
    return result


def _schema_errors(records: list[dict[str, Any]], schema_path: Path) -> list[dict[str, Any]]:
    schema = _load_object(schema_path)
    errors = []
    for error in sorted(
        Draft202012Validator(schema).iter_errors(records),
        key=lambda item: list(item.absolute_path),
    ):
        path = list(error.absolute_path)
        record_id = records[path[0]].get("id") if path and isinstance(path[0], int) else None
        errors.append(
            {
                "record_id": record_id,
                "path": [str(part) for part in path],
                "message": error.message,
            }
        )
    return errors


def _duplicates(records: list[dict[str, Any]], field: str) -> list[list[int]]:
    grouped: dict[object, list[int]] = {}
    for record in records:
        grouped.setdefault(record.get(field), []).append(int(record["id"]))
    return sorted((ids for ids in grouped.values() if len(ids) > 1), key=lambda ids: ids[0])


def _formula_review(records: list[dict[str, Any]]) -> dict[str, Any]:
    extracted = {
        formula
        for record in records
        for formula in record.get("formulas", [])
    }
    candidates = {
        match
        for record in records
        for match in FORMULA_CANDIDATE.findall(str(record["text"]))
    }
    detected = extracted & candidates
    return {
        "automated_candidate_count": len(candidates),
        "extracted_unique_count": len(extracted),
        "candidate_detection_rate": round(len(detected) / len(candidates), 4)
        if candidates
        else None,
        "candidate_names_not_extracted": sorted(candidates - extracted),
        "manual_accuracy_review": "pending-domain-expert-review",
        "limitations": "Heuristic candidates are not an authoritative formula gold set.",
    }


def build_report(
    raw_path: Path = DEFAULT_RAW,
    clean_path: Path = DEFAULT_CLEAN,
    manifest_path: Path = DEFAULT_MANIFEST,
    policy_path: Path = DEFAULT_POLICY,
    formula_annotations_path: Path = DEFAULT_FORMULAS,
) -> dict[str, Any]:
    raw = _load_records(raw_path)
    clean = _load_records(clean_path)
    manifest = _load_object(manifest_path)
    policy = _load_object(policy_path)
    formula_annotations = _load_object(formula_annotations_path)
    rebuilt = rebuild_clean_records(raw, policy, formula_annotations)
    rebuilt_text = json.dumps(rebuilt, ensure_ascii=False, indent=2).replace(
        "\n",
        "\r\n",
    )
    rebuilt_bytes = rebuilt_text.encode("utf-8")

    raw_ids = [int(record["id"]) for record in raw]
    clean_ids = [int(record["id"]) for record in clean]
    excluded_ids = sorted(set(raw_ids) - set(clean_ids))
    raw_schema_errors = _schema_errors(
        raw,
        DATA_DIR / "schema" / "raw-articles.schema.json",
    )
    clean_schema_errors = _schema_errors(
        clean,
        DATA_DIR / "schema" / "clean-articles.schema.json",
    )
    expected_known_schema_error = (
        len(raw_schema_errors) == 1
        and raw_schema_errors[0]["record_id"] == 176
        and "'category' is a required property" in raw_schema_errors[0]["message"]
    )

    file_results = {}
    for relative_path, expected in manifest["files"].items():
        path = PROJECT_ROOT / relative_path
        actual_hash = _sha256(path)
        value = json.loads(path.read_text(encoding="utf-8"))
        actual_count = len(value) if isinstance(value, (list, dict)) else None
        file_results[relative_path] = {
            "expected_sha256": expected["sha256"],
            "actual_sha256": actual_hash,
            "hash_matches": actual_hash == expected["sha256"],
            "expected_record_count": expected["record_count"],
            "actual_record_count": actual_count,
            "record_count_matches": actual_count == expected["record_count"],
        }

    expected_exclusions = sorted(int(value) for value in policy["excluded_records"])
    checks = {
        "manifest_hashes_match": all(
            item["hash_matches"] for item in file_results.values()
        ),
        "manifest_counts_match": (
            len(raw) == manifest["authority"]["local_raw_count"]
            and len(clean) == manifest["authority"]["local_clean_count"]
            and all(item["record_count_matches"] for item in file_results.values())
        ),
        "raw_ids_unique": len(raw_ids) == len(set(raw_ids)),
        "clean_ids_unique": len(clean_ids) == len(set(clean_ids)),
        "clean_schema_valid": not clean_schema_errors,
        "only_known_raw_schema_error": expected_known_schema_error,
        "exclusions_match_policy": excluded_ids == expected_exclusions,
        "clean_rebuild_matches_bytes": (
            rebuilt_bytes == clean_path.read_bytes()
        ),
    }

    standard_ids = Counter(int(record["standard_id"]) for record in clean)
    return {
        "schema_version": 1,
        "dataset_id": manifest["dataset_id"],
        "passed": all(checks.values()),
        "checks": checks,
        "authority": manifest["authority"],
        "source": manifest["source"],
        "files": file_results,
        "counts": {
            "raw_records": len(raw),
            "raw_unique_ids": len(set(raw_ids)),
            "clean_records": len(clean),
            "clean_unique_ids": len(set(clean_ids)),
            "excluded_ids": excluded_ids,
        },
        "schema": {
            "raw_errors": raw_schema_errors,
            "clean_errors": clean_schema_errors,
        },
        "duplicate_text_id_groups": _duplicates(raw, "text"),
        "standard_id": {
            "unique_value_count": len(standard_ids),
            "counts": {str(key): standard_ids[key] for key in sorted(standard_ids)},
            "semantics": "chapter-range-start, not a unique article identifier",
        },
        "formula_review": _formula_review(clean),
        "cleaning": {
            "policy": "data/cleaning-policy.json",
            "rebuilt_sha256": hashlib.sha256(rebuilt_bytes).hexdigest(),
            "byte_reproducible": checks["clean_rebuild_matches_bytes"],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    authority = report["authority"]
    formulas = report["formula_review"]
    checks = "\n".join(
        f"- {'PASS' if passed else 'FAIL'}: `{name}`"
        for name, passed in report["checks"].items()
    )
    missed = ", ".join(formulas["candidate_names_not_extracted"]) or "无"
    return f"""# 阶段 0 数据完整性基线

## 结论

审计状态：**{'通过' if report['passed'] else '失败'}**。本地原始快照为 {counts['raw_records']} 条，清洗及索引口径为 {counts['clean_records']} 条。清洗结果可由版本化策略逐字节重建。

## 口径与来源

- 原始记录/唯一 ID：{counts['raw_records']} / {counts['raw_unique_ids']}
- 清洗记录/唯一 ID：{counts['clean_records']} / {counts['clean_unique_ids']}
- 排除 ID：{counts['excluded_ids']}，原因是原始 `category=null`
- 本地 236 口径覆盖率：{counts['clean_records'] / counts['raw_records']:.2%}
- 外部 705 口径：`{authority['external_claim_status']}`，无来源、许可、版本和 ID 映射，不作为权威分母
- 来源、许可、上游版本和采集日期仍未得到证据，详见 `data/dataset-manifest.json`

## 已知质量问题

- 原始重复正文：ID 94 与 173。
- `standard_id` 仅 {report['standard_id']['unique_value_count']} 个值；其现有语义是篇章区间起点，不是唯一条文编号。唯一性应使用 `id`。
- 方剂启发式候选 {formulas['automated_candidate_count']} 个，现有提取唯一值 {formulas['extracted_unique_count']} 个，候选检测率 {formulas['candidate_detection_rate']:.2%}。
- 候选但未提取：{missed}。
- 方剂准确率仍需中医领域专家建立标注集后确认；当前数字仅是规则覆盖代理，不冒充人工准确率。

## 自动门禁

{checks}

## 重现

```shell
python scripts/data_quality.py
python scripts/data_quality.py --write-clean --update-reports
```
"""


def _write_or_compare(path: Path, content: str, update: bool) -> bool:
    if update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        return True
    return path.exists() and path.read_text(encoding="utf-8") == content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-clean", action="store_true")
    parser.add_argument("--update-reports", action="store_true")
    args = parser.parse_args()

    policy = _load_object(DEFAULT_POLICY)
    if args.write_clean:
        rebuilt = rebuild_clean_records(
            _load_records(DEFAULT_RAW),
            policy,
            _load_object(DEFAULT_FORMULAS),
        )
        DEFAULT_CLEAN.write_text(
            json.dumps(rebuilt, ensure_ascii=False, indent=2).replace("\n", "\r\n"),
            encoding="utf-8",
            newline="",
        )

    report = build_report()
    json_content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    markdown_content = render_markdown(report)
    reports_current = all(
        (
            _write_or_compare(DEFAULT_JSON_REPORT, json_content, args.update_reports),
            _write_or_compare(
                DEFAULT_MARKDOWN_REPORT,
                markdown_content,
                args.update_reports,
            ),
        )
    )
    if not reports_current:
        print("Baseline reports are missing or stale; run with --update-reports", file=sys.stderr)
    print(json_content, end="")
    return 0 if report["passed"] and reports_current else 1


if __name__ == "__main__":
    raise SystemExit(main())
