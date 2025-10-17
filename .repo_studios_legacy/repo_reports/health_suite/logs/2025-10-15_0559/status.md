# Health Suite Run Status

Fault artifacts outdir: /home/founder/jarvis2/.repo_studios/faulthandler/2025-10-15_0559
Fault summary: /home/founder/jarvis2/.repo_studios/faulthandler/2025-10-15_0559/SUMMARY.md

01. ✅ batch_clean — OK (exit=0, 48.167s)
02. ❌ pytest_logs — ERROR (exit=2, 5.672s)
    ↳ error log: .repo_studios/health_suite/logs/2025-10-15_0559/pytest_logs.err.log
03. ❌ scan_monkey_patches — ERROR (exit=1, 5.621s)
    ↳ error log: .repo_studios/health_suite/logs/2025-10-15_0559/scan_monkey_patches.err.log
04. ✅ dep_health — OK (exit=0, 0.035s)
05. ✅ compare_monkey_patch_trends — OK (exit=0, 0.049s)
06. ❌ check_import_boundaries — ERROR (exit=1, 0.186s)
    ↳ error log: .repo_studios/health_suite/logs/2025-10-15_0559/check_import_boundaries.err.log
07. ✅ test_log_health_report — OK (exit=0, 0.053s)
08. ✅ typecheck_report — OK (exit=0, 0.715s)
09. ✅ import_graph_report — OK (exit=0, 0.818s)
10. ✅ churn_complexity_heatmap — OK (exit=0, 4.922s)
11. ✅ lizard_report — OK (exit=0, 3.058s)
12. ✅ fault_dump_once — OK (exit=0, 0.013s)
13. ✅ fault_artifacts — OK (exit=0, 0.042s)
14. ✅ fault_aggregate — OK (exit=0, 0.039s)
15. ✅ fault_gate — OK (exit=0, 0.043s)
16. ✅ anchor_health — OK (exit=0, 0.064s)
17. ✅ health_suite_summary — OK (exit=0, 0.024s)
