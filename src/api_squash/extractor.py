from __future__ import annotations

import ast
from pathlib import Path

from .models import ClassSummary, FunctionSummary, ModuleSummary

PRESERVED_DECORATORS = {"property", "classmethod", "staticmethod", "overload"}


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
    decorators = _extract_decorators(node)

    return FunctionSummary(
        name=node.name,
        signature=signature,
        docstring=docstring,
        is_async=is_async,
        decorators=decorators,
    )


def _extract_decorators(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    result: list[str] = []
    for dec in node.decorator_list:
        name = _decorator_name(dec)
        if name in PRESERVED_DECORATORS:
            result.append(name)
    return result


def _decorator_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return None


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
