"""
Comment sentiment — classify each YouTube comment as positive / neutral /
negative with a Cloudflare Workers AI (GLM 5.2) call, in batches to keep cost
and latency low.

``analyze_comment_sentiment`` takes the processed comments DataFrame and returns
the same DataFrame with two extra columns:
  - ``sentiment_label``  : "positive" | "neutral" | "negative"
  - ``sentiment_score``  : float in [-1.0, 1.0]

Robust by design: if a batch response can't be parsed or the count doesn't
match, that batch falls back to neutral/0.0 rather than raising.
"""
import json
import logging
import re

import pandas as pd

from .client import chat, is_configured

logger = logging.getLogger(__name__)

_VALID_LABELS = {"positive", "neutral", "negative"}
_MAX_COMMENT_CHARS = 300  # truncate long comments to bound token usage

_SYSTEM_PROMPT = (
    "You are a precise sentiment classifier for YouTube comments. Analyze the list "
    "of comments provided. Respond with ONLY a raw JSON array of objects, one per "
    "comment in the same order. Each object must have keys 'label' (which must be "
    "'positive', 'neutral', or 'negative') and 'score' (a float between -1.0 and 1.0). "
    "Do not include any introductory text, markdown formatting, or code fences."
)


def _strip_code_fence(text: str) -> str:
    """Remove a leading/trailing ```json ... ``` fence if the model added one."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _classify_batch(texts: list) -> list:
    """Classify one batch; always returns a list of (label, score) of len(texts)."""
    fallback = [("neutral", 0.0)] * len(texts)

    numbered = "\n".join(
        f"{i + 1}. {str(t)[:_MAX_COMMENT_CHARS]}" for i, t in enumerate(texts)
    )
    try:
        reply = chat(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": numbered},
            ],
            max_tokens=2000,
            temperature=0.0,
        )
        raw = _strip_code_fence(reply)
        start_idx = raw.find("[")
        end_idx = raw.rfind("]")
        if start_idx != -1 and end_idx != -1:
            raw = raw[start_idx:end_idx + 1]
        data = json.loads(raw)
    except Exception as e:
        logger.warning("Sentiment batch failed, using neutral fallback: %s", e)
        # Log the raw reply to help debug if needed
        logger.debug("Raw reply that failed to parse: %s", reply if 'reply' in locals() else 'None')
        return fallback

    if not isinstance(data, list):
        return fallback

    out = []
    for item in data:
        label = "neutral"
        score = 0.0
        if isinstance(item, dict):
            lbl = str(item.get("label", "neutral")).lower().strip()
            if lbl in _VALID_LABELS:
                label = lbl
            try:
                score = max(-1.0, min(1.0, float(item.get("score", 0.0))))
            except (TypeError, ValueError):
                score = 0.0
        out.append((label, score))

    # Length must match; if the model dropped/added items, fall back safely.
    if len(out) != len(texts):
        logger.warning("Sentiment count mismatch (%d vs %d) — neutral fallback",
                       len(out), len(texts))
        return fallback
    return out


def analyze_comment_sentiment(comments_df: pd.DataFrame, batch_size: int = 10) -> pd.DataFrame:
    """Add ``sentiment_label`` and ``sentiment_score`` columns to ``comments_df``.

    If no API key/SDK is available the columns are still added (all neutral) so
    downstream charts never break — but callers should check ``get_client()``
    first to show the "add key" message instead.
    """
    df = comments_df.copy()
    if df.empty or "text" not in df.columns:
        df["sentiment_label"] = pd.Series(dtype="object")
        df["sentiment_score"] = pd.Series(dtype="float")
        return df

    if not is_configured():
        df["sentiment_label"] = "neutral"
        df["sentiment_score"] = 0.0
        return df

    texts = df["text"].fillna("").tolist()
    results = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        results.extend(_classify_batch(batch))

    df["sentiment_label"] = [r[0] for r in results]
    df["sentiment_score"] = [r[1] for r in results]
    return df
