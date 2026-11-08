"use strict";

const byId = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);
const formatTime = (value) => new Intl.DateTimeFormat(undefined, {
  hour: "numeric", minute: "2-digit", second: "2-digit",
}).format(new Date(value));

let report;
let signature;
let selectedItem;
let view = "pending";
let attentionOnly = false;
const selected = new Set();
let draft;

function pill(style, text) {
  return `<span class="pill ${style}">${escapeHtml(text)}</span>`;
}

function suggestion(value) {
  return {
    accept: '<span class="suggestion retain">Accept</span>',
    reject: '<span class="suggestion revoke">Reject</span>',
    review: '<span class="suggestion review">Review</span>',
  }[value];
}

function decisionLabel(value) {
  return value === "retain" ? "Approve" : "Reject";
}

function decision(value) {
  return pill(value === "retain" ? "retain" : "revoke", decisionLabel(value));
}

function needsAttention(item) {
  return !item.receipt && Boolean(item.latest_attempt);
}

function renderRows() {
  if (!report) return;
  const items = visibleItems();
  byId("items").innerHTML = items.map((item) => {
    const original = item.original_recommendation.outcome;
    const recorded = item.receipt?.outcome;
    const result = recorded ? decision(recorded) : needsAttention(item)
      ? pill("warning", item.latest_attempt.status === "refresh_required" ? "Refresh required" : "Write failed")
      : pill("pending", "Pending");
    const expected = { accept: "retain", reject: "revoke" }[original];
    const changed = recorded && expected && recorded !== expected
      ? '<div class="changed">Overrides Albus</div>' : "";
    const insights = item.insight_categories.map((label) => pill(
      label === "Role Aligned" ? "retain" : ["Overprivileged", "Terminated"].includes(label) ? "revoke" : "review", label
    )).join(" ");
    const id = escapeHtml(item.id);
    const person = escapeHtml(item.person);
    const permission = escapeHtml(item.entitlement);
    const label = `${person} · ${permission}`;
    const tour = report.campaign.id === "AD-REVIEW";
    const actions = recorded
      ? result
      : `<button type="button" class="action approve" data-action="retain" data-id="${id}" aria-label="Approve ${label}" title="Approve">✓</button>
         <button type="button" class="action reject" data-action="revoke" data-id="${id}" aria-label="Reject ${label}" title="Reject">×</button>
         ${needsAttention(item) ? result : ""}`;
    return `<tr>
      <td>${recorded ? "" : `<input type="checkbox" data-select="${id}" aria-label="Select ${person}, ${escapeHtml(item.entitlement)}" ${selected.has(item.id) ? "checked" : ""}>`}</td>
      <td><button type="button" class="item-button" data-item="${id}" aria-label="${label} details">${person}</button></td>
      <td>${escapeHtml(item.role)}</td>
      <td>${escapeHtml(item.team ?? "—")}</td>
      <td><div class="entitlement">${permission}</div>${item.privileged ? '<span class="privileged">Privileged</span>' : tour ? "" : `<div class="subline">Permission · v${item.snapshot_version}</div>`}</td>
      <td>${item.employment_status ? pill(item.employment_status === "Active" ? "retain" : "revoke", item.employment_status) : "—"}</td>
      <td class="insight-cell">${insights} <span>${escapeHtml(item.original_recommendation.basis)}</span></td>
      <td>${suggestion(original)}</td>
      <td><div class="row-actions">${actions}<button type="button" class="action note" data-item="${id}"
        aria-label="View evidence and audit note for ${label}" title="Evidence and audit note">▤</button></div>${changed}</td>
    </tr>`;
  }).join("") || '<tr><td class="empty" colspan="9">No permissions match this view.</td></tr>';
  byId("permission-count").textContent = `${items.length} ${items.length === 1 ? "Entitlement" : "Entitlements"}`;
  renderSelection();
}

function visibleItems() {
  const query = byId("search").value.trim().toLowerCase();
  const outcome = byId("suggestion-filter").value;
  return report.items.filter((item) =>
    (view === "all" || item.status === view) && (!attentionOnly || needsAttention(item)) &&
    (!outcome || item.original_recommendation.outcome === outcome) &&
    [item.person, item.entitlement, item.id, item.original_recommendation.outcome, ...item.insight_categories]
      .some((value) => value.toLowerCase().includes(query)));
}

