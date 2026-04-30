"""
Health and provider listing endpoints.

Provides:
- GET /health
- GET /api/providers
"""

from flask import Blueprint, jsonify
from config import get_provider_name
from llm_provider import LLMProviderFactory

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health():
    """Return basic health status and active provider.

    Returns:
        JSON object with `status` and `provider` keys.
    """
    return jsonify({'status': 'ok', 'provider': get_provider_name()})


@health_bp.route('/api/providers')
def providers():
    """Return available LLM providers and the currently active one.

    Returns:
        JSON object with `providers` (list) and `active` (string).
    """
    return jsonify({
        'providers': LLMProviderFactory.get_available_providers(),
        'active': get_provider_name()
    })
