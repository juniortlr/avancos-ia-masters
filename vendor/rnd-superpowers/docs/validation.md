# Validation record

The domain-neutral revision is checked with the package validator and the existing 13 helper regression tests. These verify structure and narrow utilities, not scientific accuracy across all disciplines.

```bash
python scripts/validate_project.py
python -m unittest discover -s tests -v
python scripts/audit_split.py examples/split-manifest.csv --disjoint-entities
python scripts/plan_ab.py --baseline .5 --effect .1 --units-per-period 100
```

The split fixture uses synthetic entity IDs. It checks one supplied manifest, not feature lineage or every internal model-selection fold. The A/B helper approximates independent binary, fixed-horizon, equal-allocation sample needs: .50 to .60 at alpha .05/power .80 gives 388 units per arm, 776 total. At 100 units per recruitment period that is 7.76 periods before attrition or outcome delay. These are arbitrary numerical test inputs, not project facts.

Earlier scenario planning informed general safeguards about repeated measurements, leakage, assignment units, stopping, collider bias and identification. It does not establish host-level triggering or performance of this revised package. Host installation and real-study pilots remain untested; no model training or empirical causal estimate was performed.

The current distribution excludes historical bundles so removed project-specific material is not shipped inside the archive. Version history is retained separately in the working repository.

## Review-layer addition

Six problem-definition, review and summary skills were added, bringing the catalog to 28. The static validator reports zero errors and all 13 existing helper tests still pass. These checks do not constitute behavioral validation of the new review skills. The review workflow lists future acceptance scenarios.