function renderSelection() {
  const eligible = visibleItems().filter((item) => !item.receipt);
  const count = eligible.filter((item) => selected.has(item.id)).length;
  const all = byId("select-all");
  all.disabled = eligible.length === 0;
  all.checked = count > 0 && count === eligible.length;
  all.indeterminate = count > 0 && count < eligible.length;
  byId("bulk").hidden = count === 0;
  byId("selection-count").textContent = `${count} selected`;
}

function channel(client) {
  return {
    local_review_ui: "Review workspace",
    chatgpt_work: "ChatGPT Work",
    claude_cowork: "Claude Cowork",
  }[client] || "Codex MCP";
}

function setView(next) {
  view = next;
  selected.clear();
  attentionOnly = false;
  byId("attention").setAttribute("aria-pressed", "false");
  byId("review").hidden = view === "audit";
  byId("audit").hidden = view !== "audit";
  for (const tab of document.querySelectorAll("[data-view]")) {
    if (tab.dataset.view === view) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  }
  renderRows();
}

function renderEvents() {
  byId("event-count").textContent = report.events.length;
  const items = new Map(report.items.map((item) => [item.id, item]));
  byId("events").innerHTML = report.events.map((event) => {
    const recorded = event.status === "recorded";
    const item = items.get(event.item_id);
    const message = recorded ? `${decisionLabel(event.outcome)} decision recorded`
      : event.status === "refresh_required" ? `Write blocked · snapshot v${event.current_snapshot_version} required`
      : event.status.replaceAll("_", " ");
    const receipt = recorded ? ` · Receipt ${event.receipt_id.slice(0, 8)}` : "";
    return `<li><span aria-hidden="true" class="event-icon ${recorded ? "retain" : "warning"}">${recorded ? "✓" : "!"}</span>
      <div><div class="event-title">${escapeHtml(message)}</div>
      <button type="button" class="item-button" data-item="${escapeHtml(item.id)}">${escapeHtml(item.person + " · " + item.entitlement)}</button>
      <div class="event-meta">${escapeHtml(item.id + receipt)} · ${escapeHtml(formatTime(event.attempted_at))}
      · ${channel(event.client)}</div></div></li>`;
  }).join("") || '<li class="empty">No submission attempts yet. Decisions from either surface will appear here.</li>';
}

function renderDetail() {
  const item = report?.items.find((entry) => entry.id === selectedItem);
  if (!item) return;
  const recommendation = item.original_recommendation;
  const receipt = item.receipt;
  const attempt = item.latest_attempt;
  const section = (title, body) => `<section class="detail-section"><h3>${title}</h3>${body}</section>`;
  byId("detail-id").textContent = report.campaign.id === "AD-REVIEW"
    ? "Permission details" : `${item.id} · SNAPSHOT V${item.snapshot_version}`;
  byId("detail-title").textContent = item.person;
  const original = section("Albus suggestion",
    `${suggestion(recommendation.outcome)} <span class="muted">Snapshot v${recommendation.snapshot_version}</span>
    <p class="insight">${escapeHtml(item.insight_categories.join(" · "))}</p>
    <p>${escapeHtml(recommendation.basis)}</p>`);
  const personalContext = receipt?.context_summary
    ? `<p class="muted">Reviewer-approved context</p><p>${escapeHtml(receipt.context_summary)}</p>` : "";
  const result = receipt ? section("Recorded decision",
    `${decision(receipt.outcome)}<p>${escapeHtml(receipt.reason)}</p>
    ${personalContext}
    <p class="muted">Reviewer ${escapeHtml(report.reviewer.name)} · ${channel(receipt.client)} · Snapshot v${receipt.snapshot_version}</p>
    <p class="muted">Receipt <code>${escapeHtml(receipt.receipt_id)}</code></p>
    <p class="muted">Remediation: no access changes in this simulation</p>`)
    : section("Decision status", pill(attempt ? "warning" : "pending", attempt
      ? attempt.status === "refresh_required" ? "Refresh required" : "Write failed" : "Awaiting decision"));
  const refs = receipt ? receipt.evidence : item.evidence_sources;
  const sources = new Map(item.evidence_sources.map((source) => [source.id, source]));
  const evidence = section(receipt ? "Evidence on receipt" : "Current evidence",
    refs.map((ref) => {
      const source = sources.get(ref.id);
      if (!source) return `<p><code>${escapeHtml(ref.id)} · v${ref.version}</code> · Excerpt unavailable</p>`;
      const window = source.effective_to
        ? ` · Effective ${source.effective_from} to ${source.effective_to}` : "";
      return `<details class="source"><summary><code>${escapeHtml(source.id)} · v${source.version}</code> ${escapeHtml(source.title)}</summary>
        <p class="muted">${escapeHtml(source.source_system + window)}</p>
        <p>${escapeHtml(source.excerpt)}</p></details>`;
    }).join(""));
  byId("detail-body").innerHTML = `<p class="entitlement">${escapeHtml(item.entitlement)}</p>${original}${result}${evidence}`;
}

