# Typecheck Report — now


- status: ERROR
- mypy: mypy 1.17.1 (compiled: yes)
- total errors: 1242
- files with issues: 166
- checked paths: agents/interface/chainlit api/models api/utils api/ui_data.py api/routers/ui.py

## Top Issues (up to 20)
- api/cache/invalidation.py:110 — [attr-defined] Module "api_cache_shared" has no attribute "NEGATIVE_PATHS_SHARED"
- agents/core/monitoring/exceptions.py:164 — [union-attr] Item "None" of "FrameType | None" has no attribute "f_back"
- api/metrics_range.py:80 — [arg-type] Argument 1 to "int" has incompatible type "float | int | Any | dict[Any, Any]"; expected "str | Buffer | SupportsInt | SupportsIndex | SupportsTrunc"
- api/metrics_range.py:82 — [arg-type] Argument 1 to "append" of "list" has incompatible type "float | int | Any | dict[Any, Any]"; expected "float"
- api/chat_logging.py:258 — [assignment] Incompatible types in assignment (expression has type "dict[str, Any | None]", target has type "str")
- api/chat_logging.py:324 — [dict-item] Dict entry 0 has incompatible type "str": "Any | None"; expected "str": "str"
- api/chat_logging.py:325 — [dict-item] Dict entry 1 has incompatible type "str": "Any | None"; expected "str": "str"
- api/chat_logging.py:326 — [dict-item] Dict entry 2 has incompatible type "str": "Any | None"; expected "str": "str"
- agents/system/diagnostic_agent/__init__.py:62 — [misc] Cannot assign to a type
- agents/system/diagnostic_agent/__init__.py:63 — [misc] Cannot assign to a type
- agents/system/diagnostic_agent/__init__.py:64 — [misc] Cannot assign to a type
- agents/system/diagnostic_agent/__init__.py:65 — [misc] Cannot assign to a type
- agents/system/diagnostic_agent/__init__.py:66 — [misc] Cannot assign to a type
- agents/system/diagnostic_agent/__init__.py:37 — [unused-ignore] Unused "type: ignore" comment
- agents/system/diagnostic_agent/__init__.py:67 — [unused-ignore] Unused "type: ignore" comment
- agents/system/diagnostic_agent/__init__.py:68 — [unused-ignore] Unused "type: ignore" comment
- agents/system/diagnostic_agent/__init__.py:69 — [unused-ignore] Unused "type: ignore" comment
- agents/system/diagnostic_agent/__init__.py:70 — [unused-ignore] Unused "type: ignore" comment
- agents/core/monitoring/visualization/utils/data_processing.py:151 — [assignment] Incompatible types in assignment (expression has type "float", variable has type "int")
- agents/core/monitoring/visualization/utils/data_processing.py:170 — [arg-type] Argument 1 to "fromkeys" of "dict" has incompatible type "list[float]"; expected "Iterable[int]"

## How to Reproduce
- make typecheck
- or run: /home/founder/miniconda3/bin/python -m mypy --show-error-codes --no-color-output --hide-error-context agents/interface/chainlit api/models api/utils api/ui_data.py api/routers/ui.py
