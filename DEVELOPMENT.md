# DEVELOPMENT

Local development setup and contribution guidelines.

## Prerequisites

- Python 3.10+ (recommended: 3.11 or 3.12)
- Git
- Text editor or IDE (VS Code recommended)
- Terminal/CLI experience

---

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/GauravPatil2515/dobby-textile-assistant.git
cd dobby-textile-assistant
```

### 2. Create Virtual Environment

**Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env

# Edit .env with your settings
# For development, you can use mock providers:
# LLM_PROVIDER=mock
# VISION_PROVIDER=mock
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup.

### 5. Run Development Server

```bash
python -c "from web import app; app.run(debug=True)"
```

Visit: http://localhost:5000

---

## Project Structure

```
dobby-textile-assistant/
├── web.py                    # Flask app entrypoint (40 lines)
├── config.py                 # Configuration (156 lines)
├── constants.py              # Design mappings (62 lines)
├── llm_provider.py           # AI providers (1,541 lines)
├── routes/                   # API endpoints
│   ├── __init__.py          # Route registration
│   ├── chat.py              # Chat endpoint (164 lines)
│   └── vision.py            # Image analysis (71 lines)
├── static/
│   ├── css/
│   │   └── styles.css       # Complete styling (26KB)
│   └── js/
│       ├── app.js           # App initialization
│       ├── chat.js          # Chat UI (240 lines)
│       ├── design-panel.js  # Design editor (425 lines)
│       ├── image-analysis.js # Image upload
│       ├── voice.js         # Voice input
│       └── utilities.js     # Helper functions
├── templates/
│   └── index.html           # HTML shell (134 lines)
└── api/
    └── index.py             # Vercel handler (15 lines)
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

Branch naming:
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code improvements
- `docs/` - Documentation
- `test/` - Tests

### 2. Make Changes

Edit files as needed. For example:

**Adding a new LLM provider**:
1. Edit `llm_provider.py`
2. Create class extending `LLMProvider`
3. Implement `generate_response()` method
4. Add to factory fallback chain

**Adding a new API endpoint**:
1. Create `routes/new_feature.py`
2. Create Flask blueprint
3. Register in `routes/__init__.py`

**Styling changes**:
1. Edit `static/css/styles.css`
2. Follow existing design token system
3. Test on mobile (Chrome DevTools F12 → toggle device toolbar)

### 3. Run Tests

Currently no automated tests. Manual testing:

```bash
# Test LLM provider
python -c "
from llm_provider import LLMProviderFactory
factory = LLMProviderFactory()
provider = factory.get_provider('mock')
response = provider.generate_response(
    [{'role': 'user', 'content': 'Test'}],
    'You are helpful.'
)
print(response)
"

# Test Flask app
python -c "from web import app; print('App loaded successfully')"
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

Commit message format:
```
type(scope): description

Longer explanation here if needed.

- Bullet point 1
- Bullet point 2
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### 5. Push and Create Pull Request

```bash
git push origin feature/my-feature
```

Then on GitHub:
1. Create Pull Request
2. Add description of changes
3. Request review
4. Address feedback
5. Merge when approved

---

## Testing

### Manual Testing Checklist

**Chat endpoint**:
- [ ] Send message with MockProvider
- [ ] Send message with real LLM
- [ ] Receive design specification
- [ ] Verify design panel renders

**Image analysis**:
- [ ] Upload valid image
- [ ] Verify fabric analysis
- [ ] Check design generation
- [ ] Test with different image formats

**UI Components**:
- [ ] Message input works
- [ ] Chat messages display
- [ ] Design panel renders
- [ ] Color picker functions
- [ ] Export JSON works
- [ ] Mobile responsiveness

### Load Testing

```bash
# Using Apache Bench (ab)
ab -n 100 -c 10 http://localhost:5000/health

# Using wrk
wrk -t4 -c100 -d30s http://localhost:5000/health
```

### Performance Profiling

```bash
# Install profiler
pip install py-spy

# Profile app
py-spy record -o profile.svg -- python -c "from web import app; app.run()"
```

---

## Debugging

### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "web.py",
                "FLASK_ENV": "development",
                "FLASK_DEBUG": "1"
            },
            "args": ["run"],
            "jinja": true
        }
    ]
}
```

Then press F5 to debug.

### Print Debugging

```python
# In routes/chat.py
@chat_bp.route('/chat', methods=['POST'])
def chat():
    messages = request.json.get('messages', [])
    print(f"DEBUG: Received {len(messages)} messages")
    print(f"DEBUG: Messages: {messages}")
    
    # ... rest of function
```

Watch output in terminal.

### JavaScript Debugging

Open browser DevTools (F12):
- **Console**: Run JS commands, view errors
- **Debugger**: Set breakpoints, step through code
- **Network**: View HTTP requests
- **Application**: Check localStorage, cookies

---

## Code Style

### Python (PEP 8)

Use `black` formatter:

```bash
pip install black
black web.py routes/ llm_provider.py
```

Check with `flake8`:

```bash
pip install flake8
flake8 web.py routes/ llm_provider.py
```

### JavaScript (ES6)

- Use `const` by default, `let` if needed
- Avoid `var`
- Use arrow functions: `() => {}`
- Use template literals: `` `Hello ${name}` ``
- Add comments for complex logic

Example:
```javascript
// Good
const chatPanel = document.getElementById('chat-panel');
const sendMessage = (text) => {
    console.log(`Sending: ${text}`);
};

