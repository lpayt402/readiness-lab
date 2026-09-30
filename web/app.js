const stateUrl = "/api/state";
const reviewUrl = "/api/review";
let appState = null;
let selectedId = "WI-002";
let toastTimer = null;

const byId = (id) => document.getElementById(id);
const make = (tag, className, text) => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};

function escapeLabel(value) {
  return String(value).replaceAll("_", " ").replaceAll("-", " ");
}

function selectedItem() {
  return appState.items.find((item) => item.id === selectedId) || appState.items[0];
}

function decisionsFor(itemId) {
  return appState.human_decisions.filter((decision) => decision.item_id === itemId);
}

function renderSummary() {
  const codes = new Set(appState.items.flatMap((item) => item.findings.map((finding) => finding.code)));
  const metrics = [
    ["Illustrative items", appState.items.length, "10"],
    ["Evidence records", appState.evidence.length, "?"],
    ["Open signals", appState.items.filter((item) => item.findings.length).length, "!"],
    ["Human decisions", appState.human_decisions.length, "�"],
  ];
  const summary = byId("summary");
  summary.replaceChildren();
  for (const [label, value, icon] of metrics) {
    const card = make("div", "metric");
    const text = make("div");
    text.append(make("div", "metric-label", label), make("div", "metric-value", value));
    card.append(text, make("span", "metric-icon", icon));
    summary.append(card);
  }
  byId("item-count").textContent = String(appState.items.length);
  byId("source-provenance").textContent = `Rules ${appState.ruleset_version} � source ${appState.source_pack_sha256.slice(0, 12)}.`;
}

function renderQueue() {
  const list = byId("queue-list");
  list.replaceChildren();
  for (const item of appState.items) {
    const button = make("button", "queue-item");
    button.type = "button";
    button.dataset.itemId = item.id;
    button.setAttribute("aria-current", String(item.id === selectedId));
    const title = make("span", "queue-item-title", item.title);
    const id = make("span", "queue-item-id", item.id);
    const meta = make("span", "queue-item-meta", item.owner || "Owner missing");
    const status = make("span", `status-pill status-${item.state}`, escapeLabel(item.state));
    button.append(title, id, status, meta);
    list.append(button);
  }
}

function renderFindings(item, target) {
  const section = make("section");
  const heading = make("div", "section-heading");
  heading.append(make("h3", "", "Deterministic findings"), make("span", "section-caption", `${item.findings.length} signals`));
  section.append(heading);
  const list = make("div", "findings");
  if (!item.findings.length) {
    list.append(make("div", "no-findings", "No deterministic flags for this item."));
  } else {
    for (const finding of item.findings) {
      const row = make("article", "finding");
      row.append(make("span", "finding-mark", "!"));
      const body = make("div");
      body.append(make("strong", "", escapeLabel(finding.code)), make("p", "", finding.detail));
      row.append(body);
      list.append(row);
    }
  }
  target.append(list);
}

function renderSources(item, target) {
  const heading = make("div", "section-heading");
  heading.append(make("h3", "", "Source evidence"), make("span", "section-caption", "Original text � read only"));
  target.append(heading);
  const sourceMap = new Map(appState.evidence.map((source) => [source.id, source]));
  const list = make("div", "evidence-list");
  for (const ref of item.evidence) {
    const source = sourceMap.get(ref.id);
    if (!source) continue;
    const card = make("article", "source-card");
    const top = make("div", "source-top");
    top.append(make("span", "source-id", source.id), make("span", "source-version", `Revision ${source.revision}`));
    card.append(top, make("code", "source-locator", source.locator), make("p", "source-text", source.text));
    card.append(make("code", "source-hash", `SHA-256 ${ref.sha256}`));
    list.append(card);
  }
  target.append(list);
}

function renderDetail() {
  const item = selectedItem();
  const target = byId("item-detail");
  target.replaceChildren();
  const top = make("div", "detail-topline");
  const title = make("div");
  title.append(make("div", "detail-id", `${item.id} � ${item.scope}`), make("h2", "detail-title", item.title));
  const status = make("span", `status-pill status-${item.state}`, escapeLabel(item.state));
  top.append(title, status);
  target.append(top);
  const meta = make("div", "detail-meta");
  meta.append(make("span", "", `Owner: ${item.owner || "Missing"}`), make("span", "", `Due: ${item.due_date}`), make("span", "", `Sources: ${item.evidence.length}`));
  target.append(meta);
  renderFindings(item, target);
  renderSources(item, target);
}

