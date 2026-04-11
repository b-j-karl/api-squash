# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-04-11

### Added

- Module-level `UPPER_CASE` constants included in output by default; opt out
  with `--no-constants` (#20)
- Decorator preservation for `@property`, `@classmethod`, `@staticmethod`, and
  `@overload` (#16)
- Smarter `--no-private`: private items referenced by public signatures are
  kept (#16)
- `--wrap` flag to wrap long signatures at a given width, one parameter per
  line (#14)
- Type alias support — PEP 613 (`TypeAlias`) and PEP 695 (`type X = ...`)
  (#21)
- `--public-only` flag to filter output to names listed in `__all__` (#19)
- `--dry-run` flag to estimate output size without producing full output (#23)
- `--version` flag to print the installed package version (#41)
- Benchmark table comparing output across large Python packages (#26)
- Pre-commit hooks for Ruff lint and format
- Agent skills updated with `--dry-run`, `--public-only`, `--wrap`, token
  compression guidance, and `--public-only` vs `--no-private` decision guide
  (#56)

### Fixed

- `SyntaxWarning` noise from `ast.parse()` on files with invalid escape
  sequences
- Backslash-escaped quotes handled correctly in `--wrap` parameter splitting
- `ast.TypeAlias` guarded for Python < 3.12 compatibility

### Changed

- `--no-private` CLI help aligned across README and `--help` output
- Codecov upload step hardened with token and explicit file path

## [0.1.0] - 2026-04-09

### Added

- `api-squash file` command to summarize a single Python file
- `api-squash project` command to summarize all Python files in a directory
- `--no-docstrings` flag to strip docstrings from output
- `--no-private` flag to exclude private classes and methods
- `--max-depth` flag to limit directory recursion depth
- `--exclude` flag to skip files matching glob patterns
- Compact Markdown output format with signatures, docstrings, and class
  hierarchy
- AI agent skills for Copilot CLI and Claude Code
- CI/CD pipeline with GitHub Actions (lint, test, publish to PyPI)
- Codecov integration for test coverage reporting

[Unreleased]: https://github.com/b-j-karl/api-squash/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/b-j-karl/api-squash/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/b-j-karl/api-squash/releases/tag/v0.1.0
