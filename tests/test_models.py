from api_squash.models import FunctionSummary, ClassSummary, ModuleSummary


def test_function_summary_defaults():
    func = FunctionSummary(name="greet", signature="(name: str) -> str")
    assert func.name == "greet"
    assert func.signature == "(name: str) -> str"
    assert func.docstring is None
    assert func.is_async is False
    assert func.decorators == []


def test_function_summary_all_fields():
    func = FunctionSummary(
        name="fetch",
        signature="(url: str) -> bytes",
        docstring="Fetch URL content.",
        is_async=True,
        decorators=["staticmethod", "overload"],
    )
    assert func.name == "fetch"
    assert func.docstring == "Fetch URL content."
    assert func.is_async is True
    assert func.decorators == ["staticmethod", "overload"]


def test_class_summary_defaults():
    cls = ClassSummary(name="Calculator")
    assert cls.name == "Calculator"
    assert cls.docstring is None
    assert cls.methods == []
    assert cls.bases == []


def test_class_summary_all_fields():
    method = FunctionSummary(name="add", signature="(self, a: int, b: int) -> int")
    cls = ClassSummary(
        name="Calculator",
        docstring="A simple calculator.",
        methods=[method],
        bases=["BaseClass"],
    )
    assert cls.docstring == "A simple calculator."
    assert len(cls.methods) == 1
    assert cls.bases == ["BaseClass"]


def test_module_summary_defaults():
    mod = ModuleSummary(path="example.py")
    assert mod.path == "example.py"
    assert mod.classes == []
    assert mod.functions == []


def test_module_summary_all_fields():
    func = FunctionSummary(name="main", signature="()")
    cls = ClassSummary(name="App")
    mod = ModuleSummary(path="app.py", classes=[cls], functions=[func])
    assert len(mod.classes) == 1
    assert len(mod.functions) == 1
