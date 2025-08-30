// background.js (MV3 service worker)

const DEFAULT_SERVER_URL = "http://localhost:8000/summarize";

// Create a context menu on install for right-click -> Summarize selection
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "summarize-selection",
    title: "Summarize selection",
    contexts: ["selection"]
  });
});

// Trigger from context menu
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "summarize-selection") {
    if (tab && tab.id) {
      chrome.tabs.sendMessage(tab.id, { type: "GET_SELECTION_AND_SUMMARIZE" });
    }
  }
});

// Trigger from keyboard shortcut
chrome.commands.onCommand.addListener(async (command) => {
  if (command === "summarize-selection") {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.id) {
      chrome.tabs.sendMessage(tab.id, { type: "GET_SELECTION_AND_SUMMARIZE" });
    }
  }
});

// Listen for selection text from the content script, call server, send result back
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg?.type === "SUMMARIZE_REQUEST") {
      try {
        const serverUrl = (await chrome.storage.local.get("serverUrl")).serverUrl || DEFAULT_SERVER_URL;

        // Basic payload; add auth headers if you secure your endpoint
        const res = await fetch(serverUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
            // "X-Auth-Token": "your-secret" // optional simple auth
          },
          body: JSON.stringify({
            text: msg.text,
            url: msg.url
          })
        });

        if (!res.ok) throw new Error(`Server ${res.status}`);
        const data = await res.json(); // { summary: "..." }
        chrome.tabs.sendMessage(sender.tab.id, {
          type: "SHOW_SUMMARY",
          summary: data.summary || "(No summary returned)"
        });
        // await new Promise(r => setTimeout(r, 1000)); // simulate delay
        //     chrome.tabs.sendMessage(sender.tab.id, {
        //     type: "SHOW_SUMMARY",
        //     summary: "✅ This is a fake summary. Your extension is working!"
        // });

      } catch (e) {
        chrome.tabs.sendMessage(sender.tab.id, {
          type: "SHOW_SUMMARY_ERROR",
          error: e.message || String(e)
        });
      }
    }
  })();

  // Indicate async response handled via messages, not sendResponse
  return true;
});
