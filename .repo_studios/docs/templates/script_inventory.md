# Script Inventory Template

- **Document Purpose**
	- Explain how the scripts in this folder fit into the broader Repo Studios workflows for both humans and AI collaborators.
	- Capture the relationship between producers, consumers, aggregators, orchestrators, and summarizers when applicable.
	- Last reviewed: `<YYYY-MM-DD>`
	- Maintainer or team: `<name or team>`

- **How to Use This Inventory**
	- Start with the document metadata above and verify the "Last reviewed" date before trusting the entries.
	- Browse inventory entries in order; each bullet is self-contained so AI agents can quote a single entry without additional context.
	- When updating an entry, adjust both the "Last script update" and "Last review" fields and keep descriptions in present tense.
	- If a script moves, update the path and note the relocation in the "Operational notes" sub-bullet.

- **Inventory Entries** *(repeat the following block per script)*
	- **`<script_name.py>`**
		- Location: `<relative/path/to/script_name.py>`
		- Role: `<producer | consumer | aggregator | orchestrator | summarizer | utility>`
		- Description: `<one-phrase summary of what the script does and why it matters>`
		- Primary inputs: `<key inputs or dependencies>`
		- Primary outputs: `<artifact names and formats>`
		- Invocation: `` `.venv/Scripts/python.exe <command ...>` ``
		- Last script update: `<YYYY-MM-DD>`
		- Last review: `<YYYY-MM-DD>`
		- Operational notes: `<quirks, retention rules, follow-on steps>`