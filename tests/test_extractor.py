import sys
import warnings

import pytest

from api_squash.extractor import extract_file


def test_simple_function(tmp_path):
    source = 'def greet(name: str) -> str:\n    """Say hello."""\n    return f"Hello, {name}"\n'
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.functions) == 1
    func = result.functions[0]
    assert func.name == "greet"
    assert func.signature == "(name: str) -> str"
    assert func.docstring == "Say hello."
    assert func.is_async is False


def test_function_no_annotations(tmp_path):
    source = "def add(a, b):\n    return a + b\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(a, b)"
    assert func.docstring is None


def test_function_with_defaults(tmp_path):
    source = "def connect(host: str, port: int = 8080, ssl: bool = True) -> None:\n    pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(host: str, port: int = 8080, ssl: bool = True) -> None"


def test_async_function(tmp_path):
    source = (
        'async def fetch(url: str) -> bytes:\n    """Fetch URL content."""\n    pass\n'
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.name == "fetch"
    assert func.is_async is True
    assert func.signature == "(url: str) -> bytes"


def test_class_with_methods(tmp_path):
    source = (
        "class Calculator:\n"
        '    """A simple calculator."""\n'
        "\n"
        "    def add(self, a: int, b: int) -> int:\n"
        '        """Add two numbers."""\n'
        "        return a + b\n"
        "\n"
        "    def subtract(self, a: int, b: int) -> int:\n"
        "        return a - b\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.classes) == 1
    cls = result.classes[0]
    assert cls.name == "Calculator"
    assert cls.docstring == "A simple calculator."
    assert len(cls.methods) == 2
    assert cls.methods[0].name == "add"
    assert cls.methods[0].docstring == "Add two numbers."
    assert cls.methods[1].name == "subtract"
    assert cls.methods[1].docstring is None


def test_class_with_bases(tmp_path):
    source = "class Dog(Animal, Serializable):\n    def bark(self) -> str:\n        return 'woof'\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    cls = result.classes[0]
    assert cls.bases == ["Animal", "Serializable"]


def test_args_kwargs(tmp_path):
    source = "def flexible(*args: int, **kwargs: str) -> None:\n    pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(*args: int, **kwargs: str) -> None"


def test_keyword_only_args(tmp_path):
    source = "def search(query: str, *, limit: int = 10, offset: int = 0) -> list:\n    pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(query: str, *, limit: int = 10, offset: int = 0) -> list"


def test_positional_only_args(tmp_path):
    source = "def div(a: int, b: int, /) -> float:\n    return a / b\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert func.signature == "(a: int, b: int, /) -> float"


def test_empty_file(tmp_path):
    p = tmp_path / "empty.py"
    p.write_text("", encoding="utf-8")
    result = extract_file(p)

    assert result.functions == []
    assert result.classes == []


def test_multiline_docstring(tmp_path):
    source = (
        "def process(data: list[int]) -> list[int]:\n"
        '    """Process the data.\n'
        "\n"
        "    Args:\n"
        "        data: List of integers to process.\n"
        "\n"
        "    Returns:\n"
        "        Processed list of integers.\n"
        '    """\n'
        "    return data\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert "Args:" in func.docstring
    assert "data: List of integers to process." in func.docstring
    assert "Returns:" in func.docstring


def test_complex_type_hints(tmp_path):
    source = (
        "from typing import Callable\n"
        "def transform(items: list[dict[str, int]], callback: Callable[[int], bool])"
        " -> dict[str, list[int]]:\n"
        "    pass\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    func = result.functions[0]
    assert "list[dict[str, int]]" in func.signature
    assert "Callable[[int], bool]" in func.signature
    assert "-> dict[str, list[int]]" in func.signature


def test_path_uses_forward_slashes(tmp_path):
    subdir = tmp_path / "pkg"
    subdir.mkdir()
    p = subdir / "mod.py"
    p.write_text("def f(): pass\n", encoding="utf-8")
    result = extract_file(p)

    assert "\\" not in result.path
    assert "/" in result.path


def test_file_with_only_imports(tmp_path):
    source = "import os\nfrom pathlib import Path\n"
    p = tmp_path / "imports_only.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.functions == []
    assert result.classes == []


def test_property_decorator(tmp_path):
    source = (
        "class Raster:\n"
        "    @property\n"
        "    def crs(self) -> str:\n"
        "        return self._crs\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    method = result.classes[0].methods[0]
    assert method.decorators == ["property"]


def test_classmethod_decorator(tmp_path):
    source = (
        "class Factory:\n"
        "    @classmethod\n"
        "    def create(cls) -> 'Factory':\n"
        "        return cls()\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    method = result.classes[0].methods[0]
    assert method.decorators == ["classmethod"]


def test_staticmethod_decorator(tmp_path):
    source = (
        "class Utils:\n"
        "    @staticmethod\n"
        "    def helper(x: int) -> int:\n"
        "        return x + 1\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    method = result.classes[0].methods[0]
    assert method.decorators == ["staticmethod"]


def test_overload_decorator(tmp_path):
    source = (
        "from typing import overload\n"
        "class Parser:\n"
        "    @overload\n"
        "    def parse(self, data: str) -> dict: ...\n"
        "    @overload\n"
        "    def parse(self, data: bytes) -> dict: ...\n"
        "    def parse(self, data):\n"
        "        pass\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    methods = result.classes[0].methods
    assert methods[0].decorators == ["overload"]
    assert methods[1].decorators == ["overload"]
    assert methods[2].decorators == []


def test_unrecognised_decorator_ignored(tmp_path):
    source = (
        "import functools\n"
        "class Cached:\n"
        "    @functools.lru_cache\n"
        "    def compute(self, x: int) -> int:\n"
        "        return x * 2\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    method = result.classes[0].methods[0]
    assert method.decorators == []


def test_multiple_decorators(tmp_path):
    source = (
        "from typing import overload\n"
        "class Multi:\n"
        "    @staticmethod\n"
        "    @overload\n"
        "    def do(x: int) -> int: ...\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    method = result.classes[0].methods[0]
    assert method.decorators == ["staticmethod", "overload"]


def test_invalid_escape_no_syntax_warning(tmp_path):
    source = "import re\npattern = re.compile('\\p{L}')\n"
    p = tmp_path / "bad_escape.py"
    p.write_text(source, encoding="utf-8")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = extract_file(p)

    syntax_warnings = [w for w in caught if issubclass(w.category, SyntaxWarning)]
    assert syntax_warnings == [], f"SyntaxWarning(s) leaked: {syntax_warnings}"
    assert result.functions == []


# --- Tests for constant extraction (#20) ---


def test_extract_upper_case_assign(tmp_path):
    source = "MAX_RETRIES = 3\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.constants) == 1
    const = result.constants[0]
    assert const.name == "MAX_RETRIES"
    assert const.type_annotation is None
    assert const.value == "3"


def test_extract_annotated_assign(tmp_path):
    source = "TIMEOUT: int = 30\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.constants) == 1
    const = result.constants[0]
    assert const.name == "TIMEOUT"
    assert const.type_annotation == "int"
    assert const.value == "30"


def test_extract_annotation_only(tmp_path):
    source = "BUFFER_SIZE: int\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.constants) == 1
    const = result.constants[0]
    assert const.name == "BUFFER_SIZE"
    assert const.type_annotation == "int"
    assert const.value is None


def test_extract_skips_lower_case(tmp_path):
    source = "my_variable = 42\nanother: str = 'hello'\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.constants == []


def test_extract_skips_multi_target_assign(tmp_path):
    source = "A = B = 10\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.constants == []


def test_extract_skips_tuple_unpack(tmp_path):
    source = "X, Y = 1, 2\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.constants == []


def test_extract_complex_value(tmp_path):
    source = "DEFAULT_EXCLUDES: set[str] = {'__pycache__', '.git'}\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.constants) == 1
    const = result.constants[0]
    assert const.name == "DEFAULT_EXCLUDES"
    assert const.type_annotation == "set[str]"
    assert const.value is not None


def test_extract_multiple_constants(tmp_path):
    source = "MAX_RETRIES = 3\nTIMEOUT: int = 30\ndef func(): pass\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.constants) == 2
    assert len(result.functions) == 1


def test_extract_mixed_case_skipped(tmp_path):
    """Names like 'MyClass' or 'maxRetries' are not UPPER_CASE constants."""
    source = "MyClass = type('MyClass', (), {})\nmaxRetries = 5\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.constants == []


# --- Tests for type alias extraction (#21) ---


def test_extract_pep613_type_alias(tmp_path):
    """TypeAlias annotation (PEP 613) should be extracted."""
    source = "from typing import TypeAlias\n\nPathLike: TypeAlias = str | Path\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.type_aliases) == 1
    alias = result.type_aliases[0]
    assert alias.name == "PathLike"
    assert alias.value == "str | Path"


# PEP 695 `type` statements are a syntax error on Python <3.12,
# so both ast.parse() and ast.TypeAlias are unavailable.
@pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695 requires Python 3.12+")
def test_extract_pep695_type_statement(tmp_path):
    """PEP 695 type statement (Python 3.12+) should be extracted."""
    source = "type Vector = list[float]\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.type_aliases) == 1
    alias = result.type_aliases[0]
    assert alias.name == "Vector"
    assert alias.value == "list[float]"


@pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695 requires Python 3.12+")
def test_extract_pep695_type_with_params(tmp_path):
    """PEP 695 type statement with type parameters."""
    source = "type Matrix[T] = list[list[T]]\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.type_aliases) == 1
    alias = result.type_aliases[0]
    assert alias.name == "Matrix"
    assert alias.value == "list[list[T]]"
    assert alias.type_params == ["T"]


def test_extract_pep613_typing_extensions(tmp_path):
    """typing_extensions.TypeAlias should also be recognised."""
    source = "from typing_extensions import TypeAlias\n\nUserId: TypeAlias = int\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.type_aliases) == 1
    assert result.type_aliases[0].name == "UserId"
    assert result.type_aliases[0].value == "int"


def test_extract_type_alias_not_confused_with_constant(tmp_path):
    """A TypeAlias should not also appear as a constant."""
    source = "from typing import TypeAlias\n\nMY_TYPE: TypeAlias = int\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.type_aliases) == 1
    assert result.constants == []


@pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695 requires Python 3.12+")
def test_extract_multiple_type_aliases(tmp_path):
    source = (
        "from typing import TypeAlias\n\n"
        "UserId: TypeAlias = int\n"
        "type Coord = tuple[float, float]\n"
    )
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.type_aliases) == 2
    names = [a.name for a in result.type_aliases]
    assert "UserId" in names
    assert "Coord" in names


def test_extract_pep613_qualified_typing(tmp_path):
    """typing.TypeAlias (qualified) should be recognised."""
    source = "import typing\n\nUserId: typing.TypeAlias = int\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.type_aliases) == 1
    assert result.type_aliases[0].name == "UserId"
    assert result.type_aliases[0].value == "int"


def test_extract_pep613_qualified_typing_extensions(tmp_path):
    """typing_extensions.TypeAlias (qualified) should be recognised."""
    source = "import typing_extensions\n\nUserId: typing_extensions.TypeAlias = int\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert len(result.type_aliases) == 1
    assert result.type_aliases[0].name == "UserId"
    assert result.type_aliases[0].value == "int"


def test_extract_plain_annotation_not_type_alias(tmp_path):
    """A regular annotated assignment should NOT be treated as a type alias."""
    source = "MY_VAR: int = 42\n"
    p = tmp_path / "example.py"
    p.write_text(source, encoding="utf-8")
    result = extract_file(p)

    assert result.type_aliases == []
