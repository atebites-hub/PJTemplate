"""Run GuardDog supply-chain malware heuristics for direct dependencies.

Description:
    Executes a digest-pinned GuardDog container against direct npm and PyPI
    manifests, writes JSON reports, and fails when GuardDog reports findings or
    per-dependency rule errors.
Preconditions:
    Docker is available and can pull/run the configured GuardDog image.
Postconditions:
    GuardDog JSON and stderr artifacts are written under the report directory.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

DEFAULT_GUARDDOG_IMAGE = (
    "ghcr.io/datadog/guarddog@"
    "sha256:1679817551670ab3665cd0e0192e16d1c871bb29658010052378df026033df3e"
)
DEFAULT_TIMEOUT_S = 240

NPM_METADATA_RULES = (
    "typosquatting",
    "direct_url_dependency",
    "bundled_binary",
    "release_zero",
    "potentially_compromised_email_domain",
    "unclaimed_maintainer_email_domain",
    "deceptive_author",
)
PYPI_METADATA_RULES = (
    "typosquatting",
    "bundled_binary",
    "release_zero",
    "potentially_compromised_email_domain",
    "unclaimed_maintainer_email_domain",
    "deceptive_author",
)


@dataclass(frozen=True)
class GuardDogTarget:
    """A direct-dependency manifest to scan with GuardDog."""

    ecosystem: str
    manifest: Path
    report_name: str
    rules: tuple[str, ...]


@dataclass(frozen=True)
class IgnoredFinding:
    """A time-bounded GuardDog finding exception."""

    ecosystem: str
    dependency: str
    rule: str
    ignore_until: date
    reason: str


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Directory for GuardDog JSON and stderr artifacts.",
    )
    parser.add_argument(
        "--image",
        default=os.environ.get("GUARDDOG_IMAGE", DEFAULT_GUARDDOG_IMAGE),
        help="Digest-pinned GuardDog container image.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="GuardDog exception config. Defaults to config/security/guarddog.json.",
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=int(os.environ.get("GUARDDOG_TIMEOUT_S", str(DEFAULT_TIMEOUT_S))),
        help="Per-target Docker timeout in seconds.",
    )
    return parser.parse_args(argv)


def _targets(repo_root: Path) -> tuple[GuardDogTarget, ...]:
    return (
        GuardDogTarget(
            ecosystem="npm",
            manifest=repo_root / "src" / "client" / "package.json",
            report_name="guarddog-npm-package.json",
            rules=NPM_METADATA_RULES,
        ),
        GuardDogTarget(
            ecosystem="pypi",
            manifest=repo_root / "requirements.in",
            report_name="guarddog-pypi-requirements.json",
            rules=PYPI_METADATA_RULES,
        ),
        GuardDogTarget(
            ecosystem="pypi",
            manifest=repo_root / "requirements-dev.in",
            report_name="guarddog-pypi-requirements-dev.json",
            rules=PYPI_METADATA_RULES,
        ),
    )


def _container_manifest_path(repo_root: Path, manifest: Path) -> str:
    relative = manifest.relative_to(repo_root)
    return f"/workspace/{relative.as_posix()}"


def _guarddog_command(image: str, repo_root: Path, target: GuardDogTarget) -> list[str]:
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{repo_root}:/workspace:ro",
        image,
        target.ecosystem,
        "verify",
        "--exit-non-zero-on-finding",
        "--output-format=json",
    ]
    for rule in target.rules:
        command.extend(("--rules", rule))
    command.append(_container_manifest_path(repo_root, target.manifest))
    return command


def _load_report(path: Path) -> list[dict[str, Any]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a JSON list")
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"{path}[{index}] must be a JSON object")
    return raw


def _load_ignored_findings(path: Path) -> tuple[IgnoredFinding, ...]:
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("ignored_findings", [])
    if not isinstance(entries, list):
        raise ValueError(f"{path} ignored_findings must be a list")

    ignored: list[IgnoredFinding] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"{path} ignored_findings[{index}] must be an object")
        try:
            ignore_until = datetime.strptime(str(entry["ignore_until"]), "%Y-%m-%d").replace(
                tzinfo=UTC
            )
            ignored.append(
                IgnoredFinding(
                    ecosystem=str(entry["ecosystem"]),
                    dependency=str(entry["dependency"]),
                    rule=str(entry["rule"]),
                    ignore_until=ignore_until.date(),
                    reason=str(entry["reason"]),
                )
            )
        except KeyError as exc:
            raise ValueError(f"{path} ignored_findings[{index}] is missing {exc}") from exc
    return tuple(ignored)


def _is_ignored(
    *,
    ignored: tuple[IgnoredFinding, ...],
    ecosystem: str,
    dependency: str,
    rule: str,
) -> bool:
    today = date.today()
    for finding in ignored:
        if (
            finding.ecosystem == ecosystem
            and finding.dependency == dependency
            and finding.rule == rule
            and finding.ignore_until >= today
        ):
            print(f"    ignored GuardDog finding {ecosystem}:{dependency}:{rule}: {finding.reason}")
            return True
    return False


def _has_finding(value: Any) -> bool:
    return value not in (None, False, "", [], {})


def _find_guarddog_failures(
    *,
    path: Path,
    ecosystem: str,
    ignored: tuple[IgnoredFinding, ...],
) -> list[str]:
    failures: list[str] = []
    for item in _load_report(path):
        dependency = str(item.get("dependency") or item.get("package") or "<unknown>")
        result = item.get("result")
        if not isinstance(result, dict):
            result = item
        errors = result.get("errors", {})
        if isinstance(errors, dict) and errors:
            failures.append(f"{dependency}: GuardDog rule errors: {', '.join(sorted(errors))}")
        results = result.get("results", {})
        if isinstance(results, dict):
            for rule, value in sorted(results.items()):
                if _has_finding(value) and not _is_ignored(
                    ignored=ignored,
                    ecosystem=ecosystem,
                    dependency=dependency,
                    rule=str(rule),
                ):
                    failures.append(f"{dependency}: GuardDog {rule} finding")
        elif result.get("issues", 0):
            failures.append(f"{dependency}: {result['issues']} GuardDog issue(s)")
    return failures


def _run_target(
    *,
    image: str,
    repo_root: Path,
    report_dir: Path,
    timeout_s: int,
    target: GuardDogTarget,
    ignored: tuple[IgnoredFinding, ...],
) -> list[str]:
    if not target.manifest.exists():
        # A template may not ship every manifest (e.g. no frontend package.json).
        # Treat an absent manifest as "nothing to scan", not a failure.
        print(f"    skipping {target.ecosystem}: {target.manifest} not present")
        return []

    report_path = report_dir / target.report_name
    stderr_path = report_path.with_suffix(f"{report_path.suffix}.stderr")
    command = _guarddog_command(image, repo_root, target)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return [f"{target.manifest}: GuardDog timed out after {timeout_s}s"]

    report_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    try:
        failures = _find_guarddog_failures(
            path=report_path,
            ecosystem=target.ecosystem,
            ignored=ignored,
        )
    except ValueError as exc:
        return [f"{target.manifest}: {exc}; see {stderr_path}"]
    if completed.returncode != 0 and failures:
        failures.append(
            f"{target.manifest}: GuardDog exited {completed.returncode}; see {stderr_path}"
        )
    return failures


def main(argv: list[str] | None = None) -> int:
    """Run GuardDog scans and return a process exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = args.repo_root.resolve()
    report_dir = (
        args.report_dir
        or Path(os.environ.get("SUPPLY_CHAIN_REPORT_DIR", repo_root / "logs/current/supply-chain"))
    ).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    config_path = (args.config or repo_root / "config" / "security" / "guarddog.json").resolve()
    ignored = _load_ignored_findings(config_path)

    if shutil.which("docker") is None:
        print("ERROR: GuardDog audit requires Docker", file=sys.stderr)
        return 1

    all_failures: list[str] = []
    for target in _targets(repo_root):
        print(f"GuardDog {target.ecosystem} verify {target.manifest.relative_to(repo_root)}")
        failures = _run_target(
            image=args.image,
            repo_root=repo_root,
            report_dir=report_dir,
            timeout_s=args.timeout_s,
            target=target,
            ignored=ignored,
        )
        all_failures.extend(failures)

    if all_failures:
        print("GuardDog audit failed:", file=sys.stderr)
        for failure in all_failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"GuardDog audit passed. Reports: {report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
