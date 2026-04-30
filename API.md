# API Documentation

Complete reference for all REST endpoints in the Dobby Textile Assistant.

## Base URL

- **Development**: `http://localhost:5000`
- **Production**: `https://dobby-textile-assistant.vercel.app`

## Endpoints

### GET `/`

Returns the web UI HTML page.

**Response**: HTML document (200 OK)

---

### GET `/health`

Health check endpoint returning app status and active provider configuration.

**Response** (200 OK):
```json
{
  "status": "ok",
  "llm_provider": "groq",
  "vision_provider": "gemini",
  "version": "1.0.0"
}
```

**Use Cases**:
- Verify server is running
- Check which providers are active
- Load balancer health checks

---

### POST `/chat`

Main conversational endpoint for design generation.

**Request**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "I need a formal stripe design in blue"
    }
  ]
}
```

**Request Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | Array | Yes | Message history with role/content |
| `messages[].role` | String | Yes | Either "user" or "assistant" |
| `messages[].content` | String | Yes | Message text |

**Response** (200 OK):
```json
{
  "reply": "I'd love to help create a formal blue stripe design...",
  "structured": {
    "base_color": "1E3A8A",
    "palette": ["1E3A8A", "1F2937", "E5E7EB"],
    "stripe_size": "Large",
    "design_size": "Medium",
    "pattern_type": "stripes",
    "occasion": "formal"
  },
  "has_design": true
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `reply` | String | Conversational response from AI |
| `structured` | Object | Parsed design specification (if present) |
| `has_design` | Boolean | Whether a design was generated |

**Examples**:

*Request - New Design*:
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Create a casual pink floral design for party wear"
      }
    ]
  }'
```

*Request - Design Refinement*:
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Create a casual pink floral design"
      },
      {
        "role": "assistant",
        "content": "I can create that! Here's a pink floral design..."
      },
      {
        "role": "user",
        "content": "Make the stripes wider and add more contrast"
      }
    ]
  }'
```

**Error Responses**:
```json
{
  "error": "No messages provided",
  "status": 400
}
```

---

### POST `/analyze-image`

Analyze a fabric image using vision AI.

**Request**:
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "mimeType": "image/jpeg"
}
```

**Request Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | String | Yes | Base64-encoded image with data URI prefix |
| `mimeType` | String | Yes | Image MIME type (image/jpeg, image/png) |

**Response** (200 OK):
```json
{
  "analysis": "Cotton fabric with blue stripes...",
  "design": {
    "base_color": "0066CC",
    "palette": ["0066CC", "003366", "FFFFFF"],
    "stripe_size": "Medium",
    "design_size": "Small",
    "pattern_type": "stripes",
    "occasion": "casual"
  }
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `analysis` | String | AI-generated analysis of the fabric |
| `design` | Object | Extracted design specification |

**Examples**:

*Request*:
```bash
# Assuming you have an image file
IMAGE_B64=$(base64 -i fabric.jpg | tr -d '\n')

curl -X POST http://localhost:5000/analyze-image \
  -H "Content-Type: application/json" \
  -d "{
    \"image\": \"data:image/jpeg;base64,$IMAGE_B64\",
    \"mimeType\": \"image/jpeg\"
  }"
```

**Error Responses**:
```json
{
  "error": "No image provided",
  "status": 400
}
```

```json
{
  "error": "Invalid base64 image",
  "status": 400
}
```

---

### POST `/set-vision-provider`

Switch vision provider at runtime.

**Request**:
```json
{
  "provider": "gemini"
}
```

**Request Parameters**:
| Field | Type | Options | Description |
|-------|------|---------|-------------|
| `provider` | String | `gemini`, `bedrock`, `cloud-vision`, `mock` | Vision provider to use |

**Response** (200 OK):
```json
{
  "provider": "gemini",
  "status": "switched"
}
```

**Error Responses**:
```json
{
  "error": "Unknown provider: unknown_provider",
  "status": 400
}
```

---

## Design Specification Format

All design responses follow this structure:

```json
{
  "base_color": "HEX_CODE",
  "palette": ["HEX_1", "HEX_2", "..."],
  "stripe_size": "Micro|Small|Medium|Large",
  "design_size": "Micro|Small|Medium|Large|Extra Large|Full Size",
  "pattern_type": "stripes|checks|florals|geometric|abstract",
  "occasion": "Formal|Casual|Party Wear"
}
```

**Field Descriptions**:

- **base_color** (String): Primary color in hexadecimal format (e.g., "1B4FD8")
- **palette** (Array): Array of 5-10 hex colors that harmonize with base_color
- **stripe_size** (String): Physical stripe width range
  - Micro: 6-8mm
  - Small: 9-12mm
  - Medium: 13-18mm
  - Large: 19-25mm+
- **design_size** (String): Design repeat size
  - Micro: 6cm
  - Small: 10-15cm
  - Medium: 20-30cm
  - Large: 40-60cm
  - Extra Large: 70-90cm
  - Full Size: 100cm+
- **pattern_type** (String): Design pattern classification
- **occasion** (String): Intended use case

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message describing what went wrong",
  "status": 400
}
```

**Common HTTP Status Codes**:
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 500 | Internal Server Error (LLM/Vision API failure) |

---

## Rate Limiting

- **Development**: No rate limiting
- **Production**: Subject to Vercel limits (concurrent connections, execution time)

---

## Authentication

Currently, no authentication is required. For production deployment, consider:
- API key validation
- CORS restrictions
- Request signing

---

## CORS Headers

Requests are accepted from same-origin only.

For cross-origin access, configure CORS in `config.py`:
```python
CORS_ORIGINS = ["https://example.com"]
```

---

## Timeouts

- **Chat endpoint**: 30 seconds
- **Image analysis**: 60 seconds
- **Health check**: 5 seconds

---

## Response Times (Typical)

| Endpoint | Provider | Time |
|----------|----------|------|
| `/chat` | Groq | 0.5-2s |
| `/chat` | OpenAI | 1-3s |
| `/chat` | Mock | <100ms |
| `/analyze-image` | Gemini | 2-5s |
| `/analyze-image` | Mock | <100ms |

---

## Example Workflows

### 1. Simple Design Generation

```bash
# 1. Send initial request
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "role": "user",
      "content": "Create a professional blue stripe design"
    }]
  }'

# Response includes design specification
```

### 2. Image-Based Design

```bash
# 1. Analyze an image
curl -X POST http://localhost:5000/analyze-image \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,..."
  }'

# 2. Refine based on analysis
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "The image shows a nice blue stripe pattern"
      },
      {
        "role": "assistant",
        "content": "Great! I've analyzed the fabric..."
      },
      {
        "role": "user",
        "content": "Make it formal and professional"
      }
    ]
  }'
```

### 3. Multi-Turn Refinement

```bash
# Turn 1
curl -X POST http://localhost:5000/chat \
  -d '{"messages": [{"role": "user", "content": "Pink design"}]}'

# Turn 2 (building on turn 1)
curl -X POST http://localhost:5000/chat \
  -d '{
    "messages": [
      {"role": "user", "content": "Pink design"},
      {"role": "assistant", "content": "...previous response..."},
      {"role": "user", "content": "Add more colors"}
    ]
  }'
```

---

## WebSocket Support

Currently not implemented. Planned for future versions for real-time streaming responses.

---

## Versioning

This documentation covers **API v1.0**. Version information available at `/health`.
