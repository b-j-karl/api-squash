from __future__ import annotations

from dataclasses import dataclass

from .models import ModuleSummary
from .renderer import render_module, render_project


@dataclass
class EstimateResult:
    files: int
    classes: int
    functions: int
    constants: int
    type_aliases: int
    size_bytes: int
    minimal_size_bytes: int


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

    render_kwargs = dict(
        no_docstrings=no_docstrings,
        no_private=no_private,
        no_constants=no_constants,
        public_only=public_only,
        wrap=wrap,
    )

    if files == 1:
        current_output = render_module(modules[0], **render_kwargs)
        minimal_output = render_module(
            modules[0],
            no_docstrings=True,
            no_private=True,
            no_constants=True,
            public_only=public_only,
            wrap=wrap,
        )
    else:
        current_output = render_project(modules, **render_kwargs)
        minimal_output = render_project(
            modules,
            no_docstrings=True,
            no_private=True,
            no_constants=True,
            public_only=public_only,
            wrap=wrap,
        )

    return EstimateResult(
        files=files,
        classes=classes,
        functions=functions,
        constants=constants,
        type_aliases=type_aliases,
        size_bytes=len(current_output.encode("utf-8")),
        minimal_size_bytes=len(minimal_output.encode("utf-8")),
    )


def format_estimate(result: EstimateResult) -> str:
    """Format an EstimateResult as a human-readable summary string."""
    file_word = "file" if result.files == 1 else "files"
    current_kb = result.size_bytes / 1024
    minimal_kb = result.minimal_size_bytes / 1024

    return (
        f"Scanned {result.files} {file_word}: "
        f"{result.classes} classes, "
        f"{result.functions} functions, "
        f"{result.constants} constants, "
        f"{result.type_aliases} type aliases\n"
        f"Estimated output: ~{current_kb:.1f} KB (current flags), "
        f"~{minimal_kb:.1f} KB (minimal)\n"
    )
