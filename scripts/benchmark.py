"""Benchmark api-squash against well-known Python packages.

Generates a Markdown table and injects it into README.md between
``<!-- bench-start -->`` / ``<!-- bench-end -->`` markers.

Usage:
    uv run python scripts/benchmark.py
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path

from api_squash.extractor import extract_file
from api_squash.renderer import render_project
from api_squash.scanner import scan_directory

PACKAGES: list[str] = ["click", "requests", "flask", "django", "fastapi"]

README_PATH = Path(__file__).resolve().parent.parent / "README.md"

BENCH_START = "<!-- bench-start -->"
BENCH_END = "<!-- bench-end -->"


@dataclass
class BenchmarkResult:
    package: str
    version: str
    source_files: int
    source_lines: int
    output_lines: int
    output_chars: int

    @property
    def compression_pct(self) -> int:
        if self.source_lines == 0:
            return 0
        return round((1 - self.output_lines / self.source_lines) * 100)

    @property
    def approx_tokens(self) -> int:
        return self.output_chars // 4


def _find_package_source(package_name: str) -> Path:
    """Locate the installed source directory for a package."""
    spec = importlib.util.find_spec(package_name)
    if spec is None or spec.origin is None:
        raise RuntimeError(f"Cannot find installed package: {package_name}")
    origin = Path(spec.origin)
    # origin is typically <site-packages>/<pkg>/__init__.py
    if origin.name == "__init__.py":
        return origin.parent
    return origin.parent


def benchmark_package(package_name: str) -> BenchmarkResult:
    """Run api-squash against an installed package and return metrics."""
    src_dir = _find_package_source(package_name)
    version = importlib.metadata.version(package_name)

    py_files = scan_directory(src_dir)
    source_lines = 0
    for f in py_files:
        source_lines += f.read_text(encoding="utf-8").count("\n")

    modules = []
    for file_path in py_files:
        try:
            module = extract_file(file_path)
            module.path = file_path.relative_to(src_dir).as_posix()
            modules.append(module)
        except (SyntaxError, Exception):
            continue

    output = render_project(modules) if modules else ""
    output_lines = output.count("\n")
    output_chars = len(output)

    return BenchmarkResult(
        package=package_name,
        version=version,
        source_files=len(py_files),
        source_lines=source_lines,
        output_lines=output_lines,
        output_chars=output_chars,
    )


def generate_table(results: list[BenchmarkResult]) -> str:
    """Render benchmark results as a Markdown table."""
    lines = [
        "| Package | Source files | Source lines | Output lines | Compression | ≈ Tokens |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r.package} {r.version} "
            f"| {r.source_files:,} "
            f"| {r.source_lines:,} "
            f"| {r.output_lines:,} "
            f"| {r.compression_pct}% "
            f"| {r.approx_tokens:,} |"
        )
    return "\n".join(lines)


def update_readme(table_md: str, readme_path: Path = README_PATH) -> None:
    """Replace the benchmarks section in README.md between markers."""
    text = readme_path.read_text(encoding="utf-8")

    pattern = re.compile(
        rf"({re.escape(BENCH_START)})\n(.*?\n)?({re.escape(BENCH_END)})",
        re.DOTALL,
    )
    replacement = f"{BENCH_START}\n{table_md}\n{BENCH_END}"

    new_text, count = pattern.subn(replacement, text)
    if count == 0:
        raise RuntimeError(
            f"Could not find {BENCH_START} / {BENCH_END} markers in {readme_path}"
        )

    readme_path.write_text(new_text, encoding="utf-8")


def run_all(packages: list[str] | None = None) -> list[BenchmarkResult]:
    """Benchmark all packages and return results."""
    packages = packages or PACKAGES
    results: list[BenchmarkResult] = []
    for pkg in packages:
        print(f"Benchmarking {pkg}...")
        result = benchmark_package(pkg)
        print(
            f"  {result.source_files} files, "
            f"{result.source_lines:,} source lines → "
            f"{result.output_lines:,} output lines "
            f"({result.compression_pct}% compression)"
        )
        results.append(result)
    return results


if __name__ == "__main__":
    results = run_all()
    table = generate_table(results)
    print()
    print(table)
    print()
    update_readme(table)
    print("✓ README.md updated")
