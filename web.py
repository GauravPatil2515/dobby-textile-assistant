import os
import re
import json

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return None

from flask import Flask, render_template, request, jsonify
from llm_provider import LLMProviderFactory, MockProvider
from config import get_provider_name

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# ============================================================================
# CONVERSATIONAL SYSTEM PROMPT
# Replaces the old JSON-only prompt. The LLM now converses naturally,
# gathering info, and only outputs the JSON block AFTER enough info is collected.
# ============================================================================

CHAT_SYSTEM_PROMPT = """You are Dobby, a friendly expert textile design assistant. Keep responses SHORT (1-2 sentences). Users won't read long texts.

## CONVERSATION FLOW
1. Greet and ask about the fabric design they want.
2. Gather requirements naturally (style, colors, quality, usage).
3. If asking about colors:
   - Ask how many colors are needed (e.g., 4, 8, 12).
   - Ask which is the Base color.
4. Recommend options concisely.
5. After user confirmation, output the structured JSON.

## COLOR LOGIC
When suggesting color palettes based on user input, organize them correctly:
- Example: If base color is Forest Green.
  - Family Colors (2-3): Light green, dark green.
  - Contrast Color (1): Gold / Red.
- If the user wants 10-12 colors:
  - Family colors: 4-6
  - Harmony colors: 2-3
  - Contrast colors: 1-2

## SIZE GUIDE (Use these strict technical ranges in JSON)
- **Micro**: Design Size 0.1-1 cm | Stripe Size 0.2-1 mm
- **Small**: Design Size 0.5-2 cm | Stripe Size 0.2-2 mm
- **Medium**: Design Size 2-5 cm | Stripe Size 0.2-4 mm
- **Large**: Design Size 5-25 cm | Stripe Size 0.5-10 mm

## OUTPUT STRUCTURED JSON
ONLY after confirmation, output the JSON in exactly this block:
<DESIGN_OUTPUT>
{
  "design": {
    "designSize": "Micro|Small|Medium|Large|Full Size",
    "designSizeRangeCm": { "min": number, "max": number },
    "designStyle": "Regular|Gradational|Fil-a-Fil|Counter|Multicolor|Solid",
    "weave": "Plain|Twill|Oxford|Dobby"
  },
  "stripe": {
    "stripeSizeRangeMm": { "min": number, "max": number },
    "stripeMultiplyRange": { "min": number, "max": number },
    "isSymmetry": true|false
  },
  "colors": [
    { "name": "ColorName", "type": "Base|Family|Harmony|Contrast", "percentage": number }
  ],
  "visual": {
    "contrastLevel": "Low|Medium|High"
  },
  "market": {
    "occasion": "Formal|Casual|Party Wear"
  },
  "technical": {
    "yarnCount": "20s|30s|40s|50s|60s|80s/2|100s/2",
    "construction": "string e.g. 110 x 72 / 50s x 50s"
  }
}
</DESIGN_OUTPUT>

## OPTION CHIPS
When offering choices, append exactly one tag at the end, like:
[OPTIONS:4 colors|8 colors|12 colors]
or
[OPTIONS:Micro Stripe|Medium Stripe|Large Check]
Always use | to separate. Never use bullet points for options.

## RULES
- NEVER output JSON until design is confirmed.
- KEEP REPLIES EXTREMELY SHORT.
- DO NOT list EPI, PPI, or GSM anywhere.
"""

# Initialize provider once at startup
try:
    _provider = LLMProviderFactory.get_provider(get_provider_name())
except Exception as e:
    print(f"[WARNING] Provider init failed: {e}. Using MockProvider.")
    _provider = MockProvider()


def parse_design_output(text: str):
    """Extract structured JSON from <DESIGN_OUTPUT> block if present."""
    match = re.search(r'<DESIGN_OUTPUT>\s*([\s\S]*?)\s*</DESIGN_OUTPUT>', text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'provider': get_provider_name()})


@app.route('/api/providers')
def providers():
    return jsonify({
        'providers': LLMProviderFactory.get_available_providers(),
        'active': get_provider_name()
    })


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    messages = data.get('messages', [])

    if not isinstance(messages, list) or len(messages) == 0:
        return jsonify({'error': 'messages must be a non-empty list'}), 400

    # Always inject the conversational system prompt
    if not any(m.get('role') == 'system' for m in messages):
        messages.insert(0, {'role': 'system', 'content': CHAT_SYSTEM_PROMPT})
    else:
        # Replace any existing system prompt with the conversational one
        for m in messages:
            if m.get('role') == 'system':
                m['content'] = CHAT_SYSTEM_PROMPT
                break

    try:
        reply = _provider.get_response(messages)
    except Exception as e:
        print(f"[ERROR] Provider error: {e}. Falling back to mock.")
        reply = MockProvider().get_response(messages)

    structured = parse_design_output(reply)

    # Clean reply text: remove the raw JSON block from display text
    display_reply = re.sub(r'<DESIGN_OUTPUT>[\s\S]*?</DESIGN_OUTPUT>', '', reply).strip()

    return jsonify({
        'reply': display_reply,
        'structured': structured,
        'has_design': structured is not None
    })


@app.after_request
def add_headers(response):
    response.headers['X-Provider'] = get_provider_name()
    return response


if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    app.run(host=host, port=port, debug=debug)