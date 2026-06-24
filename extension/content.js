const BADGE_CLASS = "checkeverything-badge";
const WRAP_CLASS = "checkeverything-badge-wrap";
const ATTACHED_ATTR = "data-checkeverything-attached";

const OVERVIEW_MIN_TEXT = 80;
const OVERVIEW_MAX_TEXT = 20000;

const platform = getPlatform();

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
};

const TRUST_COPY = {
  chatgpt: {
    subtitle: "Preliminary credibility signal",
    panelTitle: "AI Response Trust Breakdown",
    panelSubtitle: "Preliminary Trust Analysis",
    disclaimer:
      "Preliminary trust analysis with claim-to-source matching against fetched source excerpts.",
    roadmap:
      "Some sites block extraction or require JavaScript. Unavailable sources are labeled honestly.",
  },
  google_ai_overview: {
    subtitle: "Preliminary credibility signal",
    panelTitle: "AI Response Trust Breakdown",
    panelSubtitle: "Google AI Overview Trust Check",
    disclaimer:
      "Preliminary trust analysis of Google AI Overview text and cited sources. DOM extraction may vary by region.",
    roadmap:
      "Google AI Overview layout changes often. Analysis runs only when you click Trust Score.",
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
  not_supported: "Not clearly supported",
  unclear: "Unclear",
  source_unavailable: "Source unavailable",
};

const CLAIM_DISPLAY = {
  supported: { icon: "✓", label: "Supported", priority: 4 },
  weakly_supported: { icon: "~", label: "Weakly supported", priority: 1 },
  not_supported: { icon: "!", label: "Not clearly supported", priority: 0 },
  unclear: { icon: "?", label: "Unclear", priority: 2 },
  source_unavailable: { icon: "×", label: "Source unavailable", priority: 3 },
};

const CONFIDENCE_DISPLAY = {
  high: {
    label: "High confidence",
    fallbackNote: "Source directly supports the claim.",
  },
  medium: {
    label: "Medium confidence",
    fallbackNote: "Source is related but does not fully prove the claim.",
  },
  low: {
    label: "Low confidence",
    fallbackNote: "Source unavailable or does not clearly support the claim.",
  },
};

const SUPPORT_TO_CONFIDENCE = {
  supported: "high",
  weakly_supported: "medium",
  unclear: "medium",
  not_supported: "low",
  source_unavailable: "low",
};

const STATUS_TO_SUPPORT = {
  strongly_supported: "supported",
  weakly_supported: "weakly_supported",
  unsupported: "not_supported",
  unclear: "unclear",
  outdated: "unclear",
};

function getClaimSupportKey(claim) {
  return claim.support_label || STATUS_TO_SUPPORT[claim.status] || "unclear";
}

function getClaimDisplay(claim) {
  return CLAIM_DISPLAY[getClaimSupportKey(claim)] || CLAIM_DISPLAY.unclear;
}

function getConfidenceDisplay(claim) {
  const level = claim.confidence_level || SUPPORT_TO_CONFIDENCE[getClaimSupportKey(claim)] || "low";
  const meta = CONFIDENCE_DISPLAY[level] || CONFIDENCE_DISPLAY.low;
  const note = claim.confidence_note || meta.fallbackNote;
  return { level, label: meta.label, note };
}

function sortClaimsForDisplay(claims) {
  return [...claims].sort((a, b) => getClaimDisplay(a).priority - getClaimDisplay(b).priority);
}

function renderClaimSummary(claims) {
  if (!claims.length) return "";
  const counts = {};
  claims.forEach((claim) => {
    const key = getClaimSupportKey(claim);
    counts[key] = (counts[key] || 0) + 1;
  });
  const pills = Object.entries(CLAIM_DISPLAY)
    .filter(([key]) => counts[key])
    .map(
      ([key, display]) =>
        `<span class="checkeverything-claim-pill checkeverything-claim-pill-${key}">${display.icon} ${counts[key]} ${display.label}</span>`
    )
    .join("");
  return `<div class="checkeverything-claim-summary">${pills}</div>`;
}

function getPlatform() {
  if (location.pathname.includes("/demo/google")) {
    return "google_ai_overview";
  }
  if (location.pathname.includes("/demo/chatgpt")) {
    return "chatgpt";
  }
  if (location.hostname.includes("google.") && location.pathname.startsWith("/search")) {
    return "google_ai_overview";
  }
  return "chatgpt";
}

function getTrustCopy(resultPlatform) {
  return TRUST_COPY[resultPlatform] || TRUST_COPY.chatgpt;
}

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

function normalizeUrl(href) {
  try {
    const url = new URL(href, location.origin);
    if (url.hostname.includes("google.") && url.pathname === "/url") {
      return url.searchParams.get("q") || url.searchParams.get("url") || href;
    }
    if (url.protocol === "http:" || url.protocol === "https:") {
      return url.href;
    }
  } catch {
    return null;
  }
  return null;
}

function extractUrls(element) {
  const urls = [];
  element.querySelectorAll("a[href]").forEach((anchor) => {
    const normalized = normalizeUrl(anchor.href);
    if (normalized && !urls.includes(normalized)) urls.push(normalized);
  });
  return urls;
}

function extractContainerText(element) {
  const clone = element.cloneNode(true);
  clone.querySelectorAll(`.${WRAP_CLASS}, .checkeverything-panel`).forEach((node) => node.remove());
  return clone.textContent?.replace(/\s+/g, " ").trim() || "";
}

function extractCodeBlocks(element) {
  const blocks = [];
  element.querySelectorAll("pre code, pre").forEach((el) => {
    const text = el.textContent?.trim();
    if (text && text.length > 20) blocks.push(text);
  });
  return blocks;
}

function detectChatGPTMode(messageEl) {
  const codeBlocks = extractCodeBlocks(messageEl);
  if (codeBlocks.length > 0) {
    return {
      mode: "code",
      code: codeBlocks.join("\n\n"),
      language: "python",
      source: "chatgpt",
    };
  }
  return {
    mode: "trust",
    text: extractContainerText(messageEl),
    urls: extractUrls(messageEl),
    source: "chatgpt",
  };
}

function findAiOverviewLabelElements() {
  const matches = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const value = walker.currentNode.textContent?.trim();
    if (value && /^AI Overview$/i.test(value)) {
      const parent = walker.currentNode.parentElement;
      if (parent) matches.push(parent);
    }
  }
  return matches;
}

