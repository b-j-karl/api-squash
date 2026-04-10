import pytest

from api_squash.models import (
    ClassSummary,
    ConstantSummary,
    FunctionSummary,
    ModuleSummary,
    TypeAliasSummary,
)
from api_squash.renderer import render_module, render_project


def test_render_simple_function():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="greet",
                signature="(name: str) -> str",
                docstring="Say hello.",
            ),
        ],
    )
    output = render_module(module)
    expected = "# example.py\n\ndef greet(name: str) -> str\n  Say hello.\n"
    assert output == expected


def test_render_function_no_docstring():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(name="add", signature="(a: int, b: int) -> int"),
        ],
    )
    output = render_module(module)
    expected = "# example.py\n\ndef add(a: int, b: int) -> int\n"
    assert output == expected


def test_render_class_with_methods():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="Calculator",
                docstring="A simple calculator.",
                methods=[
                    FunctionSummary(
                        name="add",
                        signature="(self, a: int, b: int) -> int",
                        docstring="Add two numbers.",
                    ),
                    FunctionSummary(
                        name="sub",
                        signature="(self, a: int, b: int) -> int",
                    ),
                ],
            ),
        ],
    )
    output = render_module(module)
    expected = (
        "# example.py\n"
        "\n"
        "class Calculator:\n"
        "  A simple calculator.\n"
        "  def add(self, a: int, b: int) -> int\n"
        "    Add two numbers.\n"
        "  def sub(self, a: int, b: int) -> int\n"
    )
    assert output == expected


def test_render_class_with_bases():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="Dog",
                bases=["Animal", "Serializable"],
                methods=[
                    FunctionSummary(name="bark", signature="(self) -> str"),
                ],
            ),
        ],
    )
    output = render_module(module)
    assert "class Dog(Animal, Serializable):" in output


def test_render_async_function():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="fetch",
                signature="(url: str) -> bytes",
                is_async=True,
            ),
        ],
    )
    output = render_module(module)
    assert "async def fetch(url: str) -> bytes" in output


def test_render_no_docstrings_flag():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="greet",
                signature="(name: str) -> str",
                docstring="Say hello.",
            ),
        ],
    )
    output = render_module(module, no_docstrings=True)
    assert "Say hello." not in output
    assert "def greet(name: str) -> str" in output


def test_render_no_private_flag():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="MyClass",
                methods=[
                    FunctionSummary(name="__init__", signature="(self)"),
                    FunctionSummary(name="_helper", signature="(self)"),
                    FunctionSummary(name="public", signature="(self)"),
                ],
            ),
        ],
        functions=[
            FunctionSummary(name="_internal", signature="()"),
            FunctionSummary(name="public_func", signature="()"),
        ],
    )
    output = render_module(module, no_private=True)
    assert "__init__" in output
    assert "_helper" not in output
    assert "public" in output
    assert "_internal" not in output
    assert "public_func" in output


def test_render_multiline_docstring():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="process",
                signature="(data: list[int]) -> list[int]",
                docstring=(
                    "Process the data.\n"
                    "\n"
                    "Args:\n"
                    "    data: List of integers.\n"
                    "\n"
                    "Returns:\n"
                    "    Processed list."
                ),
            ),
        ],
    )
    output = render_module(module)
    assert "  Process the data." in output
    assert "  Args:" in output
    assert "      data: List of integers." in output
    assert "  Returns:" in output


def test_render_project_multiple_files():
    modules = [
        ModuleSummary(
            path="a.py",
            functions=[FunctionSummary(name="func_a", signature="()")],
        ),
        ModuleSummary(
            path="b.py",
            functions=[FunctionSummary(name="func_b", signature="()")],
        ),
    ]
    output = render_project(modules)
    assert "# a.py" in output
    assert "# b.py" in output
    assert "---" in output


def test_render_blank_line_between_top_level_items():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="A", methods=[]),
        ],
        functions=[
            FunctionSummary(name="func", signature="()"),
        ],
    )
    output = render_module(module)
    assert "class A:\n\ndef func()" in output


def test_render_empty_module():
    module = ModuleSummary(path="empty.py")
    output = render_module(module)
    assert output == "# empty.py\n"


