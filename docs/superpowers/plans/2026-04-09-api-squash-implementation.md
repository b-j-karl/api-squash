# api-squash Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that extracts Python API surfaces (signatures, type hints, docstrings) into a compact, token-efficient text format for agentic programming workflows.

**Architecture:** AST → Intermediate Model → Renderer. Python's `ast` module parses source files into dataclass models (`ModuleSummary`, `ClassSummary`, `FunctionSummary`), which are then rendered to a compact text format. A scanner discovers `.py` files for project-level scans. Click provides the CLI.

**Tech Stack:** Python 3.10+, Click (CLI), ast (parsing), pytest (testing), ruff (linting), uv (package management)

**Note:** Python is not directly on PATH in this environment. All Python/pytest commands must use `uv run` (e.g., `uv run pytest`, `uv run api-squash`).

---

## File Structure

```
api-squash/
├── pyproject.toml                  # uv-managed project config with Click dep + CLI entry point
├── src/
│   └── api_squash/
│       ├── __init__.py             # Package marker (empty)
│       ├── models.py               # Dataclasses: FunctionSummary, ClassSummary, ModuleSummary
│       ├── extractor.py            # AST walking → builds ModuleSummary from a .py file
│       ├── renderer.py             # ModuleSummary → compact text output string
│       ├── scanner.py              # Discovers .py files recursively with exclusions
│       └── cli.py                  # Click CLI: `file` and `project` commands
└── tests/
    ├── __init__.py                 # Package marker (empty)
    ├── test_models.py              # Model instantiation tests
    ├── test_extractor.py           # AST extraction tests
    ├── test_renderer.py            # Output formatting tests
    ├── test_scanner.py             # File discovery tests
    ├── test_cli.py                 # End-to-end CLI tests
    └── test_cross_platform.py      # Line endings, unicode, path separators
```

Each module has one clear responsibility. Models are separate from extractor so they can be constructed directly in renderer tests without needing real files.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/api_squash/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "api-squash"
version = "0.1.0"
description = "Extract Python API surfaces in a compact, token-efficient format"
requires-python = ">=3.10"
dependencies = [
    "click>=8.0",
]

[project.scripts]
api-squash = "api_squash.cli:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"

[tool.hatch.build.targets.wheel]
packages = ["src/api_squash"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.4",
]
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p src/api_squash tests
```

Create `src/api_squash/__init__.py` (empty file).

Create `tests/__init__.py` (empty file).

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```

Expected: Creates `.venv/`, installs Click, pytest, ruff. Output includes "Resolved N packages".

- [ ] **Step 4: Verify setup**

```bash
uv run pytest --co -q
```

Expected: "no tests ran" (exit code 5 is OK — means pytest works but found nothing).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/ tests/
git commit -m "chore: scaffold project with uv, Click, pytest, ruff"
```

---

### Task 2: Models

**Files:**
- Create: `src/api_squash/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_models.py`:

```python
from api_squash.models import FunctionSummary, ClassSummary, ModuleSummary


def test_function_summary_defaults():
    func = FunctionSummary(name="greet", signature="(name: str) -> str")
    assert func.name == "greet"
    assert func.signature == "(name: str) -> str"
    assert func.docstring is None
    assert func.is_async is False


def test_function_summary_all_fields():
    func = FunctionSummary(
        name="fetch",
        signature="(url: str) -> bytes",
        docstring="Fetch URL content.",
        is_async=True,
    )
    assert func.name == "fetch"
    assert func.docstring == "Fetch URL content."
    assert func.is_async is True


def test_class_summary_defaults():
    cls = ClassSummary(name="Calculator")
    assert cls.name == "Calculator"
    assert cls.docstring is None
    assert cls.methods == []
    assert cls.bases == []


def test_class_summary_all_fields():
    method = FunctionSummary(name="add", signature="(self, a: int, b: int) -> int")
    cls = ClassSummary(
        name="Calculator",
        docstring="A simple calculator.",
        methods=[method],
        bases=["BaseClass"],
    )
    assert cls.docstring == "A simple calculator."
    assert len(cls.methods) == 1
    assert cls.bases == ["BaseClass"]


