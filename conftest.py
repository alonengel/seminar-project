"""Pytest configuration: make the project-root modules importable from tests/."""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def _disable_real_llm(monkeypatch):
    """Tests must never call a real LLM API, even if a local .env defines keys.

    Cleared by default; tests that exercise provider selection set their own keys.
    """
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
