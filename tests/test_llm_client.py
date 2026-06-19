"""Unit tests for the optional LLM client (no real network calls)."""

import pytest

import llm_client


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class _FakeClient:
    def __init__(self, data):
        self._data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, *args, **kwargs):
        return _FakeResponse(self._data)


def _only(monkeypatch, name, value="real-key-123"):
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    if name:
        monkeypatch.setenv(name, value)


def test_env_key_rejects_empty_and_placeholders(monkeypatch):
    monkeypatch.setenv("X", "")
    assert llm_client.env_key("X") is None
    monkeypatch.setenv("X", "your-key-here")
    assert llm_client.env_key("X") is None
    monkeypatch.setenv("X", "sk-realvalue")
    assert llm_client.env_key("X") == "sk-realvalue"


def test_active_provider_priority(monkeypatch):
    _only(monkeypatch, None)
    assert llm_client.active_provider() is None
    assert llm_client.available() is False
    _only(monkeypatch, "OPENAI_API_KEY")
    assert llm_client.active_provider() == "openai"
    assert llm_client.available() is True
    monkeypatch.setenv("ANTHROPIC_API_KEY", "real-key-123")
    assert llm_client.active_provider() == "anthropic"  # anthropic takes priority


def test_complete_raises_without_provider(monkeypatch):
    _only(monkeypatch, None)
    with pytest.raises(RuntimeError):
        llm_client.complete("sys", "user")


def test_complete_openai(monkeypatch):
    _only(monkeypatch, "OPENAI_API_KEY")
    data = {"choices": [{"message": {"content": "hello"}}]}
    monkeypatch.setattr(llm_client.httpx, "Client", lambda **kwargs: _FakeClient(data))
    resp = llm_client.complete("sys", "user")
    assert resp.text == "hello"
    assert resp.provider == "openai"


def test_complete_anthropic(monkeypatch):
    _only(monkeypatch, "ANTHROPIC_API_KEY")
    data = {"content": [{"type": "text", "text": "hi there"}]}
    monkeypatch.setattr(llm_client.httpx, "Client", lambda **kwargs: _FakeClient(data))
    resp = llm_client.complete("sys", "user")
    assert resp.text == "hi there"
    assert resp.provider == "anthropic"


def test_complete_gemini(monkeypatch):
    _only(monkeypatch, "GOOGLE_API_KEY")
    data = {"candidates": [{"content": {"parts": [{"text": "yo"}]}}]}
    monkeypatch.setattr(llm_client.httpx, "Client", lambda **kwargs: _FakeClient(data))
    resp = llm_client.complete("sys", "user")
    assert resp.text == "yo"
    assert resp.provider == "gemini"
