from __future__ import annotations

import sys
from pathlib import Path

import click

from .estimator import estimate, format_estimate
from .extractor import extract_file
from .renderer import render_module, render_project
from .scanner import scan_directory


@click.group()
@click.version_option(package_name="api-squash", prog_name="api-squash")
def cli() -> None:
    """Extract Python API surfaces in a compact, token-efficient format."""


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--no-docstrings", is_flag=True, help="Strip all docstrings")
@click.option(
    "--no-private",
    is_flag=True,
    help="Skip private classes/methods (except __init__); keeps items referenced by public signatures",
)
@click.option(
    "--no-constants",
    is_flag=True,
    help="Exclude module-level UPPER_CASE constants from output",
)
@click.option(
    "--wrap",
    type=click.IntRange(min=1),
    default=None,
    help="Wrap long signatures at this width (one param per line)",
)
@click.option(
    "--public-only",
    is_flag=True,
    help="Only include names listed in __all__ (modules without __all__ are unaffected)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show estimated output size without producing the full output",
)
def file(
    path: str,
    no_docstrings: bool,
    no_private: bool,
    no_constants: bool,
    wrap: int | None,
    public_only: bool,
    dry_run: bool,
) -> None:
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

    module.path = Path(path).as_posix()

    if dry_run:
        result = estimate(
            [module],
            no_docstrings=no_docstrings,
            no_private=no_private,
            no_constants=no_constants,
            public_only=public_only,
            wrap=wrap,
        )
        click.echo(format_estimate(result), nl=False)
        return

    output = render_module(
        module,
        no_docstrings=no_docstrings,
        no_private=no_private,
        no_constants=no_constants,
        public_only=public_only,
        wrap=wrap,
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
    "--no-private",
    is_flag=True,
    help="Skip private classes/methods (except __init__); keeps items referenced by public signatures",
)
@click.option(
    "--no-constants",
    is_flag=True,
    help="Exclude module-level UPPER_CASE constants from output",
)
@click.option(
    "--wrap",
    type=click.IntRange(min=1),
    default=None,
    help="Wrap long signatures at this width (one param per line)",
)
@click.option(
    "--public-only",
    is_flag=True,
    help="Only include names listed in __all__ (modules without __all__ are unaffected)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show estimated output size without producing the full output",
)
def project(
    path: str,
    max_depth: int | None,
    exclude: tuple[str, ...],
    no_docstrings: bool,
    no_private: bool,
    no_constants: bool,
    wrap: int | None,
    public_only: bool,
    dry_run: bool,
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
            module = extract_file(file_path)
            module.path = file_path.relative_to(root).as_posix()
            modules.append(module)
        except SyntaxError as e:
            click.echo(f"Warning: Skipping {file_path}: {e}", err=True)
        except Exception as e:
            click.echo(f"Warning: Skipping {file_path}: {e}", err=True)

    if dry_run:
        result = estimate(
            modules,
            no_docstrings=no_docstrings,
            no_private=no_private,
            no_constants=no_constants,
            public_only=public_only,
            wrap=wrap,
        )
        click.echo(format_estimate(result), nl=False)
        return

    output = render_project(
        modules,
        no_docstrings=no_docstrings,
        no_private=no_private,
        no_constants=no_constants,
        public_only=public_only,
        wrap=wrap,
    )
    click.echo(output, nl=False)