def test_render_property_method():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="Raster",
                methods=[
                    FunctionSummary(
                        name="crs",
                        signature="(self) -> CRS",
                        decorators=["property"],
                    ),
                ],
            ),
        ],
    )
    output = render_module(module)
    assert "  @property\n  def crs(self) -> CRS" in output


def test_render_staticmethod():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="Utils",
                methods=[
                    FunctionSummary(
                        name="helper",
                        signature="(x: int) -> int",
                        decorators=["staticmethod"],
                    ),
                ],
            ),
        ],
    )
    output = render_module(module)
    assert "  @staticmethod\n  def helper(x: int) -> int" in output


def test_render_overload():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="parse",
                signature="(data: str) -> dict",
                decorators=["overload"],
            ),
            FunctionSummary(
                name="parse",
                signature="(data: bytes) -> dict",
                decorators=["overload"],
            ),
        ],
    )
    output = render_module(module)
    assert "@overload\ndef parse(data: str) -> dict" in output
    assert "@overload\ndef parse(data: bytes) -> dict" in output


def test_render_multiple_decorators():
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="Multi",
                methods=[
                    FunctionSummary(
                        name="do",
                        signature="(x: int) -> int",
                        decorators=["staticmethod", "overload"],
                    ),
                ],
            ),
        ],
    )
    output = render_module(module)
    assert "  @staticmethod\n  @overload\n  def do(x: int) -> int" in output


def test_render_function_no_decorators_unchanged():
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="greet",
                signature="(name: str) -> str",
                docstring="Say hello.",
            ),
        ],
    )
    output = render_module(module)
    expected = "# example.py\n\ndef greet(name: str) -> str\n  Say hello.\n"
    assert output == expected


# --- Tests for private class filtering (#25) ---


def test_no_private_filters_private_classes():
    """Private classes (names starting with _) should be stripped by --no-private."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_InternalHelper", methods=[]),
            ClassSummary(
                name="PublicAPI",
                methods=[
                    FunctionSummary(name="run", signature="(self) -> None"),
                ],
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "_InternalHelper" not in output
    assert "PublicAPI" in output


def test_no_private_keeps_public_classes():
    """Public classes should remain when --no-private is used."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="Service",
                methods=[
                    FunctionSummary(name="__init__", signature="(self)"),
                    FunctionSummary(name="start", signature="(self) -> None"),
                ],
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "class Service:" in output
    assert "__init__" in output
    assert "start" in output


# --- Tests for reference-aware keep logic (#25) ---


