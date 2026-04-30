# TROUBLESHOOTING

Common issues and solutions.

## Setup Issues

### Python Version Mismatch

**Problem**: `Error: This project requires Python 3.10+`

**Solution**:
```bash
# Check Python version
python --version  # Should be 3.10+

# If not, use python3
python3 --version

# Or install Python 3.10+ from python.org
```

---

### Virtual Environment Not Activating

**Problem**: `ModuleNotFoundError` after pip install

**Solution - Linux/macOS**:
```bash
# Check if venv exists
ls -la venv/

# Activate properly
source venv/bin/activate

# Verify it's active (should show "(venv)" in prompt)
which python
```

**Solution - Windows**:
```bash
# Run from project directory
venv\Scripts\activate

# Or use full path
C:\path\to\project\venv\Scripts\activate.bat
```

---

### Missing Dependencies

**Problem**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
# Ensure venv is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep flask
```

---

### requirements.txt Issues

**Problem**: `ERROR: Could not find a version that satisfies the requirement`

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip

# Try installing with no cache
pip install --no-cache-dir -r requirements.txt

# Or install packages individually
pip install flask python-dotenv groq openai anthropic
```

---

## Environment Configuration

### API Key Not Found

**Problem**: `KeyError: 'GROQ_API_KEY'` or similar

**Solution**:
```bash
# 1. Check .env exists
ls -la .env

# 2. Verify key is in .env
grep GROQ_API_KEY .env

# 3. Ensure .env is sourced
source .env
echo $GROQ_API_KEY  # Should show your key

# 4. Or set directly
export GROQ_API_KEY=gsk_your_key_here
```

---

### .env File Not Loading

**Problem**: App uses default values instead of .env

**Solution**:
```bash
# Check if python-dotenv is installed
pip list | grep python-dotenv

# Verify .env file permissions
ls -la .env

# Try explicit loading in Python
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(os.getenv('GROQ_API_KEY'))
"
```

---

### Wrong Provider Selected

**Problem**: App uses Mock provider instead of Groq

**Solution**:
```bash
# 1. Check which provider is set
echo $LLM_PROVIDER

# 2. Verify in .env file
cat .env | grep LLM_PROVIDER

# 3. Set correctly
export LLM_PROVIDER=groq
export GROQ_API_KEY=gsk_your_key

# 4. Verify in app
python -c "
import os
os.environ['LLM_PROVIDER'] = 'groq'
from llm_provider import LLMProviderFactory
factory = LLMProviderFactory()
provider = factory.get_provider('groq')
print(f'Provider: {provider.__class__.__name__}')
"
```

---

## API & Provider Issues

### Invalid API Key Error

**Problem**: `401 Unauthorized` or `Invalid API key`

**Solution**:
1. Verify key is correct:
```bash
# Show first/last 10 chars to verify
echo $GROQ_API_KEY | cut -c1-10 && echo ... && echo $GROQ_API_KEY | rev | cut -c1-10 | rev
```

2. Check key format:
- Groq: starts with `gsk_`
- OpenAI: starts with `sk-`
- Anthropic: starts with `sk-ant-`

3. Test key manually:
```bash
# Groq
curl -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models

# OpenAI
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

4. Regenerate key if old:
   - Go to provider dashboard
   - Create new API key
   - Update .env

---

### Rate Limit Exceeded

**Problem**: `429 Too Many Requests` or `Rate limit exceeded`

**Solution**:
- Wait a few minutes before retrying
- Use MockProvider for testing
- Switch to different provider with higher limits
- Reduce request frequency

---

### Network Timeout

**Problem**: `Connection timeout` or `Request timed out`

**Solution**:
```bash
# 1. Check internet connection
ping api.groq.com

# 2. Check DNS
nslookup api.groq.com

