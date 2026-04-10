"""Verify the README benchmark table matches live results.

This test re-runs the benchmark logic and asserts that the numbers
in README.md are identical to what the script would generate. If this
test fails, re-run ``uv run python scripts/benchmark.py`` to update
the README.

The test is skipped when installed package versions differ from those
recorded in the README (e.g. Django 6.x requires Python ≥3.12, so
older interpreters resolve a different major version).
"""

from __future__ import annotations

import importlib.metadata
import re
from pathlib import Path

import pytest

from scripts.benchmark import (
    BENCH_END,
    BENCH_START,
    PACKAGES,
    benchmark_package,
    generate_table,
)

README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def _extract_readme_table(readme_path: Path = README_PATH) -> str:
    """Extract the benchmark table between markers from README."""
    text = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(BENCH_START)}\n(.*?)\n{re.escape(BENCH_END)}",
        re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        pytest.fail(f"Could not find {BENCH_START} / {BENCH_END} markers in README.md")
    return match.group(1)


def _readme_package_versions(table: str) -> dict[str, str]:
    """Parse ``{package: version}`` from the first column of the README table."""
    versions: dict[str, str] = {}
    for line in table.splitlines():
        if line.startswith("|") and "---" not in line:
            cell = line.split("|")[1].strip()
            parts = cell.rsplit(" ", 1)
            if len(parts) == 2:
                versions[parts[0].lower()] = parts[1]
    return versions


@pytest.mark.benchmark
def test_readme_benchmarks_match_live_results() -> None:
    """README benchmark table must match freshly computed results."""
    readme_table = _extract_readme_table()
    readme_versions = _readme_package_versions(readme_table)

    mismatches: list[str] = []
    for pkg in PACKAGES:
        installed = importlib.metadata.version(pkg)
        readme_ver = readme_versions.get(pkg, "")
        if installed != readme_ver:
            mismatches.append(f"{pkg} (installed {installed}, README has {readme_ver})")

    if mismatches:
        pytest.skip(
            "Installed package versions differ from README — "
            "likely a different Python version: " + ", ".join(mismatches)
        )

    results = [benchmark_package(pkg) for pkg in PACKAGES]
    expected_table = generate_table(results)
    assert readme_table == expected_table, (
        "README benchmark table is out of date. "
        "Run `uv run python scripts/benchmark.py` to update it."
    )
