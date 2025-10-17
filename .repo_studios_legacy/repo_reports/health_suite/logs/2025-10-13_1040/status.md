# Health Suite Run Status

Fault artifacts outdir: /home/founder/jarvis2/.repo_studios/faulthandler/2025-10-13_1040
Fault summary: /home/founder/jarvis2/.repo_studios/faulthandler/2025-10-13_1040/SUMMARY.md

01. ✅ batch_clean — OK (exit=0, 47.299s)
02. ❌ pytest_logs — ERROR (exit=1, 346.683s)
    ↳ error log: .repo_studios/health_suite/logs/2025-10-13_1040/pytest_logs.err.log
03. ✅ scan_monkey_patches — OK (exit=0, 5.097s)
04. ✅ dep_health — OK (exit=0, 0.035s)
05. ✅ compare_monkey_patch_trends — OK (exit=0, 0.045s)
06. ❌ check_import_boundaries — ERROR (exit=1, 0.17s)
    ↳ error log: .repo_studios/health_suite/logs/2025-10-13_1040/check_import_boundaries.err.log
07. ✅ test_log_health_report — OK (exit=0, 0.057s)
08. ✅ typecheck_report — OK (exit=0, 0.582s)
09. ✅ import_graph_report — OK (exit=0, 0.794s)
10. ✅ churn_complexity_heatmap — OK (exit=0, 4.671s)
11. ✅ lizard_report — OK (exit=0, 2.907s)
12. ✅ fault_dump_once — OK (exit=0, 0.012s)
13. ✅ fault_artifacts — OK (exit=0, 0.043s)
14. ✅ fault_aggregate — OK (exit=0, 0.039s)
15. ✅ fault_gate — OK (exit=0, 0.041s)
16. ✅ anchor_health — OK (exit=0, 0.07s)
17. ✅ health_suite_summary — OK (exit=0, 0.028s)
