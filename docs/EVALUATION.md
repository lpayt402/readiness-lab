# Evaluation plan

Evaluation should test safe, useful workflow behavior, not claim that the demo measures FedRAMP compliance. Begin with a fixed, human-labeled synthetic set; use no live model calls until separately approved and deliberately configured. Without model evaluation, model quality is unverified.

## Test set

Include clean, ambiguous, contradictory, stale, malformed, duplicate, and adversarial cases based on wholly invented records. Cover owner alias ambiguity, a source that does not support the suggested association, conflicting MFA claims, expired evidence, wrong service scope, unknown status, a changed source revision, and instruction-like text embedded in a document. Label expected facts, citations/locators, correct abstention, and what must remain a human decision.

## Baseline and measures

First establish a deterministic baseline: parsing, validation, duplicate candidates, missing-field detection, staleness, scope enforcement, review workflow, and output without AI. Then compare optional AI proposals against the same cases. Report field-level precision, citation exactness, correct abstention on unsupported cases, owner/role discrimination, stale-source detection, reviewer correction rate, latency, and cost. Use human-labeled references and deterministic assertions; do not rely on another LLM as the sole evaluator. Separate system correctness from model suggestion quality.

## Gates before enabling a model

- Tests enforce schema, allowed scope, source revision, and citation grounding.
- No invented, mismatched, or stale citation is accepted; invalid proposals are rejected and visible.
- There is no model-side authorization, approval, or direct write path.
- The workflow remains usable with AI disabled, and uncertain or conflicting cases require human disposition.
- Set task-specific quality and abstention thresholds before evaluation. Keep results and limitations visible; do not translate scores into a compliance claim.

## Threat cases

Test prompt injection in uploaded text and model output; malicious or irrelevant URLs; citation fabrication; incorrect control/evidence association; unsupported role/owner inference; stale evidence; duplicate entities; wrong scope; and malformed inputs. Verify that content is treated as data, URLs are not followed, no model output reaches tools or writes, and audit/provenance distinguish proposal from human decision.
