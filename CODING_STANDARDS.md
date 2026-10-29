# Coding standards

Judgement calls for Python in `sqlalchemy_better_aurora_data_api/` and `test/`. Formatting, import order, and line length live in `pyproject.toml`. A Python change is finished when Ruff and the offline tests pass the way `.github/workflows/ci.yml` runs them.

These rules apply to code you add or change. Leave untouched code as it is. Quotes, names, error handling, logging, and `__all__` follow the surrounding code.

## The change

Read the task and the code it touches. Make the smallest complete change, including callers and tests the change breaks. An assumption that changes the code goes in a one-line comment or a test. Comment only a why the code cannot show, in one line.

A new branch, parser, or other logic that can return a wrong value ships with one pytest function in `test/test_offline.py`. A bug that can be shown without a cluster gets that test failing before the fix. A docstring, a comment, or a straight-line rename needs no test. Leave a live-Database failure out of `test/test_offline.py`. The live module is `test/test.py`. A new test module includes the matching edit to `.github/workflows/ci.yml`.

## Types

Annotate every parameter and the return of a function or method you add or edit, including a nested function. Include `-> None`. Leave `self` and `cls` bare. Leave local variables unannotated. A class attribute you change gets an annotation. Attributes you do not change stay unannotated.

Write `list[str]`, `dict[str, int]`, and `X | None`. Take `Callable`, `Iterator`, and `Sequence` from `collections.abc`. Take `Any` from `typing`. A `TypeVar` appears only when two signatures share it. Use a concrete type when you know the value. Use `Any` for a SQLAlchemy connection, a driver exception, or another untyped object from SQLAlchemy or the Data API. A single call site does not get its own `Protocol` or `TypedDict`. Do not add `from __future__ import annotations`.

```python
def _extract_error_code(self, exception: Any) -> Any:
    return exception.args[0].value
```

## Docstrings

A public class, function, or method you add or edit gets one PEP 257 summary line. Public means the name does not start with `_`. A public class with no docstring gets that line in the same edit. Sibling methods stay as they are. Private helpers, private classes, nested functions, and tests get no docstring. Skip `Args` and `Returns` sections. A new module under `sqlalchemy_better_aurora_data_api/` gets one summary line. The module docstring already in `__init__.py` stays as it is. Test modules get none. A docstring that names a domain concept uses the term in `GLOSSARY.md`.

```python
@classmethod
def import_dbapi(cls) -> Any:
    """Return the Aurora Data API module."""
```

## Files

New modules and new tests get no copyright header. The dialect module keeps the Apache header it already has. `LICENSE` and `NOTICE` are the attribution.

## Review

Review of the change catches a missing hint or a missing public docstring. Ruff keeps the formatting and lint job it has now.
