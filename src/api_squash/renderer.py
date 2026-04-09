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
