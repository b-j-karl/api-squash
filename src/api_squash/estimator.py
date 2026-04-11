from __future__ import annotations

from dataclasses import dataclass

from .models import ModuleSummary
from .renderer import render_module


SEPARATOR = "\n---\n\n"


@dataclass
class EstimateResult:
    files: int
    classes: int
    functions: int
    constants: int
    type_aliases: int
    size_bytes: int
    minimal_size_bytes: int


def _sum_rendered_sizes(
    modules: list[ModuleSummary],
    **render_kwargs: object,
) -> int:
    """Sum UTF-8 byte lengths of individually rendered modules plus separators."""
    total = 0
    sep_bytes = len(SEPARATOR.encode("utf-8"))
    for i, module in enumerate(modules):
        rendered = render_module(module, **render_kwargs)
        total += len(rendered.encode("utf-8"))
        if i < len(modules) - 1:
            total += sep_bytes
    return total


def estimate(
    modules: list[ModuleSummary],
    *,
    no_docstrings: bool = False,
    no_private: bool = False,
    no_constants: bool = False,
    public_only: bool = False,
    wrap: int | None = None,
) -> EstimateResult:
    """Compute entity counts and estimated output sizes for a list of modules."""
    files = len(modules)
    classes = sum(len(m.classes) for m in modules)
    functions = sum(len(m.functions) for m in modules)
    constants = sum(len(m.constants) for m in modules)
    type_aliases = sum(len(m.type_aliases) for m in modules)

    if not modules:
        return EstimateResult(
            files=0,
            classes=0,
            functions=0,
            constants=0,
            type_aliases=0,
            size_bytes=0,
            minimal_size_bytes=0,
        )

    current_kwargs = dict(
        no_docstrings=no_docstrings,
        no_private=no_private,
        no_constants=no_constants,
        public_only=public_only,
        wrap=wrap,
    )
    minimal_kwargs = dict(
        no_docstrings=True,
        no_private=True,
        no_constants=True,
        public_only=public_only,
        wrap=wrap,
    )

    if files > 1:
        size_bytes = _sum_rendered_sizes(modules, **current_kwargs)
        minimal_size_bytes = _sum_rendered_sizes(modules, **minimal_kwargs)
    else:
        size_bytes = len(render_module(modules[0], **current_kwargs).encode("utf-8"))
        minimal_size_bytes = len(
            render_module(modules[0], **minimal_kwargs).encode("utf-8")
        )

    return EstimateResult(
        files=files,
        classes=classes,
        functions=functions,
        constants=constants,
        type_aliases=type_aliases,
        size_bytes=size_bytes,
        minimal_size_bytes=minimal_size_bytes,
    )


def format_estimate(result: EstimateResult) -> str:
    """Format an EstimateResult as a human-readable summary string."""
    file_word = "file" if result.files == 1 else "files"
    current_kb = result.size_bytes / 1024
    minimal_kb = result.minimal_size_bytes / 1024

    return (
        f"Extracted {result.files} {file_word}: "
        f"{result.classes} classes, "
        f"{result.functions} functions, "
        f"{result.constants} constants, "
        f"{result.type_aliases} type aliases\n"
        f"Estimated output: {current_kb:.1f} KB (current flags), "
        f"{minimal_kb:.1f} KB (minimal)\n"
    )
