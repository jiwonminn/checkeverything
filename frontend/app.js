const SAMPLE_CODE = `import sqlite3

SECRET_KEY = "hardcoded-secret"

def login(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    return cursor.fetchone()

def process_items(items):
    total = 0
    for i in range(len(items) + 1):
        total += items[i]
    return total
`;

const SAMPLE_DIFF = `diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,6 +1,10 @@
 import sqlite3
+SECRET_KEY = "hardcoded-secret"
 def login(username, password):
     conn = sqlite3.connect("users.db")
-    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
+    query = f"SELECT * FROM users WHERE username = '{username}'"
+    cursor.execute(query)
     return cursor.fetchone()
+def save_config(data):
+    exec(data)
`;

const AGENTS = [
  "Security Agent",
  "Correctness Agent",
  "Readability Agent",
  "Performance Agent",
  "Test Coverage Agent",
];

let submissionMode = "code";

const codeEl = document.getElementById("code");
const diffEl = document.getElementById("diff");
const languageEl = document.getElementById("language");
const contextEl = document.getElementById("context");
const submitBtn = document.getElementById("submit");
const loadSampleBtn = document.getElementById("load-sample");
const loadDiffSampleBtn = document.getElementById("load-diff-sample");
const diffFileEl = document.getElementById("diff-file");
const diffSummaryEl = document.getElementById("diff-summary");
const errorEl = document.getElementById("error");
const resultsEl = document.getElementById("results");
const progressEl = document.getElementById("progress");
const charCountEl = document.getElementById("char-count");

const agentState = new Map(AGENTS.map((a) => [a, { status: "pending", report: null }]));

document.querySelectorAll(".sub-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    submissionMode = tab.dataset.mode;
    document.querySelectorAll(".sub-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".mode-panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`mode-${submissionMode}`).classList.add("active");
    updateCharCount();
  });
});

loadSampleBtn.addEventListener("click", () => {
  submissionMode = "code";
  document.querySelector('[data-mode="code"]').click();
  codeEl.value = SAMPLE_CODE;
  languageEl.value = "python";
  contextEl.value = "Demo: auth helper with known issues";
  updateCharCount();
});

loadDiffSampleBtn.addEventListener("click", () => {
  submissionMode = "diff";
  document.querySelector('[data-mode="diff"]').click();
  diffEl.value = SAMPLE_DIFF;
  parseDiffPreview();
  updateCharCount();
});

diffFileEl.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  diffEl.value = await file.text();
  submissionMode = "diff";
  document.querySelector('[data-mode="diff"]').click();
  parseDiffPreview();
  updateCharCount();
});

codeEl.addEventListener("input", updateCharCount);
diffEl.addEventListener("input", () => {
  updateCharCount();
  parseDiffPreview();
});

submitBtn.addEventListener("click", runReviewStream);

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
  });
});

async function parseDiffPreview() {
  const diff = diffEl.value.trim();
  if (!diff) {
    diffSummaryEl.classList.add("hidden");
    return;
  }
  try {
    const res = await fetch("/api/parse-diff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ diff }),
    });
    const data = await res.json();
    if (res.ok) {
      diffSummaryEl.textContent = data.context_note;
      diffSummaryEl.classList.remove("hidden");
      if (data.language) languageEl.value = data.language;
    }
  } catch {
    diffSummaryEl.classList.add("hidden");
  }
}

function buildPayload() {
  const base = {
    language: languageEl.value,
    context: contextEl.value.trim(),
    submission_type: submissionMode,
  };
  if (submissionMode === "diff") {
    return { ...base, diff: diffEl.value.trim(), code: "" };
  }
  return { ...base, code: codeEl.value.trim(), diff: "" };
}

function updateCharCount() {
  const n = submissionMode === "diff" ? diffEl.value.length : codeEl.value.length;
  charCountEl.textContent = `${n.toLocaleString()} chars`;
  charCountEl.classList.toggle("warn", n > 40000);
}

async function runReviewStream() {
  const payload = buildPayload();
  if (submissionMode === "code" && !payload.code) {
    showError("Please paste some code to review.");
    return;
  }
  if (submissionMode === "diff" && !payload.diff) {
    showError("Please paste or upload a PR diff.");
    return;
  }

  resetAgentState();
  setLoading(true);
  hideError();
  resultsEl.classList.remove("hidden");
  showProgress();
  renderAgentGrid();
  clearResults();

  try {
    const res = await fetch("/api/review/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Review request failed");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";
      for (const chunk of lines) {
        const line = chunk.trim();
        if (!line.startsWith("data: ")) continue;
        handleStreamEvent(JSON.parse(line.slice(6)));
      }
    }
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
    hideProgress();
  }
}

function handleStreamEvent(event) {
  switch (event.type) {
    case "status":
      setProgressMessage(event.message);
      break;
    case "agent_start":
      agentState.set(event.agent, { status: "running", report: null });
      renderAgentGrid();
      setProgressMessage(`${event.agent} analyzing…`);
      break;
    case "agent_complete":
      agentState.set(event.report.agent_name, { status: "done", report: event.report });
      renderAgentGrid();
      appendFindingsForAgent(event.report);
      break;
    case "coordinator_start":
      setProgressMessage(event.message || "Coordinator synthesizing…");
      break;
    case "fallback":
      setProgressMessage(event.message);
      break;
    case "complete":
      renderResults(event.data);
      break;
    case "error":
      showError(event.message);
      break;
  }
}

