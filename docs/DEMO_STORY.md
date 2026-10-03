# Demo scenario: SaaS evidence review

## Scenario

Suppose a SaaS team needs to review evidence for one service boundary before deciding what needs follow-up. Owner labels differ across records, inventory exports overlap, and some documents are stale or disagree. A feasible first step is to preserve the source references, flag those inconsistencies, and route unresolved questions to a human reviewer; this demo implements that bounded workflow locally.

The included test pack uses the synthetic label "Gizmo Cloud." Its evidence covers inconsistent owner labels, near-duplicate inventory rows, missing ownership, stale material, contradictory MFA claims, an uncertain vendor relationship, an explicit unknown, and an instruction-like note; the tests also cover malformed input. Every organization, person, record, date, and source in the pack is fabricated. The provider and vendor names are fixture labels, not actual software options, integrations, or customer references.

The fixture contains ten illustrative workflow topics: access ownership, MFA, inventory, change approvals, logging, incident response, vulnerability remediation, backups, vendor boundary, and monitoring. These are not a complete baseline, official mapping, or statement of applicability. The path label is fictional and selected by a human for the demo; the software does not decide real applicability.

## Walkthrough

1. Run the no-proposal path and show the fictional boundary and limitations notice.
2. Inspect the deterministic queue: missing owner, duplicate candidates, stale evidence, conflicting claims, and unknown state remain visible.
3. Run `--mock-suggestions`; inspect the sample suggestion and exact source citation. Its label says `synthetic-mock`; no model or provider is called.
4. Record a human edit, rejection, acceptance, or unresolved disposition with reviewer and rationale. No suggestion changes item state on its own.
5. Inspect the working paper and JSON provenance, including source pack hash, evidence revision and locator, findings, proposal source, and human decision.

The output is labeled "synthetic working paper," not an assessment or authorization decision. The demo does not claim complete coverage, certification, or the author's direct FedRAMP delivery experience.

