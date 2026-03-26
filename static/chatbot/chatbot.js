(function () {
  if (window.__COEPD_CHATBOT_LOADED__) return;
  window.__COEPD_CHATBOT_LOADED__ = true;

  const CHATBOT_FLOW_VERSION = "2026-03-16-no-whatsapp-step";

  const state = {
    isOpen: false,
    userId: localStorage.getItem("coepd_chat_uid") || `coepd_${Date.now()}`,
    loading: false,
    started: false,
  };
  localStorage.setItem("coepd_chat_uid", state.userId);

  function injectStyles() {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "/chatbot/chatbot.css";
    document.head.appendChild(css);
  }

  function injectMarkup() {
    const launcher = document.createElement("button");
    launcher.id = "coepd-chatbot-launcher";
    launcher.type = "button";
    launcher.setAttribute("aria-label", "Open chatbot");
    launcher.innerHTML = '<img src="/chatbot/robot.svg" alt="Robot"/>';

    const widget = document.createElement("section");
    widget.id = "coepd-chatbot-widget";
    widget.innerHTML = `
      <div class="cb-head">
        <div>
          <div class="cb-title">COEPD AI Advisor</div>
          <div class="cb-status">Online</div>
        </div>
        <div class="cb-head-actions">
          <button type="button" id="cb-min">_</button>
          <button type="button" id="cb-reset">R</button>
          <button type="button" id="cb-close">X</button>
        </div>
      </div>
      <div class="cb-progress"><div id="cb-progress-fill"></div></div>
      <div class="cb-log" id="cb-log"></div>
      <div class="cb-input-wrap">
        <div class="cb-options" id="cb-options"></div>
        <form id="cb-form" class="cb-input-row">
          <input id="cb-input" placeholder="Type your message..." autocomplete="off" />
          <button type="submit">></button>
        </form>
      </div>
    `;

    document.body.appendChild(launcher);
    document.body.appendChild(widget);
  }

  function nowTime() {
    const d = new Date();
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function scrollLogToBottom() {
    const log = document.getElementById("cb-log");
    if (!log) return;
    requestAnimationFrame(() => {
      log.scrollTo({ top: log.scrollHeight, behavior: "smooth" });
    });
  }

  function appendMessage(role, html, typing) {
    const log = document.getElementById("cb-log");
    if (!log) return null;
    const row = document.createElement("div");
    row.className = `cb-row ${role}`;
    const bubble = document.createElement("div");
    bubble.className = "cb-bubble";

    if (typing) {
      bubble.innerHTML = '<div class="cb-typing"><span></span><span></span><span></span></div>';
    } else {
      bubble.innerHTML = html.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      const time = document.createElement("div");
      time.className = "cb-time";
      time.textContent = nowTime();
      bubble.appendChild(time);
    }

    row.appendChild(bubble);
    log.appendChild(row);
    scrollLogToBottom();
    return row;
  }

  function setProgress(value) {
    const bar = document.getElementById("cb-progress-fill");
    bar.style.width = `${Math.max(0, Math.min(100, value || 0))}%`;
  }

  function setOptions(options) {
    const wrap = document.getElementById("cb-options");
    wrap.innerHTML = "";
    (options || []).forEach((opt) => {
      const label = typeof opt === "string" ? opt : String(opt.label || opt.value || "").trim();
      if (!label) return;
      if (/whatsapp\s*number/i.test(label)) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = label;
      btn.addEventListener("click", function () {
        if (state.loading) return;
        sendMessage(label);
      });
      wrap.appendChild(btn);
    });
  }

  function setInputEnabled(enabled) {
    const input = document.getElementById("cb-input");
    const submitBtn = document.querySelector("#cb-form button[type='submit']");
    if (input) input.disabled = !enabled;
    if (submitBtn) submitBtn.disabled = !enabled;
    const optionButtons = document.querySelectorAll("#cb-options button");
    optionButtons.forEach((btn) => {
      btn.disabled = !enabled;
    });
  }

  async function submitLeadPayload(leadPayload) {
    if (!leadPayload || typeof leadPayload !== "object") return false;
    const payload = {
      name: String(leadPayload.name || "").trim(),
      phone: String(leadPayload.phone || "").trim(),
      email: String(leadPayload.email || "").trim().toLowerCase(),
      location: String(leadPayload.location || "").trim(),
      interested_domain: String(leadPayload.interested_domain || leadPayload.domain || "").trim(),
      whatsapp: String(leadPayload.whatsapp || "").trim(),
      source: "chatbot",
      created_at: new Date().toISOString(),
    };

    if (!payload.name || !payload.email || !payload.phone) return false;

    try {
      const res = await fetch((window.__API_BASE__ || "") + "/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) return false;
      const contentType = String(res.headers.get("content-type") || "").toLowerCase();
      if (!contentType.includes("application/json")) return false;
      const data = await res.json().catch(() => ({}));
      return Boolean(data && data.ok === true && data.id);
    } catch (_err) {
      // Keep chat UX non-blocking even if lead sync fails.
      return false;
    }
  }

  async function sendMessage(message, showUserBubble = true) {
    if (state.loading || !message || !message.trim()) return;
    state.loading = true;
    setInputEnabled(false);

    const input = document.getElementById("cb-input");
    if (showUserBubble) {
      appendMessage("user", message);
    }
    input.value = "";

    const typingEl = appendMessage("bot", "", true);

    try {
      const minTypingDelay = 1000 + Math.floor(Math.random() * 1000);
      const responsePromise = fetch((window.__API_BASE__ || "") + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message.trim(), user_id: state.userId }),
      });
      const delayPromise = new Promise((resolve) => setTimeout(resolve, minTypingDelay));
      const [response] = await Promise.all([responsePromise, delayPromise]);

      if (!response.ok) {
        throw new Error(`Chat error ${response.status}`);
      }

      const data = await response.json();
      let botText = data.reply || data.text || "No response available.";
      if (/whatsapp\s*number|10-?\s*digit\s*whatsapp/i.test(botText)) {
        botText = "Thank you for sharing your details.\nOur advisor will contact you shortly.";
      }
      if (typingEl) typingEl.remove();
      appendMessage("bot", botText);
      if (data.lead_payload) {
        const saved = await submitLeadPayload(data.lead_payload);
        if (!saved) {
          appendMessage(
            "bot",
            "We could not save your details right now. Please share once again or submit via the contact form."
          );
        }
      }
      setOptions(data.options || []);
      setProgress(data.meta && typeof data.meta.progress === "number" ? data.meta.progress : 0);
      if (data.placeholder) input.placeholder = data.placeholder;
    } catch (_err) {
      if (typingEl) typingEl.remove();
      appendMessage("bot", "I'm sorry, I'm having trouble answering that right now.\nBut I can still help you book a free demo session.");
      setOptions([
        "Book Free Demo",
        "Program Benefits",
        "Course Details",
        "Duration",
        "Placement Support",
      ]);
    } finally {
      state.loading = false;
      setInputEnabled(true);
      input.focus();
    }
  }

  function bindEvents() {
    const launcher = document.getElementById("coepd-chatbot-launcher");
    const widget = document.getElementById("coepd-chatbot-widget");
    const form = document.getElementById("cb-form");
    const input = document.getElementById("cb-input");

    function ensureChatStarted() {
      if (state.started) return;
      state.started = true;
      const storedFlowVersion = localStorage.getItem("coepd_chat_flow_version");
      if (storedFlowVersion !== CHATBOT_FLOW_VERSION) {
        localStorage.setItem("coepd_chat_flow_version", CHATBOT_FLOW_VERSION);
        sendMessage("__restart__", false);
        return;
      }
      sendMessage("__init__", false);
    }

    launcher.addEventListener("click", function () {
      state.isOpen = !state.isOpen;
      widget.classList.toggle("open", state.isOpen);
      launcher.classList.toggle("open", state.isOpen);
      if (state.isOpen) {
        ensureChatStarted();
        input.focus();
      }
    });

    document.getElementById("cb-min").addEventListener("click", function () {
      state.isOpen = false;
      widget.classList.remove("open");
      launcher.classList.remove("open");
    });

    document.getElementById("cb-close").addEventListener("click", function () {
      state.isOpen = false;
      widget.classList.remove("open");
      launcher.classList.remove("open");
    });

    document.getElementById("cb-reset").addEventListener("click", function () {
      document.getElementById("cb-log").innerHTML = "";
      setProgress(0);
      setOptions([]);
      state.started = true;
      sendMessage("__restart__", false);
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      sendMessage(input.value, true);
    });
  }

  function init() {
    injectStyles();
    injectMarkup();
    bindEvents();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
