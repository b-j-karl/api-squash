from __future__ import annotations

import fnmatch
from pathlib import Path

DEFAULT_SKIP_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    ".git",
    "node_modules",
    ".tox",
    ".eggs",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
}


def scan_directory(
    root: Path,
    *,
    exclude: list[str] | None = None,
    max_depth: int | None = None,
) -> list[Path]:
    exclude = exclude or []
    found: list[Path] = []
    _walk(root, root, found, exclude, max_depth, depth=0)
    found.sort()
    return found


def _walk(
    root: Path,
    current: Path,
    found: list[Path],
    exclude: list[str],
    max_depth: int | None,
    depth: int,
) -> None:
    if max_depth is not None and depth > max_depth:
        return

    try:
        entries = sorted(current.iterdir())
    except PermissionError:
        return

    for entry in entries:
        relative = entry.relative_to(root).as_posix()

        if entry.is_dir():
            if entry.name in DEFAULT_SKIP_DIRS:
                continue
            if any(
                fnmatch.fnmatch(relative, pat) or fnmatch.fnmatch(entry.name, pat)
                for pat in exclude
            ):
                continue
            _walk(root, entry, found, exclude, max_depth, depth + 1)
        elif entry.is_file() and entry.suffix == ".py":
            if any(fnmatch.fnmatch(relative, pat) for pat in exclude):
                continue
            found.append(entry)
