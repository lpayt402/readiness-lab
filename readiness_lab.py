"""Deterministic, synthetic-only readiness workflow demonstration."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

ALLOWED_STATES = {"open", "in_review", "blocked", "complete", "unknown"}
RULESET_VERSION = "demo-1"
REQUIRED_ITEM_FIELDS = {"id", "title", "state", "owner", "scope", "evidence_ids", "due_date"}
REQUIRED_EVIDENCE_FIELDS = {"id", "revision", "locator", "text", "observed_on", "scope"}
INJECTION_MARKERS = ("ignore previous instructions", "system prompt", "reveal secrets", "call this url")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _unique_records(records: list[dict], label: str) -> None:
    _require(all(isinstance(record, dict) for record in records), f"{label} must be an object")
    ids = [record.get("id") for record in records]
    _require(all(isinstance(value, str) and value.strip() for value in ids), f"{label} id must be a non-empty string")
    _require(len(ids) == len(set(ids)), f"duplicate {label} id")


def validate_pack(pack: dict) -> None:
    _require(isinstance(pack, dict), "pack must be an object")
    _require(pack.get("schema_version") == "1.0", "unsupported schema_version")
    _require(pack.get("synthetic_only") is True, "only synthetic_only packs are accepted")
    _require(isinstance(pack.get("service"), dict) and isinstance(pack["service"].get("name"), str) and pack["service"].get("name"), "service name is required")
    _require(isinstance(pack["service"].get("boundary_id"), str) and pack["service"]["boundary_id"], "service boundary_id is required")
    _require(isinstance(pack.get("items"), list) and 8 <= len(pack["items"]) <= 12, "pack must contain 8-12 illustrative items")
    _require(isinstance(pack.get("evidence"), list), "evidence must be a list")
    _unique_records(pack["items"], "item")
    _unique_records(pack["evidence"], "evidence")
    evidence = {record["id"]: record for record in pack["evidence"]}
    for item in pack["items"]:
        _require(REQUIRED_ITEM_FIELDS <= item.keys(), f"item {item.get('id')} is missing required fields")
        _require(isinstance(item["state"], str) and item["state"] in ALLOWED_STATES, f"unknown state for item {item['id']}: {item['state']}")
        _require(item["scope"] == pack["service"].get("boundary_id"), f"scope mismatch for item {item['id']}")
        _require(isinstance(item["evidence_ids"], list), f"evidence_ids must be a list for {item['id']}")
        _require(isinstance(item["owner"], str), f"owner must be a string for {item['id']}")
        _require(all(isinstance(evidence_id, str) for evidence_id in item["evidence_ids"]), f"evidence ids must be strings for {item['id']}")
        try:
            date.fromisoformat(item["due_date"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid due_date for item {item['id']}") from exc
        for evidence_id in item["evidence_ids"]:
            _require(evidence_id in evidence, f"unknown evidence id {evidence_id} for {item['id']}")
    for record in pack["evidence"]:
        _require(REQUIRED_EVIDENCE_FIELDS <= record.keys(), f"evidence {record.get('id')} is missing required fields")
        _require(record["scope"] == pack["service"].get("boundary_id"), f"scope mismatch for evidence {record['id']}")
        _require(all(isinstance(record[field], str) and record[field] for field in ("revision", "locator", "text")), f"invalid source fields for evidence {record['id']}")
        try:
            date.fromisoformat(record["observed_on"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid observed_on for evidence {record['id']}") from exc


def analyze(pack: dict, today: str | None = None) -> dict:
    validate_pack(pack)
    as_of = date.fromisoformat(today) if today else date.today()
    evidence = {record["id"]: record for record in pack["evidence"]}
    by_group: dict[str, list[str]] = {}
    for record in pack["evidence"]:
        if record.get("duplicate_group"):
            by_group.setdefault(record["duplicate_group"], []).append(record["id"])
    analyzed = []
    for item in pack["items"]:
        findings = []
        if not item["owner"]:
            findings.append({"code": "missing_owner", "detail": "No accountable owner is recorded."})
        if item["state"] == "unknown":
            findings.append({"code": "unknown_state", "detail": "State is explicitly unknown and needs human disposition."})
        if item.get("claims") and len({claim["value"] for claim in item["claims"]}) > 1:
            findings.append({"code": "conflicting_claims", "detail": "Source claims disagree; preserve both for review."})
        seen_duplicate_groups: set[str] = set()
        for evidence_id in item["evidence_ids"]:
            record = evidence[evidence_id]
            observed = date.fromisoformat(record["observed_on"])
            if (as_of - observed).days > 365 or (record.get("expires_on") and date.fromisoformat(record["expires_on"]) < as_of):
                findings.append({"code": "stale_evidence", "detail": f"{evidence_id} is outside the illustrative freshness window."})
            if record.get("duplicate_group") and record["duplicate_group"] not in seen_duplicate_groups and len(by_group[record["duplicate_group"]]) > 1:
                findings.append({"code": "possible_duplicate", "detail": f"Related sources: {', '.join(by_group[record['duplicate_group']])}."})
                seen_duplicate_groups.add(record["duplicate_group"])
            if any(marker in record["text"].lower() for marker in INJECTION_MARKERS):
                findings.append({"code": "instruction_like_text", "detail": f"Instruction-like text in {evidence_id} is inert source data."})
        analyzed.append({"id": item["id"], "title": item["title"], "state": item["state"], "owner": item["owner"], "due_date": item["due_date"], "scope": item["scope"], "evidence": [{"id": evidence_id, "revision": evidence[evidence_id]["revision"], "locator": evidence[evidence_id]["locator"], "sha256": hashlib.sha256(evidence[evidence_id]["text"].encode()).hexdigest()} for evidence_id in item["evidence_ids"]], "findings": findings})
    return {"schema_version": "1.0", "ruleset_version": RULESET_VERSION, "as_of": as_of.isoformat(), "service": copy.deepcopy(pack["service"]), "source_pack_sha256": hashlib.sha256(json.dumps(pack, sort_keys=True).encode()).hexdigest(), "items": analyzed, "human_decisions": [], "proposal_mode": "off"}


def mock_proposals(result: dict, pack: dict) -> list[dict]:
    """Return visibly synthetic example suggestions; this function never calls a model."""
    item = next((record for record in pack["items"] if record["id"] == "WI-002"), None)
    if not item or not item["evidence_ids"]:
        return []
    source = next(record for record in pack["evidence"] if record["id"] == item["evidence_ids"][0])
    return [{"item_id": item["id"], "suggestion": "Security Team (candidate alias)", "citation": {"evidence_id": source["id"], "locator": source["locator"], "revision": source["revision"]}, "confidence": 0.42, "source": "synthetic-mock", "uncertainty": "Illustrative fixture only; confirm with a human."}]


def validate_proposal(proposal: dict, result: dict, pack: dict) -> dict:
    errors = []
    items = {item["id"]: item for item in result["items"]}
    sources = {source["id"]: source for source in pack["evidence"]}
    item = items.get(proposal.get("item_id"))
    citation = proposal.get("citation") or {}
    source = sources.get(citation.get("evidence_id"))
    if not item:
        errors.append("unknown item")
    elif not any(ref["id"] == citation.get("evidence_id") for ref in item["evidence"]):
        errors.append("citation is outside item evidence scope")
    if not source:
        errors.append("unknown citation")
    else:
        if citation.get("locator") != source["locator"]:
            errors.append("citation locator mismatch")
        if citation.get("revision") != source["revision"]:
            errors.append("citation revision mismatch")
    if not isinstance(proposal.get("suggestion"), str) or not proposal["suggestion"].strip():
        errors.append("empty suggestion")
    if proposal.get("source") not in {"synthetic-mock", "proposal-only"}:
        errors.append("unrecognized proposal source")
    if not isinstance(proposal.get("confidence"), (int, float)) or not 0 <= proposal["confidence"] <= 1:
        errors.append("confidence must be between 0 and 1")
    return {"valid": not errors, "errors": errors}


def record_review(result: dict, proposal: dict, action: str, rationale: str, reviewer: str, accepted_value: str | None = None) -> dict:
    if action not in {"accept", "edit", "reject", "unresolved"}:
        raise ValueError("action must be accept, edit, reject, or unresolved")
    if not reviewer.strip() or not rationale.strip():
        raise ValueError("reviewer and rationale are required")
    if action in {"accept", "edit"} and not (accepted_value or (proposal.get("suggestion") if action == "accept" else "")).strip():
        raise ValueError("accepted value is required for accept/edit")
    reviewed = copy.deepcopy(result)
    reviewed["human_decisions"].append({"item_id": proposal["item_id"], "action": action, "value": accepted_value if action == "edit" else proposal.get("suggestion") if action == "accept" else None, "rationale": rationale, "reviewer": reviewer, "proposal_source": proposal["source"], "citation": copy.deepcopy(proposal["citation"]), "reviewed_at": date.today().isoformat()})
    return reviewed


def render_report(result: dict, pack: dict) -> str:
    lines = ["SYNTHETIC WORKING PAPER - not an assessment, authorization, certification, or official mapping.", f"Service: {result['service']['name']} | Scope: {result['service']['boundary_id']} | As of: {result['as_of']}", "Illustrative workflow topics only; no baseline completeness or control sufficiency is represented.", "", "WORK QUEUE"]
    for item in result["items"]:
        sources = ", ".join(f"{source['id']}@{source['revision']}#{source['locator']}" for source in item["evidence"]) or "none"
        codes = ", ".join(finding["code"] for finding in item["findings"]) or "no deterministic flags"
        lines.append(f"- {item['id']} {item['title']} | state={item['state']} | owner={item['owner'] or 'MISSING'} | due={item['due_date']} | sources={sources} | flags={codes}")
    lines.extend(["", "HUMAN REVIEW DECISIONS"])
    if result["human_decisions"]:
        for decision in result["human_decisions"]:
            lines.append(f"- {decision['item_id']}: {decision['action']} by {decision['reviewer']} | {decision['rationale']} | source={decision['proposal_source']}")
    else:
        lines.append("- None recorded; suggestions do not change the queue.")
    lines.extend(["", f"Source pack SHA-256: {result['source_pack_sha256']}", "No AI service was called. Human review is required for applicability, sufficiency, risk, approval, and closure."])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic-only readiness workflow demonstration")
    parser.add_argument("--fixture", type=Path, default=Path("fixtures/gizmo_cloud.json"))
    parser.add_argument("--out", type=Path, default=Path("out"))
    parser.add_argument("--today", help="Override date for reproducible demonstration (YYYY-MM-DD)")
    parser.add_argument("--mock-suggestions", action="store_true", help="Include clearly synthetic example suggestions; no model call")
    parser.add_argument("--review-item", help="Record a human decision for an item with a mock suggestion")
    parser.add_argument("--action", choices=["accept", "edit", "reject", "unresolved"])
    parser.add_argument("--rationale")
    parser.add_argument("--reviewer")
    parser.add_argument("--value", help="Human-confirmed value for accept/edit")
    args = parser.parse_args(argv)
    try:
        pack = json.loads(args.fixture.read_text(encoding="utf-8"))
        result = analyze(pack, today=args.today)
        if args.review_item:
            if not all((args.action, args.rationale, args.reviewer)):
                raise ValueError("--review-item requires --action, --rationale, and --reviewer")
            previous_path = args.out / "review_queue.json"
            if not previous_path.exists():
                raise ValueError("run with --mock-suggestions first to create a review queue")
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
            if previous.get("source_pack_sha256") != result.get("source_pack_sha256"):
                raise ValueError("source pack changed since queue creation; regenerate proposals and re-review")
            if previous.get("ruleset_version") != result.get("ruleset_version"):
                raise ValueError("analysis rules changed since queue creation; regenerate proposals and re-review")
            proposal = next((p for p in previous.get("proposals", []) if p.get("item_id") == args.review_item), None)
            if not proposal:
                raise ValueError(f"no proposal exists for {args.review_item}; decisions require a cited proposal")
            if not validate_proposal(proposal, result, pack)["valid"]:
                raise ValueError("proposal citation failed current source/revision validation")
            result["human_decisions"] = previous.get("human_decisions", [])
            result["proposals"] = previous.get("proposals", [])
            result = record_review(result, proposal, args.action, args.rationale, args.reviewer, args.value)
        if args.mock_suggestions:
            result["proposal_mode"] = "synthetic-mock; no provider calls"
            result["proposals"] = json.loads((args.out / "review_queue.json").read_text(encoding="utf-8")).get("proposals", []) if args.review_item else mock_proposals(result, pack)
            result["proposal_validation"] = [validate_proposal(p, result, pack) for p in result["proposals"]]
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "review_queue.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        (args.out / "working_paper.txt").write_text(render_report(result, pack), encoding="utf-8")
        print(render_report(result, pack))
        print(f"Wrote {args.out / 'review_queue.json'} and {args.out / 'working_paper.txt'}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"readiness-lab: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

