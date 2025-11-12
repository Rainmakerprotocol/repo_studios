# Class Inheritance Hierarchy View Spec

**Status:** Data slice ready • Controls wired (2025-11-11)

## Goal

Visualize relationships between classes defined in CommandView inventories so reviewers can trace inheritance chains, identify architecture bottlenecks, and spot classes that still rely on external or builtin parents.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.classes` (Map) | `name`, `moduleId`, `bases`, `resolvedBases`, `derivedClassIds`, `methods`, `attributes`, `decorators`, `codeSmells` | Each record represents a class discovered during normalization and includes enriched metadata derived in the viewer layer. |
| `state.normalizedData.modules` (Map) | `classes`, `classCount`, `layerTier` | Associates classes with their owning modules for scoping and status summaries. |
| `state.normalizedData.classInheritance` (object) | `derivedByBase`, `modules`, `stats` | Provides aggregate counts, module-level indexes, and base→derived lookups for diagram scoping and status messaging. |

## Transformations

1. Normalize raw inventory class entries into canonical class records (`createClassRecord`) capturing identifiers, docstring quality, decorators, attributes, and method summaries.
2. Sanitize declared base names, remove generic suffixes, and attempt to resolve each base to a known class within the normalized dataset (local or cross-module) using heuristic matching.
3. Annotate each class with `resolvedBases` (including `matchType` of `local`, `project`, `external`, `builtin`, or `unknown`) and compute reverse edges (`derivedClassIds`) for base→derived navigation.
4. Build aggregate inheritance metadata (`buildClassInheritanceIndex`) that tracks module participation, base-to-derived adjacency lists, root/leaf counts, and references to external/builtin bases.
5. Persist module-level class counts so pack scopes can quickly decide whether to fall back to repository-wide views when a selection lacks classes.

## Planned Mermaid Output Structure

```
graph TD
  classDef local fill:#0f172a,stroke:#38bdf8,color:#f8fafc;
  classDef project fill:#1f2937,stroke:#22c55e,color:#f8fafc;
  classDef external fill:#111827,stroke:#f97316,color:#f8fafc;
  alpha_module_Base["alpha.module.Base\nRoot Class\nDerived: 2"]
  beta_service_ServiceMixin["beta.service.ServiceMixin\nExternal Base"]
  gamma_controller_Derived["gamma.controller.Derived\nMethods: 5\nBases: Base, ServiceMixin"]
  gamma_controller_Derived --> alpha_module_Base
  gamma_controller_Derived -.-> beta_service_ServiceMixin
```

Local/project relationships render as solid edges, while external/builtin bases render as dashed connectors. Nodes include module-qualified names, method counts, and optional smell indicators (e.g., abstract classes or missing docstrings).

## Implementation References

- Normalization helpers added in `viewer.js`: `createClassRecord`, `resolveClassInheritanceRelationships`, `buildClassInheritanceIndex`.
- Modules now expose `classes`, `classCount`, and class IDs, enabling pack scoping similar to function inventories.
- Aggregated inheritance metadata returned as `state.normalizedData.classInheritance` for builders to consume without recomputing graph edges.
- Builder module `ui/builders/class_inheritance_hierarchy.js` renders scoped hierarchy diagrams, highlighting focused classes, unresolved base placeholders, and repository stats.
- Viewer wiring (`buildClassInheritanceHierarchyViewDefinition`) scopes by module/domain/root selections, applies repository fallbacks, and threads status messaging + stats to the sidebar.

## Verification & Hardening

- Regression `.repo_studios/tests/tests_command_center/viewer/test_class_inheritance_data_normalization.py` validates class record creation, base resolution heuristics, and derived class indexing.
- Builder regression `.repo_studios/tests/tests_command_center/viewer/test_class_inheritance_hierarchy_view.py` exercises Mermaid rendering, stats, and placeholder handling.
- View-definition regression `.repo_studios/tests/tests_command_center/viewer/test_class_inheritance_view_definition.py` verifies scoped selection handling plus repository fallbacks.
- Code Flow coexistence harness `.repo_studios/tests/tests_command_center/viewer/test_code_flow_multi_view_coexistence.py` now covers toggling the Class Inheritance Hierarchy alongside existing pack views.
- Existing producer regression `tests/tests_producers/test_generate_function_inventory.py::test_inventory_records_class_bases` confirms CommandView payloads continue emitting accurate base lists.
- Future work will extend diff tooling and overlay additional smell/coverage signals once normalization threads more metadata into class records.

## Future Enhancements

- Resolve generic bases more precisely (e.g., `typing.Generic[T]`) by retaining template information alongside sanitized identifiers.
- Annotate abstract classes and mixins using method decorators to improve status messaging.
- Surface smell metadata (e.g., large inheritance depth, missing docstrings) directly in the diagram legend.
- Introduce diff tooling to compare inheritance graphs between CommandView snapshots.
