"""
Optional LLM client (HTTP-based, mirrors the reference projects' pattern).

A single `complete(system, user)` facade calls one provider's REST API. The
provider is chosen by which API key is present in the environment
(anthropic > openai > google); if none is set, no provider is active and the
caller falls back to the rule-based router. Secrets come only from the
environment / a local .env (never hard-coded). The model is used solely to
select a supported question template - it never generates or runs code.
"""

import os
import time
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()  # populate os.environ from a local .env (no-op if absent)

_PLACEHOLDERS = ("your-key", "example", "changeme", "paste", "xxx", "...")
_TIMEOUT = int(os.environ.get("LLM_TIMEOUT_SECONDS", "60"))
_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "2"))
_MAX_TOKENS = 512


@dataclass(frozen=True)
class LlmResponse:
    text: str
    model: str
    provider: str


def env_key(name):
    """Return a usable API key from the environment, or None (placeholders rejected)."""
    value = (os.environ.get(name) or "").strip()
    if not value or any(marker in value.lower() for marker in _PLACEHOLDERS):
        return None
    return value


def _openai(system, user, max_tokens=_MAX_TOKENS):
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {env_key('OPENAI_API_KEY')}"},
            json={
                "model": model,
                "temperature": 0,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return LlmResponse(data["choices"][0]["message"]["content"], model, "openai")


def _anthropic(system, user, max_tokens=_MAX_TOKENS):
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": env_key("ANTHROPIC_API_KEY"),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
    text = "".join(block.get("text", "") for block in data.get("content", []))
    return LlmResponse(text, model, "anthropic")


def _gemini(system, user, max_tokens=_MAX_TOKENS):
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    key = env_key("GOOGLE_API_KEY") or env_key("GEMINI_API_KEY")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(
            url,
            json={
                "contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
        )
        resp.raise_for_status()
        data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return LlmResponse(text, model, "gemini")


_DISPATCH = {"anthropic": _anthropic, "openai": _openai, "gemini": _gemini}


def active_provider():
    """Name of the provider whose key is set, or None."""
    if env_key("ANTHROPIC_API_KEY"):
        return "anthropic"
    if env_key("OPENAI_API_KEY"):
        return "openai"
    if env_key("GOOGLE_API_KEY") or env_key("GEMINI_API_KEY"):
        return "gemini"
    return None


def available():
    return active_provider() is not None


def complete(system, user, max_tokens=_MAX_TOKENS):
    """Call the active provider, retrying transient (429/5xx/transport) errors.

    `max_tokens` defaults to the small routing budget; the code-generation agent
    passes a larger value so a full snippet is not truncated.
    """
    provider = active_provider()
    if provider is None:
        raise RuntimeError("No LLM provider configured (set an API key in .env).")
    call = _DISPATCH[provider]
    attempts = max(0, _MAX_RETRIES) + 1
    for attempt in range(attempts):
        try:
            return call(system, user, max_tokens)
        except httpx.HTTPStatusError as exc:
            transient = exc.response.status_code == 429 or exc.response.status_code >= 500
            if not transient or attempt == attempts - 1:
                raise
            time.sleep(2)
        except httpx.TransportError:
            if attempt == attempts - 1:
                raise
            time.sleep(2)
    raise RuntimeError("unreachable retry state")