function renderReview() {
  const item = selectedItem();
  const panel = byId("review-panel");
  panel.replaceChildren();
  panel.append(make("p", "review-kicker", "Human review"), make("h2", "review-title", "Suggestion and decision"));
  const proposalIndex = appState.proposals.findIndex((proposal) => proposal.item_id === item.id);
  if (proposalIndex < 0) {
    panel.append(make("div", "empty-proposal", "No mock suggestion for this item. Its deterministic signals remain open for people to resolve."));
    renderDecisionHistory(item.id, panel);
    return;
  }

  const proposal = appState.proposals[proposalIndex];
  const validation = appState.proposal_validation[proposalIndex] || { valid: false, errors: ["Proposal was not validated."] };
  const history = decisionsFor(item.id);
  const latest = history[history.length - 1];
  const card = make("article", "proposal-card");
  const source = make("div", "proposal-source");
  source.append(make("span", "proposal-origin", proposal.source), make("span", "proposal-confidence", `Confidence ${proposal.confidence}`));
  card.append(source, make("p", "proposal-text", proposal.suggestion));
  const citationState = make("p", `citation-state${validation.valid ? "" : " invalid"}`, validation.valid ? "Citation verified against current source." : `Citation rejected: ${validation.errors.join("; ")}`);
  card.append(citationState);
  const citation = proposal.citation;
  card.append(make("code", "citation", `${citation.evidence_id}@${citation.revision}#${citation.locator}`));
  card.append(make("p", "uncertainty", proposal.uncertainty || "Uncertainty not stated."));
  if (latest) card.append(make("p", "decision-state", `Latest human decision: ${latest.action}. The work item state stays ${item.state}.`));
  panel.append(card);

  const form = make("form", "review-form");
  form.id = "review-form";
  const valueField = field("Edit the suggested value", "input", "review-value", proposal.suggestion);
  valueField.querySelector("input").autocomplete = "off";
  form.append(valueField);
  form.append(field("Reviewer label", "input", "reviewer", "Demo reviewer"));
  form.append(field("Rationale", "textarea", "rationale", "", "Explain your decision."));
  const actions = make("div", "action-grid");
  const actionSpecs = [["accept", "Accept", true], ["edit", "Edit value", false], ["reject", "Reject", false], ["unresolved", "Leave unresolved", false]];
  for (const [action, label, primary] of actionSpecs) {
    const button = make("button", `action-button${primary ? " primary" : ""}`, label);
    button.type = "button";
    button.dataset.action = action;
    button.disabled = !validation.valid;
    actions.append(button);
  }
  form.append(actions, make("p", "review-hint", "A rationale is required. Decisions are kept in memory until the server stops."));
  panel.append(form);
  renderDecisionHistory(item.id, panel);
}

function field(label, kind, id, initial, placeholder = "") {
  const wrapper = make("div", "field");
  const labelElement = make("label", "", label);
  labelElement.htmlFor = id;
  const input = kind === "textarea" ? make("textarea") : make("input");
  input.id = id;
  input.name = id;
  input.value = initial || "";
  input.placeholder = placeholder;
  if (id === "rationale") input.required = true;
  wrapper.append(labelElement, input);
  return wrapper;
}

function renderDecisionHistory(itemId, panel) {
  const history = decisionsFor(itemId);
  if (!history.length) return;
  const section = make("section", "history");
  section.append(make("h3", "", "Decision history"));
  for (const decision of [...history].reverse()) {
    const card = make("article", "history-item");
    const label = `${decision.action} � ${decision.reviewer} � ${decision.reviewed_at}`;
    card.append(make("strong", "", label));
    if (decision.value) card.append(make("p", "", `Value: ${decision.value}`));
    card.append(make("p", "", decision.rationale));
    section.append(card);
  }
  panel.append(section);
}

function render() {
  renderSummary();
  renderQueue();
  renderDetail();
  renderReview();
}

async function loadState() {
  const response = await fetch(stateUrl, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("The local demo could not load its fixture.");
  appState = await response.json();
  if (!appState.items.some((item) => item.id === selectedId)) selectedId = appState.items[0].id;
  render();
}

function announce(message, error = false) {
  const toast = byId("toast");
  toast.textContent = message;
  toast.style.background = error ? "#8d3d35" : "";
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 3200);
}

byId("queue-list").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-item-id]");
  if (!button) return;
  selectedId = button.dataset.itemId;
  render();
});

byId("review-panel").addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const form = byId("review-form");
  if (!form.reportValidity()) return;
  const value = form.elements["review-value"].value.trim();
  if (button.dataset.action === "edit" && !value) {
    announce("Enter the edited value first.", true);
    return;
  }
  button.disabled = true;
  try {
    const response = await fetch(reviewUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        item_id: selectedId,
        action: button.dataset.action,
        rationale: form.elements.rationale.value.trim(),
        reviewer: form.elements.reviewer.value.trim(),
        value,
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "The decision could not be recorded.");
    appState = result;
    render();
    announce("Human decision recorded. Item state unchanged.");
  } catch (error) {
    button.disabled = false;
    announce(error.message, true);
  }
});

loadState().catch((error) => {
  byId("item-detail").replaceChildren(make("div", "empty-proposal", error.message));
  byId("review-panel").replaceChildren(make("div", "empty-proposal", "Start the Python local server, then refresh this page."));
});

