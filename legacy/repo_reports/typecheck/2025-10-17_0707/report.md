# Typecheck Report — 2025-10-17_0707


- status: ERROR
- mypy: mypy 1.10.0 (compiled: yes)
- total errors: 12
- files with issues: 6
- checked paths: agents/interface/chainlit api/models api/utils api/ui_data.py api/routers/ui.py agents/core/monitoring/metrics_storage/storage/hybrid_storage/factory.py

## Top Issues (up to 20)
- api/ui_data.py:571 — [valid-type] Variable "api.ui_data.HistoricalTrendPayload" is not valid as a type
- api/ui_data.py:583 — [valid-type] Variable "api.ui_data.ModelComparisonPayload" is not valid as a type
- api/ui_data.py:595 — [valid-type] Variable "api.ui_data.PerformanceDashboardPayload" is not valid as a type
- agents/interface/chainlit/widgets/trends.py:460 — [override] Signature of "__getitem__" incompatible with supertype "Sequence"
- agents/interface/chainlit/widgets/trends.py:477 — [override] Signature of "__getitem__" incompatible with supertype "Sequence"
- agents/interface/chainlit/widgets/model_comparison.py:376 — [arg-type] Argument 1 to "float" has incompatible type "Any | None"; expected "str | Buffer | SupportsFloat | SupportsIndex"
- agents/interface/chainlit/widgets/model_comparison.py:495 — [arg-type] Argument 1 to "float" has incompatible type "Any | None"; expected "str | Buffer | SupportsFloat | SupportsIndex"
- agents/interface/chainlit/widgets/performance_dashboard.py:147 — [arg-type] Argument 1 to "float" has incompatible type "Any | None"; expected "str | Buffer | SupportsFloat | SupportsIndex"
- agents/interface/chainlit/widgets/performance_dashboard.py:223 — [arg-type] Argument 1 to "int" has incompatible type "Any | None"; expected "str | Buffer | SupportsInt | SupportsIndex | SupportsTrunc"
- agents/interface/chainlit/api_client.py:26 — [unused-ignore] Unused "type: ignore" comment
- agents/interface/chainlit/toast_sink.py:14 — [unused-ignore] Unused "type: ignore" comment
- agents/interface/chainlit/toast_sink.py:16 — [unused-ignore] Unused "type: ignore" comment

## How to Reproduce
- make typecheck
- or run: /mnt/jarvis2/.venv/bin/python -m mypy --show-error-codes --no-color-output --hide-error-context agents/interface/chainlit api/models api/utils api/ui_data.py api/routers/ui.py agents/core/monitoring/metrics_storage/storage/hybrid_storage/factory.py