# 3. Try with longer timeout
python -c "
import os
os.environ['REQUEST_TIMEOUT'] = '60'  # 60 seconds
from llm_provider import LLMProviderFactory
factory = LLMProviderFactory()
provider = factory.get_provider('groq')
response = provider.generate_response(
    [{'role': 'user', 'content': 'Hello'}],
    'Be helpful'
)
print(response)
"
```

---

### API Response Format Error

**Problem**: `ValueError: Invalid JSON` or parsing error

**Solution**:
1. Check if LLM output includes `<DESIGN_OUTPUT>` tags:
```bash
python -c "
from llm_provider import parse_design_output
text = '''Some response without design tags'''
result = parse_design_output(text)
print(result)  # None or error
"
```

2. Try different LLM provider:
```bash
export LLM_PROVIDER=mock
# Or switch to openai, anthropic, etc.
```

3. Update system prompt in `routes/chat.py`

---

## Frontend Issues

### Chat Not Sending Messages

**Problem**: Click "Send" but nothing happens

**Solution**:
1. Check browser console (F12):
   - Look for JavaScript errors
   - Check Network tab → POST /chat

2. Verify Flask server is running:
```bash
curl http://localhost:5000/health
```

3. Check message input is not empty:
   - Type in chat input field
   - Click Send

4. Clear browser cache:
   - DevTools → Application → Clear storage
   - Or Ctrl+Shift+Delete

---

### Design Panel Not Appearing

**Problem**: Send message but design panel stays hidden

**Solution**:
1. Check browser console for errors (F12)

2. Verify LLM response includes design:
```python
# In routes/chat.py, add:
print(f"DEBUG: Response: {response}")
print(f"DEBUG: Structured: {structured}")
print(f"DEBUG: Has design: {has_design}")
```

3. Try with MockProvider:
```bash
export LLM_PROVIDER=mock
```

4. Check CSS z-index on mobile:
   - Open DevTools on mobile view
   - Inspect design-panel element
   - Check z-index value

---

### Image Upload Not Working

**Problem**: Click "Upload Image" but nothing happens

**Solution**:
1. Check file format:
   - Supported: JPG, PNG, GIF, WebP
   - Not supported: BMP, TIFF, SVG

2. Check file size:
   - Max: 25MB
   - Recommended: <5MB

3. Check browser console for errors (F12)

4. Verify endpoint is working:
```bash
# Test image upload endpoint
curl -X POST http://localhost:5000/analyze-image \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/...",
    "mimeType": "image/jpeg"
  }'
```

---

### Mobile Display Issues

**Problem**: App looks broken on mobile phone

**Solution**:
1. Check viewport settings in `templates/index.html`:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
```

2. Test with Chrome DevTools (F12):
   - Click device toolbar icon
   - Select phone model
   - Test all screen sizes

3. Fix common mobile issues:
   - **Vertical scrolling broken**: Check CSS height properties
   - **Text too small**: Check font-size, use clamp()
   - **Buttons unclickable**: Check padding/tap area (min 48px)

4. Check for 100vh issues:
   - iOS has address bar that changes height
   - Use 100dvh instead in CSS (already done in styles.css)

---

### Colors Looking Wrong

**Problem**: Color picker shows different color than selected

**Solution**:
1. Check color format in code:
   - Should be hex: `#FF0000` or `FF0000`
   - Not RGB: `rgb(255, 0, 0)`

2. Verify COLOR_HEX_MAP in `design-panel.js`:
   - Check if color name exists
   - Verify hex value is correct

3. Test color conversion:
```javascript
// In browser console (F12)
const color = new Color('#FF0000');
console.log(color.hex);  // Should be #FF0000
```

---

## Server Issues

### Flask App Won't Start

**Problem**: `Error: Could not import 'web'` or similar

**Solution**:
```bash
# 1. Check for syntax errors
python -m py_compile web.py config.py llm_provider.py

# 2. Try importing directly
python -c "from web import app; print('OK')"

# 3. Check for circular imports
python -c "import routes; print(routes)"

# 4. Verify all files exist
ls -la web.py config.py constants.py llm_provider.py routes/
```

---

### Port Already in Use

**Problem**: `Address already in use` or `Port 5000 already in use`

**Solution**:
```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
export FLASK_PORT=5001
python -c "from web import app; app.run(port=5001)"
```

---

### High CPU Usage

**Problem**: Flask process using 100% CPU

**Solution**:
1. Check for infinite loops in code
2. Look for busy-wait patterns
3. Use profiler:
```bash
pip install py-spy
py-spy record -o profile.svg -- python web.py
```

4. Restart app:
```bash
# Press Ctrl+C in terminal
# Then restart
python -c "from web import app; app.run(debug=True)"
```

---

## Deployment Issues

### Vercel Deployment Fails

**Problem**: Deployment error or build failure

**Solution**:
1. Check deployment logs:
```bash
vercel logs dobby-textile-assistant
```

2. Common causes:
   - Missing environment variables → Add in Vercel dashboard
   - Python version mismatch → Use python 3.10+ in vercel.json
   - Missing dependencies → Update requirements.txt

3. Test locally:
```bash
vercel dev  # Test locally first
```

---

### Heroku Deployment Fails

