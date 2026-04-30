/**
 * @file design-panel.js
 * @description Manages the design specifications panel UI.
 *   Handles color editing, form synchronization, and JSON export.
 *
 * @state currentDesign - Current design object being edited
 */

// ── Design Panel ──────────────────────────────────────────────────────────
let currentDesign = null;

const COLOR_HEX_MAP = {
  // Blues
  "Navy Blue": "#1B3A6B", "Royal Blue": "#2151A1", "Sky Blue": "#87CEEB",
  "Oxford Blue": "#002147", "French Blue": "#0072BB", "Cobalt Blue": "#0047AB",
  "Steel Blue": "#4682B4", "Air Force Blue": "#5D8AA8", "Cornflower Blue": "#6495ED",
  "Light Blue": "#5DADE2", "Medium Blue": "#3498DB", "Dark Blue": "#1A5276",
  // Whites / Neutrals
  "White": "#FFFFFF", "Off-White": "#F8F5F0", "Ecru": "#C2B280",
  "Ivory": "#FFFFF0", "Cream": "#FFFDD0", "Snow": "#FFFAFA",
  // Reds
  "Red": "#CC0000", "Burgundy": "#800020", "Wine": "#722F37",
  "Maroon": "#800000", "Claret": "#7F1734", "Crimson": "#DC143C",
  "Dark Red": "#8B0000", "Oxblood": "#4A0000", "Cherry": "#8B0000",
  // Greens
  "Green": "#228B22", "Bottle Green": "#006A4E", "Forest Green": "#228B22",
  "Olive Green": "#6B8E23", "Hunter Green": "#355E3B", "Mint": "#98FF98",
  "Sage": "#BCB88A", "Emerald": "#50C878", "Jade": "#00A86B",
  // Greys / Blacks
  "Black": "#1A1A1A", "Charcoal Grey": "#36454F", "Mid Grey": "#808080",
  "Light Grey": "#D3D3D3", "Silver": "#C0C0C0", "Dark Charcoal": "#333333",
  "Graphite": "#383838", "Pewter": "#8F8F8D", "Slate": "#708090",
  // Browns / Tans
  "Tan": "#D2B48C", "Camel": "#C19A6B", "Khaki": "#C3B091",
  "Brown": "#795548", "Chocolate": "#7B3F00", "Coffee": "#6F4E37",
  "Mocha": "#4B3621", "Walnut": "#773F1A", "Sienna": "#A0522D",
  // Golds / Yellows
  "Gold": "#FFD700", "Mustard": "#FFDB58", "Ochre": "#CC7722",
  "Yellow": "#FFE066", "Golden": "#FFD700", "Brass": "#B5A642",
  // Pinks / Purples
  "Pink": "#FFB6C1", "Blush Pink": "#FFB7C5", "Dusty Rose": "#DCAE96",
  "Coral": "#FF6B6B", "Lavender Grey": "#B8B8D1", "Dusty Mauve": "#C4A4A4",
  "Purple": "#6B3FA0", "Lavender": "#E6E6FA", "Plum": "#8E4585",
  "Violet": "#EE82EE", "Lilac": "#C8A2C8", "Mauve": "#E0B0FF",
  // Teals / Cyans
  "Teal": "#008080", "Turquoise": "#40E0D0", "Aqua": "#00FFFF",
  "Cyan": "#00BCD4", "Aquamarine": "#7FFFD4",
  // Oranges
  "Orange": "#FF6600", "Peach": "#FFDAB9", "Apricot": "#FBCEB1",
  "Tangerine": "#FF9966", "Rust": "#B7410E",
  // Special
  "Navy": "#1B3A6B", "Charcoal": "#36454F", "Grey": "#808080",
  "Gray": "#808080", "Beige": "#D4C5A9", "Denim": "#1560BD",
  "Indigo": "#3F51B5", "Wine": "#722F37", "Rose": "#E8788A",
  "Mint Green": "#98D8C8", "Pale Pink": "#F8C8D4",
};

function getColorHex(colorName) {
  if (!colorName) return '#888888';
  const name = colorName.trim();
  
  // Direct match
  if (COLOR_HEX_MAP[name]) return COLOR_HEX_MAP[name];
  
  // Partial match
  const lower = name.toLowerCase();
  for (const [key, hex] of Object.entries(COLOR_HEX_MAP)) {
    if (key.toLowerCase().includes(lower) || lower.includes(key.toLowerCase())) {
      return hex;
    }
  }
  
  // Fallback — generate color from hash
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash) % 360;
  return `hsl(${h}, 45%, 55%)`;
}

