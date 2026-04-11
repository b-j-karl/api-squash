from pathlib import Path

ROOT = Path(__file__).parent.parent

SYNC_PAIRS = [
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


def test_skill_files_are_in_sync():
    """Deployed skill files must match their docs/ sources.

    If this test fails, run: uv run python scripts/sync_skills.py
    """
    for src_rel, dst_rel in SYNC_PAIRS:
        src = ROOT / src_rel
        dst = ROOT / dst_rel
        src_text = src.read_text(encoding="utf-8")
        dst_text = dst.read_text(encoding="utf-8")
        assert src_text == dst_text, (
            f"{dst_rel} is out of sync with {src_rel}.\n"
            "Run: uv run python scripts/sync_skills.py"
        )