**Problem**: Push rejected or app crashes on Heroku

**Solution**:
1. Check logs:
```bash
heroku logs -t
```

2. Create Procfile if missing:
```
web: python -m gunicorn -b 0.0.0.0:$PORT web:app
```

3. Set environment variables:
```bash
heroku config:set LLM_PROVIDER=groq
heroku config:set GROQ_API_KEY=gsk_...
```

4. Check Python version:
```bash
# Create runtime.txt
echo "python-3.11.4" > runtime.txt
```

---

### Serverless Cold Start

**Problem**: First request takes 30+ seconds

**Solution**:
- Cold starts are normal (2-5 seconds typical)
- Vercel may take longer first time
- Subsequent requests are fast
- Not a bug, this is expected behavior

---

## Performance Issues

### Responses Too Slow

**Problem**: Chat responses take >10 seconds

**Causes & Solutions**:

1. **Wrong provider**:
```bash
# Check if using slow provider
echo $LLM_PROVIDER

# Switch to Groq (fastest)
export LLM_PROVIDER=groq
```

2. **Network latency**:
```bash
# Ping API endpoint
ping api.groq.com

# Check latency
curl -w "Time: %{time_total}s" https://api.groq.com/openai/v1/models
```

3. **API provider overloaded**:
   - Try again later
   - Switch to different provider
   - Check provider status page

4. **Local machine slow**:
   - Close other applications
   - Check disk space
   - Check RAM availability

---

### Image Analysis Very Slow

**Problem**: Image upload takes >30 seconds

**Solution**:
1. Compress image before upload:
   - Reduce resolution
   - Reduce file size (<5MB)
   - Use JPG instead of PNG

2. Use faster vision provider:
   - Switch from Bedrock to Gemini
   - Or use Mock for testing

3. Check internet connection:
```bash
speedtest-cli  # Install and run speed test
```

---

## Security Issues

### API Key Accidentally Committed

**Problem**: API key is in GitHub repository

**Solution**:
1. Immediately rotate the key
   - Go to provider dashboard
   - Delete old key
   - Create new key

2. Remove from git history:
```bash
# Find commit with key
git log -p --all -S "gsk_" | head -50

# Use git-filter-branch (advanced)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all
```

3. Force push:
```bash
git push --force-with-lease origin main
```

---

## Data Issues

### Chat History Not Persisting

**Problem**: Refreshing page loses conversation

**Expected behavior** - This is by design. The app doesn't persist conversation history between page refreshes.

If you want to keep history:
1. Copy chat text before leaving page
2. Save design JSON manually
3. Or add database (future feature)

---

### Design Panel Shows Wrong Data

**Problem**: Design values don't match what was selected

**Solution**:
1. Clear browser cache:
   - DevTools → Application → Clear storage
   - Or Ctrl+Shift+Delete

2. Refresh page:
   - Ctrl+R or Cmd+R

3. Check for JavaScript errors (F12)

---

## Getting More Help

### Check Logs

```bash
# Flask development server logs
# Should show errors in terminal

# Browser console (F12)
# Shows JavaScript errors

# Network tab (DevTools)
# Shows HTTP requests and responses
```

### Enable Debug Logging

```python
# In web.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Then use in code
logger.debug(f"Provider: {provider}")
logger.error(f"Error: {error}")
```

### Ask for Help

1. Check existing GitHub issues
2. Search Stack Overflow
3. Open new GitHub issue with:
   - Error message
   - Steps to reproduce
   - Python version
   - OS and browser version
   - What you've already tried

---

## Known Limitations

1. **No chat history persistence** - Conversation lost on page refresh
2. **Single user at a time** - Not designed for concurrent users
3. **No database** - All data is in-memory
4. **Mobile keyboard issues** - May cover input on older phones
5. **Provider latency** - Depends on external APIs (not under our control)

---

## Still Stuck?

1. **Read the docs**:
   - [README.md](README.md) - Overview
   - [CONFIGURATION.md](CONFIGURATION.md) - Setup
   - [API.md](API.md) - Endpoints
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Design

2. **Search**:
   - GitHub issues
   - Stack Overflow
   - Google the error message

3. **Debug systematically**:
   - Check logs
   - Isolate the problem
   - Test with simpler input
   - Check each component

4. **Ask for help**:
   - Open GitHub issue
   - Include error message
   - Include steps to reproduce
   - Include environment details

---

**Still need help?** Open an issue: https://github.com/GauravPatil2515/dobby-textile-assistant/issues
