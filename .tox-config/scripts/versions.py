#!/usr/bin/env python3
"""Read and check the Python versions the project is tested on.

Two files decide everything, locally and in CI:

- ``.tox-config/versions.txt``: one tox environment per line, followed by
  its markers -- ``local`` (test.sh runs it), ``ci`` (the CI test-unit
  matrix runs it), ``experimental`` (CI only, allowed to fail);
- ``.tox-config/coverage-version.txt``: the environment that measures
  coverage.

Commands (every command checks both files first and stops on an error):

- ``check``            report errors and warnings, exit 1 on any error;
- ``local``            local environments, coverage environment excluded
                       (coverage.sh tests that one), one per line;
- ``coverage-python``  interpreter of the coverage run, e.g. ``python3.12``;
- ``coverage-version`` its version number, e.g. ``3.12``;
- ``matrix``           the CI test-unit matrix as JSON.

Standard library only, Python 3.11 or later (tomllib).
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSIONS_FILE = ROOT / ".tox-config" / "versions.txt"
COVERAGE_FILE = ROOT / ".tox-config" / "coverage-version.txt"
PYPROJECT = ROOT / "pyproject.toml"

MARKERS = ("local", "ci", "experimental")
ENV_PATTERN = re.compile(r"^py3(\d{2,})$")
CLASSIFIER_PATTERN = re.compile(r"^Programming Language :: Python :: 3\.(\d+)$")
FLOOR_PATTERN = re.compile(r"^>=\s*3\.(\d+)$")


@dataclass(frozen=True)
class Version:
    """One line of versions.txt."""

    env: str
    minor: int
    markers: frozenset[str]

    @property
    def number(self) -> str:
        return f"3.{self.minor}"

    @property
    def local(self) -> bool:
        return "local" in self.markers

    @property
    def ci(self) -> bool:
        return "ci" in self.markers

    @property
    def experimental(self) -> bool:
        return "experimental" in self.markers


@dataclass
class Report:
    """Findings of a check."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, text: str) -> None:
        self.errors.append(text)

    def warning(self, text: str) -> None:
        self.warnings.append(text)


