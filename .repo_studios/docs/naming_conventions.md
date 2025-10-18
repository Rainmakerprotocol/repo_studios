# Repo Studios Naming Conventions

Last updated: 2025-10-18

Consistent names reduce guesswork for automation and collaborators. Apply the patterns below when adding new assets to `.repo_studios/`.

## Files & Directories

- `std-global-<topic>.md` — global standards in `docs/standards/global/`.
- `std-project-<topic>.md` — project-specific standards in `docs/standards/project/`.
- `inventory_<domain>_catalog.yaml` — authoritative catalog files (e.g., `inventory_docs_catalog.yaml`).
- `reports/<topic>/latest/<artifact>` — generated views; do not commit timestamped folders unless archiving.
- `templates/<purpose>_template.md` — reusable document scaffolds.

## Scripts & Automation

- Python entry points: `scripts/<domain>/<action>.py` with verbs describing behavior (`render_inventory_views.py`).
- Make targets: prefix with `studio-` for Repo Studios workflows (`studio-validate-inventory`).
- CLI wrappers should mirror their script path (`studio-render-views` → `.repo_studios/scripts/render_inventory_views.py`).

## Tests & Fixtures

- Test files live under `tests/<domain>/test_<behavior>.py`.
- Fixtures accompanying inventory validation should live beside the tests using suffix `_fixture.yaml`.

## Inventory IDs

- Use `<category>.<slug>` format (`scripts.health.anchor_health_report`).
- Keep category aligned with folder structure (`scripts.health`, `docs.standards`).
- Favor lowercase with underscores for slugs; reserve hyphens for human-facing titles.

Revisit this guide whenever new asset types are introduced so downstream automation stays predictable.
