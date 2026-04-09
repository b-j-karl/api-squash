# python-code-context Skill

A workflow skill that uses `api-squash` to load Python API surfaces into your
agent's context before code generation, test writing, or refactoring tasks.

For CLI reference (flags, output format, examples), this skill defers to the
companion **api-squash-cli** skill.

## Installation

### Copilot CLI

```bash
cp -r copilot ~/.copilot/skills/python-code-context
```

### Claude Code

```bash
cp -r claude ~/.claude/skills/python-code-context
```

> **Prerequisite:** Install the **api-squash-cli** skill as well — this skill
> references it for command details.