function render() {
  const { items, campaign, reviewer } = report;
  const recorded = items.filter((item) => item.receipt).length;
  const failures = items.filter(needsAttention).length;
  byId("campaign-title").textContent = campaign.title;
  const app = campaign.id === "AD-REVIEW" ? `${campaign.app} (Demo)` : campaign.app;
  byId("app-title").textContent = app;
  byId("breadcrumb-app").textContent = app;
  byId("review-status").textContent = recorded === items.length ? "· Complete" : "· In Review";
  byId("progress-count").textContent = `${recorded} of ${items.length} recorded`;
  byId("total").textContent = items.length;
  byId("recorded").textContent = recorded;
  byId("pending").textContent = items.length - recorded;
  byId("attention").textContent = `${failures} needing attention`;
  byId("attention").hidden = !failures;
  if (!failures) {
    attentionOnly = false;
    byId("attention").setAttribute("aria-pressed", "false");
  }
  for (const item of items) if (item.receipt) selected.delete(item.id);
  byId("campaign-meta").textContent = `Reviewer: ${reviewer.name} · As of ${campaign.as_of}`;
  byId("run").textContent = `Demo run ${report.run_id.slice(0, 8)} · No live remediation`;
  renderRows();
  renderEvents();
  if (byId("detail").open) renderDetail();
}

function setConnection(status, label) {
  const connection = byId("connection");
  connection.className = `connection ${status}`;
  if (connection.lastElementChild.textContent !== label) connection.lastElementChild.textContent = label;
}