// Legacy compatibility
function getColourHex(name) {
  return getColorHex(name);
}

// COLOUR_MAP for datalist (color names only)
const COLOUR_MAP = Object.keys(COLOR_HEX_MAP).reduce((acc, key) => {
  acc[key.toLowerCase()] = COLOR_HEX_MAP[key];
  return acc;
}, {});

/**
 * Open the design panel
 */
function openPanel() {
  document.getElementById('designPanel').classList.add('open');
}

/**
 * Close the design panel
 */
function closePanel() {
  document.getElementById('designPanel').classList.remove('open');
}

/**
 * Render design panel with given design data
 * @param {Object} d - Design object
 */
function renderDesignPanel(d) {
  currentDesign = JSON.parse(JSON.stringify(d)); // deep copy
  buildPanelUI(currentDesign);
  openPanel();
}

/**
 * Build the complete panel UI from design data
 * @param {Object} d - Design object
 */
function buildPanelUI(d) {
  const body = document.getElementById('panelBody');
  const design  = d.design   || {};
  const stripe  = d.stripe   || {};
  const colors  = d.colors   || [];
  const visual  = d.visual   || {};
  const market  = d.market   || {};
  const tech    = d.technical|| {};

  // Helper: option list builder
  function opts(list, val) {
    return list.map(o => `<option value="${o}"${o===val?' selected':''}>${o}</option>`).join('');
  }

  // Colour rows
  function colourRowHtml(c, i) {
    const hex = getColorHex(c.name);
    const isLightColor = ['white', 'off-white', 'ivory', 'cream', 'snow', 'ecru', 'light grey', 'light blue', 'sky blue', 'yellow', 'gold', 'mustard', 'lavender', 'mint', 'peach', 'blush pink'].some(l => (c.name || '').toLowerCase().includes(l));
    const borderStyle = isLightColor ? '1.5px solid #D1D5DB' : '1.5px solid rgba(0,0,0,0.08)';
    return `
      <div class="color-row" id="colour-row-${i}">
        <div class="color-dot" id="colour-dot-${i}" style="background:${hex}; border:${borderStyle}"></div>
        <input class="panel-input" id="colour-name-${i}" value="${c.name||''}"
          oninput="updateColourName(${i})"
          list="colour-suggestions"
          placeholder="Colour name">
        <input class="panel-input" id="colour-pct-${i}" type="number"
          min="1" max="100" value="${c.percentage||50}"
          oninput="syncFromForm()"
          style="max-width: 60px; text-align: center;">
        <span style="color: var(--text-muted); font-size: var(--text-sm);">%</span>
        <button class="icon-btn" onclick="removeColour(${i})" title="Remove" style="width: 24px; height: 24px; font-size: 12px;">✕</button>
      </div>`;
  }

  const colourRows = colors.map((c,i) => colourRowHtml(c,i)).join('');

  body.innerHTML = `
    <datalist id="colour-suggestions">
      ${Object.keys(COLOUR_MAP).map(c=>`<option value="${c.split(' ').map(w=>w[0].toUpperCase()+w.slice(1)).join(' ')}">`).join('')}
    </datalist>

    <!-- ── DESIGN ─────────────────────────────────────────── -->
    <div class="design-card">
      <div class="design-card-header">✦ Design</div>
      <div class="design-card-body" style="gap:12px">

        <div class="panel-field-row">
          <div class="panel-field-group">
            <div class="panel-label">Design Size</div>
            <select class="panel-select" id="f-designSize" onchange="syncFromForm()">
              ${opts(['Micro','Small','Medium','Large','Full Size'], design.designSize)}
            </select>
          </div>
          <div class="panel-field-group">
            <div class="panel-label">Weave</div>
            <select class="panel-select" id="f-weave" onchange="syncFromForm()">
              ${opts(['Plain','Twill','Oxford','Dobby'], design.weave)}
            </select>
          </div>
        </div>

        <div class="panel-field-row">
          <div class="panel-field-group">
            <div class="panel-label">Design Style</div>
            <select class="panel-select" id="f-designStyle" onchange="syncFromForm()">
              ${opts(['Regular','Gradational','Fila Fil','Counter','Multicolor'], design.designStyle)}
            </select>
          </div>
          <div class="panel-field-group">
            <div class="panel-label">Occasion</div>
            <select class="panel-select" id="f-occasion" onchange="syncFromForm()">
              ${opts(['Formal','Casual','Party Wear'], market.occasion)}
            </select>
          </div>
        </div>

        <div class="section-divider">Size Range (cm)</div>
        ${(() => {
          const sizeRanges = {
            "Micro": { min: 0.1, max: 1.0 },
            "Small": { min: 0.5, max: 2.0 },
            "Medium": { min: 2.0, max: 5.0 },
            "Large": { min: 5.0, max: 25.0 },
            "Full Size": { min: 25.0, max: 100.0 },
          };
          const sizeRange = design.designSizeRangeCm || {};
          const fallback = sizeRanges[design.designSize] || { min: 2.0, max: 5.0 };
          const min = (sizeRange.min && sizeRange.min > 0) ? sizeRange.min : fallback.min;
          const max = (sizeRange.max && sizeRange.max > 0) ? sizeRange.max : fallback.max;
          return `
        <div class="panel-field-row">
          <div class="panel-field-group">
            <div class="panel-label">Min</div>
            <input class="panel-input" type="number" id="f-sizeMin" min="0" max="50"
              value="${min}" oninput="syncFromForm()">
          </div>
          <div class="panel-field-group">
            <div class="panel-label">Max</div>
            <input class="panel-input" type="number" id="f-sizeMax" min="0" max="50"
              value="${max}" oninput="syncFromForm()">
          </div>
        </div>`;
        })()}

      </div>
    </div>

    <!-- ── COLOURS ────────────────────────────────────────── -->
    <div class="design-card">
      <div class="design-card-header">◉ Colour Composition</div>
      <div class="design-card-body" style="gap:8px" id="colour-editor">
        ${colourRows}
        <button class="add-color-btn" onclick="addColour()">+ Add colour</button>
      </div>
    </div>

    <!-- ── STRIPE & PATTERN ───────────────────────────────── -->
    <div class="design-card">
      <div class="design-card-header">≡ Stripe & Pattern</div>
      <div class="design-card-body" style="gap:12px">

        <div class="section-divider">Stripe Size Range (mm)</div>
        <div class="panel-field-row">
          <div class="panel-field-group">
            <div class="panel-label">Min</div>
            <input class="panel-input" type="number" id="f-stripeMin" min="0" max="50"
              value="${stripe.stripeSizeRangeMm?.min??0}" oninput="syncFromForm()">
          </div>
          <div class="panel-field-group">
            <div class="panel-label">Max</div>
            <input class="panel-input" type="number" id="f-stripeMax" min="0" max="50"
              value="${stripe.stripeSizeRangeMm?.max??0}" oninput="syncFromForm()">
          </div>
        </div>

        <div class="section-divider">Multiply Range</div>
        <div class="panel-field-row">
          <div class="panel-field-group">
            <div class="panel-label">Min</div>
            <input class="panel-input" type="number" id="f-multMin" min="0" max="10"
              value="${stripe.stripeMultiplyRange?.min??0}" oninput="syncFromForm()">
          </div>
          <div class="panel-field-group">
            <div class="panel-label">Max</div>
            <input class="panel-input" type="number" id="f-multMax" min="0" max="10"
              value="${stripe.stripeMultiplyRange?.max??0}" oninput="syncFromForm()">
          </div>
        </div>

        <div class="panel-field-row">
          <div class="panel-field-group">
            <div class="panel-label">Contrast Level</div>
            <select class="panel-select" id="f-contrast" onchange="syncFromForm()">
              ${opts(['Low','Medium','High'], visual.contrastLevel)}
            </select>
          </div>
          <div class="panel-field-group">
            <div class="panel-label">Symmetry</div>
            <select class="panel-select" id="f-symmetry" onchange="syncFromForm()">
              <option value="true"${stripe.isSymmetry?' selected':''}>Symmetric</option>
              <option value="false"${!stripe.isSymmetry?' selected':''}>Asymmetric</option>
            </select>
          </div>
        </div>

      </div>
    </div>

    <!-- ── LIVE JSON ──────────────────────────────────────── -->
    <div class="json-card">
      <div class="json-card-header">
        <div class="json-card-title">Live JSON</div>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="json-changed-dot" id="jsonChangedDot"></div>
          <button class="copy-btn" id="copyBtn" onclick="copyJson()">Copy</button>
        </div>
      </div>
      <div class="json-body" id="jsonPre">${escHtml(JSON.stringify(d, null, 2))}</div>
    </div>
  `;

  // Phase 3: Filter design size options based on occasion
  filterDesignSizeByOccasion(market.occasion || "Formal");

  // Phase 3: Add event listener to occasion dropdown
  const occasionSelect = document.getElementById('f-occasion');
  if (occasionSelect) {
    occasionSelect.addEventListener('change', function() {
      filterDesignSizeByOccasion(this.value);
    });
  }
}