function resetAgentState() {
  AGENTS.forEach((a) => agentState.set(a, { status: "pending", report: null }));
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  submitBtn.querySelector(".btn-text").textContent = loading
    ? "5 agents analyzing…"
    : "Run 5-Agent Review";
  submitBtn.querySelector(".btn-spinner").classList.toggle("hidden", !loading);
}

function showProgress() {
  progressEl.classList.remove("hidden");
  progressEl.innerHTML = '<div class="progress-msg">Initializing agents…</div>';
}

function hideProgress() {
  progressEl.classList.add("hidden");
}

function setProgressMessage(msg) {
  progressEl.innerHTML = `<div class="progress-msg">${escapeHtml(msg)}</div>`;
}

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove("hidden");
}

function hideError() {
  errorEl.classList.add("hidden");
}

function clearResults() {
  document.getElementById("overall-score").textContent = "—";
  document.getElementById("verdict-badge").textContent = "—";
  document.getElementById("executive-summary").textContent = "Waiting for coordinator…";
  document.getElementById("findings-list").innerHTML = "";
  document.getElementById("action-list").innerHTML = "";
  document.getElementById("markdown-report").innerHTML = "";
  document.getElementById("meta-bar").classList.add("hidden");
}

function renderAgentGrid() {
  document.getElementById("agent-grid").innerHTML = AGENTS.map((name) => {
    const state = agentState.get(name) || { status: "pending" };
    const score = state.report?.score ?? "—";
    const count = state.report?.findings?.length ?? "—";
    return `
      <div class="agent-card status-${state.status}">
        <div class="agent-status-icon">${statusIcon(state.status)}</div>
        <h3>${escapeHtml(shortName(name))}</h3>
        <div class="agent-score">${score}</div>
        <div class="finding-count">${count === "—" ? "pending" : `${count} finding(s)`}</div>
      </div>`;
  }).join("");
}

function shortName(name) {
  return name.replace(" Agent", "");
}

function statusIcon(status) {
  if (status === "done") return "✓";
  if (status === "running") return "◌";
  return "·";
}

function appendFindingsForAgent(report) {
  const list = document.getElementById("findings-list");
  const section = document.createElement("section");
  section.className = "findings-agent-section";
  section.innerHTML = `
    <h3 class="findings-agent-title">${escapeHtml(report.agent_name)}
      <span class="score-pill">${report.score}/100</span></h3>
    <p class="findings-summary">${escapeHtml(report.summary)}</p>
    ${(report.findings || []).map((f) => `
      <article class="finding-card severity-${f.severity}">
        <div class="finding-header">
          <span class="severity-badge">${escapeHtml(f.severity)}</span>
          <strong>${escapeHtml(f.title)}</strong>
        </div>
        ${f.line_hint ? `<div class="line-hint">📍 ${escapeHtml(f.line_hint)}</div>` : ""}
        <p>${escapeHtml(f.description)}</p>
        <div class="recommendation"><strong>Fix:</strong> ${escapeHtml(f.recommendation)}</div>
      </article>`).join("")}
  `;
  list.appendChild(section);
}

function renderResults(wrapper) {
  const data = wrapper.report || wrapper;
  const meta = wrapper.report ? wrapper : null;

  document.getElementById("overall-score").textContent = data.overall_score;
  const badge = document.getElementById("verdict-badge");
  badge.textContent = formatVerdict(data.verdict);
  badge.className = `verdict-badge verdict-${data.verdict}`;
  document.getElementById("executive-summary").textContent = data.executive_summary;

  if (meta) {
    document.getElementById("meta-bar").classList.remove("hidden");
    document.getElementById("pipeline-badge").textContent =
      `Pipeline: ${meta.pipeline.toUpperCase()} · ${meta.google_technologies.join(" + ")}`;
    document.getElementById("duration-badge").textContent =
      `${meta.model} · ${meta.duration_ms}ms`;
  }

  (data.agent_reports || []).forEach((r) => {
    if (!agentState.get(r.agent_name)?.report) {
      agentState.set(r.agent_name, { status: "done", report: r });
    }
  });
  renderAgentGrid();

  if (!document.getElementById("findings-list").children.length) {
    (data.agent_reports || []).forEach(appendFindingsForAgent);
  }

  document.getElementById("markdown-report").innerHTML = renderMarkdown(data.markdown_report || "");
  document.getElementById("action-list").innerHTML = (data.action_items || []).map((item) => `
    <li class="action-item">
      <div class="priority priority-${item.priority}">${formatPriority(item.priority)}</div>
      <div class="category">${escapeHtml(item.category)}</div>
      <div class="action-text">${escapeHtml(item.action)}</div>
      <div class="rationale">${escapeHtml(item.rationale)}</div>
    </li>`).join("");
  document.querySelector("#json-output code").textContent = JSON.stringify(meta || data, null, 2);
}

function formatVerdict(v) {
  return { approve: "Approve", request_changes: "Request Changes", reject: "Reject" }[v] || v;
}

function formatPriority(p) {
  return { must_fix: "Must Fix", should_fix: "Should Fix", nice_to_have: "Nice to Have" }[p] || p;
}

function escapeHtml(str) {
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function renderMarkdown(md) {
  return escapeHtml(md)
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^(?!<[hul])/gm, (line) => (line.trim() ? `<p>${line}</p>` : ""))
    .replace(/<p><\/p>/g, "");
}

updateCharCount();
