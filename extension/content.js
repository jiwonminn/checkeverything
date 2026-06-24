const BADGE_CLASS = "checkeverything-badge";

function extractCodeBlocks(element) {
  const blocks = [];
  element.querySelectorAll("pre code, pre").forEach((el) => {
    const text = el.textContent?.trim();
    if (text && text.length > 20) blocks.push(text);
  });
  return blocks;
}

function extractReviewText(element) {
  const clone = element.cloneNode(true);
  clone.querySelectorAll(`.${BADGE_CLASS}`).forEach((n) => n.remove());
  return clone.textContent?.trim() || "";
}

function createBadge() {
  const btn = document.createElement("button");
  btn.className = BADGE_CLASS;
  btn.type = "button";
  btn.textContent = "🛡️ Review Score";
  btn.title = "Run checkeverything multi-agent review on this response";
  return btn;
}

function showPanel(anchor, data) {
  document.querySelectorAll(".checkeverything-panel").forEach((p) => p.remove());

  const report = data.report;
  const score = report?.overall_score ?? "—";
  const verdict = report?.verdict ?? "unknown";
  const pipeline = data.pipeline || "—";

  const panel = document.createElement("div");
  panel.className = "checkeverything-panel";
  panel.innerHTML = `
    <div class="checkeverything-panel-header">
      <strong>checkeverything</strong>
      <span class="checkeverything-score">${score}/100</span>
      <button class="checkeverything-close" type="button">×</button>
    </div>
    <div class="checkeverything-verdict">${verdict.replace("_", " ")}</div>
    <p class="checkeverything-summary">${report?.executive_summary || ""}</p>
    <div class="checkeverything-agents">
      ${(report?.agent_reports || [])
        .map((a) => `<span>${a.agent_name}: ${a.score}</span>`)
        .join("")}
    </div>
    <small>Pipeline: ${pipeline}</small>
  `;
  panel.querySelector(".checkeverything-close").onclick = () => panel.remove();
  anchor.insertAdjacentElement("afterend", panel);
}

function attachBadge(messageEl) {
  if (messageEl.querySelector(`.${BADGE_CLASS}`)) return;

  const badge = createBadge();
  messageEl.style.position = "relative";
  messageEl.prepend(badge);

  badge.addEventListener("click", async () => {
    badge.textContent = "Analyzing…";
    badge.disabled = true;

    const codeBlocks = extractCodeBlocks(messageEl);
    const reviewText = extractReviewText(messageEl);
    const code = codeBlocks.length ? codeBlocks.join("\n\n") : reviewText;

    chrome.runtime.sendMessage(
      { type: "review", code, language: "python" },
      (response) => {
        badge.disabled = false;
        if (!response?.ok) {
          badge.textContent = "⚠️ Error";
          badge.title = response?.error || "Review failed";
          return;
        }
        badge.textContent = `🛡️ ${response.data.report?.overall_score ?? "?"}/100`;
        showPanel(badge, response.data);
      }
    );
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