def test_module_summary_defaults():
    mod = ModuleSummary(path="example.py")
    assert mod.path == "example.py"
    assert mod.classes == []
    assert mod.functions == []


def test_module_summary_all_fields():
    func = FunctionSummary(name="main", signature="()")
    cls = ClassSummary(name="App")
    mod = ModuleSummary(path="app.py", classes=[cls], functions=[func])
    assert len(mod.classes) == 1
    assert len(mod.functions) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'api_squash.models'`

- [ ] **Step 3: Write minimal implementation**

Create `src/api_squash/models.py`:

```python
from dataclasses import dataclass, field


@dataclass
class FunctionSummary:
    name: str
    signature: str
    docstring: str | None = None
    is_async: bool = False


@dataclass
class ClassSummary:
    name: str
    docstring: str | None = None
    methods: list[FunctionSummary] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)


@dataclass
class ModuleSummary:
    path: str
    classes: list[ClassSummary] = field(default_factory=list)
    functions: list[FunctionSummary] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_models.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/api_squash/models.py tests/test_models.py
git commit -m "feat: add dataclass models for API surface representation"
```

---

### Task 3: Extractor

**Files:**
- Create: `src/api_squash/extractor.py`
- Create: `tests/test_extractor.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_extractor.py`:

```python
from api_squash.extractor import extract_file


def test_simple_function(tmp_path):
    source = 'def greet(name: str) -> str:\n    """Say hello."""\n    return f"Hello, {name}"\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.functions) == 1
    func = result.functions[0]
    assert func.name == "greet"
    assert func.signature == "(name: str) -> str"
    assert func.docstring == "Say hello."
    assert func.is_async is False


def test_function_no_annotations(tmp_path):
    source = "def add(a, b):\n    return a + b\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(a, b)"
    assert func.docstring is None


def test_function_with_defaults(tmp_path):
    source = "def connect(host: str, port: int = 8080, ssl: bool = True) -> None:\n    pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(host: str, port: int = 8080, ssl: bool = True) -> None"


def test_async_function(tmp_path):
    source = 'async def fetch(url: str) -> bytes:\n    """Fetch URL content."""\n    pass\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.name == "fetch"
    assert func.is_async is True
    assert func.signature == "(url: str) -> bytes"


def test_class_with_methods(tmp_path):
    source = (
        'class Calculator:\n'
        '    """A simple calculator."""\n'
        '\n'
        '    def add(self, a: int, b: int) -> int:\n'
        '        """Add two numbers."""\n'
        '        return a + b\n'
        '\n'
        '    def subtract(self, a: int, b: int) -> int:\n'
        '        return a - b\n'
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.classes) == 1
    cls = result.classes[0]
    assert cls.name == "Calculator"
    assert cls.docstring == "A simple calculator."
    assert len(cls.methods) == 2
    assert cls.methods[0].name == "add"
    assert cls.methods[0].docstring == "Add two numbers."
    assert cls.methods[1].name == "subtract"
    assert cls.methods[1].docstring is None


def test_class_with_bases(tmp_path):
    source = "class Dog(Animal, Serializable):\n    def bark(self) -> str:\n        return 'woof'\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    cls = result.classes[0]
    assert cls.bases == ["Animal", "Serializable"]


def test_args_kwargs(tmp_path):
    source = "def flexible(*args: int, **kwargs: str) -> None:\n    pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(*args: int, **kwargs: str) -> None"


def test_keyword_only_args(tmp_path):
    source = "def search(query: str, *, limit: int = 10, offset: int = 0) -> list:\n    pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(query: str, *, limit: int = 10, offset: int = 0) -> list"


def test_positional_only_args(tmp_path):
    source = "def div(a: int, b: int, /) -> float:\n    return a / b\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(a: int, b: int, /) -> float"


def test_empty_file(tmp_path):
    p = tmp_path / "empty.py"
    p.write_text("", encoding="utf-8")
    result = extract_file(p)

    assert result.functions == []
    assert result.classes == []


