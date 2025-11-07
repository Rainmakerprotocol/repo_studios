# Mermaid Viewer Cache

Temporary `.mmd` artifacts generated for manual debugging belong in this directory.
Use `write_mermaid_cache.py` to create or refresh cached diagrams:

```
python write_mermaid_cache.py --source path/to/definition.mmd --name duplicate_scan
```

The helper overwrites existing files, purges entries older than 24 hours, and keeps
the newest five diagrams to avoid clutter. Generated files are ignored via
`.gitignore` so the cache never leaks into commits.
