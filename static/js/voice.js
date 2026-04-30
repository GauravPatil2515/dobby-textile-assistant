/**
 * @file voice.js
 * @description Handles voice input functionality using Web Speech API.
 *   Provides toggleVoice() function for microphone input.
 *
 * @state recognition - SpeechRecognition instance
 * @state isListening - Current microphone state
 */

// ── Voice Commands ──
let recognition;
let isListening = false;

/**
 * Toggle voice recognition on/off
 * Handles microphone permissions and speech-to-text conversion
 */
function toggleVoice() {
  const micBtn = document.getElementById('micBtn');
  
  if (isListening) {
    if (recognition) recognition.stop();
    isListening = false;
    if (micBtn) micBtn.classList.remove('listening');
    return;
  }
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Voice recognition is not supported in this browser. Try Chrome.");
    return;
  }
  
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  
  recognition.onstart = () => {
    isListening = true;
    if (micBtn) micBtn.classList.add('listening');
    document.getElementById('userInput').placeholder = "Listening...";
  };
  
  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(r => r.transcript)
      .join('');
    const ta = document.getElementById('userInput');
    ta.value = ta.value ? ta.value + ' ' + transcript : transcript;
    
    // Auto-submit after short delay so user can see transcript
    if (event.results[event.results.length - 1].isFinal) {
      setTimeout(() => {
        sendMessage();
      }, 500);
    }
  };
  
  recognition.onerror = (event) => {
    console.error("Speech recognition error", event.error);
  };
  
  recognition.onend = () => {
    isListening = false;
    const micBtn = document.getElementById('micBtn');
    if (micBtn) micBtn.classList.remove('listening');
    document.getElementById('userInput').placeholder = "Describe what you're looking for, or just say hello…";
  };
  
  recognition.start();
}
