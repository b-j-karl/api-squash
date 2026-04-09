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
