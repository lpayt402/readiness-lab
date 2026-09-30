# Architecture sketch

This is a planning hypothesis, not a claim about code already present in this repository. Inspect the actual `readiness-lab` repo and the current public Servifide branch before selecting implementation details. Start by confirming the existing screens, workflows, fixture model, permissions, audit trail, and proposal/commit boundary.

## Candidate reuse

The design brief identifies public Servifide as a possible base because it appears to provide synthetic multi-file intake, source hashes and locators, retained evidence, scoped service/control objects, analyst/admin assessment lifecycle, durable tasks, audit history, a no-model path, and a provider-neutral proposal interface. Validate each element in current source and tests. Reuse only what is suitable and compatible; do not assume FedRAMP-specific mapping exists. Keep this prototype narrow rather than rebuilding a GRC suite. Do not copy private `servifide-whitelabel` code or bring it into this repo without separate explicit approval.

## Proposed components

- **Fixture and intake layer:** fabricated files only; parser results preserve raw values, stable IDs, source hashes, parser version, and precise row/page/field locators. Malformed and unsupported inputs produce visible errors.
- **Deterministic workflow:** owns validation, scope, identity/owner checks, freshness, duplicate candidates, allowed relationships, statuses, readiness counts, authorization, writes, audit events, and stale-result invalidation.
- **AI proposal adapter (optional):** receives only the bounded ambiguous subset in synthetic-only mode. Emits schema-validated candidate suggestions, citations grounded in provided source snippets, uncertainty, and abstention. Model/provider and prompt/schema version are recorded. Model output cannot invoke tools, fetch URLs, authorize actions, or write records.
- **Review surface:** shows source and proposal together, with accept/edit/reject/request-evidence/unknown decisions, reviewer identity and rationale. Only the established authorized review path can commit a human decision.
- **Portfolio view/export:** summarizes work item, status, owner, dates, source/version, reviewer decision, open ambiguity, and next step; visibly labels output as synthetic working material.

## Authority and failure behavior

Code, not the model, determines validity and state. AI may suggest candidate labels, associations, aliases, concise conflict summaries, or evidence-request wording. It may not declare compliance, decide applicability or risk, approve, close findings, choose a certification path, or certify. Unknown must remain an explicit state. Evidence presence is not evidence sufficiency; a completed task is not proof that a control works.

Uploaded text and model outputs are untrusted. Test instruction-like content, poisoned files, malicious-looking URLs, unsupported citations, hallucinated mappings, foreign IDs, stale revisions, conflicting owners, and scope mismatch. Do not fetch URLs found in evidence. Keep raw text out of routine logs; avoid live provider credentials and live model calls in this planning/prototype phase. If AI is unavailable or disabled, deterministic intake, review, and export still work.

## Provenance to retain

For each result, plan to retain source hash/version and locator, parser version, rule/policy version, input revision, proposal schema and prompt version (and provider/model if used), citation, reviewer action, actor, timestamp, and final disposition. Define redaction and retention before any hosted inference is enabled. Preserve the distinction between source facts, deterministic findings, AI proposals, and human determinations in both UI and stored records.
