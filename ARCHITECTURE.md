# ARCHITECTURE

Technical overview of the Dobby Textile Assistant system architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                    │
├─────────────────────────────────────────────────────────┤
│  HTML5/CSS3 Shell  │  Vanilla JS Modules │ Lucide Icons │
│  index.html         │  • chat.js          │ CDN         │
│  styles.css         │  • design-panel.js  │             │
│                     │  • image-analysis.js│             │
│                     │  • voice.js         │             │
│                     │  • utilities.js     │             │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP/JSON
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   BACKEND (Flask API)                    │
├─────────────────────────────────────────────────────────┤
│  web.py (Flask App Setup)                               │
│  ├─ /                      GET  (Web UI)                 │
│  ├─ /health                GET  (Status)                 │
│  └─ routes/
│     ├─ chat.py            POST (Chat endpoint)           │
│     ├─ vision.py          POST (Image analysis)          │
│     └─ __init__.py        (Route registration)           │
└──────────────────────────┬──────────────────────────────┘
                           │
                    ┌──────┴───────┐
                    ↓              ↓
        ┌─────────────────┐  ┌──────────────────┐
        │ LLM Provider    │  │ Vision Provider  │
        │ Factory         │  │ Factory          │
        └────────┬────────┘  └────────┬─────────┘
                 │                    │
        ┌────────┴─────────┐    ┌─────┴───────────┐
        │ Multiple Choices │    │ Multiple Options│
        ├─ Groq            │    ├─ Gemini 2.0     │
        ├─ OpenAI          │    ├─ AWS Bedrock    │
        ├─ Anthropic       │    ├─ Google Cloud   │
        ├─ OpenRouter      │    │  Vision         │
        └─ Mock (offline)  │    └─ Mock (offline) │
                           │
                    ┌──────┴───────┐
                    ↓              ↓
        ┌─────────────────┐  ┌──────────────────┐
        │  External APIs  │  │  External APIs   │
        ├─ api.groq.com   │  ├─ api.gemini.dev  │
        ├─ api.openai.com │  ├─ bedrock.aws     │
        ├─ claude.ai      │  └─ vision.googleapis
        └─ openrouter.ai  │
