const DEFAULT_API = "http://localhost:8080";

document.getElementById("save").addEventListener("click", () => {
  const apiUrl = document.getElementById("apiUrl").value.trim() || DEFAULT_API;
  chrome.storage.sync.set({ apiUrl }, () => {
    document.getElementById("status").textContent = "Saved!";
  });
});

chrome.storage.sync.get({ apiUrl: DEFAULT_API }, (data) => {
  document.getElementById("apiUrl").value = data.apiUrl;
});