def test_multiline_docstring(tmp_path):
    source = (
        'def process(data: list[int]) -> list[int]:\n'
        '    """Process the data.\n'
        '\n'
        '    Args:\n'
        '        data: List of integers to process.\n'
        '\n'
        '    Returns:\n'
        '        Processed list of integers.\n'
        '    """\n'
        '    return data\n'
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert "Args:" in func.docstring
    assert "data: List of integers to process." in func.docstring
    assert "Returns:" in func.docstring


def test_complex_type_hints(tmp_path):
    source = (
        "from typing import Callable\n"
        "def transform(items: list[dict[str, int]], callback: Callable[[int], bool])"
        " -> dict[str, list[int]]:\n"
        "    pass\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert "list[dict[str, int]]" in func.signature
    assert "Callable[[int], bool]" in func.signature
    assert "-> dict[str, list[int]]" in func.signature


def test_path_uses_forward_slashes(tmp_path):
    subdir = tmp_path / "pkg"
    subdir.mkdir()
    p = subdir / "mod.py"
    p.write_text("def f(): pass\n", encoding="utf-8")
    result = extract_file(p)

    assert "\\" not in result.path
    assert "/" in result.path


def test_file_with_only_imports(tmp_path):
    source = "import os\nfrom pathlib import Path\n"
    p = tmp_path / "imports_only.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.functions == []
    assert result.classes == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_extractor.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'api_squash.extractor'`

- [ ] **Step 3: Implement extractor.py**

Create `src/api_squash/extractor.py`:

```python
from __future__ import annotations

import ast
from pathlib import Path

from .models import ClassSummary, FunctionSummary, ModuleSummary


def extract_file(path: Path) -> ModuleSummary:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    classes: list[ClassSummary] = []
    functions: list[FunctionSummary] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(_extract_class(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function(node))

    return ModuleSummary(
        path=path.as_posix(),
        classes=classes,
        functions=functions,
    )


def _extract_class(node: ast.ClassDef) -> ClassSummary:
    docstring = ast.get_docstring(node)
    bases = [ast.unparse(base) for base in node.bases]
    methods: list[FunctionSummary] = []

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_extract_function(child))

    return ClassSummary(
        name=node.name,
        docstring=docstring,
        methods=methods,
        bases=bases,
    )


def _extract_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> FunctionSummary:
    docstring = ast.get_docstring(node)
    signature = _build_signature(node)
    is_async = isinstance(node, ast.AsyncFunctionDef)

    return FunctionSummary(
        name=node.name,
        signature=signature,
        docstring=docstring,
        is_async=is_async,
    )


def _build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = node.args
    params: list[str] = []

    # Combine positional-only and regular args for default alignment
    all_positional = list(args.posonlyargs) + list(args.args)
    num_positional = len(all_positional)
    num_defaults = len(args.defaults)
    default_offset = num_positional - num_defaults

    for i, arg in enumerate(all_positional):
        part = arg.arg
        if arg.annotation:
            part += f": {ast.unparse(arg.annotation)}"
        default_idx = i - default_offset
        if default_idx >= 0:
            part += f" = {ast.unparse(args.defaults[default_idx])}"
        params.append(part)
        # Insert "/" separator after positional-only args
        if args.posonlyargs and i == len(args.posonlyargs) - 1:
            params.append("/")

    if args.vararg:
        part = f"*{args.vararg.arg}"
        if args.vararg.annotation:
            part += f": {ast.unparse(args.vararg.annotation)}"
        params.append(part)
    elif args.kwonlyargs:
        params.append("*")

    for i, arg in enumerate(args.kwonlyargs):
        part = arg.arg
        if arg.annotation:
            part += f": {ast.unparse(arg.annotation)}"
        if args.kw_defaults[i] is not None:
            part += f" = {ast.unparse(args.kw_defaults[i])}"
        params.append(part)

    if args.kwarg:
        part = f"**{args.kwarg.arg}"
        if args.kwarg.annotation:
            part += f": {ast.unparse(args.kwarg.annotation)}"
        params.append(part)

    sig = f"({', '.join(params)})"
    if node.returns:
        sig += f" -> {ast.unparse(node.returns)}"

    return sig
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_extractor.py -v
```

Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add src/api_squash/extractor.py tests/test_extractor.py
git commit -m "feat: add AST extractor for Python API surfaces"
```

---

### Task 4: Renderer

**Files:**
- Create: `src/api_squash/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_renderer.py`:

```python
from api_squash.models import ClassSummary, FunctionSummary, ModuleSummary
from api_squash.renderer import render_module, render_project


def test_render_simple_function():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="greet",
                signature="(name: str) -> str",
                docstring="Say hello.",
            ),
        ],
    )
    output = render_module(module)
    expected = "# example.py\n\ndef greet(name: str) -> str\n  Say hello.\n"
    assert output == expected


def test_render_function_no_docstring():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(name="add", signature="(a: int, b: int) -> int"),
        ],
    )
    output = render_module(module)
    expected = "# example.py\n\ndef add(a: int, b: int) -> int\n"
    assert output == expected


def test_render_class_with_methods():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="Calculator",
                docstring="A simple calculator.",
                methods=[
                    FunctionSummary(
                        name="add",
                        signature="(self, a: int, b: int) -> int",
                        docstring="Add two numbers.",
                    ),
                    FunctionSummary(
                        name="sub",
                        signature="(self, a: int, b: int) -> int",
                    ),
                ],
            ),
        ],
    )
    output = render_module(module)
    expected = (
        "# example.py\n"
        "\n"
        "class Calculator:\n"
        "  A simple calculator.\n"
        "  def add(self, a: int, b: int) -> int\n"
        "    Add two numbers.\n"
        "  def sub(self, a: int, b: int) -> int\n"
    )
    assert output == expected


def test_render_class_with_bases():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="Dog",
                bases=["Animal", "Serializable"],
                methods=[
                    FunctionSummary(name="bark", signature="(self) -> str"),
                ],
            ),
        ],
    )
    output = render_module(module)
    assert "class Dog(Animal, Serializable):" in output


def test_render_async_function():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="fetch",
                signature="(url: str) -> bytes",
                is_async=True,
            ),
        ],
    )
    output = render_module(module)
    assert "async def fetch(url: str) -> bytes" in output


def test_render_no_docstrings_flag():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="greet",
                signature="(name: str) -> str",
                docstring="Say hello.",
            ),
        ],
    )
    output = render_module(module, no_docstrings=True)
    assert "Say hello." not in output
    assert "def greet(name: str) -> str" in output


def test_render_no_private_flag():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="MyClass",
                methods=[
                    FunctionSummary(name="__init__", signature="(self)"),
                    FunctionSummary(name="_helper", signature="(self)"),
                    FunctionSummary(name="public", signature="(self)"),
                ],
            ),
        ],
        functions=[
            FunctionSummary(name="_internal", signature="()"),
            FunctionSummary(name="public_func", signature="()"),
        ],
    )
    output = render_module(module, no_private=True)
    assert "__init__" in output
    assert "_helper" not in output
    assert "public" in output
    assert "_internal" not in output
    assert "public_func" in output


def test_render_multiline_docstring():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="process",
                signature="(data: list[int]) -> list[int]",
                docstring=(
                    "Process the data.\n"
                    "\n"
                    "Args:\n"
                    "    data: List of integers.\n"
                    "\n"
                    "Returns:\n"
                    "    Processed list."
                ),
            ),
        ],
    )
    output = render_module(module)
    assert "  Process the data." in output
    assert "  Args:" in output
    assert "      data: List of integers." in output
    assert "  Returns:" in output


def test_render_project_multiple_files():
    modules = [
        ModuleSummary(
            path="a.py",
            functions=[FunctionSummary(name="func_a", signature="()")],
        ),
        ModuleSummary(
            path="b.py",
            functions=[FunctionSummary(name="func_b", signature="()")],
        ),
    ]
    output = render_project(modules)
    assert "# a.py" in output
    assert "# b.py" in output
    assert "---" in output


def test_render_blank_line_between_top_level_items():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="A", methods=[]),
        ],
        functions=[
            FunctionSummary(name="func", signature="()"),
        ],
    )
    output = render_module(module)
    assert "class A:\n\ndef func()" in output


def test_render_empty_module():
    module = ModuleSummary(path="empty.py")
    output = render_module(module)
    assert output == "# empty.py\n"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_renderer.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'api_squash.renderer'`

- [ ] **Step 3: Implement renderer.py**

Create `src/api_squash/renderer.py`:

```python
from __future__ import annotations

from .models import ClassSummary, FunctionSummary, ModuleSummary


def render_module(
    module: ModuleSummary,
    *,
    no_docstrings: bool = False,
    no_private: bool = False,
) -> str:
    lines = [f"# {module.path}"]

    items: list[str] = []
    for cls in module.classes:
        items.append(
            _render_class(cls, no_docstrings=no_docstrings, no_private=no_private)
        )
    for func in module.functions:
        if no_private and _is_private(func.name):
            continue
        items.append(_render_function(func, indent=0, no_docstrings=no_docstrings))

    if items:
        lines.append("")
        lines.append("\n\n".join(items))

    return "\n".join(lines) + "\n"


def render_project(
    modules: list[ModuleSummary],
    *,
    no_docstrings: bool = False,
    no_private: bool = False,
) -> str:
    rendered = [
        render_module(module, no_docstrings=no_docstrings, no_private=no_private)
        for module in modules
    ]
    return "\n---\n\n".join(rendered)


def _render_class(
    cls: ClassSummary,
    *,
    no_docstrings: bool = False,
    no_private: bool = False,
) -> str:
    parts: list[str] = []

    if cls.bases:
        parts.append(f"class {cls.name}({', '.join(cls.bases)}):")
    else:
        parts.append(f"class {cls.name}:")

    if cls.docstring and not no_docstrings:
        parts.append(_format_docstring(cls.docstring, indent=2))

    for method in cls.methods:
        if no_private and _is_private(method.name) and method.name != "__init__":
            continue
        parts.append(_render_function(method, indent=2, no_docstrings=no_docstrings))

    return "\n".join(parts)


def _render_function(
    func: FunctionSummary,
    *,
    indent: int = 0,
    no_docstrings: bool = False,
) -> str:
    prefix = " " * indent
    parts: list[str] = []

    keyword = "async def" if func.is_async else "def"
    parts.append(f"{prefix}{keyword} {func.name}{func.signature}")

    if func.docstring and not no_docstrings:
        parts.append(_format_docstring(func.docstring, indent=indent + 2))

    return "\n".join(parts)


def _format_docstring(docstring: str, *, indent: int) -> str:
    lines = docstring.splitlines()
    prefix = " " * indent
    result: list[str] = []
    prev_blank = False
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            if not prev_blank:
                result.append("")
            prev_blank = True
        else:
            result.append(f"{prefix}{stripped}")
            prev_blank = False
    return "\n".join(result)


def _is_private(name: str) -> bool:
    return name.startswith("_")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_renderer.py -v
```

Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add src/api_squash/renderer.py tests/test_renderer.py
git commit -m "feat: add compact text renderer for API summaries"
```

---

### Task 5: Scanner

**Files:**
- Create: `src/api_squash/scanner.py`
- Create: `tests/test_scanner.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_scanner.py`:

```python
from api_squash.scanner import scan_directory


def test_finds_python_files(tmp_path):
    (tmp_path / "a.py").write_text("# a", encoding="utf-8")
    (tmp_path / "b.py").write_text("# b", encoding="utf-8")
    (tmp_path / "readme.md").write_text("# readme", encoding="utf-8")

    result = scan_directory(tmp_path)
    names = [p.name for p in result]
    assert names == ["a.py", "b.py"]


def test_finds_nested_files(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "module.py").write_text("# mod", encoding="utf-8")

    result = scan_directory(tmp_path)
    assert len(result) == 2


def test_skips_pycache(tmp_path):
    (tmp_path / "mod.py").write_text("# mod", encoding="utf-8")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "cached.py").write_text("# cached", encoding="utf-8")

    result = scan_directory(tmp_path)
    assert len(result) == 1
    assert result[0].name == "mod.py"


def test_skips_venv(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "activate.py").write_text("# activate", encoding="utf-8")

    result = scan_directory(tmp_path)
    assert len(result) == 1
    assert result[0].name == "app.py"


def test_skips_git_dir(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    git = tmp_path / ".git"
    git.mkdir()
    (git / "hook.py").write_text("# hook", encoding="utf-8")

    result = scan_directory(tmp_path)
    assert len(result) == 1


def test_exclude_pattern(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text("# test", encoding="utf-8")

    result = scan_directory(tmp_path, exclude=["tests/*"])
    assert len(result) == 1
    assert result[0].name == "app.py"


def test_exclude_dir_by_name(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001.py").write_text("# migration", encoding="utf-8")

    result = scan_directory(tmp_path, exclude=["migrations"])
    assert len(result) == 1
    assert result[0].name == "app.py"


def test_max_depth_zero(tmp_path):
    (tmp_path / "top.py").write_text("# top", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.py").write_text("# deep", encoding="utf-8")

    result = scan_directory(tmp_path, max_depth=0)
    names = [p.name for p in result]
    assert names == ["top.py"]


def test_max_depth_one(tmp_path):
    (tmp_path / "top.py").write_text("# top", encoding="utf-8")
    level1 = tmp_path / "level1"
    level1.mkdir()
    (level1 / "mid.py").write_text("# mid", encoding="utf-8")
    level2 = level1 / "level2"
    level2.mkdir()
    (level2 / "deep.py").write_text("# deep", encoding="utf-8")

    result = scan_directory(tmp_path, max_depth=1)
    names = [p.name for p in result]
    assert "top.py" in names
    assert "mid.py" in names
    assert "deep.py" not in names


def test_sorted_output(tmp_path):
    (tmp_path / "z.py").write_text("", encoding="utf-8")
    (tmp_path / "a.py").write_text("", encoding="utf-8")
    (tmp_path / "m.py").write_text("", encoding="utf-8")

    result = scan_directory(tmp_path)
    names = [p.name for p in result]
    assert names == ["a.py", "m.py", "z.py"]


def test_empty_directory(tmp_path):
    result = scan_directory(tmp_path)
    assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_scanner.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'api_squash.scanner'`

- [ ] **Step 3: Implement scanner.py**

Create `src/api_squash/scanner.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_scanner.py -v
```

Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add src/api_squash/scanner.py tests/test_scanner.py
git commit -m "feat: add project scanner for Python file discovery"
```

---

### Task 6: CLI

**Files:**
- Create: `src/api_squash/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cli.py`:

```python
from click.testing import CliRunner

from api_squash.cli import cli


def test_file_command(tmp_path):
    source = 'def greet(name: str) -> str:\n    """Say hello."""\n    return f"Hello, {name}"\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p)])
    assert result.exit_code == 0
    assert "def greet(name: str) -> str" in result.output
    assert "Say hello." in result.output


def test_file_command_nonexistent():
    runner = CliRunner()
    result = runner.invoke(cli, ["file", "nonexistent.py"])
    assert result.exit_code != 0


def test_file_command_not_python(tmp_path):
    p = tmp_path / "readme.md"
    p.write_text("# readme", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p)])
    assert result.exit_code != 0
    assert "not a Python file" in result.output


def test_file_command_no_docstrings(tmp_path):
    source = 'def greet(name: str) -> str:\n    """Say hello."""\n    return "hi"\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--no-docstrings"])
    assert result.exit_code == 0
    assert "Say hello." not in result.output
    assert "def greet" in result.output


def test_file_command_no_private(tmp_path):
    source = "def public(): pass\ndef _private(): pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--no-private"])
    assert result.exit_code == 0
    assert "public" in result.output
    assert "_private" not in result.output


def test_file_command_syntax_error(tmp_path):
    p = tmp_path / "bad.py"
    p.write_text("def broken(\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p)])
    assert result.exit_code != 0
    assert "Failed to parse" in result.output


def test_project_command(tmp_path):
    (tmp_path / "a.py").write_text(
        'def func_a() -> int:\n    """A function."""\n    return 1\n',
        encoding="utf-8",
    )
    (tmp_path / "b.py").write_text(
        'def func_b() -> str:\n    return "b"\n',
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path)])
    assert result.exit_code == 0
    assert "func_a" in result.output
    assert "func_b" in result.output
    assert "---" in result.output


def test_project_command_with_exclude(tmp_path):
    (tmp_path / "app.py").write_text("def main(): pass\n", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text(
        "def test_main(): pass\n", encoding="utf-8"
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path), "--exclude", "tests/*"])
    assert result.exit_code == 0
    assert "main" in result.output
    assert "test_main" not in result.output


def test_project_command_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path)])
    assert result.exit_code == 0


def test_project_command_skips_bad_files(tmp_path):
    (tmp_path / "good.py").write_text("def ok(): pass\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text("def broken(\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path)])
    assert result.exit_code == 0
    assert "ok" in result.output
    assert "Warning" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'api_squash.cli'`

- [ ] **Step 3: Implement cli.py**

Create `src/api_squash/cli.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

import click

from .extractor import extract_file
from .renderer import render_module, render_project
from .scanner import scan_directory


@click.group()
def cli() -> None:
    """Extract Python API surfaces in a compact, token-efficient format."""


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--no-docstrings", is_flag=True, help="Strip all docstrings")
@click.option(
    "--no-private", is_flag=True, help="Skip private methods (except __init__)"
)
def file(path: str, no_docstrings: bool, no_private: bool) -> None:
    """Summarize a single Python file."""
    file_path = Path(path)
    if file_path.suffix != ".py":
        click.echo(f"Error: {path} is not a Python file", err=True)
        sys.exit(1)

    try:
        module = extract_file(file_path)
    except SyntaxError as e:
        click.echo(f"Error: Failed to parse {path}: {e}", err=True)
        sys.exit(1)

    output = render_module(
        module, no_docstrings=no_docstrings, no_private=no_private
    )
    click.echo(output, nl=False)


@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--max-depth", type=int, default=None, help="Limit directory recursion depth"
)
@click.option("--exclude", multiple=True, help="Glob patterns to exclude")
@click.option("--no-docstrings", is_flag=True, help="Strip all docstrings")
@click.option(
    "--no-private", is_flag=True, help="Skip private methods (except __init__)"
)
def project(
    path: str,
    max_depth: int | None,
    exclude: tuple[str, ...],
    no_docstrings: bool,
    no_private: bool,
) -> None:
    """Summarize all Python files in a directory."""
    root = Path(path)
    files = scan_directory(root, exclude=list(exclude), max_depth=max_depth)

    if not files:
        click.echo(f"No Python files found in {path}", err=True)
        return

    modules = []
    for file_path in files:
        try:
            modules.append(extract_file(file_path))
        except SyntaxError as e:
            click.echo(f"Warning: Skipping {file_path}: {e}", err=True)
        except Exception as e:
            click.echo(f"Warning: Skipping {file_path}: {e}", err=True)

    output = render_project(
        modules, no_docstrings=no_docstrings, no_private=no_private
    )
    click.echo(output, nl=False)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: 11 passed

- [ ] **Step 5: Verify CLI entry point works**

```bash
uv run api-squash --help
uv run api-squash file --help
uv run api-squash project --help
```

Expected: Help text displays for all commands with correct options listed.

- [ ] **Step 6: Commit**

```bash
git add src/api_squash/cli.py tests/test_cli.py
git commit -m "feat: add Click CLI with file and project commands"
```

---

### Task 7: Cross-Platform Tests and Final Verification

**Files:**
- Create: `tests/test_cross_platform.py`

- [ ] **Step 1: Write cross-platform tests**

Create `tests/test_cross_platform.py`:

```python
from api_squash.extractor import extract_file
from api_squash.renderer import render_module


def test_crlf_line_endings(tmp_path):
    source = b'def greet(name: str) -> str:\r\n    """Say hello."""\r\n    return "hi"\r\n'
    p = tmp_path / "crlf.py"
    p.write_bytes(source)
    result = extract_file(p)

    assert result.functions[0].name == "greet"
    assert result.functions[0].docstring == "Say hello."


def test_mixed_line_endings(tmp_path):
    source = b"def a():\n    pass\r\ndef b():\r\n    pass\n"
    p = tmp_path / "mixed.py"
    p.write_bytes(source)
    result = extract_file(p)

    assert len(result.functions) == 2
    assert result.functions[0].name == "a"
    assert result.functions[1].name == "b"


def test_unicode_docstring(tmp_path):
    source = 'def greet() -> str:\n    """H\u00e9llo w\u00f6rld \U0001f30d"""\n    return "hi"\n'
    p = tmp_path / "unicode.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert "H\u00e9llo w\u00f6rld \U0001f30d" in result.functions[0].docstring


def test_unicode_function_name(tmp_path):
    source = 'def caf\u00e9() -> str:\n    return "coffee"\n'
    p = tmp_path / "unicode_name.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.functions[0].name == "caf\u00e9"


def test_path_always_forward_slashes(tmp_path):
    subdir = tmp_path / "pkg" / "sub"
    subdir.mkdir(parents=True)
    p = subdir / "mod.py"
    p.write_text("def f(): pass\n", encoding="utf-8")
    result = extract_file(p)

    assert "\\" not in result.path
    assert "/" in result.path


def test_renderer_output_uses_lf(tmp_path):
    source = b'def greet() -> str:\r\n    """Hello."""\r\n    return "hi"\r\n'
    p = tmp_path / "crlf.py"
    p.write_bytes(source)
    module = extract_file(p)
    output = render_module(module)

    assert "\r" not in output
    assert "def greet() -> str" in output
    assert "Hello." in output
```

- [ ] **Step 2: Run all tests**

```bash
uv run pytest -v
```

Expected: All tests pass (models: 6, extractor: 14, renderer: 12, scanner: 12, cli: 11, cross-platform: 6 = 61 total)

- [ ] **Step 3: Run ruff linter and formatter**

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Expected: No errors. If formatting issues exist, fix with `uv run ruff format src/ tests/`.

- [ ] **Step 4: Commit**

```bash
git add tests/test_cross_platform.py
git commit -m "test: add cross-platform tests for line endings, unicode, paths"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Models: `FunctionSummary`, `ClassSummary`, `ModuleSummary` — Task 2
- ✅ Extractor: AST walking, signatures, type hints, docstrings — Task 3
- ✅ Renderer: compact text format, `--no-docstrings`, `--no-private` — Task 4
- ✅ Scanner: recursive walk, skip dirs, exclude patterns, max-depth — Task 5
- ✅ CLI: `file` and `project` commands with all flags — Task 6
- ✅ Cross-platform: CRLF, unicode, forward-slash paths — Task 7
- ✅ Error handling: syntax errors, missing files, bad files skipped — Tasks 3, 6
- ✅ Output format: no colons, no bodies, stripped docstrings, `---` separators — Task 4

**Placeholder scan:** No TBD, TODO, "fill in later", or "similar to above" found.

**Type consistency:**
- `FunctionSummary.signature` is `str` throughout — extractor produces, renderer consumes
- `ModuleSummary.path` is `str` throughout — extractor sets via `Path.as_posix()`
- `render_module`/`render_project` both accept `no_docstrings`/`no_private` kwargs — consistent
- `extract_file` takes `Path`, returns `ModuleSummary` — consistent across extractor tests and CLI
- `scan_directory` takes `Path`, returns `list[Path]` — consistent across scanner tests and CLI
- `_is_private` checks `name.startswith("_")` with `__init__` exception in `_render_class` — consistent
