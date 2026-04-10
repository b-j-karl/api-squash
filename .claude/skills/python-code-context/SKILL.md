---
name: python-code-context
description: >-
  Load Python API surfaces into context using api-squash before working on
  code. Provides a structured workflow for gathering codebase structure —
  class hierarchies, function signatures, and module layout — so you can
  reason about a Python project without reading every source file. Covers
  scope selection (file vs project), flag selection (docstrings, private
  methods, depth), and when to drill deeper.
license: MIT License
metadata:
  skill-author: b-j-karl
---

# Python Code Context

Use `api-squash` to load Python API surfaces into your context so you can
reason about codebase structure without reading every source file.

> **CLI reference:** For command syntax, flags, and output format details,
> see the **api-squash-cli** skill.

## When to use

- Loading structural context before generating code in a Python project
- Understanding what classes, functions, and signatures exist before writing
  tests or making changes
- Orienting yourself in an unfamiliar Python codebase
- Answering "what does this project expose?" or "how is this structured?"
- Preparing context before a code review or refactor

## When not to use

- Non-Python projects
- Tasks where you already have sufficient context
- When the user explicitly asks to read full source files

---

## Workflow

### Step 1 — Decide scope

Before running anything, decide what you need:

| You need to… | Run |
|---|---|
| Understand one module | `api-squash file <path>` |
| Survey a whole project or package | `api-squash project <path>` |
| Get a high-level overview only | `api-squash project --max-depth 1 --no-docstrings <path>` |
| Minimise tokens (large codebase) | `api-squash project --no-docstrings --no-private <path>` |
| Focus on public API only | `api-squash project --no-private <path>` |

### Step 2 — Run api-squash and read the output

Run the appropriate command and read the output directly. The output is
Markdown that lists every class and function signature in the target.

If `api-squash` is not on PATH, use `uvx api-squash` instead.

```bash
# Example: survey a project's public API
api-squash project --no-private src/
```

Do **not** save to a file unless the user asks — read the stdout directly.

### Step 3 — Use the context

Now that you have the API surface loaded, proceed with the user's actual task
(code generation, test writing, refactoring, review, etc.) using the
structural knowledge you've gained.

---

## Decision guide

### When to use `file` vs `project`

- **`file`** — you already know which module matters (e.g. the user pointed at
  a specific file, or you're writing tests for one module)
- **`project`** — you need cross-module awareness (e.g. understanding imports,
  finding the right class to extend, planning a refactor across packages)

### When to strip docstrings / private methods

- **Keep docstrings** when you need to understand *what* functions do (writing
  tests, answering usage questions)
- **Strip docstrings** (`--no-docstrings`) when you only need the shape of the
  API (planning, architecture, finding the right hook point)
- **Strip private** (`--no-private`) when you only care about the public
  interface (integration work, SDK consumers)

### When to limit depth

- **`--max-depth 1`** for a quick top-level orientation in a large project
- **No depth limit** when you need the full picture

---

## Anti-patterns

- **Don't skip this step.** Reading individual files one by one wastes tokens
  and misses the big picture. Run api-squash first, then drill into specific
  files only if needed.
- **Don't dump everything.** For large codebases, start with
  `--max-depth 1 --no-docstrings` and drill deeper only into relevant
  packages.
- **Don't save to a file by default.** Read the output directly — saving
  creates cleanup work and the output is already compact.
