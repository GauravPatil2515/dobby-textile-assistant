"""
Vision analysis endpoint.

Provides POST /analyze-image which accepts JSON with keys:
- image: base64 data URL or raw base64 string
- mimeType: optional mime type (defaults to image/jpeg)

Returns:
- { success: True, structured: {...}, provider: 'name' }
- or { success: False, error: 'message' }
"""

from flask import Blueprint, request, jsonify
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
    import os
    import base64
    
    data = request.get_json() or {}
    image_b64 = data.get('image', '')
    mime_type = data.get('mimeType', 'image/jpeg')

    # Validate image input
    if not image_b64:
        return jsonify({'success': False, 'error': 'No image provided'}), 400
    
    # Handle data URL format (e.g., data:image/jpeg;base64,/9j/...)
    if image_b64.startswith('data:'):
        try:
            image_b64 = image_b64.split(',', 1)[1]
        except IndexError:
            return jsonify({'success': False, 'error': 'Invalid data URL format'}), 400
    
    # Validate base64 format
    try:
        decoded = base64.b64decode(image_b64, validate=True)
        # Check file size (max 25MB)
        if len(decoded) > 25 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'Image too large (max 25MB)'}), 400
        if len(decoded) < 100:
            return jsonify({'success': False, 'error': 'Image too small or invalid'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Invalid base64 image: {str(e)}'}), 400

    provider_name = data.get('provider')
    
    try:
        # Set vision provider override in environment
        # This is checked by get_vision_provider() at runtime
        active_provider = provider_name or _vision_provider_override
        if active_provider:
            os.environ['VISION_PROVIDER'] = active_provider
        
        provider = get_vision_provider()
        structured = provider.analyze_image(image_b64, mime_type)
        
        if not structured:
            return jsonify({
                'success': False,
                'error': 'No design data extracted from image analysis'
            }), 400

        return jsonify({
            'success': True,
            'structured': structured,
            'provider': provider.get_model_name()
        })
    except ValueError as e:
        # Configuration error (missing API key, etc.)
        print(f"[ERROR] Vision provider config error: {e}")
        return jsonify({'success': False, 'error': f'Provider error: {str(e)}'}), 400
    except Exception as e:
        print(f"[ERROR] Vision analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Analysis failed: {str(e)}'}), 500
