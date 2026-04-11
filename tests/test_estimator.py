from __future__ import annotations

from api_squash.estimator import EstimateResult, estimate, format_estimate
from api_squash.models import (
    ClassSummary,
    ConstantSummary,
    FunctionSummary,
    ModuleSummary,
    TypeAliasSummary,
)


def _make_module(
    *,
    path: str = "example.py",
    classes: list[ClassSummary] | None = None,
    functions: list[FunctionSummary] | None = None,
    constants: list[ConstantSummary] | None = None,
    type_aliases: list[TypeAliasSummary] | None = None,
) -> ModuleSummary:
    return ModuleSummary(
        path=path,
        classes=classes or [],
        functions=functions or [],
        constants=constants or [],
        type_aliases=type_aliases or [],
    )


# --- EstimateResult dataclass ---


def test_estimate_result_fields():
    result = EstimateResult(
        files=1,
        classes=2,
        functions=3,
        constants=4,
        type_aliases=5,
        size_bytes=100,
        minimal_size_bytes=50,
    )
    assert result.files == 1
    assert result.classes == 2
    assert result.functions == 3
    assert result.constants == 4
    assert result.type_aliases == 5
    assert result.size_bytes == 100
    assert result.minimal_size_bytes == 50


# --- estimate() counts ---


def test_estimate_counts_single_module():
    module = _make_module(
        classes=[ClassSummary(name="MyClass", methods=[])],
        functions=[
            FunctionSummary(name="func_a", signature="()"),
            FunctionSummary(name="func_b", signature="()"),
        ],
        constants=[ConstantSummary(name="MAX", value="10")],
        type_aliases=[TypeAliasSummary(name="Alias", value="str")],
    )
    result = estimate([module])
    assert result.files == 1
    assert result.classes == 1
    assert result.functions == 2
    assert result.constants == 1
    assert result.type_aliases == 1


def test_estimate_counts_multiple_modules():
    m1 = _make_module(
        path="a.py",
        classes=[ClassSummary(name="A", methods=[])],
        functions=[FunctionSummary(name="f1", signature="()")],
    )
    m2 = _make_module(
        path="b.py",
        functions=[
            FunctionSummary(name="f2", signature="()"),
            FunctionSummary(name="f3", signature="()"),
        ],
        constants=[
            ConstantSummary(name="X", value="1"),
            ConstantSummary(name="Y", value="2"),
        ],
    )
    result = estimate([m1, m2])
    assert result.files == 2
    assert result.classes == 1
    assert result.functions == 3
    assert result.constants == 2
    assert result.type_aliases == 0


def test_estimate_counts_class_methods_separately():
    """Class methods should NOT be counted in top-level functions count."""
    module = _make_module(
        classes=[
            ClassSummary(
                name="Cls",
                methods=[
                    FunctionSummary(name="__init__", signature="(self)"),
                    FunctionSummary(name="run", signature="(self)"),
                ],
            )
        ],
        functions=[FunctionSummary(name="standalone", signature="()")],
    )
    result = estimate([module])
    assert result.functions == 1
    assert result.classes == 1


def test_estimate_empty_modules():
    result = estimate([])
    assert result.files == 0
    assert result.classes == 0
    assert result.functions == 0
    assert result.constants == 0
    assert result.type_aliases == 0
    assert result.size_bytes == 0
    assert result.minimal_size_bytes == 0


# --- estimate() size calculation ---


def test_estimate_size_positive_for_nonempty():
    module = _make_module(
        functions=[FunctionSummary(name="hello", signature="() -> str")],
    )
    result = estimate([module])
    assert result.size_bytes > 0
    assert result.minimal_size_bytes > 0


def test_estimate_minimal_smaller_with_docstrings():
    """When docstrings exist, minimal size should be smaller than default."""
    module = _make_module(
        functions=[
            FunctionSummary(
                name="hello",
                signature="() -> str",
                docstring="A greeting function that says hello.",
            )
        ],
    )
    result = estimate([module])
    assert result.minimal_size_bytes < result.size_bytes


def test_estimate_respects_current_flags():
    """When no_docstrings is already set, current size equals minimal (for docstring dimension)."""
    module = _make_module(
        functions=[
            FunctionSummary(
                name="hello",
                signature="() -> str",
                docstring="A greeting function.",
            )
        ],
    )
    with_docs = estimate([module])
    without_docs = estimate([module], no_docstrings=True)
    # Current size with --no-docstrings should be smaller
    assert without_docs.size_bytes < with_docs.size_bytes


def test_estimate_respects_no_private():
    module = _make_module(
        functions=[
            FunctionSummary(name="public", signature="()"),
            FunctionSummary(name="_private", signature="()"),
        ],
    )
    default = estimate([module])
    no_priv = estimate([module], no_private=True)
    assert no_priv.size_bytes < default.size_bytes


def test_estimate_respects_no_constants():
    module = _make_module(
        constants=[ConstantSummary(name="MAX_SIZE", value="100")],
        functions=[FunctionSummary(name="func", signature="()")],
    )
    default = estimate([module])
    no_const = estimate([module], no_constants=True)
    assert no_const.size_bytes < default.size_bytes


# --- format_estimate() ---


def test_format_estimate_single_file():
    result = EstimateResult(
        files=1,
        classes=3,
        functions=12,
        constants=2,
        type_aliases=0,
        size_bytes=2150,
        minimal_size_bytes=820,
    )
    text = format_estimate(result)
    assert "Extracted 1 file:" in text
    assert "3 classes" in text
    assert "12 functions" in text
    assert "2 constants" in text
    assert "0 type aliases" in text
    assert "2.1 KB" in text
    assert "0.8 KB" in text
    assert "current flags" in text
    assert "minimal" in text


def test_format_estimate_multiple_files():
    result = EstimateResult(
        files=42,
        classes=15,
        functions=80,
        constants=20,
        type_aliases=5,
        size_bytes=12288,
        minimal_size_bytes=4300,
    )
    text = format_estimate(result)
    assert "Extracted 42 files:" in text
    assert "15 classes" in text


def test_format_estimate_zero_files():
    result = EstimateResult(
        files=0,
        classes=0,
        functions=0,
        constants=0,
        type_aliases=0,
        size_bytes=0,
        minimal_size_bytes=0,
    )
    text = format_estimate(result)
    assert "Extracted 0 files:" in text
    assert "0.0 KB" in text


def test_format_estimate_sub_kilobyte():
    result = EstimateResult(
        files=1,
        classes=0,
        functions=1,
        constants=0,
        type_aliases=0,
        size_bytes=500,
        minimal_size_bytes=500,
    )
    text = format_estimate(result)
    assert "0.5 KB" in text
