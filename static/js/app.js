/**
 * @file app.js
 * @description Main application initialization and DOM ready logic.
 *   Sets up Lucide icons, loads provider info, and initiates the conversation.
 *
 * @dependencies lucide@latest (loaded via CDN)
 * @state messages[] - conversation history
 * @state isLoading - prevents double-sends
 */

// ── State ──
let messages = [];
let isLoading = false;
let designPanelOpen = false;

// ── Phase 3: Occasion-based Design Size Filtering ──
const OCCASION_SIZE_MAP = {
  "Formal":     ["Micro", "Small", "Medium"],
  "Casual":     ["Medium", "Large"],
  "Party Wear": ["Micro", "Small", "Medium", "Large", "Full Size"],
};

/**
 * Filter design size options based on selected occasion
 * @param {string} occasion - The occasion type (Formal, Casual, Party Wear)
 */
function filterDesignSizeByOccasion(occasion) {
  const el = document.getElementById("f-designSize");
  if (!el) return;
  const allowed = OCCASION_SIZE_MAP[occasion] || ["Micro", "Small", "Medium", "Large", "Full Size"];
  const current = el.value;
  el.innerHTML = "";
  allowed.forEach(v => el.appendChild(new Option(v, v)));
  // Preserve selection if still valid
  if (allowed.includes(current)) el.value = current;
}

// ── Init ──
window.addEventListener('DOMContentLoaded', async () => {
  lucide.createIcons();
  adjustTextarea();

  await loadProvider();
  // Auto-send a greeting so bot initiates the conversation
  setTimeout(() => {
    hideWelcome();
    addBotTyping();
    fetchReply([{role:'user', content:'hello'}]).then(result => {
      removeTyping();
      addBotMessage(result.reply);
      messages = [{role:'user', content:'hello'}, {role:'assistant', content: result.reply}];
    });
  }, 600);

  // Phase 3: Initialize design size filter on page load
  filterDesignSizeByOccasion("Formal");
});

/**
 * Load and display the active AI provider
 */
async function loadProvider() {
  try {
    const r = await fetch('/api/providers');
    const d = await r.json();
    document.getElementById('providerLabel').textContent = d.active.toUpperCase();
  } catch(e) {
    document.getElementById('providerLabel').textContent = 'AI Ready';
  }
}

// ── Vision Model Toggle ────────────────────────────────
let activeVisionModel = 'gemini';

function initModelToggle() {
  const pills = document.querySelectorAll('.model-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', async () => {
      const model = pill.dataset.model;
      if (model === activeVisionModel) return;

      // Update active state
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeVisionModel = model;

      // Show switching toast
      showToast(`Vision: ${pill.textContent.trim()} ✓`, 'success');

      // Notify backend to switch provider
      try {
        await fetch('/api/vision-provider', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider: model })
        });
      } catch (e) {
        console.warn('Could not switch vision provider:', e);
      }
    });
  });
}

// Toast notification helper
function showToast(message, type = 'info') {
  const existing = document.getElementById('dobby-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'dobby-toast';
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('toast-show'));
  setTimeout(() => {
    toast.classList.remove('toast-show');
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}

// Initialize model toggle on page load
document.addEventListener('DOMContentLoaded', () => {
  initModelToggle();
  loadProvider();
});
