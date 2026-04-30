# CONFIGURATION

Environment setup and API key configuration guide.

## Quick Setup

1. **Copy template**:
```bash
cp .env.example .env
```

2. **Add your API keys** to `.env`

3. **Source environment**:
```bash
source .env  # Linux/Mac
# or
set -a && source .env && set +a  # Bash with error handling
```

4. **Run app**:
```bash
python -c "from web import app; app.run(debug=True)"
```

---

## Environment Variables Reference

### LLM Provider

**LLM_PROVIDER** (required)

Selects which LLM service to use:

```bash
LLM_PROVIDER=groq        # Fastest (recommended)
LLM_PROVIDER=openai      # Most capable
LLM_PROVIDER=anthropic   # Safety-focused
LLM_PROVIDER=openrouter  # Most flexible
LLM_PROVIDER=mock        # Offline testing
```

**Default**: `mock` (if no providers configured)

---

### Vision Provider

**VISION_PROVIDER** (optional)

Selects which vision/image analysis service to use:

```bash
VISION_PROVIDER=gemini       # Recommended (free tier available)
VISION_PROVIDER=bedrock      # AWS hosted
VISION_PROVIDER=cloud-vision # Google Cloud
VISION_PROVIDER=mock         # Offline testing
```

**Default**: `mock`

---

## LLM Provider Configuration

### Groq (Fastest - Recommended)

Get free API key: https://console.groq.com

```bash
# .env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_YOUR_KEY_HERE

# Optional: override default model
GROQ_MODEL=llama-3.3-70b-versatile
```

**Available models**:
- `llama-3.3-70b-versatile` (best for designs)
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`
- `gemma-7b-it`

**Pricing**: Free tier with limits

**Performance**: <1s response time

---

### OpenAI

Get API key: https://platform.openai.com/api-keys

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk_YOUR_KEY_HERE

# Optional: override default model
OPENAI_MODEL=gpt-4o-mini
```

**Available models**:
- `gpt-4o-mini` (fast, cheap)
- `gpt-4o` (most capable)
- `gpt-4-turbo`
- `gpt-3.5-turbo` (legacy)

**Pricing**: Pay-as-you-go (~$0.01-0.10 per request)

**Performance**: 1-3s response time

---

### Anthropic (Claude)

Get API key: https://console.anthropic.com

```bash
# .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant_YOUR_KEY_HERE

# Optional: override default model
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**Available models**:
- `claude-3-5-sonnet-20241022` (best performance)
- `claude-3-opus-20250219` (most capable)
- `claude-3-haiku-20250307` (fastest)

**Pricing**: Pay-as-you-go (~$0.003-0.024 per request)

**Performance**: 1-2s response time

---

### OpenRouter (Multi-Model)

Get API key: https://openrouter.ai

Supports hundreds of models. Comma-separated for fallback chain:

```bash
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or_YOUR_KEY_HERE

# Try multiple models in order
OPENROUTER_MODEL=deepseek/deepseek-r1:free,deepseek/deepseek-r1-distill-llama-70b:free,meta-llama/llama-3-70b-instruct
```

**Popular free models**:
- `deepseek/deepseek-r1:free`
- `meta-llama/llama-3-70b-instruct:free`
- `mistralai/mistral-large:free`

**Pricing**: Mix of free and paid

---

### Mock Provider (Offline)

No API key needed. Uses local state machine for responses.

```bash
# .env
LLM_PROVIDER=mock
VISION_PROVIDER=mock  # Also offline for images
```

**Use cases**:
- Development and testing
- Demo without internet
- CI/CD testing

---

## Vision Provider Configuration

### Gemini (Google - Recommended)

Get free API key: https://ai.google.dev

```bash
# .env
VISION_PROVIDER=gemini
GEMINI_API_KEY=AIza_YOUR_KEY_HERE
```

**Features**:
- Excellent fabric analysis
- Fast responses
- Free tier available

**Pricing**: Free tier (60 req/min), then $0.004 per image

**Performance**: 2-5s response time

---

### AWS Bedrock

Requires AWS account: https://aws.amazon.com

```bash
# .env
VISION_PROVIDER=bedrock
BEDROCK_AWS_REGION=us-east-1
BEDROCK_AWS_ACCESS_KEY_ID=AKIA...
BEDROCK_AWS_SECRET_ACCESS_KEY=...

# Optional: specify model
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

**Requirements**:
- AWS account with Bedrock access
- IAM user with `bedrock:InvokeModel` permission
- AWS CLI configured (optional)

**Pricing**: $0.00024 per image

---

### Google Cloud Vision

Requires Google Cloud project: https://cloud.google.com

```bash
# .env
VISION_PROVIDER=cloud-vision
GOOGLE_CLOUD_CREDENTIALS=/path/to/credentials.json
```

**Setup**:
1. Create Google Cloud project
2. Enable Vision API
3. Create service account
4. Download JSON credentials
5. Point GOOGLE_CLOUD_CREDENTIALS to file

**Pricing**: $0.0015 per image

---

### Mock Vision Provider

No setup needed. Returns simulated analysis.

```bash
# .env
VISION_PROVIDER=mock
```

