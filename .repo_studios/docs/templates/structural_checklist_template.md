# Structural Checklist Template

Last updated: 2025-10-18

Use this checklist when bootstrapping Repo Studios in a new repository or performing periodic maintenance.

```markdown
# Repo Studios Structural Checklist — <Project Name>

## Phase 1 — Foundation & Inventory
- [ ] `.repo_studios/` directory created with `docs/`, `scripts/`, `reports/`, `tests/` subfolders
- [ ] Inventory catalogs authored (`inventory_docs_catalog.yaml`, etc.)
- [ ] `make -C .repo_studios studio-validate-inventory` passes locally
- [ ] Secondary reports generated in `reports/<topic>/latest`

## Phase 2 — Migration & Normalization
- [ ] Legacy assets migrated or linked from `.repo_studios_legacy/`
- [ ] Updated Make targets (`studio-*`) published
- [ ] Inventory entries cross-reference migrated paths

## Phase 3 — Automation & Quality Gates
- [ ] Test suites wired to CI
- [ ] Secret handling templates delivered
- [ ] Environment bootstrap docs (`SETUP.md`) reviewed

## Notes
- Summary of findings, blockers, and suggested follow-ups.
```

Extend or prune sections to match the maturity of the target repository, but keep the high-level markers to aid reporting.
