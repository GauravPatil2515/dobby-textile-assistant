"""
Abstract LLM Provider interface and factory for provider-agnostic LLM calls.
Supports Groq, OpenAI, Anthropic, OpenRouter, and Mock providers.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from constants import STRIPE_SIZE_MAP, DESIGN_SIZE_MAP

# Provider instance cache — avoids re-instantiation on every request
_provider_cache: dict = {}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def get_response(self, messages: List[Dict[str, str]]) -> str:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    def analyze_image(self, image_b64: str, mime_type: str = "image/jpeg") -> Dict:
        """Analyze an image and return design JSON. Optional for base class."""
        raise NotImplementedError("Image analysis not supported by this provider")


class GroqProvider(LLMProvider):
    """Groq LLM provider."""

    def __init__(self, api_key: Optional[str] = None):
        from groq import Groq
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def get_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.is_configured():
            raise ValueError("Groq API key not configured. Set GROQ_API_KEY.")
            
        # Dynamically use vision model if any message has image content
        has_image = any(isinstance(m.get("content"), list) for m in messages)
        model_to_use = "llama-3.2-11b-vision-preview" if has_image else self.model
        
        completion = self.client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return completion.choices[0].message.content

    def get_model_name(self) -> str:
        return self.model

    def is_configured(self) -> bool:
        return bool(self.api_key)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: Optional[str] = None):
        from openai import OpenAI
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def get_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY.")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content

    def get_model_name(self) -> str:
        return self.model

    def is_configured(self) -> bool:
        return bool(self.api_key)


class AnthropicProvider(LLMProvider):
    """
    Anthropic (Claude) LLM provider.
    NOTE: Anthropic SDK requires system prompt as a separate parameter,
    NOT inside the messages list.
    """

    def __init__(self, api_key: Optional[str] = None):
        import anthropic
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

    def get_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.is_configured():
            raise ValueError("Anthropic API key not configured. Set ANTHROPIC_API_KEY.")

        # Anthropic SDK requires system as a separate top-level param
        system_content = None
        filtered_messages = []
        for m in messages:
            if m.get("role") == "system":
                system_content = m["content"]
            else:
                # Convert OpenAI vision array format to Anthropic vision array format if needed
                content = m.get("content")
                if isinstance(content, list):
                    new_content = []
                    for block in content:
                        if block.get("type") == "text":
                            new_content.append({"type": "text", "text": block["text"]})
                        elif block.get("type") == "image_url":
                            # Extract base64 data and mime type
                            url = block["image_url"]["url"]
                            if url.startswith("data:"):
                                mime, b64 = url.split(";base64,")
                                mime = mime.split(":")[1]
                                new_content.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime,
                                        "data": b64
                                    }
                                })
                            else:
                                pass # URL-only not supported by native Anthropic SDK without fetching
                    filtered_messages.append({"role": m["role"], "content": new_content})
                else:
                    filtered_messages.append(m)

        kwargs = dict(
            model=self.model,
            max_tokens=1024,
            messages=filtered_messages
        )
        if system_content:
            kwargs["system"] = system_content

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def get_model_name(self) -> str:
        return self.model

    def is_configured(self) -> bool:
        return bool(self.api_key)


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider — unified API for many models, with fallback chain."""

    def __init__(self, api_key: Optional[str] = None, model: str = None):
        from openai import OpenAI as OpenAIClient
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        env_model = os.getenv(
            "OPENROUTER_MODEL",
            "deepseek/deepseek-r1:free,deepseek/deepseek-r1-distill-llama-70b:free,google/gemini-2.0-flash-exp:free"
        )
        self.models = [m.strip() for m in (model or env_model).split(',') if m.strip()]
        self.client = None
        if self.api_key:
            self.client = OpenAIClient(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/SheeSh2777/dobby111",
                    "X-Title": "Dobby Textile Assistant"
                }
            )

    def get_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.is_configured():
            raise ValueError("OpenRouter API key not configured. Set OPENROUTER_API_KEY.")
        errors = []
        for model in self.models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024
                )
                return response.choices[0].message.content
            except Exception as e:
                errors.append(f"{model}: {e}")
                continue
        raise Exception(f"All OpenRouter models failed: {'; '.join(errors)}")

    def get_model_name(self) -> str:
        return self.models[0] if self.models else "unknown"

    def is_configured(self) -> bool:
        return bool(self.api_key)


# ============================================================================
# COLOR PALETTE BUILDER
# ============================================================================
def build_color_palette(base_color: str, color_count: int) -> list:
    """
    Build a color palette based on base color and desired count.
    
    Returns list of color dicts: [{"name": str, "type": str, "percentage": int}]
    where type is one of: "base", "family", "harmony", "contrast"
    """
    COLOR_FAMILIES = {
        "Navy Blue":    {"family": ["Royal Blue", "Steel Blue"],      "harmony": ["Cobalt Blue", "Indigo"],    "contrast": ["Gold", "White"]},
        "Sky Blue":     {"family": ["Baby Blue", "Powder Blue"],      "harmony": ["Cerulean", "Teal"],         "contrast": ["White", "Coral"]},
        "White":        {"family": ["Ivory", "Cream"],                "harmony": ["Light Grey", "Silver"],     "contrast": ["Navy Blue", "Black"]},
        "Black":        {"family": ["Charcoal", "Dark Grey"],         "harmony": ["Slate", "Graphite"],        "contrast": ["White", "Gold"]},
        "Grey":         {"family": ["Light Grey", "Slate"],           "harmony": ["Silver", "Charcoal"],       "contrast": ["White", "Red"]},
        "Beige":        {"family": ["Cream", "Sand"],                 "harmony": ["Tan", "Khaki"],             "contrast": ["Brown", "Burgundy"]},
        "Forest Green": {"family": ["Light Green", "Dark Green"],     "harmony": ["Olive", "Moss"],            "contrast": ["Gold", "Red"]},
        "Burgundy":     {"family": ["Wine", "Maroon"],                "harmony": ["Rose", "Mauve"],            "contrast": ["Gold", "Cream"]},
        "Red":          {"family": ["Crimson", "Scarlet"],            "harmony": ["Orange Red", "Rose"],       "contrast": ["White", "Navy Blue"]},
        "Yellow":       {"family": ["Lemon", "Mustard"],              "harmony": ["Gold", "Amber"],            "contrast": ["Black", "Navy Blue"]},
    }

    palette_def = COLOR_FAMILIES.get(base_color, {
        "family":   ["Light " + base_color, "Dark " + base_color],
        "harmony":  ["Neutral Grey", "Silver"],
        "contrast": ["White", "Black"]
    })

    colors = [{"name": base_color, "type": "base", "percentage": 0}]

    if color_count <= 4:
        slots = [
            *[{"name": c, "type": "family"}  for c in palette_def["family"][:2]],
            {"name": palette_def["contrast"][0], "type": "contrast"},
        ]
    elif color_count <= 8:
        slots = [
            *[{"name": c, "type": "family"}  for c in palette_def["family"][:3]],
            *[{"name": c, "type": "harmony"} for c in palette_def["harmony"][:2]],
            *[{"name": c, "type": "contrast"} for c in palette_def["contrast"][:2]],
        ]
    else:
        slots = [
            *[{"name": c, "type": "family"}  for c in (palette_def["family"] + ["Light " + base_color, "Deep " + base_color, "Soft " + base_color])[:5]],
            *[{"name": c, "type": "harmony"} for c in (palette_def["harmony"] + ["Neutral Tone"])[:3]],
            *[{"name": c, "type": "contrast"} for c in palette_def["contrast"][:2]],
        ]

    slots = slots[:color_count - 1]
    colors.extend([{**s, "percentage": 0} for s in slots])

    base_pct = 40 if color_count <= 4 else (30 if color_count <= 8 else 20)
    colors[0]["percentage"] = base_pct
    remaining = 100 - base_pct
    n = len(colors) - 1
    if n > 0:
        per_color = remaining // n
        leftover  = remaining - (per_color * n)
        for i in range(1, len(colors)):
            colors[i]["percentage"] = per_color + (leftover if i == 1 else 0)

    return colors


