"""Verify the README benchmark table matches live results.

This test re-runs the benchmark logic and asserts that the numbers
in README.md are identical to what the script would generate. If this
test fails, re-run ``uv run python scripts/benchmark.py`` to update
the README.
"""

from __future__ import annotations

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


def test_readme_benchmarks_match_live_results() -> None:
    """README benchmark table must match freshly computed results."""
    results = [benchmark_package(pkg) for pkg in PACKAGES]
    expected_table = generate_table(results)
    actual_table = _extract_readme_table()
    assert actual_table == expected_table, (
        "README benchmark table is out of date. "
        "Run `uv run python scripts/benchmark.py` to update it."
    )
