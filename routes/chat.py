"""
Chat endpoint for conversational design assistance.

Handles POST /chat requests:
- Receives message history
- Returns conversational response + optional structured design JSON
"""

import re
import json
from flask import Blueprint, request, jsonify
from providers import LLMProviderFactory, MockProvider
from config import get_provider_name

chat_bp = Blueprint('chat', __name__)

# Conversational system prompt for textile design
CHAT_SYSTEM_PROMPT = """You are Dobby, a yarn-dyed shirting design assistant for Textronics. Keep responses SHORT (1-2 sentences max).

## IMAGE ANALYSIS HANDLING
When you receive a message starting with [FABRIC IMAGE ANALYZED], acknowledge the detected colors and design specs, confirm the analysis looks correct, and ask the buyer if they want to adjust anything or proceed to finalise the design.

## QUICK FLOW
1. Greet & ask: Formal/Casual/Party wear?
2. Ask: Pattern? (Solid/Stripe/Check)
3. Ask: Colors? How many? (4, 5, 8, 12, etc.)
4. Ask: Which is Base color?
5. Suggest Family + Harmony + Contrast colors
6. Confirm & output JSON

## COLOR STRATEGY
Base Color = primary. Then add:
- Family Colors (2-3 shades of base)
- Harmony Colors (complementary)
- Contrast Colors (accents: Gold/Red/etc)

For 10-12 colors: 4-6 Family + 2-3 Harmony + 1-2 Contrast

## STRIPE SIZES
- Micro: 0.2-1.0 mm
- Small: 0.2-2.0 mm  
- Medium: 0.2-4.0 mm
- Large: 0.5-10.0 mm

## OCCASION TO SIZE MAPPING
- **Casual**: Only allow Medium / Large sizes.
- **Formal**: Only allow Micro, Small, Medium sizes.

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


def parse_design_output(text: str):
    """Extract structured JSON from <DESIGN_OUTPUT> block if present.
    
    Args:
        text: Response text that may contain JSON in <DESIGN_OUTPUT> tags.
        
    Returns:
        Parsed dict if JSON found and valid, None otherwise.
    """
    match = re.search(r'<DESIGN_OUTPUT>\s*([\s\S]*?)\s*</DESIGN_OUTPUT>', text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat message and return assistant response.
    
    Expected JSON body:
        {
            "messages": [
                {"role": "user"/"assistant"/"system", "content": "..."},
                ...
            ]
        }
    
    Returns:
        {
            "reply": "response text",
            "structured": { ...design JSON... },
            "has_design": true/false
        }
    """
    try:
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
            _provider = LLMProviderFactory.get_provider(get_provider_name())
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "reply": "Sorry, internal error.", "has_design": False}), 500
