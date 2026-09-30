# Readiness Lab

**Status: private planning draft.** Keep this repository private until its owner explicitly approves making it public. Do not publish, mirror, or share its contents externally before that approval.

Readiness Lab is a small portfolio concept for showing how a fictional cloud service can turn scattered evidence into a human-reviewed readiness work queue. The point is workflow engineering: traceable inputs, deterministic checks, cautious AI suggestions, visible uncertainty, and accountable human decisions. It is not a FedRAMP product, an assessment, certification, authorization, official crosswalk, or evidence of direct FedRAMP delivery experience.

## Proposed demo

Walk through one synthetic SaaS company, one explicitly fictional service boundary, and 8–12 illustrative work items. Ingest a few deliberately messy files; identify malformed, duplicate, stale, missing, or conflicting data; offer cited AI proposals only for ambiguous cases; let a reviewer accept, edit, reject, or leave items unresolved; then show the resulting work queue and its provenance. A no-AI path should remain usable.

All organizations, people, records, and evidence should be invented. Use synthetic data only: no employer or customer records, credentials, CUI, or copied private project code. The interface and any exported view should say that it is a synthetic working paper, not an assessment result or authorization decision.

## Boundaries

- A human chooses and verifies the applicable program path using current official guidance. The demo must not infer a path or imply a Rev. 5-to-20x mapping.
- Deterministic code handles parsing, validation, freshness, scope, IDs, state, permissions, audit, and recalculation.
- AI can suggest candidate labels, aliases, evidence associations, conflict summaries, and evidence-request questions, with source citations and uncertainty. It must be able to abstain.
- Humans alone decide applicability, sufficiency, risk acceptance, approval, and closure. No AI proposal directly changes records or grants authority.
- Unknown remains unknown. Evidence being present does not prove it is sufficient; a task being completed does not prove a control works.

## Existing project to inspect before implementation

The design brief recommends evaluating the public `justfuckmyshitup/servifide` main branch as a possible starting point. The described reusable pieces include synthetic multi-file intake, hashes and source locators, scoped controls/services, review lifecycle, audit trail, no-model baseline, and a constrained proposal contract. Treat those as leads to verify against the actual current branch and screens, not as guarantees about this new repository. Do not import the private `servifide-whitelabel` variant or copy its code at this planning stage.

Useful reading: [Servifide README](https://github.com/justfuckmyshitup/servifide/blob/main/README.md), [AI contract](https://github.com/justfuckmyshitup/servifide/blob/main/docs/AI.md), [intake and analysis design](https://github.com/justfuckmyshitup/servifide/blob/main/docs/INTAKE_AND_ANALYSIS.md), and [M3 evidence](https://github.com/justfuckmyshitup/servifide/blob/main/docs/evidence/M3-SPRINT.md).

## Source discipline

Program-specific statements must link to official sources and record the version and date checked. Start with [FedRAMP](https://www.fedramp.gov/) and the authoritative [NIST SP 800-53A Rev. 5 publication](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final) and [NIST RMF downloads / authority notice](https://csrc.nist.gov/Projects/risk-management/sp800-53-controls/downloads). Re-check current guidance before presenting any rules or timeline. This draft intentionally makes no claim about which program path applies or what future transition dates require.

See [demo story](docs/DEMO_STORY.md), [architecture](docs/ARCHITECTURE.md), [evaluation](docs/EVALUATION.md), and [roadmap](docs/ROADMAP.md).
