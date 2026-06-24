const BADGE_CLASS = "checkeverything-badge";
const WRAP_CLASS = "checkeverything-badge-wrap";

const MODE_COPY = {
  code: {
    subtitle: "Code review reliability",
    panelTitle: "AI Review Trust Breakdown",
    panelSubtitle: "Code Review Trust Score",
    disclaimer:
      "This score reflects code review quality from 5 specialist agents, not factual citation checking.",
    roadmap:
      "For general AI answers without code, CheckEverything runs preliminary credibility analysis.",
  },
  trust: {
    subtitle: "Preliminary credibility signal",
    panelTitle: "AI Response Trust Breakdown",
    panelSubtitle: "Preliminary Trust Analysis",
    disclaimer:
      "Preliminary trust analysis with claim-to-source matching against fetched source excerpts.",
    roadmap:
      "Some sites block extraction or require JavaScript. Unavailable sources are labeled honestly.",
  },
};

const CATEGORY_LABELS = {
  claim_support: "Claim Support",
  source_quality: "Source Quality",
  citation_accuracy: "Citation Accuracy",
  freshness: "Freshness",
  bias_context: "Bias / Missing Context",
};

const SUPPORT_LABEL_LABELS = {
  supported: "Supported",
  weakly_supported: "Weakly supported",
  not_supported: "Not supported",
  unclear: "Unclear",
  source_unavailable: "Source unavailable",
};

