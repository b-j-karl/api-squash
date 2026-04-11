#!/usr/bin/env python3
"""Sync skill files from docs/skills/ to .claude/skills/ and .github/skills/."""

import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent

COPIES = [
    (
        "docs/skills/api-squash-cli/claude/SKILL.md",
        ".claude/skills/api-squash-cli/SKILL.md",
    ),
    (
        "docs/skills/api-squash-cli/copilot/SKILL.md",
        ".github/skills/api-squash-cli/SKILL.md",
    ),
    (
        "docs/skills/python-code-context/claude/SKILL.md",
        ".claude/skills/python-code-context/SKILL.md",
    ),
    (
        "docs/skills/python-code-context/copilot/SKILL.md",
        ".github/skills/python-code-context/SKILL.md",
    ),
]


def sync() -> None:
    for src_rel, dst_rel in COPIES:
        src = ROOT / src_rel
        dst = ROOT / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  {src_rel} -> {dst_rel}")


if __name__ == "__main__":
    print("Syncing skill files...")
    sync()
    print("Done.")
