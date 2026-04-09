from api_squash.extractor import extract_file
from api_squash.renderer import render_module


def test_crlf_line_endings(tmp_path):
    source = (
        b'def greet(name: str) -> str:\r\n    """Say hello."""\r\n    return "hi"\r\n'
    )
    p = tmp_path / "crlf.py"
    p.write_bytes(source)
    result = extract_file(p)

    assert result.functions[0].name == "greet"
    assert result.functions[0].docstring == "Say hello."


def test_mixed_line_endings(tmp_path):
    source = b"def a():\n    pass\r\ndef b():\r\n    pass\n"
    p = tmp_path / "mixed.py"
    p.write_bytes(source)
    result = extract_file(p)

    assert len(result.functions) == 2
    assert result.functions[0].name == "a"
    assert result.functions[1].name == "b"


def test_unicode_docstring(tmp_path):
    source = 'def greet() -> str:\n    """H\u00e9llo w\u00f6rld \U0001f30d"""\n    return "hi"\n'
    p = tmp_path / "unicode.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert "H\u00e9llo w\u00f6rld \U0001f30d" in result.functions[0].docstring


def test_unicode_function_name(tmp_path):
    source = 'def caf\u00e9() -> str:\n    return "coffee"\n'
    p = tmp_path / "unicode_name.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.functions[0].name == "caf\u00e9"


def test_path_always_forward_slashes(tmp_path):
    subdir = tmp_path / "pkg" / "sub"
    subdir.mkdir(parents=True)
    p = subdir / "mod.py"
    p.write_text("def f(): pass\n", encoding="utf-8")
    result = extract_file(p)

    assert "\\" not in result.path
    assert "/" in result.path


def test_renderer_output_uses_lf(tmp_path):
    source = b'def greet() -> str:\r\n    """Hello."""\r\n    return "hi"\r\n'
    p = tmp_path / "crlf.py"
    p.write_bytes(source)
    module = extract_file(p)
    output = render_module(module)

    assert "\r" not in output
    assert "def greet() -> str" in output
    assert "Hello." in output
