"""
Vision analysis endpoint.

Provides POST /analyze-image which accepts JSON with keys:
- image: base64 data URL or raw base64 string
- mimeType: optional mime type (defaults to image/jpeg)

Returns:
- { success: True, structured: {...}, provider: 'name' }
- or { success: False, error: 'message' }
"""

from flask import Blueprint, request, jsonify, session
from llm_provider import get_vision_provider

vision_bp = Blueprint('vision', __name__)

# Store vision provider override in memory (per-process)
_vision_provider_override = None


@vision_bp.route('/api/vision-provider', methods=['POST'])
def set_vision_provider():
    """Switch the active vision provider at runtime.
    Body: { "provider": "gemini" | "bedrock" | "mock" }
    """
    global _vision_provider_override
    data = request.get_json() or {}
    provider = data.get('provider', 'mock')

    valid = {'gemini', 'bedrock', 'openrouter', 'mock'}
    if provider not in valid:
        return jsonify({'error': f'Invalid provider. Use: {valid}'}), 400

    _vision_provider_override = provider
    return jsonify({'active': provider, 'status': 'switched'})


@vision_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze a fabric/garment image and return structured design JSON.

    Expects JSON body with `image` (base64 string) and optional `mimeType`.

    Returns:
        JSON response as described in module docstring.
    """
    data = request.get_json() or {}
    image_b64 = data.get('image', '')
    mime_type = data.get('mimeType', 'image/jpeg')

    if not image_b64:
        return jsonify({'success': False, 'error': 'No image provided'}), 400

    provider_name = data.get('provider')
    
    try:
        # Check for provider in payload or fallback to override
        active_provider = provider_name or _vision_provider_override
        if active_provider:
            import os
            os.environ['VISION_PROVIDER'] = active_provider
        
        provider = get_vision_provider()
        structured = provider.analyze_image(image_b64, mime_type)

        return jsonify({
            'success': True,
            'structured': structured,
            'provider': provider.get_model_name()
        })
    except Exception as e:
        print(f"[ERROR] Vision analysis failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
