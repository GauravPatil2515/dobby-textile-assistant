# Dobby Textile Design Assistant

Provider-agnostic textile design assistant for yarn-dyed shirting with a Flask web UI, multi-provider LLM backend, and optional CLI mode.

Updated on 26 March 2026.

## What it does

- Runs a conversational textile assistant in the web app (`web.py`)
- Collects user requirements first, then returns structured design JSON when ready
- Supports multiple providers: Groq, OpenAI, Anthropic, OpenRouter, and Mock fallback
- Extracts `<DESIGN_OUTPUT>...</DESIGN_OUTPUT>` JSON from model responses for UI auto-fill
- Exposes health/provider endpoints for quick diagnostics

## Project structure

- `web.py` - Flask app, conversational system prompt, `/chat` API
- `cli.py` - terminal chatbot mode
- `llm_provider.py` - provider interface, concrete provider clients, factory
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
