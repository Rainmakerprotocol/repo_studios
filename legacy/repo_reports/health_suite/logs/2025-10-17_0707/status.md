# Health Suite Run Status

Fault artifacts outdir: /home/founder/jarvis2/.repo_studios/faulthandler/2025-10-17_0707
Fault summary: /home/founder/jarvis2/.repo_studios/faulthandler/2025-10-17_0707/SUMMARY.md

01. ✅ batch_clean — OK (exit=0, 45.798s)
02. ❌ pytest_logs — ERROR (exit=1, 415.224s)
    ↳ error log: .repo_studios/health_suite/logs/2025-10-17_0707/pytest_logs.err.log
03. ✅ scan_monkey_patches — OK (exit=0, 5.0s)
04. ✅ dep_health — OK (exit=0, 0.034s)
05. ✅ compare_monkey_patch_trends — OK (exit=0, 0.037s)
06. ❌ check_import_boundaries — ERROR (exit=1, 0.156s)
    ↳ error log: .repo_studios/health_suite/logs/2025-10-17_0707/check_import_boundaries.err.log
07. ✅ test_log_health_report — OK (exit=0, 0.057s)
08. ✅ typecheck_report — OK (exit=0, 0.612s)
09. ✅ import_graph_report — OK (exit=0, 0.568s)
10. ✅ churn_complexity_heatmap — OK (exit=0, 4.613s)
11. ✅ lizard_report — OK (exit=0, 3.297s)
12. ✅ fault_dump_once — OK (exit=0, 0.011s)
13. ✅ fault_artifacts — OK (exit=0, 0.038s)
14. ✅ fault_aggregate — OK (exit=0, 0.034s)
15. ✅ fault_gate — OK (exit=0, 0.04s)
16. ✅ anchor_health — OK (exit=0, 0.059s)
17. ✅ health_suite_summary — OK (exit=0, 0.024s)
