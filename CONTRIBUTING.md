# Contributing to api-squash

Thanks for your interest in contributing! This document describes the branching
strategy and workflow used in this project.

## Branching Strategy

We use a **gitflow-style** branching model:

```
main          ← production-ready, tagged releases only
  └── develop ← integration branch, always ahead of or equal to main
        ├── feature/  ← new features
        ├── fix/      ← bug fixes
        └── chore/    ← maintenance tasks
```

- **`main`** — stable, release-only branch. Every commit on `main` is a
  tagged release.
- **`develop`** — integration branch where feature and fix branches merge
  into. This is the default branch.

## Development Workflow

### Feature / Fix / Chore

1. Branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-feature   # or fix/, chore/
   ```
2. Make frequent, atomic commits using
   [conventional commit](https://www.conventionalcommits.org/) messages
   (e.g. `feat: add parser`, `fix: handle empty input`).
3. Open a pull request targeting **`develop`**.
4. After review, merge into `develop` (squash-merge or regular merge).

### Releases

1. When `develop` is ready for release, open a PR from `develop` → `main`.
2. Review and merge into `main`.
3. Tag the merge commit on `main` with a semver tag (e.g. `v0.2.0`).
4. Merge `main` back into `develop` to pick up the merge/tag commit.

### Hotfixes

1. Branch from `main` → `fix/<description>`.
2. Fix the issue, open a PR into `main`, and tag a patch release.
3. Merge `main` back into `develop` to keep branches in sync.

## Development Setup

```bash
# Requires Python >= 3.10 and uv (https://docs.astral.sh/uv/)
uv sync

# Run tests
uv run pytest -v

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/
```

## Code Conventions

- **TDD** — write failing tests first, then implement.
- Use `pathlib.Path` throughout; never use raw string paths.
- All file I/O uses `encoding="utf-8"` explicitly.
- Output uses forward slashes in file path headers regardless of OS.
- Use conventional commit messages (`feat:`, `fix:`, `chore:`, `docs:`, etc.).
