"""Generate reproducible SBOMs and dependency vulnerability reports."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "baselines" / "supply-chain"
NPM = shutil.which("npm") or shutil.which("npm.cmd")
NPM_REGISTRY = "https://registry.npmjs.org"


def _run(
    command: list[str],
    *,
    cwd: Path = PROJECT_ROOT,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PYTHONUTF8": "1",
        "NO_COLOR": "1",
        "NPM_CONFIG_CACHE": str(PROJECT_ROOT / ".npm-cache"),
    }
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=False,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Command failed ({completed.returncode}): {detail}")
    return completed


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _python_sbom(output: Path) -> None:
    _run(
        [
            sys.executable,
            "-m",
            "cyclonedx_py",
            "requirements",
            "requirements.txt",
            "--output-reproducible",
            "--of",
            "JSON",
            "-o",
            str(output),
        ]
    )


def _frontend_sbom(output: Path) -> None:
    if NPM is None:
        raise RuntimeError("npm executable was not found")
    with _frontend_manifest_copy() as manifest_root:
        completed = _run(
            [
                NPM,
                "sbom",
                "--package-lock-only",
                "--sbom-format",
                "cyclonedx",
                "--sbom-type",
                "application",
            ],
            cwd=manifest_root,
        )
    sbom = json.loads(completed.stdout)
    sbom.pop("serialNumber", None)
    metadata = sbom.get("metadata", {})
    if isinstance(metadata, dict):
        metadata.pop("timestamp", None)
    _write_json(output, sbom)


def _python_audit(output: Path) -> tuple[dict[str, Any], int]:
    completed = _run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "--requirement",
            "requirements.txt",
            "--require-hashes",
            "--disable-pip",
            "--progress-spinner",
            "off",
            "--format",
            "json",
        ],
        check=False,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError(f"pip-audit failed: {completed.stderr.strip()}")
    if not completed.stdout.strip():
        raise RuntimeError(f"pip-audit produced no report: {completed.stderr.strip()}")
    report = json.loads(completed.stdout)
    _write_json(output, report)
    vulnerability_count = sum(
        len(dependency.get("vulns", []))
        for dependency in report.get("dependencies", [])
    )
    return report, vulnerability_count


def _frontend_audit(output: Path) -> tuple[dict[str, Any], int]:
    if NPM is None:
        raise RuntimeError("npm executable was not found")
    with _frontend_manifest_copy() as manifest_root:
        completed = _run(
            [
                NPM,
                "audit",
                "--package-lock-only",
                "--ignore-scripts",
                "--registry",
                NPM_REGISTRY,
                "--json",
            ],
            cwd=manifest_root,
            check=False,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError(f"npm audit failed: {completed.stderr.strip()}")
    if not completed.stdout.strip():
        raise RuntimeError(f"npm audit produced no report: {completed.stderr.strip()}")
    report = json.loads(completed.stdout)
    if report.get("error") or not isinstance(report.get("metadata"), dict):
        message = report.get("message") or report.get("error") or report
        raise RuntimeError(f"npm audit returned an invalid report: {message}")
    _write_json(output, report)
    counts = report.get("metadata", {}).get("vulnerabilities", {})
    if not isinstance(counts, dict):
        raise RuntimeError("npm audit report is missing vulnerability counts")
    blocking_count = int(counts.get("high", 0)) + int(counts.get("critical", 0))
    return report, blocking_count


@contextmanager
def _frontend_manifest_copy() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="ragpp-npm-audit-") as temporary:
        root = Path(temporary)
        for filename in ("package.json", "package-lock.json"):
            shutil.copy2(FRONTEND_ROOT / filename, root / filename)
        yield root


def _summary(
    python_report: dict[str, Any],
    python_vulnerabilities: int,
    frontend_report: dict[str, Any],
    frontend_blocking: int,
) -> str:
    python_packages = len(python_report.get("dependencies", []))
    frontend_metadata = frontend_report.get("metadata", {})
    dependency_counts = frontend_metadata.get("dependencies", {})
    frontend_packages = (
        dependency_counts.get("total", 0)
        if isinstance(dependency_counts, dict)
        else frontend_metadata.get("totalDependencies", 0)
    )
    frontend_counts = frontend_metadata.get("vulnerabilities", {})
    return f"""# 阶段 0 供应链基线

- Python 锁定包：{python_packages}
- Python 已知漏洞：{python_vulnerabilities}
- 前端锁定包：{frontend_packages}
- 前端漏洞计数：`{json.dumps(frontend_counts, ensure_ascii=False, sort_keys=True)}`
- 前端高危/严重漏洞：{frontend_blocking}
- SBOM 格式：CycloneDX JSON
- Python 安装门禁：`pip --require-hashes`
- 前端安装门禁：`npm ci`

报告是生成时的漏洞数据库快照；CI 每次重新扫描，高危或严重漏洞会阻断。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fail-on-vulnerability", action="store_true")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    _python_sbom(output / "python.cdx.json")
    _frontend_sbom(output / "frontend.cdx.json")
    python_report, python_vulnerabilities = _python_audit(
        output / "python-audit.json"
    )
    frontend_report, frontend_blocking = _frontend_audit(
        output / "frontend-audit.json"
    )
    (output / "README.md").write_text(
        _summary(
            python_report,
            python_vulnerabilities,
            frontend_report,
            frontend_blocking,
        ),
        encoding="utf-8",
        newline="\n",
    )

    has_blocking_findings = python_vulnerabilities > 0 or frontend_blocking > 0
    print(
        f"Supply-chain reports generated: Python vulnerabilities="
        f"{python_vulnerabilities}, frontend high/critical={frontend_blocking}"
    )
    return 1 if args.fail_on_vulnerability and has_blocking_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
