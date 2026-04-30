# DEPLOYMENT

Complete guide for deploying Dobby Textile Assistant to production.

## Deployment Options

### Option 1: Vercel (Recommended)

Vercel provides the easiest deployment with serverless support built-in.

#### Prerequisites

- Vercel account (free at vercel.com)
- GitHub account with repository fork
- Git CLI installed

#### Steps

1. **Fork the repository**:
```bash
# On GitHub: Click "Fork"
# Or clone and push to your repo:
git clone https://github.com/GauravPatil2515/dobby-textile-assistant.git
git remote set-url origin https://github.com/YOUR_USERNAME/dobby-textile-assistant.git
git push -u origin main
```

2. **Connect to Vercel**:
```bash
npm install -g vercel
vercel login  # Sign in with GitHub
```

3. **Deploy**:
```bash
cd dobby-textile-assistant
vercel
```

Select your GitHub organization and authorize.

4. **Configure Environment Variables**:
   - In Vercel dashboard: Settings → Environment Variables
   - Add all variables from `.env.example`:

```
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
VISION_PROVIDER=gemini
FLASK_DEBUG=0
```

5. **Verify Deployment**:
```bash
# Vercel outputs deployment URL
open https://dobby-textile-assistant.vercel.app
```

**Deployment Time**: ~2 minutes

**Cost**: Free tier includes 100 serverless function calls/day

---

### Option 2: Heroku

For traditional app hosting with dynos.

#### Prerequisites

- Heroku account (free at heroku.com)
- Heroku CLI installed

#### Steps

1. **Create Procfile** in project root:
```
web: python -m gunicorn -b 0.0.0.0:$PORT web:app
```

2. **Create heroku app**:
```bash
heroku login
heroku create dobby-textile-assistant
```

3. **Set environment variables**:
```bash
heroku config:set LLM_PROVIDER=groq
heroku config:set GROQ_API_KEY=gsk_...
heroku config:set GEMINI_API_KEY=AIza...
heroku config:set FLASK_DEBUG=0
```

4. **Push to Heroku**:
```bash
git push heroku main
```

5. **View logs**:
```bash
heroku logs --tail
```

**Deployment Time**: ~5 minutes

**Cost**: Free tier (single dyno, 1GB RAM)

---

### Option 3: Railway.app

Modern alternative to Heroku.

#### Prerequisites

- Railway account (free at railway.app)
- GitHub account

#### Steps

1. **Connect GitHub repository**:
   - Go to railway.app
   - New Project → GitHub Repo
   - Select your repository

2. **Add environment variables**:
   - Variables → Add Variable
   - LLM_PROVIDER, GROQ_API_KEY, etc.

3. **Deploy**:
   - Railway auto-deploys on `git push`
   - Check deployments tab for status

**Deployment Time**: ~3 minutes

**Cost**: Free tier includes usage credits

---

### Option 4: Docker + Any Cloud

For maximum flexibility.

#### Create Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 5000

# Environment
ENV FLASK_APP=web.py
ENV FLASK_DEBUG=0

# Run with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "web:app"]
```

#### Create .dockerignore

```
.env
.git
__pycache__
.venv
venv
```

#### Build and run locally

```bash
docker build -t dobby-textile .
docker run -p 5000:5000 -e GROQ_API_KEY=gsk_... dobby-textile
```

#### Deploy to cloud

**Google Cloud Run**:
```bash
gcloud run deploy dobby-textile \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars GROQ_API_KEY=gsk_...
```

**AWS ECS**:
```bash
# Push to ECR, then create ECS service
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag dobby-textile:latest <account>.dkr.ecr.us-east-1.amazonaws.com/dobby-textile:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/dobby-textile:latest
```

---

## Environment Variables

### Required

```bash
# LLM Provider selection
LLM_PROVIDER=groq|openai|anthropic|openrouter|mock

# API Keys (required for selected provider)
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...

# Vision Provider selection
VISION_PROVIDER=gemini|bedrock|cloud-vision|mock

# Vision API Keys (if using non-mock provider)
GEMINI_API_KEY=AIza...
BEDROCK_AWS_REGION=us-east-1
BEDROCK_AWS_ACCESS_KEY_ID=...
BEDROCK_AWS_SECRET_ACCESS_KEY=...
GOOGLE_CLOUD_CREDENTIALS=/path/to/credentials.json
```

### Optional

```bash
# Flask Configuration
FLASK_DEBUG=0|1  # Default: 0 (disabled)
FLASK_HOST=127.0.0.1  # Default: localhost
FLASK_PORT=5000  # Default: 5000

# Model Selection (override defaults)
GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
OPENROUTER_MODEL=deepseek/deepseek-r1:free

# CORS Configuration
CORS_ORIGINS=https://example.com,https://another.com

