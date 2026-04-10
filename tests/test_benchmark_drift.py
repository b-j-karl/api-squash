"""Guard against benchmark data in README and SVG chart drifting from reality.

Re-runs api-squash against the same installed packages and compares results
to the values hardcoded in README.md and docs/benchmark-chart.svg.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import re
from pathlib import Path

import pytest

from api_squash.extractor import extract_file
from api_squash.renderer import render_project
from api_squash.scanner import scan_directory

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
SVG = ROOT / "docs" / "benchmark-chart.svg"

PACKAGES = ["click", "requests", "flask", "django", "fastapi"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_package_source(package_name: str) -> Path:
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        raise RuntimeError(f"Cannot find installed package: {package_name}")
    if spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations)))
    if spec.origin is None:
        raise RuntimeError(f"Cannot find installed package: {package_name}")
    return Path(spec.origin).parent


def _benchmark(package_name: str) -> dict:
    """Return live benchmark numbers for a single package."""
    src_dir = _find_package_source(package_name)
    version = importlib.metadata.version(package_name)
    py_files = scan_directory(src_dir)

    source_lines = 0
    source_chars = 0
    for f in py_files:
        text = f.read_text(encoding="utf-8")
        source_lines += len(text.splitlines())
        source_chars += len(text)

    modules = []
    for fp in py_files:
        try:
            m = extract_file(fp)
            m.path = fp.relative_to(src_dir).as_posix()
            modules.append(m)
        except Exception:
            continue

    default_output = render_project(modules) if modules else ""
    max_output = (
        render_project(modules, no_docstrings=True, no_private=True) if modules else ""
    )

    return {
        "package": package_name,
        "version": version,
        "source_files": len(py_files),
        "source_lines": source_lines,
        "source_tokens": source_chars // 4,
        "output_lines": len(default_output.splitlines()),
        "output_chars": len(default_output),
        "default_tokens": len(default_output) // 4,
        "max_tokens": len(max_output) // 4,
    }


def _parse_readme_table(text: str) -> dict[str, dict]:
    """Extract benchmark rows from the README Markdown table."""
    in_table = False
    results: dict[str, dict] = {}
    for line in text.splitlines():
        if "Source files" in line and "Source lines" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # cells: package+version, source_files, source_lines, output_lines, compression, tokens
            pkg_ver = cells[0]
            pkg = pkg_ver.rsplit(" ", 1)[0]
            results[pkg] = {
                "source_files": int(cells[1].replace(",", "")),
                "source_lines": int(cells[2].replace(",", "")),
                "output_lines": int(cells[3].replace(",", "")),
                "approx_tokens": int(cells[5].replace(",", "")),
            }
        elif in_table:
            break
    return results


def _parse_svg_tokens(text: str) -> dict[str, dict]:
    """Extract the three token-count labels per package from the SVG.

    The SVG has comment blocks like ``<!-- click — 96k / 37k / 9k -->``
    followed by three ``<text>`` value labels.
    """
    results: dict[str, dict] = {}
    # Match comment lines: <!-- package — source / default / max -->
    pattern = re.compile(
        r"<!--\s*(\w+)\s.*?(\d+(?:\.\d+)?[kM])\s*/\s*(\d+(?:\.\d+)?[kM])\s*/\s*(\d+(?:\.\d+)?[kM])"
    )
    for m in pattern.finditer(text):
        pkg = m.group(1)
        results[pkg] = {
            "source_tokens": _parse_label(m.group(2)),
            "default_tokens": _parse_label(m.group(3)),
            "max_tokens": _parse_label(m.group(4)),
        }
    return results


def _parse_label(label: str) -> int:
    """Convert '96k' → 96000, '1.4M' → 1400000."""
    if label.endswith("M"):
        return int(float(label[:-1]) * 1_000_000)
    if label.endswith("k"):
        return int(float(label[:-1]) * 1_000)
    return int(label)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

# Cache benchmarks across tests in this module (expensive to compute).
_benchmark_cache: dict[str, dict] = {}


def _get_benchmarks() -> dict[str, dict]:
    if not _benchmark_cache:
        for pkg in PACKAGES:
            _benchmark_cache[pkg] = _benchmark(pkg)
    return _benchmark_cache


@pytest.fixture(scope="module")
def live_benchmarks() -> dict[str, dict]:
    return _get_benchmarks()


class TestReadmeBenchmarkTable:
    """README benchmark table matches live data."""

    def test_table_present(self):
        text = README.read_text(encoding="utf-8")
        table = _parse_readme_table(text)
        assert table, "No benchmark table found between markers in README.md"

    def test_all_packages_present(self):
        text = README.read_text(encoding="utf-8")
        table = _parse_readme_table(text)
        for pkg in PACKAGES:
            assert pkg in table, f"{pkg} missing from README benchmark table"

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_source_files_match(self, pkg, live_benchmarks):
        text = README.read_text(encoding="utf-8")
        table = _parse_readme_table(text)
        assert table[pkg]["source_files"] == live_benchmarks[pkg]["source_files"], (
            f"{pkg}: README says {table[pkg]['source_files']} source files, "
            f"actual is {live_benchmarks[pkg]['source_files']}"
        )

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_source_lines_match(self, pkg, live_benchmarks):
        text = README.read_text(encoding="utf-8")
        table = _parse_readme_table(text)
        assert table[pkg]["source_lines"] == live_benchmarks[pkg]["source_lines"], (
            f"{pkg}: README says {table[pkg]['source_lines']} source lines, "
            f"actual is {live_benchmarks[pkg]['source_lines']}"
        )

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_output_lines_match(self, pkg, live_benchmarks):
        text = README.read_text(encoding="utf-8")
        table = _parse_readme_table(text)
        assert table[pkg]["output_lines"] == live_benchmarks[pkg]["output_lines"], (
            f"{pkg}: README says {table[pkg]['output_lines']} output lines, "
            f"actual is {live_benchmarks[pkg]['output_lines']}"
        )

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_approx_tokens_match(self, pkg, live_benchmarks):
        text = README.read_text(encoding="utf-8")
        table = _parse_readme_table(text)
        assert (
            table[pkg]["approx_tokens"] == live_benchmarks[pkg]["output_chars"] // 4
        ), (
            f"{pkg}: README says ≈{table[pkg]['approx_tokens']} tokens, "
            f"actual is {live_benchmarks[pkg]['output_chars'] // 4}"
        )


class TestSvgBenchmarkChart:
    """SVG chart token counts match live data."""

    def test_svg_exists(self):
        assert SVG.exists(), f"Benchmark chart not found at {SVG}"

    def test_all_packages_present(self):
        text = SVG.read_text(encoding="utf-8")
        tokens = _parse_svg_tokens(text)
        for pkg in PACKAGES:
            assert pkg in tokens, f"{pkg} missing from SVG chart"

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_source_tokens_within_tolerance(self, pkg, live_benchmarks):
        """SVG source token labels are within 10% of live values.

        The SVG uses rounded labels like '96k' or '1.4M', so exact match
        is not expected — but they should be within 10% of reality.
        """
        text = SVG.read_text(encoding="utf-8")
        svg_data = _parse_svg_tokens(text)
        svg_val = svg_data[pkg]["source_tokens"]
        live_val = live_benchmarks[pkg]["source_tokens"]
        pct_diff = abs(svg_val - live_val) / live_val
        assert pct_diff < 0.10, (
            f"{pkg}: SVG says ~{svg_val} source tokens, "
            f"actual is {live_val} ({pct_diff:.0%} off)"
        )

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_default_tokens_within_tolerance(self, pkg, live_benchmarks):
        text = SVG.read_text(encoding="utf-8")
        svg_data = _parse_svg_tokens(text)
        svg_val = svg_data[pkg]["default_tokens"]
        live_val = live_benchmarks[pkg]["default_tokens"]
        pct_diff = abs(svg_val - live_val) / live_val
        assert pct_diff < 0.10, (
            f"{pkg}: SVG says ~{svg_val} default tokens, "
            f"actual is {live_val} ({pct_diff:.0%} off)"
        )

    @pytest.mark.parametrize("pkg", PACKAGES)
    def test_max_tokens_within_tolerance(self, pkg, live_benchmarks):
        text = SVG.read_text(encoding="utf-8")
        svg_data = _parse_svg_tokens(text)
        svg_val = svg_data[pkg]["max_tokens"]
        live_val = live_benchmarks[pkg]["max_tokens"]
        pct_diff = abs(svg_val - live_val) / live_val
        assert pct_diff < 0.10, (
            f"{pkg}: SVG says ~{svg_val} max tokens, "
            f"actual is {live_val} ({pct_diff:.0%} off)"
        )
