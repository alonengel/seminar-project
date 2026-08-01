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


# --- key_status (startup console diagnostic) ---
class _FakeStatusClient:
    """Fake httpx.Client whose get() returns a fixed status code or raises."""

    def __init__(self, status_code=200, error=None):
        self._status_code = status_code
        self._error = error

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, *args, **kwargs):
        if self._error is not None:
            raise self._error
        resp = _FakeResponse({})
        resp.status_code = self._status_code
        return resp


def test_key_status_missing(monkeypatch):
    _only(monkeypatch, None)
    state, message = llm_client.key_status()
    assert state == "missing"
    assert ".env" in message


def test_key_status_placeholder(monkeypatch):
    _only(monkeypatch, None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "your-key-here")
    state, message = llm_client.key_status()
    assert state == "placeholder"
    assert "ANTHROPIC_API_KEY" in message


def test_key_status_ok(monkeypatch):
    _only(monkeypatch, "ANTHROPIC_API_KEY")
    monkeypatch.setattr(llm_client.httpx, "Client", lambda **kw: _FakeStatusClient(200))
    state, message = llm_client.key_status()
    assert state == "ok"
    assert "anthropic" in message


def test_key_status_rejected(monkeypatch):
    _only(monkeypatch, "OPENAI_API_KEY")
    monkeypatch.setattr(llm_client.httpx, "Client", lambda **kw: _FakeStatusClient(401))
    state, message = llm_client.key_status()
    assert state == "rejected"
    assert "REJECTED" in message


def test_key_status_unreachable_on_network_error(monkeypatch):
    _only(monkeypatch, "GOOGLE_API_KEY")
    error = llm_client.httpx.ConnectError("no internet")
    monkeypatch.setattr(llm_client.httpx, "Client", lambda **kw: _FakeStatusClient(error=error))
    state, message = llm_client.key_status()
    assert state == "unreachable"
    assert "gemini" in message


def test_key_status_unreachable_on_server_error(monkeypatch):
    _only(monkeypatch, "ANTHROPIC_API_KEY")
    monkeypatch.setattr(llm_client.httpx, "Client", lambda **kw: _FakeStatusClient(500))
    state, _ = llm_client.key_status()
    assert state == "unreachable"