function findAiOverviewByAttributes() {
  return [
    ...document.querySelectorAll('[aria-label*="AI Overview" i]'),
    ...document.querySelectorAll('[data-attrid*="AI Overview" i]'),
  ];
}

function isOverviewContainer(element) {
  if (!element || element.matches("body, html, #main, #search, #center_col, #rcnt")) {
    return false;
  }
  const text = extractContainerText(element);
  return text.length >= OVERVIEW_MIN_TEXT && text.length <= OVERVIEW_MAX_TEXT;
}

function resolveOverviewContainer(seedElement) {
  let node = seedElement;
  let best = null;

  for (let depth = 0; depth < 10 && node; depth += 1) {
    if (isOverviewContainer(node)) best = node;
    node = node.parentElement;
  }

  return best;
}

function findGoogleAiOverviewContainers() {
  const candidates = new Set();
  const seeds = [...findAiOverviewLabelElements(), ...findAiOverviewByAttributes()];

  seeds.forEach((seed) => {
    const container = resolveOverviewContainer(seed);
    if (container) candidates.add(container);
  });

  return [...candidates];
}

function detectGoogleOverviewMode(containerEl) {
  return {
    mode: "trust",
    text: extractContainerText(containerEl),
    urls: extractUrls(containerEl),
    source: "google_ai_overview",
  };
}

