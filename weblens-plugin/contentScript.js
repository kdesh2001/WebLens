// contentScript.js

// Keep a single panel instance
let panelHost = null;

function getSelectedText() {
  let text = (window.getSelection && window.getSelection().toString()) || "";
  if (!text) {
    const el = document.activeElement;
    const isTextInput =
      el &&
      (el.tagName === "TEXTAREA" ||
        (el.tagName === "INPUT" && /^(text|search|url|tel|password|email)$/i.test(el.type)));
    if (isTextInput && typeof el.selectionStart === "number" && el.selectionStart !== el.selectionEnd) {
      text = el.value.substring(el.selectionStart, el.selectionEnd);
    }
  }
  return (text || "").trim();
}

function ensurePanel() {
  if (panelHost) return panelHost;

  panelHost = document.createElement("div");
  panelHost.style.all = "initial"; // reduce inherited styles
  panelHost.style.position = "fixed";
  panelHost.style.top = "16px";
  panelHost.style.right = "16px";
  panelHost.style.zIndex = "2147483647"; // top-most
  document.documentElement.appendChild(panelHost);

  const root = panelHost.attachShadow({ mode: "open" });
  const style = document.createElement("style");
  style.textContent = `
    .card {
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Apple Color Emoji", "Segoe UI Emoji";
      width: 380px;
      max-height: 60vh;
      background: #fff;
      border: 1px solid rgba(0,0,0,.12);
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,.15);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      background: #f7f7f8;
      border-bottom: 1px solid rgba(0,0,0,.06);
      cursor: move; /* drag handle */
    }
    .title { font-weight: 600; font-size: 14px; color: #111; }
    .close {
      all: unset; cursor: pointer; font-weight: 700; padding: 0 6px; border-radius: 6px;
    }
    .close:hover { background: rgba(0,0,0,.06); }
    .body {
      padding: 12px;
      overflow: auto;
      line-height: 1.4;
      font-size: 14px;
      color: #222;
      white-space: pre-wrap;
    }
    .muted { color: #666; }
    .error { color: #b00020; }
  `;
  root.appendChild(style);

  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <div class="header">
      <div class="title">Quick Summarizer</div>
      <button class="close" title="Close">×</button>
    </div>
    <div class="body"><span class="muted">Preparing…</span></div>
  `;
  root.appendChild(card);

  // Close
  card.querySelector(".close").addEventListener("click", () => {
    panelHost.remove();
    panelHost = null;
  });

  // Dragging
  let dragging = false, startX = 0, startY = 0, startTop = 0, startRight = 0;
  card.querySelector(".header").addEventListener("mousedown", (e) => {
    dragging = true;
    startX = e.clientX;
    startY = e.clientY;
    const rect = panelHost.getBoundingClientRect();
    startTop = rect.top;
    startRight = window.innerWidth - rect.right;
    e.preventDefault();
  });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const dy = e.clientY - startY;
    const dx = e.clientX - startX;
    panelHost.style.top = Math.max(8, startTop + dy) + "px";
    panelHost.style.right = Math.max(8, startRight - dx) + "px";
  });
  window.addEventListener("mouseup", () => (dragging = false));

  return panelHost;
}

function showMessage(html, isError = false) {
  const host = ensurePanel();
  const body = host.shadowRoot.querySelector(".body");
  body.innerHTML = html;
  if (isError) body.classList.add("error");
  else body.classList.remove("error");
}

function showLoading() {
  showMessage(`<span class="muted">Summarizing…</span>`);
}

// Handle background requests
chrome.runtime.onMessage.addListener((msg) => {
  if (msg?.type === "GET_SELECTION_AND_SUMMARIZE") {
    const text = getSelectedText();
    if (!text) {
      showMessage(`<span class="muted">No text selected.</span>`);
      return;
    }
    showLoading();
    chrome.runtime.sendMessage({
      type: "SUMMARIZE_REQUEST",
      text,
      url: location.href
    });
  } else if (msg?.type === "SHOW_SUMMARY") {
    showMessage(msg.summary);
  } else if (msg?.type === "SHOW_SUMMARY_ERROR") {
    showMessage(`Error: ${msg.error}`, true);
  }
});
