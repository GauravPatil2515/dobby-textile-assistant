/**
 * @file image-analysis.js
 * @description Handles image upload, preview, and analysis functionality.
 *   Calls /analyze-image endpoint and displays results.
 *
 * @state lastImageBase64 - Base64 encoded image data
 */

// ── Image Uploads ──
let lastImageBase64 = null;

/**
 * Handle image file upload and trigger analysis
 * @param {Event} event - File input change event
 */
function handleImageUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    lastImageBase64 = e.target.result;
    document.getElementById('imagePreview').src = lastImageBase64;
    document.getElementById('imagePreviewContainer').style.display = 'block';
    // Call analyzeImage with the file
    analyzeImage(file);
  };
  reader.readAsDataURL(file);
  event.target.value = ''; // reset
}

/**
 * Clear the uploaded image and reset state
 */
function clearImage() {
  lastImageBase64 = null;
  document.getElementById('imagePreview').src = '';
  document.getElementById('imagePreviewContainer').style.display = 'none';
}

/**
 * Analyze uploaded image using the vision API
 * @param {File} file - Image file to analyze
 */
async function analyzeImage(file) {
  // Validate file type and size
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  if (!validTypes.includes(file.type)) {
    addBotMessage('❌ Please upload a valid image (JPEG, PNG, GIF, or WebP).');
    return;
  }
  if (file.size > 15 * 1024 * 1024) { // 15MB limit
    addBotMessage('❌ Image must be less than 15MB.');
    return;
  }

  hideWelcome();
  setLoading(true);
  addBotTyping();

  try {
    // Call the /analyze-image endpoint with base64 + mimeType
    const response = await fetch('/analyze-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image: lastImageBase64,
        mimeType: file.type
      })
    });

    removeTyping();

    if (!response.ok) {
      const err = await response.json();
      addBotMessage(`❌ Analysis failed: ${err.error || 'Unknown error'}`);
      setLoading(false);
      return;
    }

    const result = await response.json();

    if (!result.success) {
      addBotMessage(`❌ Analysis failed: ${result.error || 'Unknown error'}`);
      setLoading(false);
      return;
    }

    // Display design results
    if (result.structured) {
      // Show a summary message
      const colors = result.structured.colors || [];
      const colorStr = colors.map(c => c.name).join(', ') || 'Unknown';
      const design = result.structured.design || {};
      const occasion = result.structured.market?.occasion || 'Unspecified';
      
      addBotMessage(
        `🎨 I've analyzed your fabric image!\n\n` +
        `**Colors:** ${colorStr}\n` +
        `**Design Size:** ${design.designSize || 'Unknown'}\n` +
        `**Style:** ${design.designStyle || 'Unknown'}\n` +
        `**Occasion:** ${occasion}\n` +
        `**Provider:** ${result.provider || 'mock'}`
      );

      // Populate the design panel with the analyzed results
      renderDesignPanel(result.structured);

      // Build a context message from the vision result and inject into conversation
      const visionContext = {
        role: 'user',
        content: `[FABRIC IMAGE ANALYZED]
Colors detected: ${colors.map(c => `${c.name} (${c.percentage}%)`).join(', ')}
Design Size: ${design.designSize || 'Unknown'} (${design.designSizeRangeCm?.min || 0}–${design.designSizeRangeCm?.max || 0} cm)
Design Style: ${design.designStyle || 'Unknown'}
Weave: ${design.weave || 'Unknown'}
Stripe range: ${result.structured.stripe?.stripeSizeRangeMm?.min || 0}–${result.structured.stripe?.stripeSizeRangeMm?.max || 0} mm
Symmetry: ${result.structured.stripe?.isSymmetry ? 'Symmetric' : 'Asymmetric'}
Contrast: ${result.structured.visual?.contrastLevel || 'Unknown'}
Occasion: ${occasion}

Please confirm this design analysis and ask if I want to adjust anything.`
      };

      // Add to messages array so the LLM has context about the image analysis
      messages.push(visionContext);
      
      // Also add the bot's summary to messages
      messages.push({
        role: 'assistant',
        content: `I've analyzed your fabric image. Colors: ${colorStr}. Design Size: ${design.designSize || 'Unknown'}. Style: ${design.designStyle || 'Unknown'}. Occasion: ${occasion}. Provider: ${result.provider || 'mock'}`
      });
    } else {
      addBotMessage('📊 Analysis complete, but no structured data returned.');
    }
  } catch (err) {
    console.error('Analysis error:', err);
    removeTyping();
    addBotMessage(`❌ Error: ${err.message}`);
  } finally {
    setLoading(false);
  }
}
