---
name: api-squash-cli
description: >-
  Extract Python API surfaces in a compact, token-efficient Markdown format.
  Parses Python source files using the AST and produces concise summaries
  containing only classes, functions, and their signatures. Supports
  single-file and whole-project summarisation with options to strip docstrings,
  exclude private methods, limit recursion depth, and exclude paths by glob
  pattern.
license: MIT License
metadata:
  skill-author: b-j-karl
---

# api-squash

Extract Python API surfaces in a compact, token-efficient Markdown format using
AST parsing. Produces summaries containing only classes, functions, and their
signatures — no implementation details, no function bodies.

## When to use

- Summarising a Python module or project's public API
- Understanding codebase structure before generating code, writing tests, or
  planning refactors
- Gathering structural context without wasting tokens on full source files
- Answering questions like "what classes/functions does this project expose?"
- Preparing context for code-generation agents that need interface awareness

## When not to use

- Non-Python projects
- Reading full source code or implementation details
- Projects where you need function bodies, not just signatures

---

## Installation

```bash
pip install api-squash
```

If `api-squash` is not installed, install it before proceeding. In development
repos that bundle it, use `uv run api-squash` instead. To run without
installation, use `uvx api-squash`.

---

## Commands

### `api-squash file` — single-module summary

```bash
api-squash file [OPTIONS] PATH
```

| Option | Description |
|---|---|
| `--no-docstrings` | Strip all docstrings from the output |
| `--no-private` | Skip private classes/methods (except `__init__`); keeps items referenced by public signatures |
| `--no-constants` | Exclude module-level UPPER_CASE constants from output |

**Examples:**

```bash
# Full summary with docstrings and private methods
api-squash file src/auth/models.py

# Minimal summary — signatures only
api-squash file --no-docstrings --no-private src/auth/models.py
```

### `api-squash project` — whole-project summary

```bash
api-squash project [OPTIONS] PATH
```

| Option | Description |
|---|---|
| `--max-depth INTEGER` | Limit directory recursion depth |
| `--exclude TEXT` | Glob patterns to exclude (repeatable) |
| `--no-docstrings` | Strip all docstrings from the output |
| `--no-private` | Skip private classes/methods (except `__init__`); keeps items referenced by public signatures |
| `--no-constants` | Exclude module-level UPPER_CASE constants from output |

Common directories(`__pycache__`, `.venv`, `.git`, `node_modules`, `build`,
`dist`) are excluded automatically.

**Examples:**

```bash
# Summarise entire project
api-squash project src/

# Summarise top-level modules only, excluding tests
api-squash project --max-depth 1 --exclude "tests/*" src/

# Compact summary for token-constrained contexts
api-squash project --no-docstrings --no-private src/
```

---

## Output format

The output is Markdown-style, optimised for LLM consumption:

- **File headers** — each module starts with `# path/to/file.py`
- **Classes** — rendered as `class Name(Base):` with docstrings indented below
- **Functions / methods** — rendered as `def name(signature) -> return_type`
  with docstrings indented below
- **Module separators** — in project mode, modules are separated by `---`

### Example output

For a file containing an `AcmeClient` class:

```
# acme/client.py

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

With `--no-docstrings --no-private`:

```
# acme/client.py

class Config:

class AcmeClient:
  def __init__(self, config: Config) -> None
  async def get_user(self, user_id: int) -> dict
  async def list_users(self, *, active: bool = True) -> list[dict]
```

---

## Practical patterns

### Capture output to a file for later use

```bash
api-squash project src/ > api-surface.md
```

### Choosing the right flags

| Context | Recommended flags |
|---|---|
| Full API documentation | *(none — defaults)* |
| Quick structural overview | `--no-docstrings` |
| Minimal token budget | `--no-docstrings --no-private` |
| Top-level architecture only | `--max-depth 1 --no-docstrings` |
| Large codebase (30+ files) | `--max-depth 1 --no-docstrings`, then drill into subpackages |
| Exclude test files | `--exclude "tests/*" --exclude "test_*"` |

### Combining with other tools

```bash
# Summarise API, then use the output as context for code generation
api-squash project src/ > api-surface.md

# Summarise only a specific subpackage
api-squash project src/api_squash/
```