def _content_lines(path: Path) -> list[tuple[int, str]]:
    """Non-empty, non-comment lines of a file, with their line numbers."""
    lines: list[tuple[int, str]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = raw.split("#", 1)[0].strip()
        if text:
            lines.append((number, text))
    return lines


def read_versions(report: Report) -> list[Version]:
    """Parse versions.txt; malformed lines are reported and skipped."""
    if not VERSIONS_FILE.is_file():
        report.error(f"{VERSIONS_FILE.name}: file not found")
        return []
    versions: list[Version] = []
    seen: set[str] = set()
    for number, text in _content_lines(VERSIONS_FILE):
        where = f"{VERSIONS_FILE.name}:{number}"
        env, *markers = text.split()
        match = ENV_PATTERN.match(env)
        if match is None:
            report.error(f"{where}: '{env}' is not a pyNNN environment name")
            continue
        if env in seen:
            report.error(f"{where}: {env} is listed twice")
            continue
        seen.add(env)
        unknown = [m for m in markers if m not in MARKERS]
        if unknown:
            report.error(
                f"{where}: unknown marker(s) {', '.join(unknown)}"
                f" (expected: {', '.join(MARKERS)})"
            )
            continue
        if len(set(markers)) != len(markers):
            report.error(f"{where}: a marker is repeated")
            continue
        if not markers:
            report.error(f"{where}: {env} has no marker (local, ci or both)")
            continue
        version = Version(env, int(match.group(1)), frozenset(markers))
        if version.experimental and not version.ci:
            report.error(f"{where}: experimental applies to ci only; add ci")
            continue
        if version.experimental and version.local:
            report.error(
                f"{where}: {env} is experimental, it cannot be local"
                " (the local run must pass)"
            )
            continue
        versions.append(version)
    return versions


def read_coverage(report: Report, versions: list[Version]) -> Version | None:
    """Parse coverage-version.txt and check it against versions.txt."""
    if not COVERAGE_FILE.is_file():
        report.error(f"{COVERAGE_FILE.name}: file not found")
        return None
    lines = _content_lines(COVERAGE_FILE)
    if len(lines) != 1:
        report.error(
            f"{COVERAGE_FILE.name}: expected exactly one environment,"
            f" found {len(lines)}"
        )
        return None
    number, env = lines[0]
    where = f"{COVERAGE_FILE.name}:{number}"
    found = next((v for v in versions if v.env == env), None)
    if found is None:
        report.error(f"{where}: {env} is not listed in {VERSIONS_FILE.name}")
        return None
    if not (found.local and found.ci) or found.experimental:
        report.error(
            f"{where}: {env} must be marked local and ci, and not experimental,"
            f" in {VERSIONS_FILE.name}"
        )
        return None
    return found


def check_project(report: Report, versions: list[Version]) -> None:
    """Compare the stable CI versions with the metadata of pyproject.toml."""
    stable = {v.minor for v in versions if v.ci and not v.experimental}
    if not stable:
        report.error(f"{VERSIONS_FILE.name}: no stable ci version")
    if not any(v.local for v in versions):
        report.error(f"{VERSIONS_FILE.name}: no local version")
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    declared = {
        int(m.group(1))
        for c in project.get("classifiers", [])
        if (m := CLASSIFIER_PATTERN.match(c)) is not None
    }
    for minor in sorted(stable - declared):
        report.error(
            f"pyproject.toml: 3.{minor} is tested in ci but has no"
            f" 'Programming Language :: Python :: 3.{minor}' classifier"
        )
    for minor in sorted(declared - stable):
        report.error(
            f"pyproject.toml: the 3.{minor} classifier has no stable ci"
            f" version in {VERSIONS_FILE.name}"
        )
    floor = FLOOR_PATTERN.match(str(project.get("requires-python", "")).strip())
    if floor is not None and stable and int(floor.group(1)) != min(stable):
        report.warning(
            f"pyproject.toml: requires-python is >=3.{floor.group(1)} but the"
            f" lowest stable ci version is 3.{min(stable)}"
        )
    for version in versions:
        if version.local and not version.ci:
            report.warning(f"{version.env} is tested locally but not in ci")
        if version.ci and not version.experimental and not version.local:
            report.warning(f"{version.env} is tested in ci but not locally")


def load() -> tuple[list[Version], Version | None, Report]:
    """Read and check both files."""
    report = Report()
    versions = read_versions(report)
    coverage = read_coverage(report, versions)
    check_project(report, versions)
    return versions, coverage, report


def main(argv: list[str]) -> int:
    commands = ("check", "local", "coverage-python", "coverage-version", "matrix")
    if len(argv) != 1 or argv[0] not in commands:
        print(f"usage: versions.py {{{','.join(commands)}}}", file=sys.stderr)
        return 2
    command = argv[0]
    versions, coverage, report = load()
    for text in report.warnings:
        print(f"warning: {text}", file=sys.stderr)
    for text in report.errors:
        print(f"error: {text}", file=sys.stderr)
    if report.errors or coverage is None:
        print(f"versions: {len(report.errors)} error(s)", file=sys.stderr)
        return 1
    if command == "check":
        print(
            f"versions: ok — local {' '.join(v.env for v in versions if v.local)};"
            f" ci {' '.join(v.env for v in versions if v.ci)};"
            f" coverage {coverage.env}; {len(report.warnings)} warning(s)",
            file=sys.stderr,
        )
    elif command == "local":
        for version in versions:
            if version.local and version != coverage:
                print(version.env)
    elif command == "coverage-python":
        print(f"python{coverage.number}")
    elif command == "coverage-version":
        print(coverage.number)
    else:
        include = [
            {
                "python-version": v.number,
                "tox-env": v.env,
                "experimental": v.experimental,
            }
            for v in versions
            if v.ci
        ]
        print(json.dumps({"include": include}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
