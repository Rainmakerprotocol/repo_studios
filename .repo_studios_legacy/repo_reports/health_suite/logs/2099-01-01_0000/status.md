# Health Suite Run Status

Fault artifacts outdir: /home/founder/jarvis2/.repo_studios/faulthandler/2099-01-01_0000
Fault summary: /home/founder/jarvis2/.repo_studios/faulthandler/2099-01-01_0000/SUMMARY.md

01. ❌ batch_clean — ERROR (exit=124, 1.006s)
    ↳ error log: .repo_studios/health_suite/logs/2099-01-01_0000/batch_clean.err.log
02. ❌ pytest_logs — ERROR (exit=124, 1.005s)
    ↳ error log: .repo_studios/health_suite/logs/2099-01-01_0000/pytest_logs.err.log
03. ❌ scan_monkey_patches — ERROR (exit=124, 1.005s)
    ↳ error log: .repo_studios/health_suite/logs/2099-01-01_0000/scan_monkey_patches.err.log
04. ✅ dep_health — OK (exit=0, 0.277s)
05. ✅ compare_monkey_patch_trends — OK (exit=0, 0.285s)
06. ❌ check_import_boundaries — ERROR (exit=1, 0.463s)
    ↳ error log: .repo_studios/health_suite/logs/2099-01-01_0000/check_import_boundaries.err.log
07. ✅ test_log_health_report — OK (exit=0, 0.316s)
08. ❌ typecheck_report — ERROR (exit=124, 1.006s)
    ↳ error log: .repo_studios/health_suite/logs/2099-01-01_0000/typecheck_report.err.log
09. ❌ import_graph_report — ERROR (exit=124, 1.005s)
    ↳ error log: .repo_studios/health_suite/logs/2099-01-01_0000/import_graph_report.err.log
10. ❌ churn_complexity_heatmap — ERROR (exit=124, 1.005s)
    ↳ error log: .repo_studios/health_suite/logs/2099-01-01_0000/churn_complexity_heatmap.err.log
11. ❌ lizard_report — ERROR (exit=124, 1.005s)
    ↳ error log: .repo_studios/health_suite/logs/2099-01-01_0000/lizard_report.err.log
12. ✅ fault_dump_once — OK (exit=0, 0.252s)
13. ✅ fault_artifacts — OK (exit=0, 0.255s)
14. ✅ fault_aggregate — OK (exit=0, 0.262s)
15. ✅ fault_gate — OK (exit=0, 0.251s)
16. ✅ anchor_health — OK (exit=0, 0.292s)
17. ✅ health_suite_summary — OK (exit=0, 0.253s)
