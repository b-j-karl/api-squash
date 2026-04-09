from __future__ import annotations

import re

from .models import ClassSummary, ConstantSummary, FunctionSummary, ModuleSummary


def render_module(
    module: ModuleSummary,
    *,
    no_docstrings: bool = False,
    no_private: bool = False,
    no_constants: bool = False,
) -> str:
    lines = [f"# {module.path}"]

    keep_names: set[str] = set()
    if no_private:
        keep_names = _collect_referenced_private_names(module)

    items: list[str] = []
    if not no_constants:
        for const in module.constants:
            if no_private and _is_private(const.name):
                continue
            items.append(_render_constant(const))
    for cls in module.classes:
        if no_private and _is_private(cls.name) and cls.name not in keep_names:
            continue
        items.append(
            _render_class(cls, no_docstrings=no_docstrings, no_private=no_private)
        )
    for func in module.functions:
        if no_private and _is_private(func.name) and func.name not in keep_names:
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
    no_constants: bool = False,
) -> str:
    rendered = [
        render_module(
            module,
            no_docstrings=no_docstrings,
            no_private=no_private,
            no_constants=no_constants,
        )
        for module in modules
    ]
    return "\n---\n\n".join(rendered)


def _render_constant(const: ConstantSummary) -> str:
    parts = [const.name]
    if const.type_annotation:
        parts.append(f": {const.type_annotation}")
    if const.value is not None:
        parts.append(f" = {const.value}")
    return "".join(parts)


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

    for dec in func.decorators:
        parts.append(f"{prefix}@{dec}")

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


def _collect_referenced_private_names(module: ModuleSummary) -> set[str]:
    """Find private names referenced in public signatures or class bases."""
    private_names: set[str] = set()
    for cls in module.classes:
        if _is_private(cls.name):
            private_names.add(cls.name)
    for func in module.functions:
        if _is_private(func.name):
            private_names.add(func.name)

    if not private_names:
        return set()

    pattern = re.compile(
        r"\b(" + "|".join(re.escape(n) for n in private_names) + r")\b"
    )

    keep: set[str] = set()

    for cls in module.classes:
        is_public_cls = not _is_private(cls.name)
        if is_public_cls:
            for base in cls.bases:
                keep.update(pattern.findall(base))
        for method in cls.methods:
            # Scan public methods and __init__ (which is always kept)
            is_visible = is_public_cls and (
                not _is_private(method.name) or method.name == "__init__"
            )
            if is_visible:
                keep.update(pattern.findall(method.signature))

    for func in module.functions:
        if not _is_private(func.name):
            keep.update(pattern.findall(func.signature))

    return keep & private_names
