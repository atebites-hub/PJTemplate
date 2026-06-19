"""Audit npm manifests for Mini Shai-Hulud-style worm indicators."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REPORT = Path("logs/current/supply-chain/npm-worm-audit.json")
DEPENDENCY_FIELDS = (
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
)


@dataclass(frozen=True)
class Finding:
    """A deterministic supply-chain policy finding."""

    severity: str
    kind: str
    path: str
    detail: str
    reason: str

    def to_json(self) -> dict[str, str]:
        """Return a JSON-serializable finding representation."""
        return {
            "severity": self.severity,
            "kind": self.kind,
            "path": self.path,
            "detail": self.detail,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CompiledPattern:
    """A regular expression plus the reason it exists."""

    regex: re.Pattern[str]
    reason: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the npm worm audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--client-dir", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--report-path", type=Path)
    parser.add_argument(
        "--extra-package-json",
        action="append",
        default=[],
        type=Path,
        help="Additional npm package.json files to scan, for global CLI tools such as GitNexus.",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> object:
    """Load a JSON document from disk."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def compile_patterns(raw_patterns: Iterable[dict[str, str]]) -> list[CompiledPattern]:
    """Compile regex policy entries from the JSON config."""
    patterns: list[CompiledPattern] = []
    for entry in raw_patterns:
        pattern = entry.get("pattern")
        reason = entry.get("reason", "policy match")
        if not pattern:
            raise ValueError("pattern entry is missing a pattern")
        patterns.append(CompiledPattern(regex=re.compile(pattern), reason=reason))
    return patterns


def package_name_from_lock_path(lock_path: str, package_data: object) -> str:
    """Derive the npm package name for a package-lock package entry."""
    if isinstance(package_data, dict) and isinstance(package_data.get("name"), str):
        return package_data["name"]
    marker = "node_modules/"
    if marker not in lock_path:
        return lock_path or "<root>"
    tail = lock_path.rsplit(marker, 1)[1]
    parts = tail.split("/")
    if tail.startswith("@") and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def iter_dependency_specs(document: object, location: str) -> Iterable[tuple[str, str, str]]:
    """Yield dependency name/spec pairs from package manifests or lock entries."""
    if not isinstance(document, dict):
        return
    for field in DEPENDENCY_FIELDS:
        dependencies = document.get(field)
        if not isinstance(dependencies, dict):
            continue
        for name, spec in dependencies.items():
            if isinstance(name, str) and isinstance(spec, str):
                yield field, name, spec
    bundled = document.get("bundledDependencies") or document.get("bundleDependencies")
    if isinstance(bundled, list):
        for name in bundled:
            if isinstance(name, str):
                yield "bundledDependencies", name, "<bundled>"
    elif isinstance(bundled, dict):
        for name, spec in bundled.items():
            if isinstance(name, str) and isinstance(spec, str):
                yield "bundledDependencies", name, spec
    del location


def check_package_patterns(
    *,
    package_name: str,
    path: str,
    package_patterns: list[CompiledPattern],
) -> list[Finding]:
    """Return findings for package names matching blocked IOC patterns."""
    findings: list[Finding] = []
    for pattern in package_patterns:
        if pattern.regex.search(package_name):
            findings.append(
                Finding(
                    severity="critical",
                    kind="blocked_package",
                    path=path,
                    detail=f"blocked package {package_name}",
                    reason=pattern.reason,
                )
            )
    return findings


def check_dependency_specs(
    *,
    document: object,
    path: str,
    blocked_prefixes: tuple[str, ...],
    package_patterns: list[CompiledPattern],
) -> list[Finding]:
    """Return findings for blocked dependency names or source specs."""
    findings: list[Finding] = []
    for field, name, spec in iter_dependency_specs(document, path):
        dep_path = f"{path}:{field}:{name}"
        findings.extend(
            check_package_patterns(
                package_name=name,
                path=dep_path,
                package_patterns=package_patterns,
            )
        )
        lowered = spec.lower()
        if lowered.startswith(blocked_prefixes):
            findings.append(
                Finding(
                    severity="high",
                    kind="blocked_dependency_spec",
                    path=dep_path,
                    detail=f"{name} uses source spec {spec}",
                    reason=(
                        "npm dependency source specs must resolve through the npm registry "
                        "lockfile path"
                    ),
                )
            )
    return findings


def check_lifecycle_scripts(
    *,
    package_name: str,
    version: str,
    scripts: object,
    path: str,
    blocked_scripts: set[str],
) -> list[Finding]:
    """Return findings for dangerous npm lifecycle hooks in package manifests."""
    if not isinstance(scripts, dict):
        return []
    findings: list[Finding] = []
    for name, command in scripts.items():
        if name not in blocked_scripts:
            continue
        findings.append(
            Finding(
                severity="high",
                kind="blocked_lifecycle_script",
                path=f"{path}:scripts:{name}",
                detail=f"{package_name}@{version} defines {name}: {command}",
                reason="install-time lifecycle hooks are the execution boundary for npm worms",
            )
        )
    return findings


