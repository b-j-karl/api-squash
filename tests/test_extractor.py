import warnings

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