---

## Flask Configuration

### Debug Mode

```bash
# Enable debug mode (development only)
FLASK_DEBUG=1

# Disable (production)
FLASK_DEBUG=0
```

**Effects of FLASK_DEBUG=1**:
- Auto-reload on code changes
- Interactive debugger on errors
- Detailed error pages

**⚠️ NEVER enable in production**

---

### Server Configuration

```bash
# Host to listen on
FLASK_HOST=127.0.0.1  # Localhost only
FLASK_HOST=0.0.0.0    # All interfaces

# Port to listen on
FLASK_PORT=5000
FLASK_PORT=8080
FLASK_PORT=3000
```

---

### CORS Configuration

```bash
# Allow requests from specific origins
CORS_ORIGINS=http://localhost:3000,https://example.com

# Default: localhost only
```

---

## Advanced Configuration

### Logging

```bash
# Log level
LOG_LEVEL=DEBUG       # Verbose logging
LOG_LEVEL=INFO        # Standard logging
LOG_LEVEL=WARNING     # Only warnings
LOG_LEVEL=ERROR       # Only errors
```

### Cache Settings

```bash
# Response caching (planned feature)
CACHE_TYPE=redis
REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=300
```

### Rate Limiting (Planned)

```bash
# Requests per minute
RATE_LIMIT_RPM=60
RATE_LIMIT_PER_USER=10
```

---

## Configuration Examples

### Development (No API Keys)

```bash
# .env
LLM_PROVIDER=mock
VISION_PROVIDER=mock
FLASK_DEBUG=1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

Run:
```bash
python -c "from web import app; app.run(debug=True)"
```

### Development (With Real APIs)

```bash
# .env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
VISION_PROVIDER=gemini
GEMINI_API_KEY=AIza_...
FLASK_DEBUG=1
```

### Production (Vercel)

```bash
# Set in Vercel dashboard:
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
VISION_PROVIDER=gemini
GEMINI_API_KEY=AIza_...
FLASK_DEBUG=0
```

### Production (Heroku)

```bash
heroku config:set LLM_PROVIDER=groq
heroku config:set GROQ_API_KEY=gsk_...
heroku config:set VISION_PROVIDER=gemini
heroku config:set GEMINI_API_KEY=AIza_...
heroku config:set FLASK_DEBUG=0
```

### Multiple LLM Fallback (OpenRouter)

```bash
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or_...
OPENROUTER_MODEL=deepseek/deepseek-r1:free,meta-llama/llama-3-70b-instruct:free,mistralai/mistral-large:free

# Automatically tries free models first
```

---

## Verifying Configuration

### Check LLM Provider

```bash
python -c "
from llm_provider import LLMProviderFactory
factory = LLMProviderFactory()
provider = factory.get_provider('groq')
print(f'Provider: {provider.__class__.__name__}')
"
```

### Check Vision Provider

```bash
python -c "
from llm_provider import get_vision_provider
provider = get_vision_provider()
print(f'Provider: {provider.__class__.__name__}')
"
```

### Test API Connectivity

```bash
python -c "
import os
from llm_provider import LLMProviderFactory

factory = LLMProviderFactory()
provider = factory.get_provider(os.getenv('LLM_PROVIDER', 'mock'))

response = provider.generate_response(
    [{'role': 'user', 'content': 'Hello'}],
    'You are a helpful assistant.'
)
print(f'Response: {response[:100]}...')
"
```

---

## Troubleshooting Configuration

### API Key Errors

**Issue**: `401 Unauthorized`

**Solution**:
1. Verify key is correct in `.env`
2. Check key hasn't been rotated
3. Test key manually:
```bash
curl -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models
```

### Provider Not Found

**Issue**: `Unknown provider: xyz`

**Solution**:
1. Check spelling of LLM_PROVIDER
2. Valid values: groq, openai, anthropic, openrouter, mock
3. Ensure .env is sourced:
```bash
source .env
echo $LLM_PROVIDER
```

### Fallback Not Working

**Issue**: OpenRouter not trying fallback models

**Solution**:
1. Ensure OPENROUTER_MODEL contains comma-separated list
2. Format: `model1,model2,model3`
3. Test:
```bash
echo $OPENROUTER_MODEL
```

---

## Security Best Practices

1. **Never commit .env**:
   - Always in .gitignore
   - Check before committing: `git status`

2. **Rotate keys regularly**:
   - Every 3-6 months
   - Immediately if leaked

3. **Use environment variables**:
   - Never hardcode API keys
   - Never pass in query strings

4. **Limit key permissions**:
   - Give API keys only needed scopes
   - Create separate keys for different environments

5. **Monitor key usage**:
   - Check API provider dashboards regularly
   - Set up alerts for unusual activity

---

## Environment Variable Priority

1. **`.env` file** (highest priority if present)
2. **System environment variables**
3. **Default values in code** (lowest priority)

Example:
```bash
# This uses system env var
export GROQ_API_KEY=abc123
python app.py

# But .env takes precedence
GROQ_API_KEY=xyz789  # In .env
python app.py  # Uses xyz789
```

---

See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup instructions.
