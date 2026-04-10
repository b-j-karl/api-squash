from importlib.metadata import version

from click.testing import CliRunner

from api_squash.cli import cli


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert version("api-squash") in result.output


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


# --- Tests for --no-constants flag (#20) ---


def test_file_command_includes_constants_by_default(tmp_path):
    source = "MAX_RETRIES = 3\ndef func(): pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p)])
    assert result.exit_code == 0
    assert "MAX_RETRIES = 3" in result.output
    assert "def func()" in result.output


def test_file_command_no_constants(tmp_path):
    source = "MAX_RETRIES = 3\ndef func(): pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--no-constants"])
    assert result.exit_code == 0
    assert "MAX_RETRIES" not in result.output
    assert "def func()" in result.output


def test_project_command_includes_constants_by_default(tmp_path):
    (tmp_path / "config.py").write_text("DEFAULT_PORT: int = 8080\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path)])
    assert result.exit_code == 0
    assert "DEFAULT_PORT: int = 8080" in result.output


def test_project_command_no_constants(tmp_path):
    (tmp_path / "config.py").write_text(
        "DEFAULT_PORT: int = 8080\ndef run(): pass\n", encoding="utf-8"
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path), "--no-constants"])
    assert result.exit_code == 0
    assert "DEFAULT_PORT" not in result.output
    assert "def run()" in result.output


# --- Tests for --wrap flag (#14) ---


def test_file_command_wrap(tmp_path):
    source = "def long_func(a: int, b: int, c: int, d: int, e: int, f: int) -> None:\n    pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--wrap", "40"])
    assert result.exit_code == 0
    assert "def long_func(\n" in result.output
    assert ") -> None" in result.output


def test_project_command_wrap(tmp_path):
    (tmp_path / "mod.py").write_text(
        "def long_func(a: int, b: int, c: int, d: int, e: int) -> None:\n    pass\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path), "--wrap", "40"])
    assert result.exit_code == 0
    assert "def long_func(\n" in result.output


# --- Tests for --public-only flag (#19) ---


def test_file_command_public_only(tmp_path):
    source = (
        '__all__ = ["public_func"]\ndef public_func(): pass\ndef internal(): pass\n'
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--public-only"])
    assert result.exit_code == 0
    assert "public_func" in result.output
    assert "internal" not in result.output


def test_project_command_public_only(tmp_path):
    (tmp_path / "__init__.py").write_text(
        '__all__ = ["exported"]\ndef exported(): pass\ndef hidden(): pass\n',
        encoding="utf-8",
    )
    (tmp_path / "utils.py").write_text(
        "def helper(): pass\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path), "--public-only"])
    assert result.exit_code == 0
    assert "exported" in result.output
    assert "hidden" not in result.output
    # utils.py has no __all__, so everything shows
    assert "helper" in result.output


# --- Tests for --dry-run flag (#23) ---


def test_file_dry_run(tmp_path):
    source = (
        "MAX_RETRIES = 3\n"
        "class MyClass:\n"
        "    def method(self): pass\n"
        "def func_a() -> int:\n"
        '    """A function."""\n'
        "    return 1\n"
        "def func_b() -> str:\n"
        '    return "b"\n'
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--dry-run"])
    assert result.exit_code == 0
    assert "Scanned 1 file:" in result.output
    assert "1 classes" in result.output
    assert "2 functions" in result.output
    assert "1 constants" in result.output
    assert "KB" in result.output
    # Should NOT contain the actual rendered output
    assert "def func_a" not in result.output


def test_file_dry_run_no_rendered_output(tmp_path):
    source = 'def greet(name: str) -> str:\n    """Say hello."""\n    return "hi"\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--dry-run"])
    assert result.exit_code == 0
    assert "def greet" not in result.output
    assert "Say hello." not in result.output
    assert "Scanned 1 file:" in result.output


def test_project_dry_run(tmp_path):
    (tmp_path / "a.py").write_text(
        'def func_a() -> int:\n    """A function."""\n    return 1\n',
        encoding="utf-8",
    )
    (tmp_path / "b.py").write_text(
        "class B:\n    def run(self): pass\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "Scanned 2 files:" in result.output
    assert "1 classes" in result.output
    assert "1 functions" in result.output
    assert "current flags" in result.output
    assert "minimal" in result.output
    # Should NOT contain the actual rendered output
    assert "def func_a" not in result.output
    assert "class B" not in result.output


def test_file_dry_run_combined_with_no_docstrings(tmp_path):
    source = 'def greet():\n    """Say hello."""\n    pass\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")

    runner = CliRunner()
    result_default = runner.invoke(cli, ["file", str(p), "--dry-run"])
    result_no_docs = runner.invoke(
        cli, ["file", str(p), "--dry-run", "--no-docstrings"]
    )
    assert result_default.exit_code == 0
    assert result_no_docs.exit_code == 0
    # Both should show summary, not rendered output
    assert "Scanned 1 file:" in result_default.output
    assert "Scanned 1 file:" in result_no_docs.output


def test_project_dry_run_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["project", str(tmp_path), "--dry-run"])
    # Empty project still prints "No Python files found" to stderr
    assert result.exit_code == 0


def test_file_dry_run_syntax_error(tmp_path):
    p = tmp_path / "bad.py"
    p.write_text("def broken(\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["file", str(p), "--dry-run"])
    assert result.exit_code != 0
    assert "Failed to parse" in result.output
