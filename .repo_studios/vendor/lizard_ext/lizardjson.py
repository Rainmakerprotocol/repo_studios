"""JSON output extension for lizard (auto-installed)."""

from __future__ import annotations

import json
from typing import Iterable

from lizard import get_warnings


def _serialize_function(func):
    return {
        "name": getattr(func, "name", None),
        "long_name": getattr(func, "long_name", None),
        "cyclomatic_complexity": getattr(func, "cyclomatic_complexity", None),
        "token_count": getattr(func, "token_count", None),
        "parameter_count": getattr(func, "parameter_count", None),
        "length": getattr(func, "length", None),
        "nloc": getattr(func, "nloc", None),
        "start_line": getattr(func, "start_line", None),
        "end_line": getattr(func, "end_line", None),
        "file": getattr(func, "filename", None),
    }


def _serialize_module(module):
    return {
        "filename": getattr(module, "filename", None),
        "nloc": getattr(module, "nloc", None),
        "cyclomatic_complexity": getattr(module, "CCN", None),
        "token_count": getattr(module, "token_count", None),
        "function_list": [_serialize_function(func) for func in getattr(module, "function_list", [])],
    }


def print_json(result: Iterable, option, scheme, total_factory):
    modules = [module for module in result if module]
    print(json.dumps([_serialize_module(module) for module in modules], indent=2))
    warnings = list(get_warnings(modules, option))
    warning_count = len(warnings)
    if getattr(option, "number", -1) >= 0 and warning_count > option.number:
        return warning_count
    return warning_count


class LizardExtension:  # pragma: no cover - compatibility shim
    ordering_index = 10_000

    def set_args(self, parser):
        parser.set_defaults(printer=print_json)

    def __call__(self, tokens, reader):
        for token in tokens:
            yield token
