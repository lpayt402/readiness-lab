# Architecture

The first slice is a portable Python standard-library CLI. It is intentionally small and has no server, external service, live AI provider, or credential configuration.

## Components and authority

- `fixtures/gizmo_cloud.json` is a fabricated service boundary, ten workflow items, and twelve evidence records.
- `readiness_lab.py` validates the schema and scope, computes freshness and duplicate/conflict/injection indicators, hashes sources, validates cited proposals, stores human decisions, and renders a labeled report.
- `tests/test_readiness.py` exercises malformed data, unknown states, prompt-injection-like text, proposal citation failures, and human decision provenance.
- The optional `mock_proposals` function returns a fixed, visibly synthetic example. It never calls a model. The no-suggestion workflow is the default.

Deterministic code owns parsing, scope, state, source references, revision matching, and output. A future model, if separately approved, could only return a proposal conforming to the validator: a known item, a cited source already in that item's scope, exact locator and revision, bounded confidence, and a recognized proposal origin. There is no provider adapter in this slice. Invalid proposals are rejected; there is no auto-approval or write-through path.

Source text is untrusted data. The prototype does not fetch links or execute instructions found in evidence. Humans alone decide applicability, sufficiency, risk acceptance, approval, and closure. Unknown remains explicit. Evidence presence and task completion do not demonstrate that a control works.

## Provenance

The queue records an as-of date, whole-pack SHA-256, per-evidence content SHA-256, source ID, revision, and locator. Human decisions retain reviewer, action, rationale, timestamp, cited revision, and proposal origin. Changing the pack invalidates review against the prior queue and requires regeneration.

This prototype has no user authentication, durable multi-user audit service, access control, or retention policy. Do not use it with real customer, employer, CUI, or credential data.