// ── Colour editor helpers ──────────────────────────────────────────────────
/**
 * Update color name and preview dot
 * @param {number} i - Color index
 */
function updateColourName(i) {
  const nameEl = document.getElementById(`colour-name-${i}`);
  const dotEl  = document.getElementById(`colour-dot-${i}`);
  if (dotEl) dotEl.style.background = getColourHex(nameEl.value);
  syncFromForm();
}

/**
 * Add a new color to the design
 */
function addColour() {
  if (!currentDesign) return;
  currentDesign.colors = currentDesign.colors || [];
  currentDesign.colors.push({ name: 'White', percentage: 10 });
  buildPanelUI(currentDesign);
  // Scroll colour editor into view
  setTimeout(() => {
    const el = document.getElementById('colour-editor');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 50);
}

/**
 * Remove a color from the design
 * @param {number} i - Color index to remove
 */
function removeColour(i) {
  if (!currentDesign || !currentDesign.colors) return;
  if (currentDesign.colors.length <= 1) return; // keep at least 1
  currentDesign.colors.splice(i, 1);
  buildPanelUI(currentDesign);
  syncFromForm();
}

// ── Sync form → currentDesign → JSON ──────────────────────────────────────
/**
 * Synchronize form values with current design object
 */
function syncFromForm() {
  if (!currentDesign) return;

  const g = id => document.getElementById(id);
  const iv = id => { const el = g(id); return el ? el.value : ''; };
  const in_ = id => { const el = g(id); return el ? (parseFloat(el.value)||0) : 0; };

  // Design
  currentDesign.design = {
    designSize:      iv('f-designSize'),
    designSizeRangeCm: { min: in_('f-sizeMin'), max: in_('f-sizeMax') },
    designStyle:     iv('f-designStyle'),
    weave:           iv('f-weave'),
  };

  // Colours — read from rows
  const colours = [];
  let rowIdx = 0;
  while (document.getElementById(`colour-name-${rowIdx}`) !== null) {
    const name = iv(`colour-name-${rowIdx}`);
    const pct  = parseFloat(iv(`colour-pct-${rowIdx}`)) || 0;
    if (name) colours.push({ name, percentage: pct });
    rowIdx++;
  }
  if (colours.length) currentDesign.colors = colours;

  // Stripe
  currentDesign.stripe = {
    stripeSizeRangeMm:    { min: in_('f-stripeMin'), max: in_('f-stripeMax') },
    stripeMultiplyRange:  { min: in_('f-multMin'),   max: in_('f-multMax')   },
    isSymmetry: iv('f-symmetry') === 'true',
  };

  // Visual + Market
  currentDesign.visual  = { contrastLevel: iv('f-contrast') };
  currentDesign.market  = { occasion: iv('f-occasion') };

  // Technical specs removed
  
  updateLiveJson();
}

/**
 * Update the live JSON display
 */
function updateLiveJson() {
  const pre = document.getElementById('jsonPre');
  const dot = document.getElementById('jsonChangedDot');
  if (!pre || !currentDesign) return;
  pre.textContent = JSON.stringify(currentDesign, null, 2);
  if (dot) dot.classList.add('visible');
}

// ── Copy JSON ──────────────────────────────────────────────────────────────
/**
 * Copy JSON to clipboard with visual feedback
 */
function copyJson() {
  const pre = document.getElementById('jsonPre');
  if (!pre) return;
  navigator.clipboard.writeText(pre.textContent).then(() => {
    const btn = document.getElementById('copyBtn');
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}
