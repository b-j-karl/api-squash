from click.testing import CliRunner

from api_squash.cli import cli


def test_file_command(tmp_path):
    source = 'def greet(name: str) -> str:\n    """Say hello."""\n    return f"Hello, {name}"\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p)])
    assert result.exit_code == 0
    assert "def greet(name: str) -> str" in result.output
    assert "Say hello." in result.output


def test_file_command_nonexistent():
    runner = CliRunner()
    result = runner.invoke(cli, ["file", "nonexistent.py"])
    assert result.exit_code != 0


def test_file_command_not_python(tmp_path):
    p = tmp_path / "readme.md"
    p.write_text("# readme", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p)])
    assert result.exit_code != 0
    assert "not a Python file" in result.output


def test_file_command_no_docstrings(tmp_path):
    source = 'def greet(name: str) -> str:\n    """Say hello."""\n    return "hi"\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--no-docstrings"])
    assert result.exit_code == 0
    assert "Say hello." not in result.output
    assert "def greet" in result.output


def test_file_command_no_private(tmp_path):
    source = "def public(): pass\ndef _private(): pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--no-private"])
    assert result.exit_code == 0
    assert "def public" in result.output
    assert "def _private" not in result.output


def test_file_command_syntax_error(tmp_path):
    p = tmp_path / "bad.py"
    p.write_text("def broken(\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p)])
    assert result.exit_code != 0
    assert "Failed to parse" in result.output


def test_project_command(tmp_path):
    (tmp_path / "a.py").write_text(
        'def func_a() -> int:\n    """A function."""\n    return 1\n',
        encoding="utf-8",
    )
    (tmp_path / "b.py").write_text(
        'def func_b() -> str:\n    return "b"\n',
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path)])
    assert result.exit_code == 0
    assert "func_a" in result.output
    assert "func_b" in result.output
    assert "---" in result.output


def test_project_command_with_exclude(tmp_path):
    (tmp_path / "app.py").write_text("def main(): pass\n", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("def test_main(): pass\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path), "--exclude", "tests/*"])
    assert result.exit_code == 0
    assert "main" in result.output
    assert "test_main" not in result.output


def test_project_command_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path)])
    assert result.exit_code == 0


def test_project_command_skips_bad_files(tmp_path):
    (tmp_path / "good.py").write_text("def ok(): pass\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text("def broken(\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path)])
    assert result.exit_code == 0
    assert "ok" in result.output
    assert "Warning" in result.output
