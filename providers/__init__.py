"""
Provider package for LLM and Vision model integration.

Provides pluggable interfaces for:
- LLM providers (Groq, OpenAI, Anthropic, OpenRouter, Mock)
- Vision providers (Gemini Vision, Mock)
"""

# Import from the main llm_provider.py file (which contains all provider classes)
# This maintains backward compatibility while organizing the package structure
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_provider import (
    LLMProvider,
    GroqProvider,
    OpenAIProvider,
    AnthropicProvider,
    OpenRouterProvider,
    MockProvider,
    LLMProviderFactory,
    build_color_palette,
    MockVisionProvider,
    GeminiVisionProvider,
    get_vision_provider,
)

__all__ = [
    "LLMProvider",
    "GroqProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OpenRouterProvider",
    "MockProvider",
    "LLMProviderFactory",
    "build_color_palette",
    "MockVisionProvider",
    "GeminiVisionProvider",
    "get_vision_provider",
]