def test_no_private_keeps_private_class_referenced_in_return_type():
    """A private class referenced in a public function's return type should be kept."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_ResponseSchema", methods=[]),
        ],
        functions=[
            FunctionSummary(
                name="get_response",
                signature="() -> _ResponseSchema",
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "class _ResponseSchema:" in output
    assert "def get_response() -> _ResponseSchema" in output


def test_no_private_keeps_private_class_referenced_in_param_type():
    """A private class referenced in a public function's parameter should be kept."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_Config", methods=[]),
        ],
        functions=[
            FunctionSummary(
                name="setup",
                signature="(config: _Config) -> None",
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "class _Config:" in output


def test_no_private_keeps_private_class_in_generic_type():
    """A private class inside a generic type (e.g., list[_Item]) should be kept."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_Item", methods=[]),
        ],
        functions=[
            FunctionSummary(
                name="get_items",
                signature="() -> list[_Item]",
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "class _Item:" in output


def test_no_private_keeps_private_class_used_as_base():
    """A private class used as a base of a public class should be kept."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_BaseModel", methods=[]),
            ClassSummary(
                name="User",
                bases=["_BaseModel"],
                methods=[
                    FunctionSummary(name="__init__", signature="(self, name: str)"),
                ],
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "class _BaseModel:" in output
    assert "class User(_BaseModel):" in output


def test_no_private_strips_unreferenced_private_class():
    """A private class with no public references should be stripped."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_Unused", methods=[]),
            ClassSummary(name="_Referenced", methods=[]),
        ],
        functions=[
            FunctionSummary(
                name="build",
                signature="() -> _Referenced",
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "_Unused" not in output
    assert "class _Referenced:" in output


def test_no_private_strips_private_class_only_referenced_by_private():
    """A private class referenced only in private function signatures should be stripped."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_Internal", methods=[]),
        ],
        functions=[
            FunctionSummary(
                name="_helper",
                signature="() -> _Internal",
            ),
            FunctionSummary(
                name="public_func",
                signature="() -> str",
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "_Internal" not in output
    assert "_helper" not in output
    assert "public_func" in output


def test_no_private_keeps_private_func_referenced_in_public_signature():
    """A private function referenced in a public function's signature should be kept."""
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="_default_factory",
                signature="() -> dict",
            ),
            FunctionSummary(
                name="create",
                signature="(factory: Callable = _default_factory) -> dict",
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "_default_factory" in output
    assert "create" in output


def test_no_private_keeps_private_class_referenced_in_init():
    """A private class referenced in __init__ params should be kept."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_Settings", methods=[]),
            ClassSummary(
                name="App",
                methods=[
                    FunctionSummary(
                        name="__init__",
                        signature="(self, settings: _Settings)",
                    ),
                    FunctionSummary(
                        name="run",
                        signature="(self) -> None",
                    ),
                ],
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "class _Settings:" in output


def test_no_private_keeps_private_class_referenced_in_public_method():
    """A private class referenced in a public method's signature should be kept."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(name="_Result", methods=[]),
            ClassSummary(
                name="Service",
                methods=[
                    FunctionSummary(
                        name="process",
                        signature="(self) -> _Result",
                    ),
                ],
            ),
        ],
    )
    output = render_module(module, no_private=True)
    assert "class _Result:" in output


# --- Tests for constant rendering (#20) ---


def test_render_constant_with_value():
    module = ModuleSummary(
        path="example.py",
        constants=[ConstantSummary(name="MAX_RETRIES", value="3")],
    )
    output = render_module(module)
    assert "MAX_RETRIES = 3" in output


def test_render_constant_annotated():
    module = ModuleSummary(
        path="example.py",
        constants=[ConstantSummary(name="TIMEOUT", type_annotation="int", value="30")],
    )
    output = render_module(module)
    assert "TIMEOUT: int = 30" in output


def test_render_constant_annotation_only():
    module = ModuleSummary(
        path="example.py",
        constants=[ConstantSummary(name="BUFFER_SIZE", type_annotation="int")],
    )
    output = render_module(module)
    assert "BUFFER_SIZE: int" in output
    assert "= " not in output.split("BUFFER_SIZE")[1].split("\n")[0]


def test_render_constants_before_classes_and_functions():
    module = ModuleSummary(
        path="example.py",
        constants=[ConstantSummary(name="VERSION", value="'1.0'")],
        classes=[ClassSummary(name="Foo", methods=[])],
        functions=[FunctionSummary(name="bar", signature="()")],
    )
    output = render_module(module)
    version_pos = output.index("VERSION")
    foo_pos = output.index("class Foo")
    bar_pos = output.index("def bar")
    assert version_pos < foo_pos < bar_pos


def test_render_no_constants_flag():
    module = ModuleSummary(
        path="example.py",
        constants=[ConstantSummary(name="MAX_RETRIES", value="3")],
        functions=[FunctionSummary(name="run", signature="()")],
    )
    output = render_module(module, no_constants=True)
    assert "MAX_RETRIES" not in output
    assert "def run()" in output


def test_render_no_private_filters_private_constants():
    module = ModuleSummary(
        path="example.py",
        constants=[
            ConstantSummary(name="_INTERNAL", value="True"),
            ConstantSummary(name="PUBLIC_CONST", value="42"),
        ],
    )
    output = render_module(module, no_private=True)
    assert "_INTERNAL" not in output
    assert "PUBLIC_CONST = 42" in output


def test_render_constants_default_on():
    """Constants are rendered by default (no flag needed)."""
    module = ModuleSummary(
        path="example.py",
        constants=[ConstantSummary(name="API_VERSION", value="'2.0'")],
    )
    output = render_module(module)
    assert "API_VERSION = '2.0'" in output