class MockProvider(LLMProvider):
    """
    Stateful mock provider used when no real API key is available.
    Tracks conversation stage by reading full message history.
    Responds conversationally — never dumps raw JSON until design is confirmed.
    """

    def __init__(self):
        self.model = "mock-model"

    def _get_stage(self, messages: List[Dict[str, str]]) -> str:
        """
        Determine conversation stage by looking at what the LAST ASSISTANT MESSAGE asked.
        This is far more reliable than keyword-matching user input, which causes loops.
        """
        user_msgs = []
        for m in messages:
            if m["role"] == "user":
                c = m["content"]
                if isinstance(c, list):
                    # Combine all text blocks
                    c = " ".join([b["text"] for b in c if b.get("type") == "text"])
                user_msgs.append(c.lower().strip())
                
        assistant_msgs = [m["content"].lower() for m in messages if m["role"] == "assistant"]
        num_turns    = len(user_msgs)

        if num_turns == 0:
            return "greeting"

        last_user = user_msgs[-1]

        # ── Always-first checks ───────────────────────────────────────────────

        # Explanation requests (can come at any point)
        explain_kw = ["what is dobby", "what's dobby", "explain dobby", "dobby weave",
                      "what is yarn", "explain dobby"]
        if any(kw in last_user for kw in explain_kw):
            return "explain"

        # Greeting on first turn
        if num_turns <= 1:
            greet_kw = ["hello", "hi", "hey", "good morning", "good afternoon", "howdy"]
            if any(last_user == kw or last_user.startswith(kw + " ") or last_user.startswith(kw + "!") for kw in greet_kw):
                return "greeting"

        # ── Use last assistant message to know what was ASKED ─────────────────
        last_bot = assistant_msgs[-1] if assistant_msgs else ""

        # Bot just showed Option A / Option B → user is confirming a design
        if "option a" in last_bot and "option b" in last_bot:
            return "finalize"

        # Bot asked for percentage split
        if "percentage split" in last_bot or "[options:50%" in last_bot or "50% / 50%" in last_bot:
            return "percentage_given"

        # Bot asked for stripe size
        if "stripe size" in last_bot or "[options:micro (0.2-1mm)" in last_bot:
            return "stripe_size_given"

        # Bot asked for color count
        if "how many colors" in last_bot or "[options:2|4|6|8|12]" in last_bot:
            return "color_count_given"

        # Bot asked for base color
        if "base color" in last_bot or "which color should be the base" in last_bot:
            return "base_color_given"

        # Bot asked for quality tier
        if ("standard quality" in last_bot and "premium quality" in last_bot) or            ("50s yarn" in last_bot and "60s yarn" in last_bot):
            return "quality_given"

        # Bot asked for colour
        if "what colour" in last_bot or "colour are you thinking" in last_bot or            "colour combination" in last_bot or "colours would you like" in last_bot or            "colour palette" in last_bot or "colours does the school" in last_bot or            "[options:navy" in last_bot or "[options:white" in last_bot or            "popular solid colour" in last_bot or "popular stripe" in last_bot or            "popular check" in last_bot:
            return "colour_given"

        # Bot asked for pattern
        if "pattern or design" in last_bot or "what pattern" in last_bot or            "pattern preference" in last_bot or "[options:solid colour" in last_bot or            "[options:oxford" in last_bot or "[options:red +" in last_bot:
            return "pattern_given"

        # Bot asked for occasion / what the shirt is for
        if "what is this shirt" in last_bot or "shirt fabric for" in last_bot or            "what kind of shirt" in last_bot or "[options:formal office" in last_bot:
            # If user answered with an occasion keyword, advance to occasion_given
            occasion_kw = ["formal", "office", "business", "casual", "school", "uniform",
                           "party", "wedding", "sportswear", "sport", "work", "daily",
                           "weekend", "festive", "summer", "winter", "flannel"]
            if any(kw in last_user for kw in occasion_kw):
                return "occasion_given"
            return "need_occasion"

        # ── Fallback: keyword match on user input only as last resort ─────────

        # Confirmation keywords — but ONLY if options were shown
        confirm_kw = ["yes, finali", "yes finali", "go ahead", "confirm", "finalise", "finalize",
                      "yes, that", "that one", "approved", "proceed"]
        if any(kw in last_user for kw in confirm_kw):
            if any("option a" in a or "option b" in a for a in assistant_msgs):
                return "finalize"

        # Occasion keywords — fallback for early turns
        occasion_kw = ["formal", "office", "business", "casual", "school", "uniform",
                       "party", "wedding", "sportswear", "sport", "work", "daily",
                       "weekend", "festive", "summer", "winter", "flannel"]
        if num_turns <= 4 and any(kw in last_user for kw in occasion_kw):
            return "occasion_given"

        if num_turns >= 3:
            return "push_forward"

        return "need_occasion"

    def get_response(self, messages: List[Dict[str, str]]) -> str:
        stage = self._get_stage(messages)
        
        user_msgs = []
        for m in messages:
            if m["role"] == "user":
                c = m["content"]
                if isinstance(c, list):
                    c = " ".join([b["text"] for b in c if b.get("type") == "text"])
                user_msgs.append(str(c).lower().strip())
                
        assistant_msgs = [m["content"].lower() for m in messages if m["role"] == "assistant"]
        last_user    = user_msgs[-1] if user_msgs else ""
        last         = last_user  # alias — all stage handlers use this

        # ── Greeting ──────────────────────────────────────────────────────────
        if stage == "greeting":
            return (
                "Hi! I'm **Dobby**, your design assistant. 🧵\n\n"
                "Let's create your perfect shirt design. What's it for?\n"
                "[OPTIONS:Formal office|Casual weekend|School uniform|Party wear|Sportswear|Winter flannel]"
            )

        # ── Explanation request ────────────────────────────────────────────────
        if stage == "explain":
            return (
                "**Dobby weave** = small geometric patterns woven into fabric (not printed). \n"
                "Very popular for premium shirts. Asked anything else?"
            )

        # ── Occasion given ─────────────────────────────────────────────────────
        if stage == "occasion_given":
            if any(kw in last for kw in ["formal", "office", "business", "work", "corporate"]):
                return (
                    "Formal shirts are our speciality! 👔\n\n"
                    "For office/formal wear, I'd recommend a **Plain weave poplin** — "
                    "crisp, smooth, and very professional. Yarn count would be 50s or 60s.\n\n"
                    "Now, what **pattern or design** are you thinking?\n"
                    "[OPTIONS:Solid colour|Pin stripe|Bengal stripe|Graph check|Window pane check|Fil-a-fil texture|Dobby geometric|Shadow stripe|Herringbone|Micro check|Tattersall check|Ombre stripe]"
                )
            if any(kw in last for kw in ["casual", "weekend", "daily", "everyday", "relaxed"]):
                return (
                    "Great! What **pattern** do you like?\n"
                    "[OPTIONS:Solid|Stripe|Check|Gingham|Plaid|Oxford|Textured]"
                )
            if any(kw in last for kw in ["school", "uniform"]):
                return (
                    "Perfect! School uniforms need durability. What **colors** does the school use?\n"
                    "[OPTIONS:White + Navy|White + Sky Blue|White + Grey|Light Blue + White|White only|Navy + White]"
                )
            if any(kw in last for kw in ["party", "wedding", "festive", "celebration"]):
                return (
                    "Party wear shines! What **color palette**?\n"
                    "[OPTIONS:Burgundy + Gold|Royal Blue + White|Emerald + Black|Purple + Cream|Navy + Gold|Teal + White]"
                )
            if any(kw in last for kw in ["flannel", "winter"]):
                return (
                    "Winter flannel! Choose your **check pattern & colors**.\n"
                    "[OPTIONS:Red + Black|Navy + White|Brown + Beige|Grey + Black|Burgundy + Grey|Forest Green + Red|Plaid Blue|Tartan]"
                )
            # Generic occasion fallback
            return (
                "Great! What **pattern or design** interests you?\n"
                "[OPTIONS:Solid Color|Stripe|Check|Gingham|Fil-a-Fil|Dobby|Herringbone|Shadow Stripe]"
            )

        # ── Pattern given ──────────────────────────────────────────────────────
        if stage == "pattern_given":
            if any(kw in last for kw in ["solid", "plain colour", "plain color", "no pattern", "one color", "one colour"]):
                return (
                    "Solid color! What **shade** would you prefer?\\n"
                    "[OPTIONS:White|Sky Blue|Light Blue|Navy|Charcoal|Cream|Pink|Lavender|Sage|Olive|Coral|Steel Blue]"
                )
            if any(kw in last for kw in ["stripe", "pin", "bengal"]):
                return (
                    "What stripe size do you prefer?\n"
                    "[OPTIONS:Micro|Small|Medium|Large]"
                )
            if any(kw in last for kw in ["check", "plaid", "tartan"]):
                return (
                    "Checks! What **color combination**?\\n"
                    "[OPTIONS:Navy + White|Brown + Beige|Red + Black|Blue + Green|Grey + Black|Burgundy + Gold|Teal + White|Camel + Brown]"
                )
            return (
                "Great pattern choice! What **colors** would work best?\\n"
                "[OPTIONS:Two Colors|Three Colors|Single Color]\\"
            )

        # ── Stripe size given ──────────────────────────────────────────────────────
        if stage == "stripe_size_given":
            if "micro" in last:
                self.stripe_size_name = "Micro"
            elif "small" in last:
                self.stripe_size_name = "Small"
            elif "large" in last:
                self.stripe_size_name = "Large"
            else:
                self.stripe_size_name = "Medium"
            return (
                "How many colors do you want in the design?\n"
                "[OPTIONS:2|4|6|8|12]"
            )

        # ── Color count given ──────────────────────────────────────────────────
        if stage == "color_count_given":
            # Parse number from user reply
            count_map = {"2": 2, "4": 4, "6": 6, "8": 8, "12": 12}
            self.color_count = count_map.get(last.strip(), 4)
            return (
                "Which color should be the **base color** of your design?\n"
                "[OPTIONS:White|Navy Blue|Sky Blue|Black|Grey|Beige|Forest Green|Burgundy]"
            )

        # ── Base color given ───────────────────────────────────────────────────
        if stage == "base_color_given":
            base_options = ["white", "navy blue", "sky blue", "black", 
                            "grey", "beige", "forest green", "burgundy"]
            matched = next((b for b in base_options if b in last), None)
            self.base_color = matched.title() if matched else "White"
            return (
                "Great choice! Let me suggest two design options:\n\n"
                "**A** — Classic & Formal\n"
                "**B** — Smart Casual\n\n"
                "Which appeals to you?\n"
                "[OPTIONS:Option A|Option B|Different Style]"
            )

        # ── Colour given ───────────────────────────────────────────────────────
        if stage == "colour_given":
            # Check if two colours mentioned — if so, ask for percentage split
            has_two_colours = (
                (" and " in last or "/" in last or "+" in last or "," in last) and
                sum(1 for kw in ["blue", "white", "navy", "grey", "gray", "black", "red",
                                  "green", "pink", "brown", "cream", "maroon", "gold",
                                  "yellow", "beige", "ivory", "charcoal", "sky", "light"]
                    if kw in last) >= 1
            )
            # Also check full conversation for two-colour mentions
            all_user_so_far = " ".join([m["content"].lower() for m in messages if m["role"] == "user"])
            colour_count = sum(1 for kw in ["navy", "blue", "white", "grey", "gray", "black",
                                             "red", "green", "pink", "cream", "maroon", "sky",
                                             "charcoal", "beige", "ivory", "gold"]
                               if kw in last)
            if colour_count >= 2 or has_two_colours:
                return (
                    "Great combo! How should we **split the colors**?\\n"
                    "[OPTIONS:50/50 Equal|60/40 First Dominant|70/30 First Strong|75/25 More First|80/20 Strongly First]"
                )
            return (
                "Perfect! Ready to finalize your design?\\n"
                "[OPTIONS:Yes, Finalize|Show Options|More Colors]"
            )

        # ── Percentage given — now ask quality ────────────────────────────────
        if stage == "percentage_given":
            return (
                "Perfect! Ready to finalize your shirt design?\\n"
                "[OPTIONS:Yes, Create Design|Review Choices|Start Over]"
            )

        # ── Quality given — now present options ────────────────────────────────
        if stage == "quality_given":
            # Detect colour from earlier messages
            all_user = " ".join([m["content"].lower() for m in messages if m["role"] == "user"])

            colour1, colour2 = "Navy Blue", "White"
            if "sky blue" in all_user or "sky" in all_user:
                colour1, colour2 = "Sky Blue", "White"
            elif "charcoal" in all_user:
                colour1, colour2 = "Charcoal", "White"
            elif "black" in all_user:
                colour1, colour2 = "Black", "White"
            elif "white" in all_user and "blue" not in all_user:
                colour1, colour2 = "White", "Off-White"
            elif "red" in all_user:
                colour1, colour2 = "Red", "White"
            elif "green" in all_user:
                colour1, colour2 = "Forest Green", "White"
            elif "grey" in all_user or "gray" in all_user:
                colour1, colour2 = "Charcoal Grey", "White"
            elif "pink" in all_user:
                colour1, colour2 = "Pale Pink", "White"

            return (
                f"**Option A — {colour1}/{colour2} Formal**\\n"
                f"Plain weave, crisp & professional.\\n\\n"
                f"**Option B — {colour1}/Texture**\\n"
                f"Oxford weave, relaxed feel.\\n"
                f"[OPTIONS:Option A|Option B|Show More Options]"
            )

        # ── Push forward if stuck ──────────────────────────────────────────────
        if stage == "push_forward":
            return (
                "Let me suggest two great options:\\n\\n"
                "**A — Formal Classic (Navy/White, Plain)**\\n"
                "Crisp & professional.\\n\\n"
                "**B — Smart Casual (Sky Blue/White, Oxford)**\\n"
                "Relaxed texture. Which appeals you?\\n"
                "[OPTIONS:Option A|Option B|Different Style]"
            )

        # ── Finalize — output the design JSON ─────────────────────────────────
        if stage == "finalize":
            # Read all user messages to infer design choices
            all_user = " ".join([m["content"].lower() for m in messages if m["role"] == "user"])
            assistant_msgs = [m["content"].lower() for m in messages if m["role"] == "assistant"]
            last_options = next((a for a in reversed(assistant_msgs) if "option a" in a), "")
            # Get stripe size name (stored from earlier or inferred)
            stripe_size_name = getattr(self, 'stripe_size_name', 'Medium')
            stripe_range = STRIPE_SIZE_MAP.get(stripe_size_name, STRIPE_SIZE_MAP["Medium"])
            # Infer premium vs standard
            is_premium = any(kw in all_user for kw in ["premium", "luxury", "fine", "option b"])
            is_option_b = "option b" in all_user or "b" == all_user.split()[-1] if all_user.split() else False

            # ── Parse colours from conversation ────────────────────────────────
            colour1, colour2 = "Navy Blue", "White"
            pct1, pct2 = 60, 40

            # Map keywords to proper colour names
            colour_map = {
                "navy blue": "Navy Blue", "navy": "Navy Blue",
                "sky blue": "Sky Blue", "light blue": "Light Blue",
                "white": "White", "off-white": "Off-White", "ivory": "Ivory", "cream": "Cream",
                "black": "Black", "charcoal": "Charcoal Grey", "grey": "Grey", "gray": "Grey",
                "red": "Red", "maroon": "Maroon", "burgundy": "Burgundy",
                "green": "Forest Green", "mint": "Mint Green",
                "pink": "Pale Pink", "rose": "Rose",
                "gold": "Gold", "yellow": "Yellow", "beige": "Beige",
                "brown": "Brown", "indigo": "Indigo", "teal": "Teal", "purple": "Purple",
            }

            # Find all colours mentioned across the whole conversation
            detected = []
            for kw, name in colour_map.items():
                if kw in all_user and name not in detected:
                    detected.append(name)

            if len(detected) >= 2:
                colour1, colour2 = detected[0], detected[1]
            elif len(detected) == 1:
                colour1 = detected[0]
                colour2 = "White" if colour1 != "White" else "Off-White"

            # ── Parse percentage split from conversation ────────────────────────
            import re as _re
            # Look for patterns like "50-50", "60/40", "60 40", "70 percent", "50 50"
            pct_patterns = [
                r"(\d+)\s*[-/]\s*(\d+)",          # 60-40, 60/40
                r"(\d+)\s*%.*?(\d+)\s*%",          # 60% ... 40%
                r"(\d+)\s+(\d+)\s*(?:percent|%)?", # 60 40
            ]
            found_pct = False
            for pat in pct_patterns:
                m = _re.search(pat, all_user)
                if m:
                    a, b = int(m.group(1)), int(m.group(2))
                    if 10 <= a <= 90 and 10 <= b <= 90 and abs((a + b) - 100) <= 5:
                        pct1, pct2 = a, b
                        found_pct = True
                        break

            # Handle "equal", "half", "50-50", "same" keywords
            if not found_pct:
                if any(kw in all_user for kw in ["equal", "half and half", "50-50", "50/50", "same amount", "split equally"]):
                    pct1, pct2 = 50, 50

            # Infer weave and specs
            if is_premium and not is_option_b:
                yarn, epi, ppi, gsm, construction = "60s", 144, 80, 108, "144 x 80 / 60s x 60s"
                weave, design_style = "Plain", "Regular"
                size, size_name = "Micro", "Micro"
                contrast = "Low"
                occasion = "Formal"
            elif is_premium and is_option_b:
                yarn, epi, ppi, gsm, construction = "80s/2", 172, 90, 105, "172 x 90 / 80s/2 x 80s/2"
                weave, design_style = "Plain", "Fil-a-Fil"
                size, size_name = "Micro", "Micro"
                contrast = "Low"
                occasion = "Formal"
            elif "oxford" in all_user or "casual" in all_user or is_option_b:
                yarn, epi, ppi, gsm, construction = "40s", 100, 80, 120, "100 x 80 / 40s x 40s"
                weave, design_style = "Oxford", "Regular"
                size, size_name = "Small", "Small"
                contrast = "Medium"
                occasion = "Casual"
            elif "solid" in all_user or "plain colour" in all_user or "plain color" in all_user:
                yarn, epi, ppi, gsm, construction = "50s", 132, 72, 115, "132 x 72 / 50s x 50s"
                weave, design_style = "Plain", "Solid"
                size, size_name = "Full Size", "Full Size"
                contrast = "Low"
                occasion = "Formal"
                # Only force 100% if user mentioned just one colour
                # If two colours were mentioned, keep detected split (allow texture blend)
                detected_colours_count = sum(1 for kw in ["navy", "blue", "white", "grey",
                    "gray", "black", "red", "green", "pink", "cream", "maroon", "sky",
                    "charcoal", "beige", "ivory", "gold"] if kw in all_user)
                if detected_colours_count < 2:
                    pct1, pct2 = 100, 0
                    colour2 = colour1  # truly single-colour solid
            elif "check" in all_user or "plaid" in all_user:
                yarn, epi, ppi, gsm, construction = "40s", 100, 80, 118, "100 x 80 / 40s x 40s"
                weave, design_style = "Twill", "Regular"
                size, size_name = "Medium", "Medium"
                contrast = "High"
                occasion = "Casual"
            else:
                # default: formal stripe
                yarn, epi, ppi, gsm, construction = "50s", 132, 72, 115, "132 x 72 / 50s x 50s"
                weave, design_style = "Plain", "Regular"
                size, size_name = "Small", stripe_size_name  # use user-selected stripe size or Small
                contrast = "Medium"
                occasion = "Formal"

            # ── Build colors using build_color_palette() if user selected via new path ─────
            color_count = getattr(self, 'color_count', None)
            base_color  = getattr(self, 'base_color', None)
            
            if color_count and base_color:
                # User went through color_count → base_color flow
                colors = build_color_palette(base_color, color_count)
                # Build colors_json from palette
                colors_json_lines = []
                for color in colors:
                    colors_json_lines.append(f'    {{ "name": "{color["name"]}", "type": "{color["type"]}", "percentage": {color["percentage"]} }}')
                colors_json = ',\n'.join(colors_json_lines)
            else:
                # ── Backward compatibility: old color path ────────────────────────────
                colour1, colour2 = "Navy Blue", "White"
                pct1, pct2 = 60, 40

                # Map keywords to proper colour names
                colour_map = {
                    "navy blue": "Navy Blue", "navy": "Navy Blue",
                    "sky blue": "Sky Blue", "light blue": "Light Blue",
                    "white": "White", "off-white": "Off-White", "ivory": "Ivory", "cream": "Cream",
                    "black": "Black", "charcoal": "Charcoal Grey", "grey": "Grey", "gray": "Grey",
                    "red": "Red", "maroon": "Maroon", "burgundy": "Burgundy",
                    "green": "Forest Green", "mint": "Mint Green",
                    "pink": "Pale Pink", "rose": "Rose",
                    "gold": "Gold", "yellow": "Yellow", "beige": "Beige",
                    "brown": "Brown", "indigo": "Indigo", "teal": "Teal", "purple": "Purple",
                }

                # Find all colours mentioned across the whole conversation
                detected = []
                for kw, name in colour_map.items():
                    if kw in all_user and name not in detected:
                        detected.append(name)

                if len(detected) >= 2:
                    colour1, colour2 = detected[0], detected[1]
                elif len(detected) == 1:
                    colour1 = detected[0]
                    colour2 = "White" if colour1 != "White" else "Off-White"

                # ── Parse percentage split from conversation ────────────────────────
                import re as _re
                # Look for patterns like "50-50", "60/40", "60 40", "70 percent", "50 50"
                pct_patterns = [
                    r"(\d+)\s*[-/]\s*(\d+)",          # 60-40, 60/40
                    r"(\d+)\s*%.*?(\d+)\s*%",          # 60% ... 40%
                    r"(\d+)\s+(\d+)\s*(?:percent|%)?", # 60 40
                ]
                found_pct = False
                for pat in pct_patterns:
                    m = _re.search(pat, all_user)
                    if m:
                        a, b = int(m.group(1)), int(m.group(2))
                        if 10 <= a <= 90 and 10 <= b <= 90 and abs((a + b) - 100) <= 5:
                            pct1, pct2 = a, b
                            found_pct = True
                            break

                # Handle "equal", "half", "50-50", "same" keywords
                if not found_pct:
                    if any(kw in all_user for kw in ["equal", "half and half", "50-50", "50/50", "same amount", "split equally"]):
                        pct1, pct2 = 50, 50

                colors_json = f'    {{ "name": "{colour1}", "percentage": {pct1} }}'
                if pct2 > 0 and colour1 != colour2:
                    colors_json += f',\n    {{ "name": "{colour2}", "percentage": {pct2} }}'

            # Build stripe section using named size mapping
            if design_style == "Solid":
                stripe_section = (
                    '  "stripe": {\n'
                    '    "stripeSizeRangeMm": { "min": 0, "max": 0 },\n'
                    '    "stripeMultiplyRange": { "min": 0, "max": 0 },\n'
                    '    "isSymmetry": true,\n'
                    '    "note": "N/A - solid colour"\n'
                    '  },'
                )
            else:
                # Use the mapped stripe range
                stripe_section = (
                    f'  "stripe": {{\n'
                    f'    "stripeSizeRangeMm": {{ "min": {stripe_range["min"]}, "max": {stripe_range["max"]} }},\n'
                    f'    "stripeMultiplyRange": {{ "min": 1, "max": 2 }},\n'
                    f'    "isSymmetry": true\n'
                    f'  }},'
                )

            # Get design size range from map
            design_size_range = DESIGN_SIZE_MAP.get(size, DESIGN_SIZE_MAP["Medium"])

            summary = (
                f"Your {occasion.lower()} {design_style.lower()} shirt in "
                f"{colour1}{f'/{colour2}' if colour1 != colour2 and pct2 > 0 else ''} with {weave.lower()} weave. Perfect!"
            )

            return (
                f"Perfect! Design finalised.\n\n"
                f"<DESIGN_OUTPUT>\n"
                f"{{\n"
                f'  "design": {{\n'
                f'    "designSize": "{size}",\n'
                f'    "designSizeRangeCm": {{ "min": {design_size_range["min"]}, "max": {design_size_range["max"]} }},\n'
                f'    "designStyle": "{design_style}",\n'
                f'    "weave": "{weave}"\n'
                f'  }},\n'
                f"{stripe_section}\n"
                f'  "colors": [\n'
                f"{colors_json}\n"
                f'  ],\n'
                f'  "visual": {{ "contrastLevel": "{contrast}" }},\n'
                f'  "market": {{ "occasion": "{occasion}" }}\n'
                f'}}\n'
                f'</DESIGN_OUTPUT>\n\n'
                f'{summary}'
            )

        # ── Default fallback ─────────────────────────────────────────────────
        # If we reach here, check if user actually gave an occasion we missed
        occasion_kw = ["formal", "office", "business", "casual", "school", "uniform",
                       "party", "wedding", "sportswear", "sport", "work", "daily",
                       "weekend", "festive", "summer", "winter", "flannel"]
        if any(kw in last_user for kw in occasion_kw):
            # Re-route directly to occasion handler
            stage = "occasion_given"
            # Re-run occasion_given logic inline
            if any(kw in last_user for kw in ["formal", "office", "business", "work", "corporate"]):
                return (
                    "Formal wear! What **pattern**?\n"
                    "[OPTIONS:Solid|Stripe|Check|Gingham|Fil-a-Fil|Dobby|Herringbone]"
                )
            if any(kw in last_user for kw in ["casual", "weekend", "daily", "everyday", "relaxed", "sport"]):
                return (
                    "Casual! What **pattern** would you prefer?\n"
                    "[OPTIONS:Solid Color|Stripe|Check|Gingham|Oxford|Herringbone|Madras Plaid]"
                )
            if any(kw in last_user for kw in ["school", "uniform"]):
                return (
                    "School uniforms! Choose your **colors**.\n"
                    "[OPTIONS:White + Navy|White + Sky Blue|White + Grey|Light Blue + White|Navy + White|White Only]"
                )
            if any(kw in last_user for kw in ["party", "wedding", "festive", "celebration"]):
                return (
                    "Party wear! Select your **color palette**.\n"
                    "[OPTIONS:Burgundy + Gold|Royal Blue + White|Emerald + Black|Purple + Cream|Navy + Gold|Teal + White|Deep Purple + Silver]"
                )
            if any(kw in last_user for kw in ["winter", "flannel"]):
                return (
                    "Flannel! Choose your **check pattern & colors**.\n"
                    "[OPTIONS:Red + Black|Navy + White|Brown + Beige|Grey + Black|Burgundy + Grey|Forest Green + Red|Plaid Blue]"
                )

        return (
            "Let me help you design the perfect shirt! 🧵\n\n"
            "What is this shirt fabric for?\n"
            "[OPTIONS:Formal office wear|Casual weekend|School uniform|Party / festive wear|Sportswear|Winter flannel]"
        )

    def get_model_name(self) -> str:
        return self.model

    def is_configured(self) -> bool:
        return True


