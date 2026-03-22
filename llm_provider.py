"""
Abstract LLM Provider interface and factory for provider-agnostic LLM calls.
Supports Groq, OpenAI, Anthropic, OpenRouter, and Mock providers.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

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
        completion = self.client.chat.completions.create(
            model=self.model,
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
        user_msgs    = [m["content"].lower().strip() for m in messages if m["role"] == "user"]
        assistant_msgs = [m["content"].lower() for m in messages if m["role"] == "assistant"]
        num_turns    = len(user_msgs)

        if num_turns == 0:
            return "greeting"

        last_user = user_msgs[-1]

        # ── Always-first checks ───────────────────────────────────────────────

        # Explanation requests (can come at any point)
        explain_kw = ["what is dobby", "what's dobby", "explain dobby", "dobby weave",
                      "what is gsm", "what is epi", "what is yarn", "explain gsm"]
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
        user_msgs    = [m["content"].lower().strip() for m in messages if m["role"] == "user"]
        assistant_msgs = [m["content"].lower() for m in messages if m["role"] == "assistant"]
        last_user    = user_msgs[-1] if user_msgs else ""
        last         = last_user  # alias — all stage handlers use this

        # ── Greeting ──────────────────────────────────────────────────────────
        if stage == "greeting":
            return (
                "Hello! I'm **Dobby**, your yarn-dyed shirting design assistant. 🧵\n\n"
                "I help you create complete fabric specifications — from pattern and colour "
                "all the way to yarn count, weave type, and GSM.\n\n"
                "To get started: **what is this shirt fabric for?**\n"
                "[OPTIONS:Formal office wear|Casual weekend|School uniform|Party / festive wear|Sportswear|Winter flannel]"
            )

        # ── Explanation request ────────────────────────────────────────────────
        if stage == "explain":
            return (
                "Great question! Here's a quick glossary:\n\n"
                "**Dobby weave** — Small geometric patterns woven directly into the fabric structure "
                "(not printed). Creates a subtle raised texture that looks refined up close. "
                "Very popular for premium formal shirts.\n\n"
                "**GSM** (grams per sq. metre) — How heavy the fabric feels. "
                "110 GSM = light & breathable. 200+ GSM = thick warm flannel.\n\n"
                "**Yarn Count** — How fine the thread is. Higher number = finer, smoother fabric. "
                "50s is standard office-wear. 80s/2 is silky luxury.\n\n"
                "**EPI/PPI** — Ends Per Inch / Picks Per Inch — thread density. "
                "More threads = tighter, smoother, more expensive fabric.\n\n"
                "Now — what kind of shirt are you looking to design?"
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
                    "Casual shirts are fun! 😊\n\n"
                    "For everyday casual wear, I'd suggest either:\n\n"
                    "- **Oxford weave** — basket texture, relaxed feel, very popular\n"
                    "- **Flannel check** — warm, heavy (200 GSM), great for winter\n"
                    "- **Plain poplin** — lightweight, easy to wear\n\n"
                    "Do you have a **pattern** preference?\n"
                    "[OPTIONS:Oxford solid|Flannel check|Casual stripe|Gingham check|Madras plaid|Buffalo check|Double stripe|Herringbone|Brushed solid|Windowpane|Tartan|Simple solid]"
                )
            if any(kw in last for kw in ["school", "uniform"]):
                return (
                    "School uniforms need to be durable and easy to maintain! 📚\n\n"
                    "I'd recommend a **Plain weave** with 40s yarn — "
                    "it's crisp, durable, and easy to iron. GSM around 115-120.\n\n"
                    "What **colours** does the school use?\n"
                    "[OPTIONS:White + Navy Blue|White + Sky Blue|White + Grey|White + Dark Green|Light Blue + White|White only|Grey + White|Cream + Brown]"
                )
            if any(kw in last for kw in ["party", "wedding", "festive", "celebration"]):
                return (
                    "Party wear is all about standing out! 🎉\n\n"
                    "I'd suggest a **Dobby weave** with rich jewel tones — "
                    "the woven texture catches light beautifully at events.\n\n"
                    "What **colour palette** are you thinking?\n"
                    "[OPTIONS:Deep Burgundy + Gold|Royal Blue + White|Emerald Green + Black|Midnight Black + Silver|Purple + Cream|Teal + White|Crimson + Ivory|Navy + Gold|Burnt Orange + Brown|Magenta + Black]"
                )
            if any(kw in last for kw in ["flannel", "winter"]):
                return (
                    "A flannel shirt — perfect for colder weather! 🧣\n\n"
                    "Flannel uses a **Twill weave** with 20s-30s yarn, giving it that "
                    "soft, heavy feel (180-220 GSM). Often brushed on the surface.\n\n"
                    "What **check pattern** and colour would you like?\n"
                    "[OPTIONS:Red + Black tartan|Blue + Green + White tartan|Brown + Beige check|Navy + White check|Grey + Black check|Camel + Brown check|Green + Yellow plaid|Burgundy + Grey check|Orange + Black plaid|Forest Green + Red]"
                )
            # Generic occasion fallback
            return (
                "Got it! What **pattern or design** are you thinking for this shirt?\n\n"
                "For example: solid colour, stripes, checks, subtle texture (fil-a-fil or dobby)?"
            )

        # ── Pattern given ──────────────────────────────────────────────────────
        if stage == "pattern_given":
            if any(kw in last for kw in ["solid", "plain colour", "plain color", "no pattern", "one color", "one colour"]):
                return (
                    "A solid colour shirt — timeless and versatile! ✨\n\n"
                    "For solid formal shirts, a **Fil-a-Fil** or **Dobby weave** adds "
                    "subtle texture so it doesn't look flat — much more refined than a plain solid.\n\n"
                    "What **colour** are you thinking?\n\n"
                    "Popular solid colour choices:\n"
                    "[OPTIONS:White|Sky Blue|Light Blue|Pale Pink|Mint Green|Cream|Charcoal Grey|Navy Blue|Lavender|Sage Green|Dusty Rose|Ivory|Coral|Steel Blue|Olive|Lilac|Buttercup Yellow|Slate Grey]"
                )
            if any(kw in last for kw in ["stripe", "pin", "bengal"]):
                return (
                    "Classic stripes — always sharp! 📏\n\n"
                    "What **colours** would you like for the stripe?\n\n"
                    "Popular stripe combinations:\n"
                    "[OPTIONS:Navy Blue + White|Sky Blue + White|Charcoal + White|Black + White|Royal Blue + Gold|Burgundy + Cream|Forest Green + White|Teal + White|Maroon + Silver|Indigo + Pale Yellow|Brown + Beige|Grey + White]"
                )
            if any(kw in last for kw in ["check", "plaid", "tartan"]):
                return (
                    "Checks are very versatile!\n\n"
                    "What **colours** would you like in the check?\n\n"
                    "Popular check combinations:\n"
                    "[OPTIONS:Navy + White|Brown + Beige|Red + Black|Blue + Green + White|Grey + Black|Olive + Cream|Burgundy + Gold|Teal + White|Camel + Brown|Orange + Navy|Pink + White|Mint + Grey]"
                )
            return (
                "Great pattern choice! 🎨\n\n"
                "What **colour or colour combination** would you like? "
                "Any specific shades in mind, or shall I suggest some popular options?"
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
                    "Great colour combination! 🎨\n\n"
                    "What **percentage split** would you like between the two colours?\n\n"
                    "What percentage split?\n"
                    "[OPTIONS:50% / 50% — equal|60% / 40% — slightly dominant|70% / 30% — one dominant|65% / 35%|75% / 25%|80% / 20% — one strongly dominant]"
                )
            return (
                "Perfect colour choice! 🎨\n\n"
                "Last question — are you looking for **premium quality** or **standard quality**?\n\n"
                "[OPTIONS:Standard quality (50s yarn, 115 GSM)|Premium quality (60s yarn, 108 GSM)|Luxury quality (80s/2 yarn, 105 GSM)]"
            )

        # ── Percentage given — now ask quality ────────────────────────────────
        if stage == "percentage_given":
            return (
                "Got it — I'll use that split for the colours. ✅\n\n"
                "One more thing — are you looking for **premium quality** or **standard quality**?\n\n"
                "[OPTIONS:Standard quality (50s yarn, 115 GSM)|Premium quality (60s yarn, 108 GSM)|Luxury quality (80s/2 yarn, 105 GSM)]"
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
                colour1, colour2 = "White", "White"
                colour2 = "Off-White"
            elif "red" in all_user:
                colour1, colour2 = "Red", "White"
            elif "green" in all_user:
                colour1, colour2 = "Forest Green", "White"
            elif "grey" in all_user or "gray" in all_user:
                colour1, colour2 = "Charcoal Grey", "White"
            elif "pink" in all_user:
                colour1, colour2 = "Pale Pink", "White"

            is_premium = any(kw in last for kw in ["premium", "luxury", "fine", "best", "high"])

            if is_premium:
                return (
                    f"Here are two premium options based on what you've told me:\n\n"
                    f"**Option A — Fine Formal ({colour1}/{colour2})**\n"
                    f"60s yarn · 144×80 construction · 108 GSM · Plain weave\n"
                    f"Very smooth, light, and elegant — perfect for important meetings.\n\n"
                    f"**Option B — Luxury Fil-a-Fil ({colour1}/Mélange)**\n"
                    f"80s/2 yarn · 172×90 construction · 105 GSM · Plain weave\n"
                    f"Silky feel with a subtle two-tone texture — a truly premium shirt.\n\n"
                    f"Which option would you like to go with? Or shall I blend elements from both?"
                )
            else:
                return (
                    f"Here are two great options for you:\n\n"
                    f"**Option A — Classic Formal ({colour1}/{colour2})**\n"
                    f"50s yarn · 132×72 construction · 115 GSM · Plain weave\n"
                    f"Crisp, professional, and breathable — ideal for everyday office wear.\n\n"
                    f"**Option B — Smart Textured ({colour1}/Subtle)**\n"
                    f"40s yarn · 100×80 construction · 120 GSM · Oxford weave\n"
                    f"Slightly heavier with a basket weave texture — more relaxed formal look.\n\n"
                    f"Which one appeals to you? Type **Option A** or **Option B**, "
                    f"or tell me what you'd like to tweak."
                )

        # ── Push forward if stuck ──────────────────────────────────────────────
        if stage == "push_forward":
            return (
                "Based on what you've shared so far, let me suggest two directions:\n\n"
                "**Option A — Formal Classic**\n"
                "Navy Blue/White · Plain weave · 50s yarn · 115 GSM\n"
                "Crisp, professional, great for office use.\n\n"
                "**Option B — Smart Casual**\n"
                "Sky Blue/White · Oxford weave · 40s yarn · 120 GSM\n"
                "Relaxed texture, versatile for both work and weekend.\n\n"
                "Which would you like to go with? Or tell me your colour/pattern preference "
                "and I'll tailor it exactly."
            )

        # ── Finalize — output the design JSON ─────────────────────────────────
        if stage == "finalize":
            # Read all user messages to infer design choices
            all_user = " ".join([m["content"].lower() for m in messages if m["role"] == "user"])
            assistant_msgs = [m["content"].lower() for m in messages if m["role"] == "assistant"]
            last_options = next((a for a in reversed(assistant_msgs) if "option a" in a), "")

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
                stripe_min, stripe_max = 1, 3
                size, size_min, size_max = "Micro", 1, 3
                contrast = "Low"
                occasion = "Formal"
            elif is_premium and is_option_b:
                yarn, epi, ppi, gsm, construction = "80s/2", 172, 90, 105, "172 x 90 / 80s/2 x 80s/2"
                weave, design_style = "Plain", "Fil-a-Fil"
                stripe_min, stripe_max = 1, 1
                size, size_min, size_max = "Micro", 1, 2
                contrast = "Low"
                occasion = "Formal"
            elif "oxford" in all_user or "casual" in all_user or is_option_b:
                yarn, epi, ppi, gsm, construction = "40s", 100, 80, 120, "100 x 80 / 40s x 40s"
                weave, design_style = "Oxford", "Regular"
                stripe_min, stripe_max = 2, 8
                size, size_min, size_max = "Small", 2, 5
                contrast = "Medium"
                occasion = "Casual"
            elif "solid" in all_user or "plain colour" in all_user or "plain color" in all_user:
                yarn, epi, ppi, gsm, construction = "50s", 132, 72, 115, "132 x 72 / 50s x 50s"
                weave, design_style = "Plain", "Solid"
                stripe_min, stripe_max = None, None  # N/A for solid
                size, size_min, size_max = "Full Size", 10, 20  # full fabric repeat size
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
                stripe_min, stripe_max = 4, 12
                size, size_min, size_max = "Medium", 4, 8
                contrast = "High"
                occasion = "Casual"
            else:
                # default: formal stripe
                yarn, epi, ppi, gsm, construction = "50s", 132, 72, 115, "132 x 72 / 50s x 50s"
                weave, design_style = "Plain", "Regular"
                stripe_min, stripe_max = 2, 6
                size, size_min, size_max = "Small", 2, 5
                contrast = "Medium"
                occasion = "Formal"

            colors_json = f'    {{ "name": "{colour1}", "percentage": {pct1} }}'
            if pct2 > 0 and colour1 != colour2:
                colors_json += f',\n    {{ "name": "{colour2}", "percentage": {pct2} }}'

            if stripe_min is None:
                stripe_section = (
                    '  "stripe": {\n'
                    '    "stripeSizeRangeMm": { "min": 0, "max": 0 },\n'
                    '    "stripeMultiplyRange": { "min": 0, "max": 0 },\n'
                    '    "isSymmetry": true,\n'
                    '    "note": "N/A - solid colour"\n'
                    '  },'
                )
            elif stripe_min > 0:
                stripe_section = (
                    f'  "stripe": {{\n'
                    f'    "stripeSizeRangeMm": {{ "min": {stripe_min}, "max": {stripe_max} }},\n'
                    f'    "stripeMultiplyRange": {{ "min": 1, "max": 2 }},\n'
                    f'    "isSymmetry": true\n'
                    f'  }},'
                )
            else:
                stripe_section = (
                    f'  "stripe": {{\n'
                    f'    "stripeSizeRangeMm": {{ "min": 0, "max": 0 }},\n'
                    f'    "stripeMultiplyRange": {{ "min": 0, "max": 0 }},\n'
                    f'    "isSymmetry": true\n'
                    f'  }},'
                )

            summary = (
                f"A {occasion.lower()} {design_style.lower()} shirt in "
                f"{colour1}{f'/{colour2}' if colour1 != colour2 and pct2 > 0 else ''} — "
                f"{weave.lower()} weave with {yarn} yarn. "
                f"At {gsm} GSM it'll feel "
                f"{'light and breathable' if gsm < 115 else 'crisp and professional' if gsm < 130 else 'comfortable with good drape'}. "
                f"Great choice!"
            )

            return (
                f"Your design is finalised! Here are the complete specifications:\n\n"
                f"<DESIGN_OUTPUT>\n"
                f"{{\n"
                f'  "design": {{\n'
                f'    "designSize": "{size}",\n'
                f'    "designSizeRangeCm": {{ "min": {size_min}, "max": {size_max} }},\n'
                f'    "designStyle": "{design_style}",\n'
                f'    "weave": "{weave}"\n'
                f'  }},\n'
                f"{stripe_section}\n"
                f'  "colors": [\n'
                f"{colors_json}\n"
                f'  ],\n'
                f'  "visual": {{ "contrastLevel": "{contrast}" }},\n'
                f'  "market": {{ "occasion": "{occasion}" }},\n'
                f'  "technical": {{\n'
                f'    "yarnCount": "{yarn}",\n'
                f'    "construction": "{construction}",\n'
                f'    "gsm": {gsm},\n'
                f'    "epi": {epi},\n'
                f'    "ppi": {ppi}\n'
                f'  }}\n'
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
                    "Formal shirts are our speciality! 👔\n\n"
                    "For office/formal wear, I'd recommend a **Plain weave poplin** — "
                    "crisp, smooth, and very professional. Yarn count would be 50s or 60s.\n\n"
                    "Now, what **pattern or design** are you thinking?\n"
                    "[OPTIONS:Solid colour|Pin stripe|Bengal stripe|Graph check|Window pane check|Fil-a-fil texture|Dobby geometric|Shadow stripe|Herringbone|Micro check|Tattersall check|Ombre stripe]"
                )
            if any(kw in last_user for kw in ["casual", "weekend", "daily", "everyday", "relaxed", "sport"]):
                return (
                    "Casual shirts are fun! 😊\n\n"
                    "For everyday casual wear, I'd suggest a relaxed weave or fun pattern.\n\n"
                    "What **pattern** are you thinking?\n"
                    "[OPTIONS:Oxford solid|Flannel check|Casual stripe|Gingham check|Madras plaid|Buffalo check|Double stripe|Herringbone|Brushed solid|Windowpane|Tartan|Simple solid]"
                )
            if any(kw in last_user for kw in ["school", "uniform"]):
                return (
                    "School uniforms need to be durable and easy to maintain! 📚\n\n"
                    "I'd recommend a **Plain weave** with 40s yarn — crisp, durable, easy to iron.\n\n"
                    "What **colours** does the school use?\n"
                    "[OPTIONS:White + Navy Blue|White + Sky Blue|White + Grey|White + Dark Green|Light Blue + White|White only|Grey + White|Cream + Brown]"
                )
            if any(kw in last_user for kw in ["party", "wedding", "festive", "celebration"]):
                return (
                    "Party wear is all about standing out! 🎉\n\n"
                    "I'd suggest a **Dobby weave** with rich jewel tones.\n\n"
                    "What **colour palette** are you thinking?\n"
                    "[OPTIONS:Deep Burgundy + Gold|Royal Blue + White|Emerald Green + Black|Midnight Black + Silver|Purple + Cream|Teal + White|Crimson + Ivory|Navy + Gold|Burnt Orange + Brown|Magenta + Black]"
                )
            if any(kw in last_user for kw in ["winter", "flannel"]):
                return (
                    "A flannel shirt — perfect for colder weather! 🧣\n\n"
                    "Flannel uses a **Twill weave** with 20s-30s yarn (180-220 GSM), soft and warm.\n\n"
                    "What **check pattern and colour** would you like?\n"
                    "[OPTIONS:Red + Black tartan|Blue + Green + White tartan|Brown + Beige check|Navy + White check|Grey + Black check|Camel + Brown check|Green + Yellow plaid|Burgundy + Grey check]"
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