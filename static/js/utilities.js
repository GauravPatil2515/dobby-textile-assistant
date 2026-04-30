/**
 * @file utilities.js
 * @description Utility functions for textarea auto-resize and helper functions.
 *   Provides adjustTextarea() and other shared utilities.
 */

/**
 * Initialize textarea auto-resize and keyboard shortcuts
 */
function adjustTextarea() {
  const ta = document.getElementById('userInput');
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 130) + 'px';
  });
  ta.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading) sendMessage();
    }
  });
}
