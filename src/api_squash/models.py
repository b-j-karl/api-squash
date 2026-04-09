from dataclasses import dataclass, field


@dataclass
class FunctionSummary:
    name: str
    signature: str
    docstring: str | None = None
    is_async: bool = False


@dataclass
class ClassSummary:
    name: str
    docstring: str | None = None
    methods: list[FunctionSummary] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)


@dataclass
class ModuleSummary:
    path: str
    classes: list[ClassSummary] = field(default_factory=list)
    functions: list[FunctionSummary] = field(default_factory=list)
