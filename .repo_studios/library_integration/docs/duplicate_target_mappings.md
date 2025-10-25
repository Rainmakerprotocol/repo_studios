# Duplicate Target Mappings (Baseline – 2025-10-24)

This document maps the first four duplicate hotspots to their future home inside `.repo_studios/library/`, following the training guide naming rules.

| Duplicate Name | Current Usage Notes | Target Library Path | Rationale |
| --- | --- | --- | --- |
| `_copy_latest` | Appears in artifact producers that publish timestamped runs and maintain a "latest" pointer. | `artifact_lifecycle/versioning/create_latest_link.py` | Lives in artifact lifecycle, handles versioning concerns, mirrors existing blueprint entry. |
| `write_artifacts` | Aggregates writing of JSON/Markdown/TSV outputs for reports. | `artifact_lifecycle/structured_output/write_json_artifact.py` + neighbors | Split responsibilities across existing structured output modules; primary JSON writer lands here while Markdown/TSV logic maps to sibling modules. |
| `parse_args` | CLI entrypoint helpers repeated across scripts. | `cli_patterns/common_args/repo_root_arg.py` and related | Normalize argument builders into dedicated files so each flag is discoverable per the naming guide. |
| `configure_logging` | Standard logging.basicConfig wrapper duplicated in producers. | `logging_setup/configuration/configure_basic_logging.py` | Exactly matches blueprint naming; isolates logging responsibility. |

## Usage Notes

- These mappings align 1:1 with the generator blueprint; no new folders are required.
- When migration begins, create only the modules needed—avoid seeding the entire blueprint with placeholders.
- Annotate extraction PRs with the selected target so future audits trace the decision path.
