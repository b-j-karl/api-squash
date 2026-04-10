# AGENTS.md

## Build & Run

- **Package manager:** uv
- **Install deps:** `uv sync`
- **Run tests:** `uv run pytest -v`
- **Lint:** `uv run ruff check src/ tests/`
- **Format:** `uv run ruff format src/ tests/`
- **CLI:** `uv run api-squash --help`

> **Note:** Python is not directly on PATH in this environment. Always use `uv run` for all Python commands.

## Project Structure

- Source code: `src/api_squash/`
- Tests: `tests/`
- Specs: `docs/superpowers/specs/`
- Plans: `docs/superpowers/plans/`

## Conventions

- TDD: Write failing tests first, then implement
- Use `pathlib.Path` throughout, never raw string paths
- Output uses forward slashes in file path headers regardless of OS
- All file I/O uses `encoding="utf-8"` explicitly
- Frequent, atomic commits with conventional commit messages
- New output features default to ON; use `--no-X` opt-out flags (not `--include-X` opt-in)
- Always create a dedicated feature branch (e.g. `feat/description`) before implementing an issue