def check_install_script_allowlist(
    *,
    package_name: str,
    version: str,
    path: str,
    has_install_script: bool,
    allowed_install_scripts: set[tuple[str, str]],
) -> list[Finding]:
    """Return findings for package-lock install scripts outside the allowlist."""
    if not has_install_script or (package_name, version) in allowed_install_scripts:
        return []
    return [
        Finding(
            severity="high",
            kind="unapproved_install_script",
            path=path,
            detail=f"{package_name}@{version} has an install script in package-lock.json",
            reason="lockfile install scripts require explicit review and allowlist entry",
        )
    ]


def check_text_patterns(
    *,
    path: Path,
    display_path: str,
    text_patterns: list[CompiledPattern],
) -> list[Finding]:
    """Return findings for known IOC text markers in a file."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[Finding] = []
    for pattern in text_patterns:
        if pattern.regex.search(text):
            findings.append(
                Finding(
                    severity="critical",
                    kind="known_ioc_text",
                    path=display_path,
                    detail=f"matched pattern {pattern.regex.pattern}",
                    reason=pattern.reason,
                )
            )
    return findings


def check_persistence_files(
    *,
    repo_root: Path,
    entries: Iterable[dict[str, object]],
    text_patterns: list[CompiledPattern],
) -> list[Finding]:
    """Return findings for suspicious IDE or agent persistence files."""
    findings: list[Finding] = []
    for entry in entries:
        relative = str(entry.get("path", ""))
        if not relative:
            raise ValueError("persistence file entry is missing a path")
        path = repo_root / relative
        if not path.exists():
            if not bool(entry.get("allow_missing", True)):
                findings.append(
                    Finding(
                        severity="high",
                        kind="missing_persistence_file",
                        path=relative,
                        detail="required persistence sentinel file is missing",
                        reason=str(entry.get("reason", "persistence policy")),
                    )
                )
            continue
        size = path.stat().st_size
        if size == 0 and bool(entry.get("allow_empty", True)):
            continue
        if size > 0 and not bool(entry.get("allow_non_empty", False)):
            findings.append(
                Finding(
                    severity="high",
                    kind="unexpected_persistence_file_content",
                    path=relative,
                    detail=f"{relative} is non-empty ({size} bytes)",
                    reason=str(entry.get("reason", "persistence policy")),
                )
            )
        findings.extend(
            check_text_patterns(path=path, display_path=relative, text_patterns=text_patterns)
        )
    return findings


def audit_package_json(
    *,
    path: Path,
    package_patterns: list[CompiledPattern],
    text_patterns: list[CompiledPattern],
    blocked_prefixes: tuple[str, ...],
    blocked_scripts: set[str],
) -> list[Finding]:
    """Audit the frontend package manifest."""
    document = load_json(path)
    if not isinstance(document, dict):
        raise ValueError(f"{path} must be a JSON object")
    package_name = str(document.get("name", "<root>"))
    version = str(document.get("version", "0.0.0"))
    display_path = str(path)
    findings = check_text_patterns(
        path=path,
        display_path=display_path,
        text_patterns=text_patterns,
    )
    findings.extend(
        check_package_patterns(
            package_name=package_name,
            path=f"{display_path}:name",
            package_patterns=package_patterns,
        )
    )
    findings.extend(
        check_dependency_specs(
            document=document,
            path=display_path,
            blocked_prefixes=blocked_prefixes,
            package_patterns=package_patterns,
        )
    )
    findings.extend(
        check_lifecycle_scripts(
            package_name=package_name,
            version=version,
            scripts=document.get("scripts"),
            path=display_path,
            blocked_scripts=blocked_scripts,
        )
    )
    return findings


def audit_package_lock(
    *,
    path: Path,
    package_patterns: list[CompiledPattern],
    text_patterns: list[CompiledPattern],
    blocked_prefixes: tuple[str, ...],
    blocked_scripts: set[str],
    allowed_install_scripts: set[tuple[str, str]],
) -> list[Finding]:
    """Audit package-lock package metadata and install-script flags."""
    document = load_json(path)
    if not isinstance(document, dict):
        raise ValueError(f"{path} must be a JSON object")
    findings = check_text_patterns(
        path=path,
        display_path=str(path),
        text_patterns=text_patterns,
    )
    packages = document.get("packages")
    if not isinstance(packages, dict):
        return findings
    for lock_path, package_data in packages.items():
        if not isinstance(lock_path, str) or not isinstance(package_data, dict):
            continue
        package_name = package_name_from_lock_path(lock_path, package_data)
        version = str(package_data.get("version", "0.0.0"))
        display_path = f"{path}:packages:{lock_path or '<root>'}"
        findings.extend(
            check_package_patterns(
                package_name=package_name,
                path=display_path,
                package_patterns=package_patterns,
            )
        )
        findings.extend(
            check_dependency_specs(
                document=package_data,
                path=display_path,
                blocked_prefixes=blocked_prefixes,
                package_patterns=package_patterns,
            )
        )
        findings.extend(
            check_lifecycle_scripts(
                package_name=package_name,
                version=version,
                scripts=package_data.get("scripts"),
                path=display_path,
                blocked_scripts=blocked_scripts,
            )
        )
        findings.extend(
            check_install_script_allowlist(
                package_name=package_name,
                version=version,
                path=display_path,
                has_install_script=bool(package_data.get("hasInstallScript", False)),
                allowed_install_scripts=allowed_install_scripts,
            )
        )
        resolved = package_data.get("resolved")
        if isinstance(resolved, str) and resolved.lower().startswith(("git:", "git+")):
            findings.append(
                Finding(
                    severity="high",
                    kind="blocked_resolved_source",
                    path=f"{display_path}:resolved",
                    detail=f"{package_name}@{version} resolves from {resolved}",
                    reason="git-sourced lockfile packages bypass npm registry review",
                )
            )
    return findings


def write_report(
    *,
    report_path: Path,
    repo_root: Path,
    checked_files: list[str],
    findings: list[Finding],
) -> None:
    """Write the audit result JSON report."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "fail" if findings else "pass",
        "repo_root": str(repo_root),
        "checked_files": checked_files,
        "summary": {
            "findings": len(findings),
            "critical": sum(1 for finding in findings if finding.severity == "critical"),
            "high": sum(1 for finding in findings if finding.severity == "high"),
        },
        "findings": [finding.to_json() for finding in findings],
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the npm worm audit and return a process exit code."""
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    client_dir = (args.client_dir or repo_root / "src" / "client").resolve()
    config_path = args.config or repo_root / "config" / "security" / "npm-worm-audit.json"
    report_path = args.report_path or repo_root / DEFAULT_REPORT
    config = load_json(config_path)
    if not isinstance(config, dict):
        raise ValueError(f"{config_path} must be a JSON object")

    package_patterns = compile_patterns(config.get("blocked_package_patterns", []))
    text_patterns = compile_patterns(config.get("blocked_text_patterns", []))
    blocked_prefixes = tuple(
        str(prefix).lower() for prefix in config["blocked_dependency_spec_prefixes"]
    )
    blocked_scripts = {str(name) for name in config.get("blocked_lifecycle_scripts", [])}
    allowed_install_scripts = {
        (str(entry["package"]), str(entry["version"]))
        for entry in config.get("allowed_install_scripts", [])
    }

    package_json = client_dir / "package.json"
    package_lock = client_dir / "package-lock.json"
    checked_files: list[str] = []
    findings: list[Finding] = []
    # A template may not ship a frontend. Scan npm manifests only when present;
    # the persistence-file checks below run regardless.
    if package_json.exists():
        checked_files.append(str(package_json))
        findings.extend(
            audit_package_json(
                path=package_json,
                package_patterns=package_patterns,
                text_patterns=text_patterns,
                blocked_prefixes=blocked_prefixes,
                blocked_scripts=blocked_scripts,
            )
        )
    if package_lock.exists():
        checked_files.append(str(package_lock))
        findings.extend(
            audit_package_lock(
                path=package_lock,
                package_patterns=package_patterns,
                text_patterns=text_patterns,
                blocked_prefixes=blocked_prefixes,
                blocked_scripts=blocked_scripts,
                allowed_install_scripts=allowed_install_scripts,
            )
        )
    for extra_package_json in args.extra_package_json:
        extra_path = extra_package_json.resolve()
        if not extra_path.exists():
            continue
        checked_files.append(str(extra_path))
        findings.extend(
            audit_package_json(
                path=extra_path,
                package_patterns=package_patterns,
                text_patterns=text_patterns,
                blocked_prefixes=blocked_prefixes,
                blocked_scripts=blocked_scripts,
            )
        )
    persistence_entries = config.get("persistence_files", [])
    if not isinstance(persistence_entries, list):
        raise ValueError("persistence_files must be a list")
    checked_files.extend(
        str(repo_root / str(entry.get("path", ""))) for entry in persistence_entries
    )
    findings.extend(
        check_persistence_files(
            repo_root=repo_root,
            entries=persistence_entries,
            text_patterns=text_patterns,
        )
    )

    write_report(
        report_path=report_path,
        repo_root=repo_root,
        checked_files=checked_files,
        findings=findings,
    )
    if findings:
        print(
            f"npm worm audit failed with {len(findings)} finding(s); see {report_path}",
            file=sys.stderr,
        )
        return 1
    print(f"npm worm audit passed; report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