def test_render_project_passes_no_constants():
    modules = [
        ModuleSummary(
            path="a.py",
            constants=[ConstantSummary(name="FOO", value="1")],
            functions=[FunctionSummary(name="func_a", signature="()")],
        ),
    ]
    output = render_project(modules, no_constants=True)
    assert "FOO" not in output
    assert "func_a" in output


def test_render_empty_module_with_constants():
    """A module with only constants should not appear empty."""
    module = ModuleSummary(
        path="config.py",
        constants=[
            ConstantSummary(name="DEFAULT_PORT", type_annotation="int", value="8080")
        ],
    )
    output = render_module(module)
    assert "# config.py" in output
    assert "DEFAULT_PORT: int = 8080" in output


def test_render_multiple_constants_grouped():
    """Multiple constants should be on consecutive lines without blank lines between them."""
    module = ModuleSummary(
        path="config.py",
        constants=[
            ConstantSummary(name="MAX_RETRIES", value="3"),
            ConstantSummary(name="TIMEOUT", type_annotation="int", value="30"),
            ConstantSummary(name="BUFFER_SIZE", value="1024"),
        ],
    )
    output = render_module(module)
    assert "MAX_RETRIES = 3\nTIMEOUT: int = 30\nBUFFER_SIZE = 1024" in output


# --- Tests for type alias rendering (#21) ---


def test_render_pep613_type_alias():
    module = ModuleSummary(
        path="example.py",
        type_aliases=[TypeAliasSummary(name="PathLike", value="str | Path")],
    )
    output = render_module(module)
    assert "PathLike = str | Path" in output


def test_render_pep695_type_alias():
    module = ModuleSummary(
        path="example.py",
        type_aliases=[
            TypeAliasSummary(name="Vector", value="list[float]", is_type_statement=True)
        ],
    )
    output = render_module(module)
    assert "type Vector = list[float]" in output


def test_render_pep695_type_alias_with_params():
    module = ModuleSummary(
        path="example.py",
        type_aliases=[
            TypeAliasSummary(
                name="Matrix",
                value="list[list[T]]",
                type_params=["T"],
                is_type_statement=True,
            )
        ],
    )
    output = render_module(module)
    assert "type Matrix[T] = list[list[T]]" in output


def test_render_type_aliases_before_classes():
    """Type aliases should appear after constants but before classes."""
    module = ModuleSummary(
        path="example.py",
        constants=[ConstantSummary(name="VERSION", value="'1.0'")],
        type_aliases=[TypeAliasSummary(name="UserId", value="int")],
        classes=[ClassSummary(name="User")],
    )
    output = render_module(module)
    version_pos = output.index("VERSION")
    alias_pos = output.index("UserId")
    class_pos = output.index("class User")
    assert version_pos < alias_pos < class_pos


def test_render_type_alias_not_filtered_by_no_private():
    """Type aliases should not be filtered by --no-private."""
    module = ModuleSummary(
        path="example.py",
        type_aliases=[TypeAliasSummary(name="_Internal", value="int")],
    )
    output = render_module(module, no_private=True)
    assert "_Internal" in output


def test_render_multiple_type_aliases():
    module = ModuleSummary(
        path="example.py",
        type_aliases=[
            TypeAliasSummary(name="UserId", value="int"),
            TypeAliasSummary(name="Coord", value="tuple[float, float]"),
        ],
    )
    output = render_module(module)
    assert "UserId = int" in output
    assert "Coord = tuple[float, float]" in output


# --- Tests for line wrapping (#14) ---


def test_wrap_short_signature_unchanged():
    """Signatures within the wrap width should not be wrapped."""
    module = ModuleSummary(
        path="example.py",
        functions=[FunctionSummary(name="greet", signature="(name: str) -> str")],
    )
    output = render_module(module, wrap=80)
    assert "def greet(name: str) -> str" in output
    assert output.count("\n") < 5  # compact, no extra lines


def test_wrap_long_signature():
    """Signatures exceeding wrap width get one param per line."""
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="run_pipeline",
                signature="(input_path: Path, output_path: Path, format: str, verbose: bool, workers: int, timeout: float, retries: int) -> Result",
            )
        ],
    )
    output = render_module(module, wrap=40)
    assert "def run_pipeline(\n" in output
    assert "    input_path: Path,\n" in output
    assert "    retries: int,\n" in output
    assert ") -> Result" in output