class LLMProviderFactory:
    """Factory for creating and caching LLM providers."""

    _providers = {
        "groq": GroqProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "openrouter": OpenRouterProvider,
        "mock": MockProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        cls._providers[name.lower()] = provider_class

    @classmethod
    def get_provider(cls, provider_name: str = "groq") -> LLMProvider:
        provider_name = provider_name.lower().strip()

        # Return cached instance if available
        if provider_name in _provider_cache:
            return _provider_cache[provider_name]

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Unknown provider '{provider_name}'. Available: {available}")

        provider = cls._providers[provider_name]()

        if not provider.is_configured():
            raise ValueError(
                f"Provider '{provider_name}' is not configured. Missing API key."
            )

        _provider_cache[provider_name] = provider
        return provider

    @classmethod
    def get_available_providers(cls) -> List[str]:
        return list(cls._providers.keys())


# ============================================================================
# VISION PROVIDERS (Image Analysis)
# ============================================================================

import json
import hashlib
import base64

VISION_PROMPT = """You are an expert yarn-dyed shirting fabric analyst
with 20+ years of experience in textile manufacturing.

Analyze this fabric/garment image with extreme precision.
Return ONLY a valid JSON object — no markdown, no explanation, no code fences.

ANALYSIS INSTRUCTIONS:

1. COLORS — Look very carefully at the actual yarn threads, not just the
   overall impression. Yarn-dyed fabrics have individual colored yarns
   woven together. Identify each distinct yarn color separately.

   Common shirting colors to look for:
   - Blues: Navy Blue, Royal Blue, Sky Blue, Cobalt Blue, French Blue,
     Prussian Blue, Oxford Blue, Cornflower Blue, Air Force Blue
   - Whites/Creams: White, Off-White, Ecru, Cream, Ivory
   - Reds: Red, Burgundy, Wine, Maroon, Claret, Crimson, Oxblood
   - Greens: Bottle Green, Forest Green, Olive Green, Sage, Hunter Green
   - Browns: Tan, Camel, Khaki, Chocolate, Coffee
   - Greys: Light Grey, Mid Grey, Charcoal Grey, Graphite, Silver
   - Blacks: Black, Near-Black, Dark Charcoal
   - Yellows/Golds: Gold, Yellow, Mustard, Ochre
   - Pinks: Pink, Dusty Rose, Blush
   - Purples: Purple, Lavender, Lilac, Plum

   For EACH color:
   - Use the most specific textile industry name (e.g. "Navy Blue" not "dark blue")
   - Estimate percentage of total fabric surface covered by that yarn color
   - Assign type: "base" (dominant), "family" (similar tone to base),
     "harmony" (complementary), "contrast" (opposing/accent)
   - All percentages MUST sum to exactly 100
   - Base color always has the HIGHEST percentage

2. DESIGN — Analyze the structural pattern:

   CRITICAL PATTERN DETECTION RULE:
   - If you see stripes crossing in BOTH horizontal AND vertical directions
     forming squares or rectangles → designStyle MUST be "Counter"
   - If you see a plaid, check, tartan, gingham, or windowpane → "Counter"
   - "Regular" is ONLY for fabrics with parallel stripes in ONE direction only
   - When in doubt between Regular and Counter → choose "Counter"

   SIZE DETECTION GUIDE (look at the check repeat width):
   - If the full check repeat (one complete square) is smaller than a fingernail → Micro
   - If it fits 3-4 repeats across a shirt button placket width → Small
   - If it fits 1-2 repeats across a shirt button placket width → Medium
   - If the check is clearly large/bold, one repeat is palm-width → Large
   - For most visible plaid/tartan fabrics → Large

   - designSize: How large is the repeat pattern?
     Micro = tiny hairline details under 1cm
     Small = subtle detail 0.5–2cm (fine stripes, mini checks)
     Medium = clearly visible 2–5cm (regular stripes, medium checks)
     Large = bold 5–25cm (wide stripes, large plaids)
     Full Size = pattern covers most of garment >25cm

   - designStyle:
     Regular = uniform repeating stripes of equal spacing (ONE direction only)
     Gradational = stripes that change in width/color intensity
     Fila Fil = 2-color alternating single threads (salt & pepper effect)
     Counter = checks or squares formed by crossing stripes (BOTH directions)
     Multicolor = 4+ colors in complex non-regular arrangement

   - weave: Look at the texture/construction:
     Plain = flat, simple over-under weave, smooth surface
     Twill = diagonal lines visible on surface (denim-like)
     Oxford = small basketweave texture, slightly raised
     Dobby = small geometric raised patterns woven into fabric

3. STRIPE ANALYSIS — For striped or checked fabrics:
   - Measure stripe widths relative to each other
   - stripeSizeRangeMm: typical range of individual stripe widths in mm
   - stripeMultiplyRange: how many times the repeat multiplies
   - isSymmetry: true if stripe sequence mirrors itself (A-B-C-B-A pattern)

4. VISUAL CONTRAST:
   Low = colors are close in tone (e.g. navy + medium blue + white)
   Medium = moderate difference (e.g. navy + white + light blue)
   High = strong contrast (e.g. black + white, navy + bright yellow)

5. OCCASION — Based on color palette and pattern formality:
   Formal = dark base colors (navy, black, charcoal, white),
            fine/subtle patterns, business appropriate
   Casual = medium/bright colors, relaxed patterns, everyday wear
   Party Wear = bold colors, high contrast, festive patterns,
               rich colors (burgundy+gold, black+red etc.)

CRITICAL RULES:
- For a dark plaid: identify ALL the crossing stripe colors separately
- For a check: the warp (horizontal) and weft (vertical) yarn colors
  may be different — list both
- Never say just "Red" when "Burgundy" or "Wine" is more accurate
- Never return fewer than 2 colors for any fabric
- If you see a windowpane check, the thin crossing lines are a separate color
- Percentages: base 30-55%, secondary 20-35%, others divide the rest
- ALWAYS include ALL fields: colors, design (with designSizeRangeCm), stripe, visual, market

Return this exact JSON structure:
{
  "colors": [
    {"name": "Navy Blue", "type": "base", "percentage": 45},
    {"name": "White",     "type": "contrast", "percentage": 30},
    {"name": "Royal Blue","type": "family", "percentage": 25}
  ],
  "design": {
    "designSize": "Small",
    "designSizeRangeCm": {"min": 0.5, "max": 2.0},
    "designStyle": "Regular",
    "weave": "Oxford"
  },
  "stripe": {
    "stripeSizeRangeMm":   {"min": 0.2, "max": 2.0},
    "stripeMultiplyRange": {"min": 1, "max": 3},
    "isSymmetry": true
  },
  "visual":  {"contrastLevel": "High"},
  "market":  {"occasion": "Formal"}
}"""


# Design style normalization mapping
DESIGN_STYLE_MAP = {
    "solid": "Regular",
    "plain": "Regular",
    "stripe": "Regular",
    "stripes": "Regular",
    "check": "Counter",
    "checks": "Counter",
    "plaid": "Counter",
    "tartan": "Counter",
    "gingham": "Counter",
    "windowpane": "Counter",
    "fila fil": "Fila Fil",
    "filafil": "Fila Fil",
    "fil-a-fil": "Fila Fil",
    "gradational": "Gradational",
    "multicolor": "Multicolor",
    "multi": "Multicolor",
}


def normalize_design_style(value: str) -> str:
    """Normalize design style to valid schema value."""
    valid = {"Regular", "Gradational", "Fila Fil", "Counter", "Multicolor"}
    if not value:
        return "Regular"
    if value in valid:
        return value
    return DESIGN_STYLE_MAP.get(value.lower(), "Regular")


class MockVisionProvider:
    """Mock vision provider for testing and offline use."""

    MOCK_RESULTS = [
        {
            "colors": [
                {"name": "Navy Blue", "type": "Base", "percentage": 50},
                {"name": "White", "type": "Contrast", "percentage": 50},
            ],
            "design": {
                "designSize": "Large",
                "designSizeRangeCm": {"min": 5, "max": 15},
                "designStyle": "Regular",
                "weave": "Twill",
            },
            "stripe": {
                "stripeSizeRangeMm": {"min": 5, "max": 10},
                "stripeMultiplyRange": {"min": 1, "max": 1},
                "isSymmetry": True,
                "stripeSize": "Large",
            },
            "visual": {
                "contrastLevel": "High",
                "texture": "Twill",
            },
            "market": {
                "occasion": "Formal",
            },
        },
        {
            "colors": [
                {"name": "Red", "type": "Base", "percentage": 40},
                {"name": "Dark Red", "type": "Family", "percentage": 30},
                {"name": "Black", "type": "Harmony", "percentage": 20},
                {"name": "White", "type": "Contrast", "percentage": 10},
            ],
            "design": {
                "designSize": "Medium",
                "designSizeRangeCm": {"min": 2, "max": 5},
                "designStyle": "Regular",
                "weave": "Twill",
            },
            "stripe": {
                "stripeSizeRangeMm": {"min": 3, "max": 8},
                "stripeMultiplyRange": {"min": 1, "max": 2},
                "isSymmetry": True,
                "stripeSize": "Medium",
            },
            "visual": {
                "contrastLevel": "High",
                "texture": "Checks",
            },
            "market": {
                "occasion": "Casual",
            },
        },
        {
            "colors": [
                {"name": "Light Blue", "type": "Base", "percentage": 60},
                {"name": "White", "type": "Family", "percentage": 40},
            ],
            "design": {
                "designSize": "Small",
                "designSizeRangeCm": {"min": 0.5, "max": 2},
                "designStyle": "Fil-a-Fil",
                "weave": "Oxford",
            },
            "stripe": {
                "stripeSizeRangeMm": {"min": 0.5, "max": 2},
                "stripeMultiplyRange": {"min": 0, "max": 0},
                "isSymmetry": True,
                "stripeSize": "Small",
            },
            "visual": {
                "contrastLevel": "Low",
                "texture": "Oxford",
            },
            "market": {
                "occasion": "Formal",
            },
        },
        {
            "colors": [
                {"name": "Emerald", "type": "Base", "percentage": 45},
                {"name": "Gold", "type": "Harmony", "percentage": 35},
                {"name": "Black", "type": "Contrast", "percentage": 20},
            ],
            "design": {
                "designSize": "Medium",
                "designSizeRangeCm": {"min": 2, "max": 5},
                "designStyle": "Gradational",
                "weave": "Jacquard",
            },
            "stripe": {
                "stripeSizeRangeMm": {"min": 2, "max": 6},
                "stripeMultiplyRange": {"min": 1, "max": 3},
                "isSymmetry": True,
                "stripeSize": "Medium",
            },
            "visual": {
                "contrastLevel": "High",
                "texture": "Jacquard",
            },
            "market": {
                "occasion": "Party Wear",
            },
        },
    ]

    def analyze_image(self, image_b64: str, mime_type: str = "image/jpeg") -> Dict:
        """Return a deterministic mock result based on image hash."""
        # Use hash to ensure same image always gets same result
        image_hash = int(hashlib.md5(image_b64.encode()).hexdigest(), 16)
        result_index = image_hash % len(self.MOCK_RESULTS)
        return self.MOCK_RESULTS[result_index].copy()

    def get_model_name(self) -> str:
        return "mock-vision"

    def is_configured(self) -> bool:
        return True


class GeminiVisionProvider:
    """Google Gemini vision provider for real image analysis."""

    def __init__(self, api_key: str):
        """Initialize Gemini provider."""
        self.api_key = api_key
        self.model_name = "gemini-2.0-flash"
        try:
            import google.genai
            self.client = google.genai.Client(api_key=api_key)
        except ImportError:
            raise ImportError("google-genai package not installed. Run: pip install google-genai")

    def analyze_image(self, image_b64: str, mime_type: str = "image/jpeg") -> Dict:
        """Analyze image using Gemini Vision API."""
        if not self.client:
            print("⚠ Gemini client not available — falling back to mock")
            return MockVisionProvider().analyze_image(image_b64, mime_type)

        try:
            # Remove data URI prefix if present
            if image_b64.startswith("data:"):
                # Extract just the base64 part
                image_b64 = image_b64.split(",", 1)[1]

            # Decode base64 to validate
            image_bytes = base64.b64decode(image_b64)

            # Call Gemini API with vision
            import google.genai.types as types

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type
                    ),
                    VISION_PROMPT
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.05,        # LOWER = more consistent, precise
                    top_p=0.8,               # reduces randomness
                    top_k=20,                # focuses on most likely tokens
                    candidate_count=1,
                    max_output_tokens=1024,  # enough for our JSON schema
                )
            )

            # Parse response
            result_text = response.text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            try:
                result = json.loads(result_text)

                # Validate required keys exist
                required_keys = ['colors', 'design', 'stripe', 'visual', 'market']
                for key in required_keys:
                    if key not in result:
                        raise ValueError(f"Gemini response missing key: {key}")

                # Validate colors sum to 100
                total_pct = sum(c.get('percentage', 0) for c in result.get('colors', []))
                if abs(total_pct - 100) > 5:
                    # Normalize to 100
                    factor = 100 / total_pct if total_pct > 0 else 1
                    for c in result['colors']:
                        c['percentage'] = round(c['percentage'] * factor)
                    # Fix rounding to ensure exact 100
                    diff = 100 - sum(c['percentage'] for c in result['colors'])
                    result['colors'][-1]['percentage'] += diff

                # Ensure base color has highest percentage
                if result['colors']:
                    max_pct = max(c['percentage'] for c in result['colors'])
                    base_colors = [c for c in result['colors'] if c['type'] == 'base']
                    if base_colors and base_colors[0]['percentage'] < max_pct:
                        # Swap percentages so base is dominant
                        dominant = max(result['colors'], key=lambda c: c['percentage'])
                        dominant['type'] = 'base'
                        for c in result['colors']:
                            if c != dominant and c['type'] == 'base':
                                c['type'] = 'family'

                # Complete missing schema fields
                result = self._complete_schema(result)
                # Fix common pattern misclassifications
                result = self._fix_pattern_logic(result)

                return result
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠ Gemini response error: {e} — falling back to mock")
                return MockVisionProvider().analyze_image(image_b64, mime_type)

        except Exception as e:
            print(f"⚠ Gemini API error: {str(e)[:200]}... falling back to mock")
            return MockVisionProvider().analyze_image(image_b64, mime_type)

    def _complete_schema(self, result: dict) -> dict:
        """Ensure all required schema fields are present with sensible defaults."""
        design = result.get("design", {})
        design.setdefault("designSize", "Medium")
        design.setdefault("designStyle", "Regular")
        design.setdefault("weave", "Plain")

        size_ranges = {
            "Micro":     {"min": 0.1, "max": 1.0},
            "Small":     {"min": 0.5, "max": 2.0},
            "Medium":    {"min": 2.0, "max": 5.0},
            "Large":     {"min": 5.0, "max": 25.0},
            "Full Size": {"min": 25.0, "max": 100.0},
        }
        design.setdefault(
            "designSizeRangeCm",
            size_ranges.get(design.get("designSize", "Medium"), {"min": 2.0, "max": 5.0})
        )
        result["design"] = design

        if "stripe" not in result:
            stripe_defaults = {
                "Small":  {"min": 0.2, "max": 2.0},
                "Medium": {"min": 0.2, "max": 4.0},
                "Large":  {"min": 0.5, "max": 10.0},
            }
            stripe_range = stripe_defaults.get(design.get("designSize", "Medium"), {"min": 0.2, "max": 4.0})
            result["stripe"] = {
                "stripeSizeRangeMm":   stripe_range,
                "stripeMultiplyRange": {"min": 1, "max": 3},
                "isSymmetry":          True
            }

        if "visual" not in result:
            colors = result.get("colors", [])
            has_contrast = any(c.get("type") == "contrast" for c in colors)
            result["visual"] = {"contrastLevel": "High" if has_contrast else "Medium"}

        result.setdefault("market", {"occasion": "Casual"})

        return result

    def _fix_pattern_logic(self, result: dict) -> dict:
        """Apply business rules to catch common misclassifications."""
        design = result.get("design", {})
        colors = result.get("colors", [])

        # Normalize design style to valid schema values
        design["designStyle"] = normalize_design_style(design.get("designStyle", "Regular"))

        if len(colors) >= 3 and design.get("designStyle") == "Regular":
            design["designStyle"] = "Counter"

        if len(colors) >= 4 and design.get("designSize") == "Small":
            design["designSize"] = "Medium"
            design["designSizeRangeCm"] = {"min": 2.0, "max": 5.0}

        result["design"] = design
        return result

    def get_model_name(self) -> str:
        return self.model_name

    def is_configured(self) -> bool:
        return bool(self.api_key)


