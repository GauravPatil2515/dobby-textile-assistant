# Textronics DesignDobby AI
> AI-powered yarn-dyed shirting design assistant for textile buyers

## What It Does
Guides buyers through shirt design decisions via a conversational chat interface.
Outputs structured JSON specifications ready for textile manufacturing —
covering colors, weave type, stripe dimensions, pattern style, and occasion.

## Screenshots
<!-- Add screenshots after deployment -->

## Tech Stack

| Layer       | Technology                     | Purpose                          |
|-------------|-------------------------------|-----------------------------------|
| Frontend    | HTML5, CSS3, Vanilla JS        | Chat UI, design panel, voice     |
| Backend     | Python 3.10+, Flask            | Routes, LLM orchestration        |
| Chat AI     | Groq (primary), MockProvider   | Conversation + design generation |
| Vision AI   | Gemini 2.0 Flash (optional)    | Fabric image analysis            |
| Deployment  | Vercel (api/index.py)          | Serverless production hosting    |

## Quick Start

### Prerequisites
- Python 3.10+
- pip
- `config.py` - environment/provider configuration and base system prompt
- `api/index.py` - Vercel entrypoint importing `app` from `web.py`
- `static/`, `templates/` - frontend assets

## Requirements

- Python 3.10+ recommended
- API key for at least one provider (unless using `mock`)

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```bash
# Active provider: groq | openai | anthropic | openrouter | mock
LLM_PROVIDER=groq

# Provider API keys
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional model overrides
GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
OPENROUTER_MODEL=deepseek/deepseek-r1:free,deepseek/deepseek-r1-distill-llama-70b:free

# Optional Flask runtime config
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=1
```

Security note: never commit `.env` files or API keys.

## Run locally

### Web app

```bash
python web.py
```

Open `http://127.0.0.1:5000`.

### CLI mode

```bash
python cli.py
```

Type `exit` to quit.

## API endpoints

- `GET /` - web UI
- `GET /health` - returns app status and active provider
- `GET /api/providers` - available + active providers
- `POST /chat` - chat endpoint

### `POST /chat` request

```json
{
    "messages": [
        { "role": "user", "content": "I need a premium formal stripe shirt in blue tones." }
    ]
}
```

### `POST /chat` response

```json
{
    "reply": "Short conversational assistant text",
    "structured": { "...": "parsed JSON when present" },
    "has_design": true
}
```

Notes:

- Web route always injects/replaces the system prompt with the conversational prompt in `web.py`.
- Structured JSON is parsed only when the model includes `<DESIGN_OUTPUT>...</DESIGN_OUTPUT>`.
- The JSON block is removed from `reply` before frontend display.

## Provider support

`llm_provider.py` includes:

- `GroqProvider`
- `OpenAIProvider`
- `AnthropicProvider`
- `OpenRouterProvider` (supports fallback chain from comma-separated models)
- `MockProvider`
- `LLMProviderFactory`

Switch provider via env var:

```bash
export LLM_PROVIDER=openai
python web.py
```

## Deployment (Vercel)

This repo includes Vercel wiring:

- `api/index.py` imports `app` from `web.py`
- `vercel.json` controls routing/build behavior

Set the same provider env vars in your Vercel project settings.

## Notes and caveats

- `web.py` uses its own conversational prompt (`CHAT_SYSTEM_PROMPT`).
- `cli.py` uses `config.SYSTEM_PROMPT` and does not currently strip `<DESIGN_OUTPUT>` tags.
- If provider initialization fails, web and CLI fall back to `MockProvider`.

## License

MIT