```

## Component Breakdown

### 1. Frontend Layer

**Files**: `templates/index.html`, `static/css/styles.css`, `static/js/*.js`

**Responsibilities**:
- Render responsive UI shell
- Handle user interactions (message input, image upload, design editing)
- Send HTTP requests to backend
- Parse and display responses
- Manage design panel state

**Key Components**:

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| HTML Shell | `index.html` | 134 | DOM structure with semantic markup |
| Styling | `styles.css` | 26KB | Complete design system + responsive layout |
| Chat | `chat.js` | 240 | Message handling and chat UI |
| Design Panel | `design-panel.js` | 425 | Design editor with color palette management |
| Image Upload | `image-analysis.js` | Variable | Fabric image analysis UI |
| Voice Input | `voice.js` | Variable | Web Speech API integration |
| Utilities | `utilities.js` | Variable | Helper functions |

### 2. Backend Layer

**Files**: `web.py`, `config.py`, `constants.py`, `llm_provider.py`, `routes/`

**Responsibilities**:
- Handle HTTP requests
- Orchestrate LLM and vision provider calls
- Parse and validate responses
- Return JSON responses

**Core Modules**:

#### web.py (Flask Entrypoint)
```python
# 40 lines total
from flask import Flask
from routes import register_routes

app = Flask(__name__, static_folder='static', template_folder='templates')
register_routes(app)

# Vercel: api/index.py imports this app
```

**Responsibilities**:
- Flask app initialization
- Static/template folder configuration
- Debug mode control
- Route registration

#### config.py (Configuration)
```python
# 156 lines
import os
from dotenv import load_dotenv

SYSTEM_PROMPT = "..."  # Note: unused (dead code)
VISION_PROVIDER = os.getenv('VISION_PROVIDER', 'mock')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# ... more configuration
```

**Responsibilities**:
- Load environment variables
- Define system prompts
- Provider configuration
- API key management

#### constants.py (Textile Mappings)
```python
# 62 lines - single source of truth for design data

STRIPE_SIZE_MAP = {
    "Micro": (6, 8),        # mm
    "Small": (9, 12),
    "Medium": (13, 18),
    "Large": (19, 25),
}

DESIGN_SIZE_MAP = {
    "Micro": 6,             # cm
    "Small": 12,
    "Medium": 25,
    # ...
}

COLOR_FAMILIES = {
    "Blue": {
        "base": "#0066CC",
        "family": ["#003366", "#0099FF"],
        "harmony": ["#00CC66", "#FFCC00"],
        "contrast": ["#FF6600"],
    },
    # ... 10 total color families
}
```

**Responsibilities**:
- Central storage for textile design mappings
- Color palette definitions
- Design size classifications
- Pattern size ranges

#### llm_provider.py (Core Intelligence)
```python
# 1,541 lines - largest module

class LLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    def generate_response(self, messages, system_prompt):
        raise NotImplementedError()

class GroqProvider(LLMProvider):
    """Groq API implementation - fastest option"""
    
class OpenAIProvider(LLMProvider):
    """OpenAI API implementation"""
    
class AnthropicProvider(LLMProvider):
    """Anthropic Claude API implementation"""
    
class OpenRouterProvider(LLMProvider):
    """OpenRouter multi-model implementation"""
    
class MockProvider(LLMProvider):
    """Offline mock provider for testing - 300+ lines of state detection"""
    def _get_stage(self):
        # Sophisticated conversation stage detection via keyword analysis
        
class LLMProviderFactory:
    """Factory pattern with caching and fallback chain"""
    def get_provider(self, provider_name):
        # Returns cached provider or creates new instance
        # Fallback: Groq → OpenAI → Anthropic → OpenRouter → Mock
```

**Responsibilities**:
- LLM provider implementations
- Vision provider implementations
- Design generation logic
- Color palette building
- Response parsing
- Fallback chain management
- Caching mechanism

#### routes/ (API Endpoints)

**routes/__init__.py** (10 lines)
```python
def register_routes(app):
    from .chat import chat_bp
    from .health import health_bp
    from .vision import vision_bp
    
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(vision_bp)
```

**routes/chat.py** (164 lines)
```python
@chat_bp.route('/chat', methods=['POST'])
def chat():
    messages = request.json.get('messages', [])
    
    # Inject system prompt (CHAT_SYSTEM_PROMPT, 70 lines)
    # Get LLM provider
    # Call provider.generate_response()
    # Parse design output with regex
    # Return structured response
```

**routes/vision.py** (71 lines)
```python
@vision_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    image = request.json.get('image')  # Base64
    
    # Get vision provider
    # Call provider.analyze(image)
    # Parse design output
    # Return analysis + design
```

### 3. Provider Layer

**LLM Providers** (llm_provider.py):

| Provider | API | Latency | Cost | Status |
|----------|-----|---------|------|--------|
| **Groq** | api.groq.com | <1s | Free tier | ✅ Production |
| **OpenAI** | api.openai.com | 1-3s | Paid | ✅ Production |
| **Anthropic** | claude.ai | 1-3s | Paid | ✅ Production |
| **OpenRouter** | openrouter.ai | 1-3s | Paid | ✅ Production |
| **Mock** | None (local) | <100ms | Free | ✅ Development |

**Vision Providers** (llm_provider.py):

| Provider | API | Quality | Cost | Status |
|----------|-----|---------|------|--------|
| **Gemini 2.0** | gemini.google | Excellent | Paid | ✅ Production |
| **AWS Bedrock** | bedrock.aws | Excellent | Paid | ✅ Production |
| **Cloud Vision** | vision.googleapis | Good | Paid | ✅ Production |
| **Mock** | None (local) | Simulated | Free | ✅ Development |

### 4. Data Flow

#### Chat Flow
```
User Input
    ↓
chat.js: fetchReply(messages)
    ↓
POST /chat {messages}
    ↓
routes/chat.py: chat()
    ├─ Inject CHAT_SYSTEM_PROMPT
    ├─ Get LLM provider via factory
    ├─ Call provider.generate_response()
    │  └─ Call external API (Groq/OpenAI/...)
    ├─ Parse response for <DESIGN_OUTPUT> tags
    ├─ Extract JSON design specification
    └─ Return {reply, structured, has_design}
    ↓
chat.js: renderBotMessage(reply)
    ├─ Parse [OPTIONS:...] tags
    ├─ Render message bubble
    └─ Render option chips
    ↓
design-panel.js: renderDesignPanel(design)
    ├─ Build form UI
    ├─ Populate color picker
    └─ Show JSON preview
```

#### Image Analysis Flow
```
User Uploads Image
    ↓
image-analysis.js: uploadImage(file)
    ├─ Convert to base64
    └─ POST /analyze-image
    ↓
routes/vision.py: analyze_image()
    ├─ Get vision provider via factory
    ├─ Call provider.analyze(image)
    │  └─ Call external API (Gemini/Bedrock/...)
    ├─ Parse design output
    └─ Return {analysis, design}
    ↓
image-analysis.js: displayAnalysis(result)
    ├─ Show fabric analysis text
    └─ Populate design panel
```

## Design Patterns

### 1. Factory Pattern

**Purpose**: Abstraction for provider selection and caching

```python
class LLMProviderFactory:
    _provider_cache = {}  # Global cache
    
    def get_provider(self, provider_name):
        if provider_name in self._provider_cache:
            return self._provider_cache[provider_name]  # Cached
        
        provider = self._create_provider(provider_name)
        self._provider_cache[provider_name] = provider
        return provider
```

**Benefits**:
- Decouple provider selection from code
- Easy to add new providers
- Automatic caching

### 2. Strategy Pattern

**Purpose**: Pluggable algorithms for different providers

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate_response(self, messages, system_prompt):
        pass

# Different strategies:
class GroqProvider(LLMProvider):
    def generate_response(self, messages, system_prompt):
        # Groq-specific implementation
        
class OpenAIProvider(LLMProvider):
    def generate_response(self, messages, system_prompt):
        # OpenAI-specific implementation
```

**Benefits**:
- Same interface, different implementations
- Easy provider switching
- Runtime selection

### 3. Fallback Chain

**Purpose**: Automatic provider fallback on failure

```python
FALLBACK_CHAIN = [
    "groq",
    "openai",
    "anthropic",
    "openrouter",
    "mock"
]

# If Groq fails, try OpenAI, then Anthropic, etc.
for provider_name in FALLBACK_CHAIN:
    try:
        provider = get_provider(provider_name)
        return provider.generate_response(...)
    except Exception:
        continue
```

**Benefits**:
- High availability
- Graceful degradation
- Offline support (Mock provider)

### 4. State Machine (MockProvider)

**Purpose**: Simulate conversation stages without API

```python
class MockProvider(LLMProvider):
    def _get_stage(self):
        # Keyword analysis: "color" → stage 2
        # Multi-word phrases: "stripe pattern" → stage 3
        # Return: "initial" | "style" | "size" | "finalize"
        
    def generate_response(self, messages, system_prompt):
        stage = self._get_stage()
        
        if stage == "initial":
            return self._response_initial()
        elif stage == "style":
            return self._response_style()
        # ... etc
```

**Benefits**:
- No API dependencies
- Predictable behavior
- Development/testing friendly

## Scalability Considerations

### Current Limitations

1. **Global Provider Cache**: Not thread-safe
   - Issue: Concurrent requests may race on provider creation
   - Impact: Low (typical usage is 1-2 concurrent users)

2. **Vision Provider Override**: Module-level binding
   - Issue: Environment variable changes don't affect imported providers
   - Impact: Must restart app to switch vision provider

3. **No Request Queuing**: All requests hit APIs immediately
   - Issue: API rate limits may be exceeded under load
   - Impact: Low (typical: <10 req/sec)

### Future Scalability

For production scaling (100+ concurrent users):

1. **Add Redis Caching**: Cache provider responses
   - 5-minute TTL on design generation
   - Reduce API calls by 80%+

2. **Implement Request Queue**: Use Celery + RabbitMQ
   - Queue design requests
   - Distribute across worker nodes

3. **Add API Rate Limiting**: Per-user quotas
   - 10 requests/minute per user
   - Prevent abuse

4. **Implement Thread-Safe Provider Caching**: Use threading.Lock()
   - Protect global cache from race conditions

## Deployment Architecture

### Development
```
User Browser → localhost:5000 → Flask dev server → APIs
```

### Production (Vercel)
```
User Browser → vercel.app → api/index.py → Flask app → APIs
                (serverless)  (FaaS handler)
```

**Vercel Configuration** (`vercel.json`):
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/api/index.py" }
  ]
}
```

**API Handler** (`api/index.py`):
```python
from web import app

# Vercel automatically calls: app(environ, start_response)
```

## Security Architecture

1. **API Key Management**:
   - Keys stored in `.env` (git-ignored)
   - Never committed to repository
   - Environment variables in Vercel project settings

2. **Input Validation**:
   - Base64 image validation
   - Message content sanitization
   - Provider name whitelisting

3. **CORS**:
   - Same-origin only (development)
   - Configurable for production

4. **Error Handling**:
   - No sensitive data in error responses
   - Graceful fallbacks
   - Detailed logs (server-side only)

## Monitoring & Observability

**Currently**: Logging to stdout (Flask development)

**Recommended for Production**:
1. Structured logging (JSON format)
2. Application Performance Monitoring (APM)
   - New Relic
   - DataDog
3. Error tracking (Sentry)
4. Metrics collection (Prometheus)

---

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.
