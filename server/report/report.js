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

function pill(style, text) {
  return `<span class="pill ${style}">${escapeHtml(text)}</span>`;
}

function suggestion(value) {
  return {
    accept: pill("retain", "Accept"),
    reject: pill("revoke", "Reject"),
    review: pill("review", "Review"),
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
  const filter = byId("filter").value;
  const items = report.items.filter((item) =>
    filter === "all" || item.status === filter || (filter === "attention" && needsAttention(item)));
  byId("items").innerHTML = items.map((item) => {
    const original = item.original_recommendation.outcome;
    const recorded = item.receipt?.outcome;
    const result = recorded ? decision(recorded) : needsAttention(item)
      ? pill("warning", item.latest_attempt.status === "refresh_required" ? "Refresh required" : "Write failed")
      : pill("pending", "Pending");
    const expected = { accept: "retain", reject: "revoke" }[original];
    const changed = recorded && expected && recorded !== expected ? '<div class="changed">Differs from suggestion</div>' : "";
    const insights = escapeHtml(item.insight_categories.join(" · "));
    return `<tr>
      <td><button type="button" class="item-button" data-item="${escapeHtml(item.id)}"
        aria-label="${escapeHtml(item.person + ", " + item.entitlement + ", audit details")}">${escapeHtml(item.person)}</button>
        <div class="entitlement">${escapeHtml(item.entitlement)}</div></td>
      <td>${suggestion(original)}<div class="insight">${insights}</div></td><td>${result}${changed}</td>
    </tr>`;
  }).join("") || '<tr><td class="empty" colspan="3">No items in this view.</td></tr>';
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
      <div class="event-meta">${escapeHtml(item.person + " · " + item.id + receipt)}<br>
      ${escapeHtml(formatTime(event.attempted_at))} · Personal agent</div></div></li>`;
  }).join("") || '<li class="empty">No submission attempts yet. Decisions will appear here as the agent records them.</li>';
}

function renderDetail() {
  const item = report?.items.find((entry) => entry.id === selectedItem);
  if (!item) return;
  const recommendation = item.original_recommendation;
  const receipt = item.receipt;
  const attempt = item.latest_attempt;
  const section = (title, body) => `<section class="detail-section"><h3>${title}</h3>${body}</section>`;
  byId("detail-id").textContent = `${item.id} · SNAPSHOT V${item.snapshot_version}`;
  byId("detail-title").textContent = item.person;
  const original = section("Albus suggestion",
    `${suggestion(recommendation.outcome)} <span class="muted">Snapshot v${recommendation.snapshot_version}</span>
    <p class="insight">${escapeHtml(item.insight_categories.join(" · "))}</p>
    <p>${escapeHtml(recommendation.basis)}</p>`);
  const result = receipt ? section("Recorded decision",
    `${decision(receipt.outcome)}<p>${escapeHtml(receipt.reason)}</p>
    <p class="muted">Reviewer ${escapeHtml(report.reviewer.name)} · Snapshot v${receipt.snapshot_version}</p>
    <p class="muted">Receipt <code>${escapeHtml(receipt.receipt_id)}</code></p>
    <p class="muted">Remediation: no access changes in this simulation</p>`)
    : section("Decision status", pill(attempt ? "warning" : "pending", attempt
      ? attempt.status === "refresh_required" ? "Refresh required" : "Write failed" : "Awaiting decision"));
  const refs = receipt ? receipt.evidence : item.evidence_refs.map((id) => ({ id }));
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
  const percent = Math.round(100 * recorded / (items.length || 1));
  byId("campaign-title").textContent = campaign.title;
  byId("progress-count").textContent = `${recorded} of ${items.length} recorded`;
  byId("percentage").textContent = `${percent}%`;
  byId("progress").max = items.length || 1;
  byId("progress").value = recorded;
  byId("recorded").textContent = recorded;
  byId("pending").textContent = items.length - recorded;
  byId("attention").textContent = items.filter(needsAttention).length;
  byId("campaign-meta").textContent = `${campaign.id} · Reviewer ${reviewer.name} · As of ${campaign.as_of}`;
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
        byId("filter").value = "all";
        byId("detail").close();
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

byId("filter").addEventListener("change", renderRows);
byId("items").addEventListener("click", (event) => {
  const button = event.target.closest("[data-item]");
  if (!button) return;
  selectedItem = button.dataset.item;
  renderDetail();
  byId("detail").showModal();
});
refresh();
