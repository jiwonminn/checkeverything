const CE_UNSUPPORTED_ID = "checkeverything-unsupported-banner";

if (!document.getElementById(CE_UNSUPPORTED_ID)) {
  const site = location.hostname.includes("gemini.") ? "Gemini" : "this site";
  const banner = document.createElement("div");
  banner.id = CE_UNSUPPORTED_ID;
  banner.textContent = `CheckEverything does not run on ${site}. Use ChatGPT or Google Search (AI Overview).`;
  banner.style.cssText =
    "position:fixed;bottom:16px;right:16px;z-index:2147483647;max-width:320px;padding:10px 14px;" +
    "font:600 12px system-ui,sans-serif;color:#202124;background:#fef7e0;border:1px solid #f9ab00;" +
    "border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.12);cursor:pointer;";
  banner.title = "Click to dismiss";
  banner.addEventListener("click", () => banner.remove());
  document.documentElement.appendChild(banner);
}
