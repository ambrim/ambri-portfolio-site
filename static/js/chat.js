document.addEventListener("DOMContentLoaded", () => {
  /* -----------------------------
   * DOM Elements
   * ----------------------------- */
  const chatHeader = document.getElementById("chat-header");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatMessages = document.getElementById("chat-messages");
  const leftMain = document.getElementById("left-main");

  const toggleChatBtn = document.getElementById("toggle-chat");
  const toggleHistoryBtn = document.getElementById("toggle-history");

  /* -----------------------------
   * State
   * ----------------------------- */
  let chatMode = "chat";
  let isGenerating = false;

  /* -----------------------------
   * Markdown Config
   * ----------------------------- */
  if (window.marked) {
    marked.setOptions({
      headerIds: false,
      mangle: false
    });

    marked.use({
      renderer: {
        html() {
          return "";
        }
      }
    });
  }

  /* -----------------------------
   * Rendering helpers
   * ----------------------------- */

  function addChatMessage(text, role) {
    const wrapper = document.createElement("div");
    wrapper.className = `chat-message ${role}`;

    if (role === "user") {
      wrapper.innerHTML = `
        <div class="chat-content">
          <div class="chat-text">${text}</div>
        </div>
      `;
    } else {
      wrapper.innerHTML = marked.parse(text);
    }

    chatMessages.appendChild(wrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function addHistoryBubble(entry) {
    const bubble = document.createElement("div");
    bubble.className = "chat-message history";
    bubble.innerHTML = `
      <div class="history-card">
        <div class="history-title">${entry.query}</div>
        <div class="history-subtitle">${new Date(entry.timestamp).toLocaleString()}</div>
      </div>
    `;

    bubble.addEventListener("click", () => restoreHistory(entry.id));
    chatMessages.appendChild(bubble);
  }

  /* -----------------------------
   * Chat submit handler with streaming
   * ----------------------------- */

    chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    const submitBtn = chatForm.querySelector('button[type="submit"]');
    const requestId = Date.now().toString();

    addChatMessage(message, "user");
    chatInput.value = "";
    
    chatInput.disabled = true;
    submitBtn.disabled = true;
    isGenerating = true;  // NEW: Set generating flag
    
    // Disable tab switching during generation
    toggleChatBtn.disabled = true;
    toggleHistoryBtn.disabled = true;
    
    // Create a progress message element
    let progressEl = document.createElement("div");
    progressEl.className = "chat-message agent thinking";
    progressEl.innerHTML = `<span class="progress-text">Starting...</span>`;
    chatMessages.appendChild(progressEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const response = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction: message, request_id: requestId })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.status === 'started' || data.status === 'orchestrating' || 
                  data.status === 'progress' || data.status === 'finalizing') {
                progressEl.innerHTML = `<span class="progress-text">${data.message}</span>`;
                chatMessages.scrollTop = chatMessages.scrollHeight;
              }
              
              if (data.status === 'complete') {
                progressEl.remove();
                
                if (data.history) {
                  renderChatHistory(data.history);
                }
                
                if (data.html) {
                  leftMain.innerHTML = data.html;
                }
              }
              
              // Handle error
              if (data.status === 'error') {
                progressEl.remove();
                addChatMessage(`Error: ${data.message}`, "agent");
              }
            } catch (parseError) {
              console.error('Failed to parse SSE data:', parseError);
            }
          }
        }
      }

      chatInput.disabled = false;
      submitBtn.disabled = false;
      isGenerating = false;
      
      toggleChatBtn.disabled = false;
      toggleHistoryBtn.disabled = false;
      
      chatInput.focus();

    } catch (err) {
      console.error(err);
      if (progressEl && progressEl.parentNode) {
        progressEl.remove();
      }
      
      chatInput.disabled = false;
      submitBtn.disabled = false;
      isGenerating = false;
      
      toggleChatBtn.disabled = false;
      toggleHistoryBtn.disabled = false;
      
      addChatMessage("Failed to reach server.", "agent");
    }
  });

  /* -----------------------------
   * Mode switching
   * ----------------------------- */

    function setMode(mode) {
      if (isGenerating) {
        return;
      }
      
      chatMode = mode;

      toggleChatBtn.classList.toggle("active", mode === "chat");
      toggleHistoryBtn.classList.toggle("active", mode === "history");

      chatMessages.innerHTML = "";

      if (mode === "chat") {
        chatInput.disabled = false;
        chatHeader.innerHTML = "<h3>Chat with Portfolio Agent</h3>";
        loadChatHistory();
      } else {
        chatInput.disabled = true;
        chatHeader.innerHTML = "<h3>UI History</h3>";
        loadUIHistory();
      }
    }

  /* -----------------------------
   * Chat history mode
   * ----------------------------- */

  function loadChatHistory() {
    fetch("/chat/history")
      .then(res => res.json())
      .then(data => {
        chatMessages.innerHTML = "";

        if (!data.success) {
          addChatMessage("Error retrieving chat history. Refresh the page to retry.", "agent");
          return;
        }

        if (!data.entries || data.entries.length === 0) {
          addChatMessage("Ask me about projects, experience, or skills—I'll generate what you want to see.", "agent");
          return;
        }

        renderChatHistory(data.entries);
      });
  }

  function renderChatHistory(history) {
    chatMessages.innerHTML = "";
    history.forEach(msg => {
      addChatMessage(msg.content, msg.role);
    });

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  /* -----------------------------
   * HTML history mode
   * ----------------------------- */

  function loadUIHistory() {
    fetch("/ui/history")
      .then(res => res.json())
      .then(data => {
        chatMessages.innerHTML = "";

        if (!data.success) {
          addChatMessage("Error retrieving UI history. Try again in a few moments.", "agent");
          return;
        }

        if (!data.entries || data.entries.length === 0) {
          addChatMessage("No UI history yet.", "agent");
          return;
        }

        data.entries.forEach(entry => {
          addHistoryBubble(entry);
        });
      });
  }

  async function restoreHistory(id) {
    try {
      const res = await fetch(`/ui/history/${id}`);
      const data = await res.json();

      if (data.html) {
        leftMain.innerHTML = data.html;
      }
      
      setMode("chat");
    } catch (err) {
      console.error('Failed to restore UI:', err);
      addChatMessage("Failed to restore UI.", "agent");
    }
  }

  /* -----------------------------
   * Init
   * ----------------------------- */

  toggleChatBtn.addEventListener("click", () => setMode("chat"));
  toggleHistoryBtn.addEventListener("click", () => setMode("history"));

  setMode("chat");
});