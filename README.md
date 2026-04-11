# api-squash

> Extract Python API surfaces in a compact, token-efficient format.

[![CI](https://github.com/b-j-karl/api-squash/actions/workflows/ci.yml/badge.svg)](https://github.com/b-j-karl/api-squash/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/b-j-karl/api-squash/branch/develop/graph/badge.svg)](https://codecov.io/gh/b-j-karl/api-squash)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

Agentic AI workflows need to understand a codebase's API surface without
burning context on implementation details. Pasting entire source files into a
prompt wastes tokens on function bodies, comments, and boilerplate that the
agent doesn't need.

**api-squash** parses Python source files using the AST and produces concise
Markdown summaries containing only the public API surface — classes, functions,
and their signatures — so AI agents can ingest a full project's interface in a
fraction of the tokens.

Built for agentic AI workflows: code-generation agents, autonomous refactoring
pipelines, and any system where an LLM needs to reason about code structure
programmatically.

## Installation

```bash
pip install api-squash
```

Or run without installing via [uvx](https://docs.astral.sh/uv/guides/tools/):

```bash
uvx api-squash --help
```

For development:

```bash
# Requires the uv package manager (https://docs.astral.sh/uv/)
uv sync
```

## Quick Start

Summarize a single file:

```bash
api-squash file path/to/module.py
```

Summarize an entire project:

```bash
api-squash project path/to/project/
```

### Example

Given a file `example_api.py`:

```python
"""Client for the Acme API."""

from dataclasses import dataclass


@dataclass
class Config:
    """Connection settings."""
    host: str
    port: int = 443
    timeout: float = 30.0


class AcmeClient:
    """High-level client for the Acme REST API."""

    def __init__(self, config: Config) -> None:
        self._config = config

    async def get_user(self, user_id: int) -> dict:
        """Fetch a single user by ID."""
        ...

    async def list_users(self, *, active: bool = True) -> list[dict]:
        """Return all users, optionally filtered."""
        ...

    def _build_url(self, path: str) -> str:
        ...
```

Running `api-squash file example_api.py` produces:

```
# example_api.py

class Config:
  Connection settings.

class AcmeClient:
  High-level client for the Acme REST API.
  def __init__(self, config: Config) -> None
  async def get_user(self, user_id: int) -> dict
    Fetch a single user by ID.
  async def list_users(self, *, active: bool = True) -> list[dict]
    Return all users, optionally filtered.
  def _build_url(self, path: str) -> str
```

With `--no-docstrings --no-private`, the output shrinks further:

```
# example_api.py

class Config:

class AcmeClient:
  def __init__(self, config: Config) -> None
  async def get_user(self, user_id: int) -> dict
  async def list_users(self, *, active: bool = True) -> list[dict]
```

## Benchmarks

Measured against real-world Python packages — not estimates. Default flags,
no docstring or private stripping.

<!-- bench-start -->
| Package | Source files | Source lines | Output lines | Compression | ≈ Tokens |
|---|---|---|---|---|---|
| click 8.3.2 | 17 | 11,136 | 3,262 | 71% | 36,961 |
| requests 2.33.1 | 18 | 5,626 | 1,527 | 73% | 14,606 |
| flask 3.1.3 | 24 | 9,199 | 3,595 | 61% | 38,586 |
| django 6.0.4 | 899 | 161,043 | 31,308 | 81% | 279,987 |
| fastapi 0.135.3 | 48 | 19,350 | 1,977 | 90% | 97,730 |
<!-- bench-end -->

*Reproduce with `uv run python scripts/benchmark.py`.*

## CLI Reference

### `api-squash file`

Summarize a single Python file.

```
Usage: api-squash file [OPTIONS] PATH
```

| Option | Description |
|---|---|
| `--no-docstrings` | Strip all docstrings from the output |
| `--no-private` | Skip private classes/methods (except `__init__`); keeps items referenced by public signatures |
| `--no-constants` | Exclude module-level UPPER_CASE constants from output |

### `api-squash project`

Summarize all Python files in a directory.

```
Usage: api-squash project [OPTIONS] PATH
```

| Option | Description |
|---|---|
| `--max-depth INTEGER` | Limit directory recursion depth |
| `--exclude TEXT` | Glob patterns to exclude (can be repeated) |
| `--no-docstrings` | Strip all docstrings from the output |
| `--no-private` | Skip private classes/methods (except `__init__`); keeps items referenced by public signatures |
| `--no-constants` | Exclude module-level UPPER_CASE constants from output |

Common directories like `__pycache__`, `.venv`, `.git`, `node_modules`,
`build`, and `dist` are skipped automatically.

> **Tip — large codebases:** If the project has more than ~30 source files,
> start with `--max-depth 1 --no-docstrings` to get a high-level overview,
> then drill into specific subpackages as needed. This avoids flooding an
> LLM's context window with the full API surface.

## Output Format

api-squash produces Markdown-style output designed for easy reading and
token-efficient LLM consumption:

- **File headers** — each module starts with `# path/to/file.py`
- **Classes** — rendered as `class Name(Base):` with docstrings indented below
- **Functions / methods** — rendered as `def name(signature) -> return_type`
  with docstrings indented below
- **Separators** — in project mode, modules are separated by `---`

## Development

**Prerequisites:** Python ≥ 3.10, [uv](https://docs.astral.sh/uv/)

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -v

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/
```

## Project Structure

```
src/api_squash/
├── cli.py          # Click CLI entry points
├── extractor.py    # AST-based API extraction
├── models.py       # Data models (ModuleSummary, ClassSummary, FunctionSummary)
├── renderer.py     # Markdown output rendering
└── scanner.py      # Directory scanning with exclusion patterns
```

## License

[MIT](LICENSE)