// Bad
var chatPanel = document.querySelector('#chat-panel');
function sendMessage(text) {
    console.log('Sending: ' + text);
}
```

### CSS

- Use CSS variables from design tokens
- Mobile-first approach
- Use `clamp()` for fluid sizing
- Comment non-obvious rules

Example:
```css
/* Good */
.card {
    background-color: var(--bg-secondary);
    padding: clamp(1rem, 5vw, 2rem);
    border-radius: var(--radius-md);
}

/* Bad */
.card {
    background-color: #f5f5f5;
    padding: 20px;
    border-radius: 8px;
}
```

---

## Documentation

### Code Comments

Add comments for:
- Why code does something (not what)
- Complex algorithms
- Edge cases
- Non-obvious design decisions

Example:
```python
# Bad
def get_stripe_size(size_name):
    # Get stripe size
    return STRIPE_SIZE_MAP[size_name]

# Good
def get_stripe_size(size_name):
    # Return (min_mm, max_mm) tuple for physical stripe width
    # Used by textile mills to interpret design specifications
    return STRIPE_SIZE_MAP[size_name]
```

### Docstrings

Add docstrings to functions and classes:

```python
def generate_design(base_color, occasion):
    """Generate textile design specification.
    
    Args:
        base_color (str): Hex color code (e.g., "FF0000")
        occasion (str): Use case ("Formal", "Casual", "Party Wear")
    
    Returns:
        dict: Design specification with base_color, palette, stripe_size, etc.
    
    Raises:
        ValueError: If color code is invalid
    """
    pass
```

### README Updates

When adding features, update README.md:
- Add to feature list
- Update architecture diagram if needed
- Add troubleshooting section if complex

---

## Adding New Features

### Feature: New LLM Provider

1. **Edit `llm_provider.py`**:
```python
class MyLLMProvider(LLMProvider):
    """My custom LLM provider."""
    
    def generate_response(self, messages, system_prompt):
        """Generate response using my API."""
        # Implementation here
        pass
```

2. **Register in factory**:
```python
class LLMProviderFactory:
    def _create_provider(self, provider_name):
        if provider_name == 'my_provider':
            return MyLLMProvider()
        # ... other providers
```

3. **Update docs**:
- Add to [CONFIGURATION.md](CONFIGURATION.md)
- Add to README provider table

### Feature: New API Endpoint

1. **Create `routes/new_feature.py`**:
```python
from flask import Blueprint, request

new_bp = Blueprint('new_feature', __name__)

@new_bp.route('/new-endpoint', methods=['POST'])
def new_endpoint():
    """New endpoint description."""
    data = request.json
    # Implementation here
    return {'result': 'success'}
```

2. **Register in `routes/__init__.py`**:
```python
def register_routes(app):
    from .new_feature import new_bp
    app.register_blueprint(new_bp)
```

3. **Add tests and docs**

### Feature: New UI Component

1. **Create `static/js/new-component.js`**:
```javascript
const NewComponent = {
    init() {
        // Initialize component
    },
    render(data) {
        // Render to DOM
    }
};

// Export for use in app.js
window.NewComponent = NewComponent;
```

2. **Add script tag to `templates/index.html`**:
```html
<script src="static/js/new-component.js"></script>
```

3. **Initialize in `static/js/app.js`**:
```javascript
NewComponent.init();
```

---

## Performance Tips

1. **Use MockProvider for development**
   - Instant responses
   - No API rate limits
   - No internet needed

2. **Cache API responses**
   - Similar designs return same spec
   - Reduce API calls 80%+

3. **Optimize frontend**
   - Minify CSS/JS for production
   - Use Chrome DevTools Performance tab
   - Profile with py-spy (Python)

4. **Monitor API usage**
   - Log all requests
   - Track response times
   - Alert on errors

---

## Deployment Testing

### Test Before Pushing

```bash
# Lint Python
flake8 web.py routes/ llm_provider.py

# Test imports
python -c "from web import app; print('OK')"

# Test Flask
python web.py

# Check for debug mode
grep "FLASK_DEBUG.*'1'" web.py config.py
```

### Test Production Config

```bash
# Simulate production
export FLASK_DEBUG=0
export LLM_PROVIDER=groq
export GROQ_API_KEY=your_key

python -c "from web import app; app.run()"
```

### Test with Vercel CLI

```bash
npm install -g vercel

# Test locally
vercel dev

# Deploy preview
vercel --prod
```

---

## Getting Help

### Resources

- [Python Docs](https://docs.python.org/3/)
- [Flask Docs](https://flask.palletsprojects.com/)
- [MDN Web Docs](https://developer.mozilla.org/en-US/)
- [Stack Overflow](https://stackoverflow.com/)

### Community

- Open issues on GitHub
- Check existing issues first
- Include error messages and steps to reproduce

---

## Contribution Guidelines

1. Fork the repository
2. Create feature branch (`git checkout -b feature/my-feature`)
3. Make changes with clear commits
4. Test thoroughly
5. Push to branch (`git push origin feature/my-feature`)
6. Open Pull Request with description
7. Address code review feedback
8. Merge when approved

**Code review criteria**:
- [ ] Code follows style guide
- [ ] No obvious bugs
- [ ] Well-documented
- [ ] Tests added (if applicable)
- [ ] No breaking changes

---

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.
