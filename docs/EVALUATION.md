# Evaluation

This evaluation checks synthetic workflow behavior, not FedRAMP compliance or model quality. There are no live model calls.

## Fixed cases

The fixture includes synthetic clean and ambiguous material, an empty owner, a duplicate candidate group, old/expired evidence, conflicting MFA claims, an explicit unknown state, and instruction-like text. Unit tests add malformed records, invalid states, invented source IDs, and revision mismatch.

## Current checks

- Schema, item count, unique identifiers, allowed state, service boundary, and evidence references are deterministic.
- Freshness uses a simple illustrative 365-day window and explicit expiry. This is a demo rule, not an official requirement.
- Suggestion validation checks item scope, source ID, exact locator, exact revision, bounded confidence, and synthetic proposal origin.
- Human review requires an action, reviewer, and rationale; accept/edit requires a value. A human disposition does not silently change deterministic item state.
- Prompt-injection-like text is flagged as inert content; the system does not interpret it as instructions.

No model-quality, citation precision, cost, or latency result is claimed. Before enabling a real model, separately define data handling and retention, approval boundaries, task-specific quality/abstention gates, provider configuration, and evaluation. Do not translate a score into a compliance claim.