function createBadgeWrap(mode, trustPlatform) {
  const copy = mode === "code" ? MODE_COPY.code : getTrustCopy(trustPlatform);
  const wrap = document.createElement("div");
  wrap.className = WRAP_CLASS;
  wrap.dataset.mode = mode;
  wrap.dataset.platform = trustPlatform || "chatgpt";

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
  return { wrap, badge, subtitle, detailsBtn, copy };
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
  const copy = getTrustCopy(data.platform || "chatgpt");
  const categories = data.categories || {};
  const claims = sortClaimsForDisplay(data.claims || []);

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
      const supportKey = getClaimSupportKey(claim);
      const display = getClaimDisplay(claim);
      const confidence = getConfidenceDisplay(claim);
      const matchedDomain = sourceDomain(claim.matched_source);
      const note = claim.evidence_note || claim.note;
      return `
        <li class="checkeverything-claim checkeverything-claim-${supportKey}">
          <div class="checkeverything-claim-status-row">
            <span class="checkeverything-claim-icon" aria-hidden="true">${display.icon}</span>
            <span class="checkeverything-claim-status checkeverything-claim-status-${supportKey}">${escapeHtml(display.label)}</span>
          </div>
          <div class="checkeverything-claim-confidence checkeverything-confidence-${confidence.level}">
            <strong>${escapeHtml(confidence.label)}</strong> — ${escapeHtml(confidence.note)}
          </div>
          <div class="checkeverything-claim-label">Claim</div>
          <div class="checkeverything-claim-text">${escapeHtml(claim.text)}</div>
          ${matchedDomain ? `<div class="checkeverything-claim-source"><strong>Source:</strong> ${escapeHtml(matchedDomain)}</div>` : ""}
          ${note ? `<div class="checkeverything-claim-note"><strong>Evidence:</strong> ${escapeHtml(note)}</div>` : ""}
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
    ${claims.length ? `<div class="checkeverything-claims-section"><div class="checkeverything-claims-heading">Claims</div>${renderClaimSummary(claims)}<ul class="checkeverything-claims">${claimRows}</ul></div>` : ""}
    <small>Analysis type: ${escapeHtml(data.analysis_type || "preliminary")}${data.pipeline && data.pipeline !== "gemini" ? ` · ${escapeHtml(data.pipeline)} data` : ""}</small>
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
  document.querySelectorAll(".checkeverything-panel").forEach((panel) => panel.remove());

  const panel = document.createElement("div");
  panel.className = "checkeverything-panel";
  panel.innerHTML =
    result.mode === "trust" ? renderTrustPanel(result) : renderCodePanel(result);
  panel.querySelector(".checkeverything-close").onclick = () => panel.remove();
  anchor.insertAdjacentElement("afterend", panel);
}

function buildAnalyzePayload(detected) {
  return {
    type: "analyze",
    text: detected.text,
    urls: detected.urls,
    source: detected.source,
  };
}

function attachBadge(targetEl, detected) {
  if (targetEl.querySelector(`.${WRAP_CLASS}`) || targetEl.hasAttribute(ATTACHED_ATTR)) {
    return;
  }

  const trustPlatform = detected.source || "chatgpt";
  const { wrap, badge, detailsBtn, copy } = createBadgeWrap(detected.mode, trustPlatform);
  let lastResult = null;

  targetEl.setAttribute(ATTACHED_ATTR, "1");
  if (getComputedStyle(targetEl).position === "static") {
    targetEl.style.position = "relative";
  }
  targetEl.prepend(wrap);

  detailsBtn.addEventListener("click", () => {
    if (lastResult) showPanel(wrap, lastResult);
  });

  badge.addEventListener("click", () => {
    if (lastResult) {
      showPanel(wrap, lastResult);
      return;
    }

    if (!detected.text || detected.text.length < 20) {
      badge.textContent = "⚠️ No content";
      badge.title = "Could not extract enough AI Overview text to analyze.";
      return;
    }

    badge.textContent = "Analyzing response…";
    badge.disabled = true;
    detailsBtn.hidden = true;

    const payload =
      detected.mode === "code"
        ? { type: "review", code: detected.code, language: detected.language }
        : buildAnalyzePayload(detected);

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
      badge.title = copy.disclaimer;
      detailsBtn.hidden = false;
      showPanel(wrap, lastResult);
    });
  });
}

function scanChatGPTMessages() {
  if (location.pathname.includes("/demo/chatgpt")) {
    document
      .querySelectorAll('[data-message-author-role="assistant"]')
      .forEach((messageEl) => attachBadge(messageEl, detectChatGPTMode(messageEl)));
    return;
  }
  document
    .querySelectorAll('[data-message-author-role="assistant"]')
    .forEach((messageEl) => attachBadge(messageEl, detectChatGPTMode(messageEl)));
}

function scanGoogleAiOverviews() {
  if (location.pathname.includes("/demo/google")) {
    const block = document.querySelector(".ai-overview-block");
    if (block) attachBadge(block, detectGoogleOverviewMode(block));
    return;
  }
  findGoogleAiOverviewContainers().forEach((containerEl) => {
    attachBadge(containerEl, detectGoogleOverviewMode(containerEl));
  });
}

function scanPage() {
  try {
    if (platform === "google_ai_overview") {
      scanGoogleAiOverviews();
      return;
    }
    scanChatGPTMessages();
  } catch {
    // Defensive: never crash the host page if Google DOM changes.
  }
}

let scanScheduled = false;
function scheduleScan() {
  if (scanScheduled) return;
  scanScheduled = true;
  requestAnimationFrame(() => {
    scanScheduled = false;
    scanPage();
  });
}

const observer = new MutationObserver(() => scheduleScan());
observer.observe(document.body, { childList: true, subtree: true });
scheduleScan();