def get_vision_provider():
    """Factory function to get appropriate vision provider."""
    from config import VISION_PROVIDER, GEMINI_API_KEY, CLOUD_VISION_API_KEY

    provider_name = VISION_PROVIDER.lower().strip()

    if provider_name == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError(
                "Gemini vision provider selected but GEMINI_API_KEY not set. "
                "Set GEMINI_API_KEY environment variable or use VISION_PROVIDER=mock"
            )
        return GeminiVisionProvider(GEMINI_API_KEY)
    elif provider_name == "cloud-vision":
        if not CLOUD_VISION_API_KEY:
            print("⚠ Cloud Vision API key not set — falling back to mock")
            return MockVisionProvider()
        try:
            from google.cloud import vision as cloud_vision
            client = vision.ImageAnnotatorClient()
            return CloudVisionProvider(CLOUD_VISION_API_KEY)
        except ImportError:
            print("⚠ google-cloud-vision not installed — falling back to mock")
            return MockVisionProvider()
    else:
        # Default to mock provider
        return MockVisionProvider()


class BedrockVisionProvider:
    """AWS Bedrock provider for vision with Gemma 3 12B."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model_name = "bedrock-gemma-3-12b"
        self.client = None

        try:
            import boto3
            self.client = boto3.client(
                'bedrock-runtime',
                aws_access_key_id=api_key,
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        except ImportError:
            print("⚠ boto3 not installed for Bedrock Vision")
        except Exception as e:
            print(f"⚠ Bedrock Vision client error: {e}")

    def analyze_image(self, image_b64: str, mime_type: str = 'image/jpeg') -> dict:
        """Analyze image using Bedrock Gemma 3 12B."""
        if not self.client:
            return MockVisionProvider().analyze_image(image_b64, mime_type)

        try:
            # For now, fallback to mock since Bedrock vision may not be available
            print("⚠ Bedrock vision not fully implemented, using mock")
            return MockVisionProvider().analyze_image(image_b64, mime_type)

        except Exception as e:
            print(f"⚠ Bedrock Vision error: {e}")
            return MockVisionProvider().analyze_image(image_b64, mime_type)

    def get_model_name(self) -> str:
        return self.model_name

    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)


class CloudVisionProvider:
    """Google Cloud Vision API provider for image analysis."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            from google.cloud import vision
            self.client = vision.ImageAnnotatorClient()
        except ImportError:
            self.client = None
            print("⚠ google-cloud-vision package not installed")

    def analyze_image(self, image_b64: str, mime_type: str = 'image/jpeg') -> dict:
        """Analyze image using Google Cloud Vision API."""
        if not self.client:
            return MockVisionProvider().analyze_image(image_b64, mime_type)

        try:
            # Extract base64 data if it's a data URL
            if ',' in image_b64:
                image_b64 = image_b64.split(',', 1)[1]

            import base64
            image_content = base64.b64decode(image_b64)

            # Create image object
            from google.cloud import vision
            image = vision.Image(content=image_content)

            # Detect colors
            image_properties = self.client.image_properties(image=image)
            colors = []
            if image_properties.annotation.colors:
                for i, color_info in enumerate(image_properties.annotation.colors[:6]):
                    color = color_info.color
                    rgb_name = self._rgb_to_name(color.red, color.green, color.blue)
                    colors.append({
                        "name": rgb_name,
                        "type": "base" if i == 0 else "contrast",
                        "percentage": int(color_info.score * 100)
                    })

            # Normalize percentages
            if colors:
                total = sum(c['percentage'] for c in colors)
                if total > 0:
                    for c in colors:
                        c['percentage'] = int(c['percentage'] / total * 100)

            return {
                "colors": colors or [{"name": "Grey", "type": "base", "percentage": 100}],
                "design": {
                    "designSize": "Medium",
                    "designSizeRangeCm": {"min": 2.0, "max": 5.0},
                    "designStyle": "Regular",
                    "weave": "Plain"
                },
                "stripe": {
                    "stripeSizeRangeMm": {"min": 0.2, "max": 4.0},
                    "stripeMultiplyRange": {"min": 1, "max": 3},
                    "isSymmetry": True
                },
                "visual": {"contrastLevel": "Medium"},
                "market": {"occasion": "Casual"}
            }
        except Exception as e:
            print(f"⚠ Cloud Vision error: {e}")
            return MockVisionProvider().analyze_image(image_b64, mime_type)

    def _rgb_to_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB to closest textile color name."""
        color_map = {
            (0, 0, 0): "Black", (255, 255, 255): "White",
            (139, 0, 0): "Dark Red", (178, 34, 34): "Firebrick",
            (205, 92, 92): "Indian Red", (220, 20, 60): "Crimson",
            (255, 0, 0): "Red", (255, 127, 80): "Coral",
            (255, 165, 0): "Orange", (255, 215, 0): "Gold",
            (255, 255, 0): "Yellow", (173, 255, 47): "Green Yellow",
            (0, 255, 0): "Lime", (0, 255, 127): "Spring Green",
            (0, 128, 0): "Green", (0, 100, 0): "Dark Green",
            (0, 255, 255): "Cyan", (0, 206, 209): "Dark Turquoise",
            (0, 191, 255): "Deep Sky Blue", (30, 144, 255): "Dodger Blue",
            (0, 0, 255): "Blue", (0, 0, 139): "Dark Blue",
            (75, 0, 130): "Indigo", (128, 0, 128): "Purple",
            (255, 0, 255): "Magenta", (255, 192, 203): "Pink",
            (188, 143, 143): "Rosy Brown", (205, 133, 63): "Peru",
            (210, 180, 140): "Tan", (139, 69, 19): "Saddle Brown",
            (160, 82, 45): "Sienna", (128, 128, 0): "Olive",
            (128, 128, 128): "Grey", (169, 169, 169): "Dark Grey",
        }

        min_dist = float('inf')
        closest = "Grey"
        for (cr, cg, cb), name in color_map.items():
            dist = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest = name
        return closest

    def get_model_name(self) -> str:
        return "cloud-vision"

    def is_configured(self) -> bool:
        return bool(self.api_key)