# Logging
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
```

---

## Provider Setup

### Groq (Recommended)

1. **Create account**: https://console.groq.com
2. **Create API key**:
   - Go to API keys section
   - Create new key
   - Copy key value
3. **Set in environment**:
```bash
export GROQ_API_KEY=gsk_YOUR_KEY
```
4. **Test**:
```bash
python -c "from groq import Groq; print(Groq(api_key=os.getenv('GROQ_API_KEY')).models.list())"
```

**Cost**: Free tier includes 30k tokens/month

---

### OpenAI

1. **Create account**: https://platform.openai.com
2. **Add payment method**
3. **Create API key**:
   - User → API keys
   - Create new secret key
4. **Set in environment**:
```bash
export OPENAI_API_KEY=sk-YOUR_KEY
```

**Cost**: Pay-as-you-go (~$0.01-0.10 per request)

---

### Google Gemini

1. **Create account**: https://ai.google.dev
2. **Create API key**:
   - API keys page
   - Create new key
3. **Set in environment**:
```bash
export GEMINI_API_KEY=AIza_YOUR_KEY
```

**Cost**: Free tier includes 60 requests/minute

---

### AWS Bedrock

1. **Enable Bedrock**:
   - AWS Console → Bedrock
   - Accept terms
2. **Create IAM user**:
   - Permissions: bedrock:InvokeModel
3. **Set credentials**:
```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export BEDROCK_AWS_REGION=us-east-1
```

**Cost**: Pay-as-you-go (~$0.001-0.01 per request)

---

## Monitoring & Logging

### Vercel

**View logs**:
```bash
vercel logs dobby-textile-assistant
```

**Real-time logs**:
```bash
vercel logs dobby-textile-assistant --follow
```

**Dashboard**: https://vercel.com/dashboard

---

### Heroku

**View logs**:
```bash
heroku logs -t
```

**View specific dyno**:
```bash
heroku logs -t -d web.1
```

---

### Self-Hosted

**View application logs**:
```bash
# If running with gunicorn
tail -f /var/log/gunicorn.log

# If running with systemd
journalctl -u dobby-textile -f
```

---

## Performance Optimization

### 1. Enable Caching

```python
# In config.py
RESPONSE_CACHE_TTL = 300  # 5 minutes
DESIGN_CACHE = {}

# Then use in routes:
cache_key = hash(messages)
if cache_key in DESIGN_CACHE:
    return DESIGN_CACHE[cache_key]
```

### 2. Use CDN for Static Files

Vercel automatically serves CSS/JS from CDN.

For self-hosted:
```python
# Use Flask-Caching
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/')
@cache.cached(timeout=3600)
def index():
    return render_template('index.html')
```

### 3. Enable Compression

```python
# In web.py
from flask_compress import Compress
Compress(app)
```

### 4. Database Connection Pooling

```python
# If adding database later
from sqlalchemy.pool import QueuePool

db = SQLAlchemy(app, engine_options={
    "poolclass": QueuePool,
    "pool_size": 10,
    "pool_recycle": 3600,
})
```

---

## Security Checklist

- [ ] All API keys in `.env` (never committed)
- [ ] `.env` added to `.gitignore`
- [ ] `.gitignore` includes `__pycache__`, `venv`, `*.pyc`
- [ ] FLASK_DEBUG set to 0 in production
- [ ] CORS configured for allowed origins only
- [ ] HTTPS enabled (automatic on Vercel/Heroku)
- [ ] Rate limiting enabled (if high traffic)
- [ ] Input validation on all endpoints
- [ ] Error messages don't expose sensitive info
- [ ] Access logs enabled for audit trail

---

## Scaling Strategy

### Phase 1: MVP (Current)
- Single Vercel instance
- Groq + Gemini providers
- ~100 daily active users

### Phase 2: Growth
- Add Redis for caching
- Implement request queuing
- Monitor API usage
- ~1K daily active users

### Phase 3: Enterprise
- Multi-region deployment
- Load balancing
- Database (PostgreSQL)
- Admin dashboard
- ~10K daily active users

---

## Troubleshooting

### Deployment Fails

**Check logs**:
```bash
# Vercel
vercel logs -t

# Heroku
heroku logs -t

# Docker
docker logs <container_id>
```

**Common issues**:
- Missing environment variables
- Python version mismatch
- Missing dependencies

### App is Slow

**Causes**:
- Cold start (first request takes 1-2 seconds)
- API provider slow response
- Frontend JS parsing

**Solutions**:
- Use Groq for faster responses
- Enable caching
- Minify frontend JS

### API Key Errors

**Check keys are valid**:
```bash
# Test Groq key
curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models

# Test OpenAI key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

---

## Backup & Recovery

### GitHub as Backup

All code is version-controlled on GitHub.

```bash
# Clone latest version anytime
git clone https://github.com/GauravPatil2515/dobby-textile-assistant.git
```

### Database Backup (if added)

```bash
# PostgreSQL backup
pg_dump -h localhost -U user dobby_db > backup.sql

# Restore
psql -h localhost -U user dobby_db < backup.sql
```

---

## DNS & Custom Domain

### Vercel with Custom Domain

1. **Add domain in Vercel dashboard**
2. **Update DNS provider**:
   - Add CNAME record pointing to Vercel
3. **Verify ownership**
4. **Enable SSL** (automatic)

Example DNS record:
```
dobby.yourdomain.com CNAME cname.vercel-dns.com
```

---

## SSL/TLS Certificates

**Vercel**: Automatic (Let's Encrypt)

**Heroku**: Automatic (ACM)

**Self-hosted**: Use Certbot
```bash
sudo certbot certonly --standalone -d yourdomain.com
```

---

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help.
