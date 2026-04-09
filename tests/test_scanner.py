from api_squash.scanner import scan_directory


def test_finds_python_files(tmp_path):
    (tmp_path / "a.py").write_text("# a", encoding="utf-8")
    (tmp_path / "b.py").write_text("# b", encoding="utf-8")
    (tmp_path / "readme.md").write_text("# readme", encoding="utf-8")

    result = scan_directory(tmp_path)
    names = [p.name for p in result]
    assert names == ["a.py", "b.py"]


def test_finds_nested_files(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "module.py").write_text("# mod", encoding="utf-8")

    result = scan_directory(tmp_path)
    assert len(result) == 2


def test_skips_pycache(tmp_path):
    (tmp_path / "mod.py").write_text("# mod", encoding="utf-8")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "cached.py").write_text("# cached", encoding="utf-8")

    result = scan_directory(tmp_path)
    assert len(result) == 1
    assert result[0].name == "mod.py"


def test_skips_venv(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "activate.py").write_text("# activate", encoding="utf-8")

    result = scan_directory(tmp_path)
    assert len(result) == 1
    assert result[0].name == "app.py"


def test_skips_git_dir(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    git = tmp_path / ".git"
    git.mkdir()
    (git / "hook.py").write_text("# hook", encoding="utf-8")

    result = scan_directory(tmp_path)
    assert len(result) == 1


def test_exclude_pattern(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text("# test", encoding="utf-8")

    result = scan_directory(tmp_path, exclude=["tests/*"])
    assert len(result) == 1
    assert result[0].name == "app.py"


def test_exclude_dir_by_name(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001.py").write_text("# migration", encoding="utf-8")

    result = scan_directory(tmp_path, exclude=["migrations"])
    assert len(result) == 1
    assert result[0].name == "app.py"


def test_max_depth_zero(tmp_path):
    (tmp_path / "top.py").write_text("# top", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.py").write_text("# deep", encoding="utf-8")

    result = scan_directory(tmp_path, max_depth=0)
    names = [p.name for p in result]
    assert names == ["top.py"]


def test_max_depth_one(tmp_path):
    (tmp_path / "top.py").write_text("# top", encoding="utf-8")
    level1 = tmp_path / "level1"
    level1.mkdir()
    (level1 / "mid.py").write_text("# mid", encoding="utf-8")
    level2 = level1 / "level2"
    level2.mkdir()
    (level2 / "deep.py").write_text("# deep", encoding="utf-8")

    result = scan_directory(tmp_path, max_depth=1)
    names = [p.name for p in result]
    assert "top.py" in names
    assert "mid.py" in names
    assert "deep.py" not in names


def test_sorted_output(tmp_path):
    (tmp_path / "z.py").write_text("", encoding="utf-8")
    (tmp_path / "a.py").write_text("", encoding="utf-8")
    (tmp_path / "m.py").write_text("", encoding="utf-8")

    result = scan_directory(tmp_path)
    names = [p.name for p in result]
    assert names == ["a.py", "m.py", "z.py"]


def test_empty_directory(tmp_path):
    result = scan_directory(tmp_path)
    assert result == []
