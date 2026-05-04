# Dobby Textile Design Assistant

An intelligent AI-powered system for analyzing fabric images and generating customized textile designs using advanced LLM and vision capabilities.

## 🎯 Features

- **Smart Fabric Analysis**: Analyze textile images using multiple vision AI providers (Gemini, AWS Bedrock, Google Cloud Vision)
- **Conversational Design Generation**: Natural language interface for discussing and refining textile designs
- **Multiple LLM Support**: Choose between Groq, OpenAI, Anthropic, or OpenRouter for design generation
- **Interactive Design Editor**: Real-time design specification editing with color palette management
- **Offline Mode**: MockProvider for development and testing without API keys
- **Responsive UI**: Modern light-mode web interface optimized for desktop and mobile
- **Vercel Deployment**: Serverless deployment ready with Vercel integration

## 🏗️ Architecture

- **Backend**: Python Flask API with modular blueprint architecture
- **Frontend**: Vanilla JavaScript with 6 modular components (no framework dependencies)
- **Providers**: Factory pattern with pluggable LLM and vision providers
- **Strategy Pattern**: Fallback chain for LLM selection (Groq → OpenAI → Anthropic → OpenRouter)
- **Deployment**: Vercel serverless with environment-based configuration

## 📋 Requirements

- Python 3.10+
- Node.js 18+ (for Vercel CLI, optional)
- API keys for at least one LLM provider (Groq recommended, free tier available)
- Vision API key (optional: Gemini for image analysis)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**:
```bash
git clone https://github.com/GauravPatil2515/dobby-textile-assistant.git
cd dobby-textile-assistant
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Run development server**:
```bash
python -c "from web import app; app.run(debug=True)"
```

Visit `http://localhost:5000` in your browser.

### Using MockProvider (No API Keys Needed)

To test without API keys, set environment variables:
```bash
export LLM_PROVIDER=mock
export VISION_PROVIDER=mock
# Then run the server
```

## 📚 Documentation

- **[API.md](API.md)** - Complete endpoint documentation with examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed technical architecture
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Vercel deployment guide
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Local setup and contribution guidelines
- **[CONFIGURATION.md](CONFIGURATION.md)** - Environment and API key setup
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

## 🔑 Supported Providers

### LLM Providers
| Provider | Speed | Cost | Recommended |
|----------|-------|------|-------------|
| **Groq** | ⚡⚡⚡ Fastest | Free tier available | ✅ Recommended |
| **OpenAI** | ⚡⚡ Fast | Paid only | Enterprise |
| **Anthropic** | ⚡ Moderate | Paid only | Quality |
| **OpenRouter** | ⚡ Moderate | Paid only | Flexibility |
| **Mock** | ⚡⚡⚡ Local | Free | Development |

### Vision Providers
| Provider | Quality | Cost | Fallback |
|----------|---------|------|----------|
| **Gemini 2.0 Flash** | Excellent | Paid | First choice |
| **AWS Bedrock** | Excellent | Paid | Second choice |
| **Google Cloud Vision** | Good | Paid | Third choice |
| **Mock** | Simulated | Free | Local testing |

## 💡 Core Concepts

### Textile Design Specification
Each design includes:
- **Base Color**: RGB values for primary color
- **Color Palette**: 5-10 harmonious colors with family relationships
- **Stripe Sizes**: Micro/Small/Medium/Large (6mm to 25mm+)
- **Design Sizes**: Repeat sizes from Micro (6cm) to Full Size (100cm+)
- **Pattern Type**: Stripes, checks, florals, geometric, abstract
- **Occasion**: Formal, Casual, Party Wear (affects design complexity)

### Conversation Flow
1. User uploads fabric image or describes design idea
2. AI analyzes and generates design recommendations
3. User can refine using natural language ("Make stripes wider", "Use blue palette")
4. Design panel opens with editable specifications
5. Export design as JSON for production

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 2.0+
- **Python**: 3.10+
- **AI/ML**: Groq, OpenAI, Anthropic APIs
- **Vision**: Gemini, AWS Bedrock, Google Cloud Vision
- **Deployment**: Vercel Serverless
- **Config**: python-dotenv

### Frontend
- **HTML5/CSS3**: Semantic markup with modern CSS
- **JavaScript**: Vanilla ES6 (no frameworks)
- **Icons**: Lucide Icons via CDN
- **Typography**: Inter font family
- **Responsive**: Mobile-first design, 100% client-side

## 📦 Project Structure

```
dobby-textile-assistant/
├── web.py                    # Flask app entrypoint
├── config.py                 # Configuration & prompts
├── constants.py              # Textile design constants
├── llm_provider.py           # LLM & vision providers (1,541 lines)
├── routes/
│   ├── __init__.py          # Route registration
│   ├── chat.py              # Chat endpoint (164 lines)
│   └── vision.py            # Image analysis endpoint (71 lines)
├── static/
│   ├── css/styles.css       # Complete styling (26KB)
│   └── js/
│       ├── app.js           # App initialization
│       ├── chat.js          # Message handling
│       ├── design-panel.js  # Design editor (425 lines)
│       ├── image-analysis.js # Image upload UI
│       ├── voice.js         # Voice input
│       └── utilities.js     # Helpers
├── templates/
│   └── index.html           # HTML shell (134 lines)
├── api/
│   └── index.py             # Vercel serverless handler
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── vercel.json              # Vercel config
└── README.md                # This file

```

## 🔐 Security

- **Environment Variables**: All API keys stored in `.env` (git-ignored)
- **CORS**: Configured for same-origin requests
- **Input Validation**: Base64 image validation, text sanitization
- **Error Handling**: Graceful fallbacks, no sensitive data in responses

## 📊 Performance

- **LLM Response**: 0.5-3 seconds (Groq is fastest)
- **Image Analysis**: 1-5 seconds (Gemini 2.0 Flash)
- **Frontend**: <200ms for UI interactions
- **Deployment**: <50ms cold start on Vercel

## 🐛 Known Issues & Limitations

- Design output parsing from LLMs varies by provider
- Vision analysis quality depends on image quality and fabric contrast
- Mobile viewport may show scrolling issues on iOS 14-15
- Concurrent requests share vision provider state (not thread-safe by design)

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [DEVELOPMENT.md](DEVELOPMENT.md) for contribution guidelines.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Gaurav Patil**
- GitHub: [@GauravPatil2515](https://github.com/GauravPatil2515)
- Email: gaurav@textile.ai

**Yuvraj karunakaran**
- GitHub:yuvrajkaiml(https://github.com/yuvrajkaiml)
- Email: yuvraj@textile.ai

## 🙏 Acknowledgments

- Groq for high-speed LLM inference
- Google Gemini for advanced vision capabilities
- AWS Bedrock for enterprise vision options
- The open-source community for tools and libraries

## 📞 Support

For issues, questions, or feedback:
- Open an issue on [GitHub](https://github.com/GauravPatil2515/dobby-textile-assistant/issues)
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first

---

**Status**: ✅ Production Ready | **Last Updated**: 2024 | **Version**: 1.0.0
