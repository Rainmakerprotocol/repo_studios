# Repo Studios Script Layout

This directory houses the active automation suite for Repo Studios. Scripts are grouped by the role they play in the data and automation pipeline so coding agents can locate the right tool quickly.

## Category Map

- `producers/` – base-layer scripts that gather data directly from source systems and emit raw artifacts for downstream consumers.
- `consumers/` – single-hop analyzers that operate on one producer’s output to generate targeted reports or validations.
- `aggregators/` – multi-source combiners that blend several producer/consumer artifacts into higher-order insights.
- `orchestrators/` – top-level entry points that coordinate producer, consumer, and aggregator scripts into cohesive suites.
- `summarizers/` – final-mile storytellers that distill suite outputs into executive or machine-readable digests.
- `utilities/` – cross-cutting helpers (runtime shims, maintenance tasks) that support all tiers.
- `manifest/` – migration manifest and planning notes retained for historical tracking during the restructure.

## Operating Notes

- Each tier will ship with a local README describing expected inputs, outputs, run cadence, and ownership as we refactor the scripts.
- Continue recording legacy → new relocations inside `manifest/scripts_manifest.yaml` until the rewrite is complete.
- Log-producing scripts should adopt the upcoming silent `prune_logs` helper to cap artifact history without noisy output.
- Orchestrators that previously lived in legacy Make targets will be renamed with the `studio-` prefix when we re-enable automation.

## Immediate TODOs

- Backfill tier-level READMEs summarizing responsibilities, inputs, and downstream dependencies.
- Update `scripts_manifest.yaml` to reference the new tier folders and mark completed moves.
- Draft the reusable `prune_logs` helper under `utilities/` and retrofit log-heavy scripts during migration.
