/**
 * @file chat.js
 * @description Handles chat message rendering, API calls to /chat,
 *   and option button creation for the Dobby textile assistant.
 *
 * @requires design-panel.js - buildPanelUI(), openPanel()
 * @state messages[] - conversation history
 * @state isLoading - prevents double-sends
 */

/**
 * Send a message to the chat API
 * @param {Array} msgs - Array of message objects with role and content
 * @returns {Promise} Response from /chat endpoint
 */
async function fetchReply(msgs) {
  const r = await fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({messages: msgs})
  });
  if (!r.ok) throw new Error('Request failed');
  return r.json();
}

/**
 * Send the current user message and handle the response
 */
async function sendMessage() {
  const ta = document.getElementById('userInput');
  const text = ta.value.trim();
  if (!text && !lastImageBase64 || isLoading) return;

  hideWelcome();
  addUserMessage(text, lastImageBase64);
  
  // Prepare message format
  let msgContent = text || "Analyze this fabric image.";
  if (lastImageBase64) {
    // Create multi-part content if there is an image
    msgContent = [
      { type: "text", text: msgContent },
      { type: "image_url", image_url: { url: lastImageBase64 } }
    ];
  }
  
  messages.push({role: 'user', content: msgContent});
  
  ta.value = '';
  ta.style.height = 'auto';
  clearImage();
  
  setLoading(true);
  addBotTyping();

  try {
    const result = await fetchReply(messages);
    removeTyping();
    addBotMessage(result.reply);
    messages.push({role: 'assistant', content: result.reply});

    if (result.has_design && result.structured) {
      renderDesignPanel(result.structured);
      addDesignBanner();
    }
  } catch(err) {
    console.error(err);
    removeTyping();
    addBotMessage('Sorry, I ran into an issue. Please try again. ' + err.message);
  }
  setLoading(false);
}

/**
 * Send a starter chip message
 * @param {HTMLElement} el - The chip element that was clicked
 */
function sendStarter(el) {
  document.getElementById('userInput').value = el.textContent;
  sendMessage();
}

// ── UI Helpers ──
/**
 * Hide the welcome screen
 */
function hideWelcome() {
  const w = document.getElementById('welcomeState');
  if (w) { w.style.display = 'none'; }
}

/**
 * Add a user message to the chat
 * @param {string} text - Message text
 * @param {string} imgBase64 - Base64 image data (optional)
 */
function addUserMessage(text, imgBase64=null) {
  const el = document.createElement('div');
  el.className = 'message-row user';
  
  let contentHtml = '';
  if (imgBase64) {
    contentHtml += `<img src="${imgBase64}" style="max-width:200px; border-radius:8px; display:block; margin-bottom:8px;">`;
  }
  if (text) {
    contentHtml += escHtml(text);
  }
  
  el.innerHTML = `
    <div class="message-user">${contentHtml}</div>`;
  appendMsg(el);
  lucide.createIcons();
}

/**
 * Add a bot message to the chat with optional option buttons
 * @param {string} text - Message text that may contain [OPTIONS:...] tag
 */
function addBotMessage(text) {
  // Extract [OPTIONS:...] tag if present
  const optMatch = text.match(/\[OPTIONS:([^\]]+)\]/);
  const cleanText = text.replace(/\[OPTIONS:[^\]]+\]/g, '').trim();

  const el = document.createElement('div');
  el.className = 'message-row bot';
  el.innerHTML = `
    <div class="bot-avatar">🧵</div>
    <div class="message-bot">${formatBotText(cleanText)}</div>`;
  appendMsg(el);

  // Render option chips below the bubble
  if (optMatch) {
    const options = optMatch[1].split('|').map(o => o.trim()).filter(Boolean);
    const chipsEl = document.createElement('div');
    chipsEl.className = 'options-row';
    chipsEl.id = 'lastChips';
    chipsEl.innerHTML = options.map(o =>
      `<button class="option-btn" onclick="pickOption(this, '${o.replace(/'/g,"&#39;")}')">${o}</button>`
    ).join('');
    appendMsg(chipsEl);
    lucide.createIcons();
  }
}

/**
 * Handle option button click
 * @param {HTMLElement} btn - The button that was clicked
 * @param {string} value - The option value
 */
function pickOption(btn, value) {
  // Disable all chips in this group
  const wrap = btn.closest('.options-row');
  if (wrap) wrap.querySelectorAll('.option-btn').forEach(c => c.disabled = true);
  // Send the chosen value as a user message
  document.getElementById('userInput').value = value;
  sendMessage();
}

/**
 * Add typing indicator to chat
 */
function addBotTyping() {
  const el = document.createElement('div');
  el.className = 'message-row bot';
  el.id = 'typingIndicator';
  el.innerHTML = `
    <div class="bot-avatar">🧵</div>
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  appendMsg(el);
  lucide.createIcons();
}

/**
 * Remove typing indicator from chat
 */
function removeTyping() {
  const t = document.getElementById('typingIndicator');
  if (t) t.remove();
}

/**
 * Add design ready banner
 */
function addDesignBanner() {
  const el = document.createElement('div');
  el.className = 'design-ready-banner';
  el.innerHTML = `<span>✦</span> <strong>Design specifications generated</strong> — click to view <span class="arrow">→</span>`;
  el.onclick = () => openPanel();
  appendMsg(el);
  lucide.createIcons();
}

/**
 * Append a message element to the chat container
 * @param {HTMLElement} el - Element to append
 */
function appendMsg(el) {
  const container = document.getElementById('chatMessages');
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

/**
 * Set loading state
 * @param {boolean} val - Loading state
 */
function setLoading(val) {
  isLoading = val;
  document.getElementById('sendBtn').disabled = val;
}

// ── Text formatting ──
/**
 * Escape HTML characters
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
}

/**
 * Format bot message text with markdown-like syntax
 * @param {string} text - Text to format
 * @returns {string} Formatted HTML
 */
function formatBotText(text) {
  // Bold **text**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Newlines
  text = text.replace(/\n/g, '<br>');
  return text;
}