function sourceDomain(url) {
  if (!url) return null;
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function extractCodeBlocks(element) {
  const blocks = [];
  element.querySelectorAll("pre code, pre").forEach((el) => {
    const text = el.textContent?.trim();
    if (text && text.length > 20) blocks.push(text);
  });
  return blocks;
}

function extractUrls(element) {
  const urls = [];
  element.querySelectorAll('a[href^="http"]').forEach((a) => {
    const href = a.href;
    if (href && !urls.includes(href)) urls.push(href);
  });
  return urls;
}

function extractResponseText(element) {
  const clone = element.cloneNode(true);
  clone.querySelectorAll(`.${WRAP_CLASS}`).forEach((n) => n.remove());
  clone.querySelectorAll(".checkeverything-panel").forEach((n) => n.remove());
  return clone.textContent?.trim() || "";
}

function detectMode(messageEl) {
  const codeBlocks = extractCodeBlocks(messageEl);
  if (codeBlocks.length > 0) {
    return {
      mode: "code",
      code: codeBlocks.join("\n\n"),
      language: "python",
    };
  }
  return {
    mode: "trust",
    text: extractResponseText(messageEl),
    urls: extractUrls(messageEl),
  };
}

function createBadgeWrap(mode) {
  const copy = MODE_COPY[mode];
  const wrap = document.createElement("div");
  wrap.className = WRAP_CLASS;
  wrap.dataset.mode = mode;

  const badge = document.createElement("button");
  badge.className = BADGE_CLASS;
  badge.type = "button";
  badge.textContent = "🛡️ Trust Score";
  badge.title = `Analyze ${copy.subtitle} with CheckEverything`;

  const subtitle = document.createElement("span");
  subtitle.className = "checkeverything-badge-subtitle";
  subtitle.textContent = copy.subtitle;

  const detailsBtn = document.createElement("button");
  detailsBtn.className = "checkeverything-details-btn";
  detailsBtn.type = "button";
  detailsBtn.textContent = "View Details";
  detailsBtn.hidden = true;

  wrap.append(badge, subtitle, detailsBtn);
  return { wrap, badge, subtitle, detailsBtn };
}

function renderSourceSummary(summary) {
  if (!summary) return "";
  const lines = [
  `<div class="checkeverything-source-stats">
    <div><strong>Sources checked:</strong> ${summary.sources_checked}</div>
    <div><strong>Reachable:</strong> ${summary.reachable_count}/${summary.sources_checked}</div>
    <div><strong>Primary/official sources:</strong> ${summary.primary_official_count}</div>
  </div>`,
  ];
  if (summary.issues?.length) {
    lines.push(
      `<ul class="checkeverything-source-issues">${summary.issues
        .map((issue) => `<li>${escapeHtml(issue)}</li>`)
        .join("")}</ul>`
    );
  }
  return lines.join("");
}

function renderSourcesList(sources) {
  if (!sources?.length) return "";
  const rows = sources
    .map(
      (source) => `
      <li class="checkeverything-source-item ${source.reachable ? "" : "checkeverything-source-unreachable"}">
        <div class="checkeverything-source-url">${escapeHtml(source.domain)}</div>
        <div class="checkeverything-source-meta">
          ${source.reachable ? "Reachable" : "Unreachable"}
          · ${escapeHtml(source.source_quality)}
        </div>
        ${source.title ? `<div class="checkeverything-source-title">${escapeHtml(source.title)}</div>` : ""}
        ${source.notes ? `<div class="checkeverything-source-note">${escapeHtml(source.notes)}</div>` : ""}
      </li>
    `
    )
    .join("");
  return `<ul class="checkeverything-sources">${rows}</ul>`;
}

function renderTrustPanel(data) {
  const copy = MODE_COPY.trust;
  const categories = data.categories || {};
  const claims = data.claims || [];

  const categoryRows = Object.entries(CATEGORY_LABELS)
    .map(([key, label]) => {
      const cat = categories[key];
      if (!cat) return "";
      return `
        <tr>
          <td>${escapeHtml(label)}</td>
          <td class="checkeverything-cat-score">${cat.score}%</td>
          <td>${escapeHtml(cat.summary || "")}</td>
        </tr>
      `;
    })
    .join("");

  const claimRows = claims
    .map((claim) => {
      const status =
        SUPPORT_LABEL_LABELS[claim.support_label] ||
        SUPPORT_LABEL_LABELS[claim.status] ||
        claim.status;
      const matchedDomain = sourceDomain(claim.matched_source);
      const note = claim.evidence_note || claim.note;
      return `
        <li class="checkeverything-claim checkeverything-claim-${claim.support_label || claim.status}">
          <div class="checkeverything-claim-label">Claim</div>
          <div class="checkeverything-claim-text">${escapeHtml(claim.text)}</div>
          <div class="checkeverything-claim-meta"><strong>Status:</strong> ${escapeHtml(status)}</div>
          ${matchedDomain ? `<div class="checkeverything-claim-source"><strong>Source:</strong> ${escapeHtml(matchedDomain)}</div>` : ""}
          ${note ? `<div class="checkeverything-claim-note"><strong>Note:</strong> ${escapeHtml(note)}</div>` : ""}
        </li>
      `;
    })
    .join("");

  return `
    <div class="checkeverything-panel-header">
      <div>
        <strong>${copy.panelTitle}</strong>
        <div class="checkeverything-panel-subtitle">${copy.panelSubtitle}</div>
      </div>
      <span class="checkeverything-score">${data.overall_score ?? "—"}%</span>
      <button class="checkeverything-close" type="button" aria-label="Close">×</button>
    </div>
    <p class="checkeverything-disclaimer">${copy.disclaimer}</p>
    <p class="checkeverything-roadmap-note">${copy.roadmap}</p>
    <p class="checkeverything-headline">${escapeHtml(data.headline || "")}</p>
    <p class="checkeverything-summary">${escapeHtml(data.support_summary || "")}</p>
    <table class="checkeverything-category-table">
      <thead>
        <tr><th>Category</th><th>Score</th><th>Meaning</th></tr>
      </thead>
      <tbody>${categoryRows}</tbody>
    </table>
    ${renderSourceSummary(data.source_summary)}
    ${renderSourcesList(data.sources)}
    ${claims.length ? `<ul class="checkeverything-claims">${claimRows}</ul>` : ""}
    <small>Analysis type: ${escapeHtml(data.analysis_type || "preliminary")}</small>
  `;
}

function renderCodePanel(data) {
  const copy = MODE_COPY.code;
  const report = data.report;
  const score = report?.overall_score ?? "—";
  const verdict = (report?.verdict ?? "unknown").replace(/_/g, " ");

  return `
    <div class="checkeverything-panel-header">
      <div>
        <strong>${copy.panelTitle}</strong>
        <div class="checkeverything-panel-subtitle">${copy.panelSubtitle}</div>
      </div>
      <span class="checkeverything-score">${score}/100</span>
      <button class="checkeverything-close" type="button" aria-label="Close">×</button>
    </div>
    <p class="checkeverything-disclaimer">${copy.disclaimer}</p>
    <p class="checkeverything-roadmap-note">${copy.roadmap}</p>
    <div class="checkeverything-verdict">${escapeHtml(verdict)}</div>
    <p class="checkeverything-summary">${escapeHtml(report?.executive_summary || "")}</p>
    <div class="checkeverything-agents">
      ${(report?.agent_reports || [])
        .map((a) => `<span>${escapeHtml(a.agent_name)}: ${a.score}</span>`)
        .join("")}
    </div>
    <small>Pipeline: ${escapeHtml(data.pipeline || "—")}</small>
  `;
}

function getScoreFromResult(result) {
  if (result.mode === "trust") return result.overall_score ?? "?";
  return result.report?.overall_score ?? "?";
}

function showPanel(anchor, result) {
  document.querySelectorAll(".checkeverything-panel").forEach((p) => p.remove());

  const panel = document.createElement("div");
  panel.className = "checkeverything-panel";
  panel.innerHTML =
    result.mode === "trust" ? renderTrustPanel(result) : renderCodePanel(result);
  panel.querySelector(".checkeverything-close").onclick = () => panel.remove();
  anchor.insertAdjacentElement("afterend", panel);
}

function attachBadge(messageEl) {
  if (messageEl.querySelector(`.${WRAP_CLASS}`)) return;

  const detected = detectMode(messageEl);
  const { wrap, badge, detailsBtn } = createBadgeWrap(detected.mode);
  let lastResult = null;

  messageEl.style.position = "relative";
  messageEl.prepend(wrap);

  detailsBtn.addEventListener("click", () => {
    if (lastResult) showPanel(wrap, lastResult);
  });

  badge.addEventListener("click", () => {
    if (lastResult) {
      showPanel(wrap, lastResult);
      return;
    }

    badge.textContent = "Analyzing response…";
    badge.disabled = true;
    detailsBtn.hidden = true;

    const payload =
      detected.mode === "code"
        ? { type: "review", code: detected.code, language: detected.language }
        : { type: "analyze", text: detected.text, urls: detected.urls };

    chrome.runtime.sendMessage(payload, (response) => {
      badge.disabled = false;
      if (!response?.ok) {
        badge.textContent = "⚠️ Error";
        badge.title = response?.error || "Analysis failed";
        return;
      }
      lastResult = response.data;
      const score = getScoreFromResult(lastResult);
      badge.textContent = `🛡️ Trust Score: ${score}%`;
      badge.title = MODE_COPY[lastResult.mode].disclaimer;
      detailsBtn.hidden = false;
      showPanel(wrap, lastResult);
    });
  });
}

function scanMessages() {
  document
    .querySelectorAll('[data-message-author-role="assistant"]')
    .forEach(attachBadge);
}

const observer = new MutationObserver(() => scanMessages());
observer.observe(document.body, { childList: true, subtree: true });
scanMessages();
