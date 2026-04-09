# api-squash Design Spec

## Problem

Agentic programming workflows consume large context windows. When an LLM needs to understand a Python codebase's API surface, sending full source files wastes tokens on implementation details, blank lines, and syntax noise. There is no lightweight CLI tool that extracts just the API surface — signatures, types, docstrings — in a format optimized for minimal token usage.

## Proposed Solution

A CLI tool called `api-squash` that uses Python's `ast` module to extract the public API surface of Python files and projects, and renders it in a compact, token-efficient text format to stdout.

## Architecture

**Approach: AST → Intermediate Model → Renderer**

Source files are parsed into structured dataclass models, which are then rendered to the compact output format. This separation keeps extraction logic independent from formatting, making both easy to test and extend.

### Components

```
api-squash/
├── pyproject.toml              # uv-managed, Click dependency
├── src/
│   └── api_squash/
│       ├── __init__.py
│       ├── cli.py              # Click CLI entry point
│       ├── extractor.py        # AST walking, builds model
│       ├── models.py           # Dataclasses for extracted API surface
│       ├── renderer.py         # Compact text output formatter
│       └── scanner.py          # Project-level file discovery
└── tests/
    ├── test_extractor.py
    ├── test_renderer.py
    ├── test_scanner.py
    └── test_cli.py
```

#### 1. Models (`models.py`)

Dataclasses representing the extracted API surface:

- **`FunctionSummary`**: name, parameters (with type hints), return type, docstring, is_method flag
- **`ClassSummary`**: name, docstring, list of `FunctionSummary` (methods), base classes
- **`ModuleSummary`**: file path, list of `ClassSummary`, list of top-level `FunctionSummary`

#### 2. Extractor (`extractor.py`)

Uses Python's `ast` module to walk a source file and produce a `ModuleSummary`:

- Visits `ast.FunctionDef` and `ast.AsyncFunctionDef` for functions/methods
- Visits `ast.ClassDef` for classes and their methods
- Extracts `ast.get_docstring()` for each node
- Reconstructs signature strings from `ast.arguments` including type annotations
- Handles return type annotations
- Skips function bodies entirely — only signatures and docstrings matter

#### 3. Renderer (`renderer.py`)

Takes `ModuleSummary` (or list for project scan) and produces compact text:

- File path as `# path/to/file.py` header
- Class name and docstring (no triple quotes, stripped)
- Method/function signatures without trailing `:` or body
- Full docstrings (all lines) indented under their function, with noise stripped
- One blank line between top-level items, no blank lines within classes
- `---` separator between files in project scans

#### 4. Scanner (`scanner.py`)

Discovers `.py` files for project-level scanning:

- Recursive directory walk using `pathlib.Path`
- Skips common non-source dirs: `__pycache__`, `.venv`, `venv`, `.git`, `node_modules`, `.tox`, `.eggs`
- Supports `--exclude` glob patterns
- Supports `--max-depth` to limit recursion
- Sorts files for deterministic output

#### 5. CLI (`cli.py`)

Click-based CLI with two commands:

```
# Single file
api-squash file path/to/module.py

# Entire project
api-squash project path/to/project/

# With options
api-squash project . --max-depth 3 --exclude "tests/*" --exclude "migrations/*"
api-squash file module.py --no-docstrings --no-private
```

**Commands:**
- `file <path>` — Summarize a single Python file
- `project <path>` — Scan and summarize all Python files in a directory

**Flags:**
- `--max-depth N` — Limit directory recursion depth (project command only)
- `--exclude PATTERN` — Glob patterns to skip, repeatable (project command only)
- `--no-docstrings` — Strip all docstrings for ultra-compact output
- `--no-private` — Skip `_private` and `__dunder__` methods (except `__init__`)

Output always goes to stdout for pipe-friendliness.

## Output Format

The compact format strips syntax noise while preserving all semantic information:

```
# example.py

class UserService:
  Manages user CRUD operations.
  def __init__(self, db: Database) -> None
  def get_user(self, user_id: int) -> User | None
    Fetch user by ID from the database.
    Returns None if no user matches.
  def create_user(self, name: str, email: str) -> User
    Create and return a new user.
    Args:
      name: Display name
      email: Must be unique
    Returns: The created User object
    Raises: DuplicateEmailError if email exists
  def delete_user(self, user_id: int) -> bool

def connect_db(url: str, pool_size: int = 5) -> Database
  Establish database connection pool.
  Uses asyncpg under the hood. Pool is
  lazily initialized on first query.
```

**Token-saving strategies applied:**
- No triple-quote delimiters on docstrings
- No colon after function signatures, no function body
- Leading/trailing blank lines stripped from docstrings
- Consecutive blank lines within docstrings collapsed to one
- Redundant whitespace stripped
- No import statements, no decorators, no constants
- Indentation shows structure (2-space indent)

**What is preserved:**
- Full docstring content (Args, Returns, Raises, examples)
- All type hints on parameters and return types
- Class hierarchy via nesting
- File path context via `#` headers

## Testing Strategy

All tests use **pytest**.

### Unit Tests

**`test_extractor.py`**
- Functions with various type hints (simple, Union, Optional, generics)
- Classes with methods, `__init__`, properties
- Async functions and methods
- Docstrings: single-line, multi-line, none
- Edge cases: empty files, files with only imports, syntax errors (graceful skip)
- Nested classes

**`test_renderer.py`**
- Known models → snapshot text comparison
- Docstring stripping: triple-quote removal, whitespace normalization
- Indentation correctness
- `--no-docstrings` flag behavior
- `--no-private` flag behavior
- Multi-file project output with `---` separators

**`test_scanner.py`**
- File discovery in nested directories (using `tmp_path`)
- Exclusion of `__pycache__`, `.venv`, etc.
- Custom `--exclude` patterns
- `--max-depth` limiting
- Deterministic sort order

**`test_cli.py`**
- End-to-end with Click's `CliRunner`
- `file` command: valid file, nonexistent file, non-Python file
- `project` command: valid directory, empty directory, with flags
- Error messages for bad inputs

### Cross-Platform Tests

- **Path separators**: Use `pathlib.Path` throughout; tests verify output uses forward slashes in headers regardless of OS
- **Line endings**: Test files with `\n`, `\r\n`, and mixed line endings produce consistent output
- **Unicode**: Test files and docstrings containing non-ASCII characters (e.g., emoji, CJK)

### Error Handling

- Invalid/unparseable Python files: log a warning to stderr, skip the file, continue scanning
- Non-existent paths: clear error message, exit code 1
- Binary/non-Python files in project scan: silently skip
- Permission denied: warn to stderr, skip, continue

## Dependencies

- **Runtime**: `click` (CLI framework)
- **Dev**: `pytest`, `ruff` (linting/formatting)
- **Stdlib only** for parsing: `ast`, `pathlib`, `textwrap`

## Package Management

- **uv** for dependency management and virtual environment
- `pyproject.toml` with `[project.scripts]` entry point for `api-squash`

## Future Ideas (Out of Scope)

These are not part of the initial implementation but noted for potential GitHub issues:

- JSON output format
- Filtering by visibility (public only)
- Token count estimation in output
- Integration as a library (not just CLI)
- Support for other languages beyond Python
