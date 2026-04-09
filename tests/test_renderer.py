from api_squash.models import ClassSummary, FunctionSummary, ModuleSummary
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