async function refresh() {
  try {
    const response = await fetch("/api/report", { signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error("Report unavailable");
    const nextSignature = await response.text();
    if (nextSignature !== signature) {
      const next = JSON.parse(nextSignature);
      if (report && next.run_id !== report.run_id) {
        byId("search").value = "";
        byId("notice").hidden = true;
        byId("detail").close();
        byId("confirm").close();
        byId("suggestion-filter").value = "";
        setView("pending");
      }
      report = next;
      render();
      signature = nextSignature;
    }
    setConnection("live", "Live sync");
  } catch {
    setConnection("offline", report ? "Disconnected · last known state" : "Report unavailable");
  } finally {
    window.setTimeout(refresh, 1000);
  }
}

function openDetail(event) {
  const button = event.target.closest("[data-item]");
  if (!button) return;
  selectedItem = button.dataset.item;
  renderDetail();
  byId("detail").showModal();
}

function openDecision(outcome, items) {
  if (!items.length) return;
  draft = { outcome, items, runId: report.run_id, key: crypto.randomUUID() };
  byId("confirm-title").textContent = `${decisionLabel(outcome)} ${items.length === 1 ? "permission" : `${items.length} permissions`}`;
  byId("confirm-items").innerHTML = items.map((item) =>
    `<li><strong>${escapeHtml(item.person)}</strong> · ${escapeHtml(item.entitlement)} · v${item.snapshot_version}</li>`).join("");
  byId("reason").value = "";
  byId("confirm-error").textContent = "";
  byId("evidence-picker").hidden = items.length !== 1;
  const item = items[0];
  byId("evidence-options").innerHTML = items.length === 1 ? item.evidence_sources.map((source) =>
    `<label><input type="checkbox" value="${escapeHtml(source.id)}" ${item.evidence_refs.includes(source.id) ? "checked" : ""}>
      ${escapeHtml(source.title)} · ${escapeHtml(source.id)} v${source.version}</label>`).join("") : "";
  byId("confirm").showModal();
}

async function recordDecision(event) {
  event.preventDefault();
  const button = byId("confirm-action");
  const error = byId("confirm-error");
  const reason = byId("reason").value.trim();
  const evidence = Array.from(document.querySelectorAll("#evidence-options input:checked"), (input) => input.value);
  if (!reason || (draft.items.length === 1 && !evidence.length)) {
    error.textContent = "Add an audit note and cite at least one evidence source.";
    return;
  }
  const request = {
    review_id: report.campaign.id, run_id: draft.runId, idempotency_key: draft.key, reviewer_confirmed: true,
    decisions: draft.items.map((item) => ({
      item_id: item.id, snapshot_version: item.snapshot_version, outcome: draft.outcome, reason,
      evidence_refs: draft.items.length === 1 ? evidence : item.evidence_refs,
    })),
  };
  button.disabled = true;
  error.textContent = "";
  try {
    const response = await fetch("/api/decisions", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request),
      signal: AbortSignal.timeout(10000),
    });
    const result = await response.json();
    if (request.run_id !== report.run_id) return;
    if (!response.ok) throw new Error(result.error || "Decision could not be recorded.");
    const recorded = result.results.filter((entry) => entry.status === "recorded").length;
    const failures = result.results.filter((entry) => entry.status !== "recorded");
    for (const entry of result.results) selected.delete(entry.item_id);
    byId("confirm").close();
    const notice = byId("notice");
    notice.textContent = `${recorded} recorded.` + (failures.length
      ? " " + failures.map((entry) => `${entry.item_id}: ${entry.status.replaceAll("_", " ")}`).join(" · ") : "");
    notice.hidden = false;
  } catch (failure) {
    if (request.run_id === report.run_id) error.textContent = failure.message;
  } finally {
    button.disabled = false;
  }
}

document.querySelector(".tabs").addEventListener("click", (event) => {
  const tab = event.target.closest("[data-view]");
  if (tab) setView(tab.dataset.view);
});
byId("search").addEventListener("input", () => { selected.clear(); renderRows(); });
byId("toggle-filters").addEventListener("click", () => {
  const filters = byId("filters");
  filters.hidden = !filters.hidden;
  byId("toggle-filters").setAttribute("aria-expanded", String(!filters.hidden));
  byId("toggle-filters").textContent = filters.hidden ? "Show Filters" : "Hide Filters";
});
byId("suggestion-filter").addEventListener("change", () => { selected.clear(); renderRows(); });
byId("attention").addEventListener("click", () => {
  attentionOnly = !attentionOnly;
  selected.clear();
  byId("attention").setAttribute("aria-pressed", String(attentionOnly));
  renderRows();
});
byId("clear-selection").addEventListener("click", () => { selected.clear(); renderRows(); });
byId("select-all").addEventListener("change", (event) => {
  selected.clear();
  if (event.target.checked) for (const item of visibleItems()) if (!item.receipt) selected.add(item.id);
  renderRows();
});
byId("items").addEventListener("change", (event) => {
  const id = event.target.dataset.select;
  if (!id) return;
  if (event.target.checked) selected.add(id);
  else selected.delete(id);
  renderSelection();
});
byId("items").addEventListener("click", (event) => {
  const action = event.target.closest("[data-action]");
  if (action) openDecision(action.dataset.action, report.items.filter((item) => item.id === action.dataset.id && !item.receipt));
  else openDetail(event);
});
byId("events").addEventListener("click", openDetail);
byId("bulk").addEventListener("click", (event) => {
  const action = event.target.closest("[data-bulk]");
  if (action) openDecision(action.dataset.bulk, visibleItems().filter((item) => selected.has(item.id) && !item.receipt));
});
byId("confirm-form").addEventListener("submit", recordDecision);
byId("cancel").addEventListener("click", () => {
  if (!byId("confirm-action").disabled) byId("confirm").close();
});
byId("confirm").addEventListener("cancel", (event) => {
  if (byId("confirm-action").disabled) event.preventDefault();
});
refresh();