def test_wrap_method_indented():
    """Wrapped method signatures should respect class indentation."""
    module = ModuleSummary(
        path="example.py",
        classes=[
            ClassSummary(
                name="MyClass",
                methods=[
                    FunctionSummary(
                        name="process",
                        signature="(self, data: list[int], threshold: float, normalize: bool, output_format: str) -> dict[str, Any]",
                    )
                ],
            )
        ],
    )
    output = render_module(module, wrap=40)
    assert "  def process(\n" in output
    assert "      self,\n" in output
    assert "  ) -> dict[str, Any]" in output


def test_wrap_preserves_nested_generics():
    """Commas inside generic types should not cause splits."""
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="transform",
                signature="(data: dict[str, list[int]], callback: Callable[[int, str], bool]) -> tuple[str, int]",
            )
        ],
    )
    output = render_module(module, wrap=40)
    assert "    data: dict[str, list[int]]," in output
    assert "    callback: Callable[[int, str], bool]," in output


def test_wrap_async_function():
    """Async functions should wrap correctly."""
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="fetch_data",
                signature="(url: str, headers: dict[str, str], timeout: float, retries: int) -> Response",
                is_async=True,
            )
        ],
    )
    output = render_module(module, wrap=40)
    assert "async def fetch_data(\n" in output
    assert ") -> Response" in output


def test_wrap_none_does_not_wrap():
    """When wrap is None (default), no wrapping occurs."""
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="long_func",
                signature="(a: int, b: int, c: int, d: int, e: int, f: int, g: int) -> None",
            )
        ],
    )
    output = render_module(module)
    assert "def long_func(a: int, b: int, c: int" in output
    # Should be a single line
    for line in output.splitlines():
        if "def long_func" in line:
            assert "-> None" in line
            break
    else:
        pytest.fail("Expected 'def long_func' line not found in output")


def test_wrap_with_decorators():
    """Decorators should appear before the wrapped signature."""
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="my_prop",
                signature="(self, value: str, validate: bool, transform: Callable, default: str | None) -> None",
                decorators=["property"],
            )
        ],
    )
    output = render_module(module, wrap=40)
    lines = output.splitlines()
    prop_line = next(i for i, line in enumerate(lines) if "@property" in line)
    def_line = next(i for i, line in enumerate(lines) if "def my_prop(" in line)
    assert def_line == prop_line + 1


def test_wrap_project_passes_through():
    """The wrap option should be passed through render_project."""
    modules = [
        ModuleSummary(
            path="a.py",
            functions=[
                FunctionSummary(
                    name="long_func",
                    signature="(a: int, b: int, c: int, d: int, e: int, f: int) -> None",
                )
            ],
        ),
    ]
    output = render_project(modules, wrap=40)
    assert "def long_func(\n" in output


def test_wrap_malformed_signature_no_parens():
    """Malformed signature without parens falls back to single-line."""
    module = ModuleSummary(
        path="example.py",
        functions=[FunctionSummary(name="bad", signature="-> None")],
    )
    output = render_module(module, wrap=10)
    assert "def bad-> None" in output


def test_wrap_default_with_comma_in_string():
    """Commas inside quoted default values should not split params."""
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="fmt",
                signature="(sep: str = 'a,b', end: str = 'x') -> None",
            )
        ],
    )
    output = render_module(module, wrap=20)
    assert "    sep: str = 'a,b'," in output
    assert "    end: str = 'x'," in output


def test_wrap_default_with_escaped_quote_and_comma():
    """Commas inside strings with escaped quotes should not split params."""
    module = ModuleSummary(
        path="example.py",
        functions=[
            FunctionSummary(
                name="greet",
                signature=r"""(msg: str = "he said \"hi,bye\"", end: str = 'x') -> None""",
            )
        ],
    )
    output = render_module(module, wrap=20)
    assert r'    msg: str = "he said \"hi,bye\"",' in output
    assert "    end: str = 'x'," in output
