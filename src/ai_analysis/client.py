"""
Cloudflare Workers AI client for the AI features.

Uses the free Cloudflare Workers AI endpoint (model: GLM 5.2) via plain HTTP
``requests`` — no extra SDK. Everything degrades gracefully: if the token is
missing, ``is_configured()`` is False and the UI shows a "set your key" message
instead of crashing.

Auth needs two things:
  - CLOUDFLARE_API_TOKEN   (required)  — your Workers AI API token
  - CLOUDFLARE_ACCOUNT_ID  (optional)  — auto-detected from the token if unset

To switch the model, change CF_MODEL below — that is the only place it lives.
"""
import os
import logging
import json

import requests

logger = logging.getLogger(__name__)

# ── Model (Cloudflare Workers AI) ────────────────────────────────────────
# Both AI features (insights + sentiment) use this one model.
CF_MODEL = "@cf/meta/llama-3.1-8b-instruct"

_CF_BASE = "https://api.cloudflare.com/client/v4"
_REQUEST_TIMEOUT = 90  # seconds

# Cache the auto-detected account id so we don't re-fetch it every call.
_account_id_cache = None


def _secret(key: str):
    """Read a secret from st.secrets (Streamlit Cloud) or os.getenv (local .env)."""
    try:
        import streamlit as st
        val = st.secrets.get(key, os.getenv(key))
    except Exception:
        val = os.getenv(key)
    if val is None:
        return None
    val = str(val).strip()
    return val or None


def get_token():
    """Return the Cloudflare API token, or None if not set."""
    return _secret("CLOUDFLARE_API_TOKEN")


def _resolve_account_id(token: str):
    """Return the Cloudflare account id: explicit env var, cache, or auto-detect."""
    global _account_id_cache
    explicit = _secret("CLOUDFLARE_ACCOUNT_ID")
    if explicit:
        return explicit
    if _account_id_cache:
        return _account_id_cache
    try:
        r = requests.get(
            f"{_CF_BASE}/accounts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        r.raise_for_status()
        accounts = r.json().get("result", []) or []
        if accounts:
            _account_id_cache = accounts[0]["id"]
            return _account_id_cache
    except Exception as e:
        logger.warning("Could not auto-detect Cloudflare account id: %s", e)
    return None


def is_configured() -> bool:
    """True if a Cloudflare token is present (cheap check for UI gating)."""
    return get_token() is not None


def chat(messages: list, max_tokens: int = 1024, temperature: float = 0.3) -> str:
    """Send a chat request to Cloudflare Workers AI and return the text reply.

    ``messages`` is an OpenAI-style list of {"role", "content"} dicts.
    Raises on any failure (missing config, HTTP error, unexpected shape) — the
    callers in insights.py / sentiment.py catch and degrade.
    """
    token = get_token()
    if not token:
        raise RuntimeError("CLOUDFLARE_API_TOKEN is not set")
    account_id = _resolve_account_id(token)
    if not account_id:
        raise RuntimeError(
            "Could not determine Cloudflare account id — set CLOUDFLARE_ACCOUNT_ID")

    url = f"{_CF_BASE}/accounts/{account_id}/ai/run/{CF_MODEL}"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"messages": messages, "max_tokens": max_tokens, "temperature": temperature},
        timeout=_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    # Helper to return string response (serializing if API returned parsed JSON)
    def _to_str(val) -> str:
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return str(val).strip()

    # Native Workers AI shape: {"result": {"response": "..."}, "success": true}
    result = data.get("result") if isinstance(data, dict) else None
    if isinstance(result, dict):
        if result.get("response") is not None:
            return _to_str(result["response"])
        choices = result.get("choices")
        if choices:
            return _to_str(choices[0]["message"]["content"])
    # OpenAI-compatible shape fallback: {"choices": [...]}
    if isinstance(data, dict) and data.get("choices"):
        return _to_str(data["choices"][0]["message"]["content"])

    raise RuntimeError(f"Unexpected Cloudflare AI response: {str(data)[:200]}")
