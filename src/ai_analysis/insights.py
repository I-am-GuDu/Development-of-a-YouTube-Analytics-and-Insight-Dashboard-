"""
AI Insights — turn the already-computed channel metrics into a plain-English
performance analysis plus concrete action tips, using one Cloudflare Workers AI
(GLM 5.2) call.

This replaces the old keyword-based "recommendations" with a real LLM read of
the numbers. All errors are swallowed and returned as ``{'ok': False, ...}`` so
the UI never crashes.
"""
import logging
import pandas as pd

from .client import chat, is_configured

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior YouTube growth analyst. You are given a channel's "
    "performance numbers. Write a short, practical report in Markdown with "
    "exactly two parts:\n"
    "1. A 3-4 sentence plain-English summary of how the channel is doing.\n"
    "2. A '### Action tips' heading followed by 4-6 bullet points, each a "
    "specific, concrete thing the creator should do next (reference the actual "
    "numbers where useful). Avoid generic advice. Do not invent data that was "
    "not provided."
)

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _best_posting_slot(video_df: pd.DataFrame):
    """Return (day_name, hour) with the highest average engagement, or None."""
    if video_df is None or video_df.empty or "publish_date" not in video_df.columns:
        return None
    df = video_df.copy()
    df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
    df = df.dropna(subset=["publish_date"])
    if df.empty:
        return None
    df["dow"] = df["publish_date"].dt.dayofweek
    df["hour"] = df["publish_date"].dt.hour
    grouped = df.groupby(["dow", "hour"])["engagement_rate"].mean()
    if grouped.empty:
        return None
    best_dow, best_hour = grouped.idxmax()
    return _DAY_NAMES[int(best_dow)], int(best_hour)


def _build_summary(channel_data: dict, metrics: dict, video_df: pd.DataFrame,
                   forecast: dict = None) -> str:
    """Compact text block fed to the model — small on purpose to keep cost low."""
    lines = []
    lines.append(f"Channel: {channel_data.get('title', 'Unknown')}")
    lines.append(f"Subscribers: {channel_data.get('subscriber_count', 0):,}")
    lines.append(f"Total lifetime views: {channel_data.get('view_count', 0):,}")
    lines.append(f"Total videos: {channel_data.get('video_count', 0):,}")
    lines.append(f"Videos analyzed: {len(video_df) if video_df is not None else 0}")

    if metrics:
        lines.append(f"Avg views/video (recent): {metrics.get('avg_views_per_video', 0):,.0f}")
        lines.append(f"Avg engagement rate: {metrics.get('avg_engagement_rate', 0):.2f}%")
        lines.append(f"Avg likes/video: {metrics.get('avg_likes_per_video', 0):,.0f}")
        lines.append(f"Avg comments/video: {metrics.get('avg_comments_per_video', 0):,.0f}")
        lines.append(f"Videos posted in last 30 days: {metrics.get('video_growth_trend', 0)}")

    slot = _best_posting_slot(video_df)
    if slot:
        lines.append(f"Best posting slot (highest avg engagement): {slot[0]} around {slot[1]:02d}:00")

    if video_df is not None and not video_df.empty:
        top = video_df.nlargest(5, "view_count")
        lines.append("Top 5 videos by views:")
        for _, v in top.iterrows():
            title = str(v.get("title", ""))[:90]
            lines.append(
                f"  - \"{title}\" — {int(v['view_count']):,} views, "
                f"{v['engagement_rate']:.2f}% engagement"
            )
        if "category" in video_df.columns:
            cat = (video_df.groupby("category")["engagement_rate"].mean()
                   .sort_values(ascending=False))
            if not cat.empty:
                best_cat = cat.index[0]
                lines.append(f"Best-performing inferred category: {best_cat} ({cat.iloc[0]:.2f}% avg engagement)")

    if forecast and forecast.get("current_avg_engagement") is not None \
            and forecast.get("confidence") not in (None, "error"):
        lines.append(
            f"Engagement forecast: current avg {forecast.get('current_avg_engagement', 0):.2f}% "
            f"→ projected {forecast.get('projected_avg_engagement', 0):.2f}% "
            f"(confidence: {forecast.get('confidence', 'n/a')})"
        )

    return "\n".join(lines)


def generate_insights(channel_data: dict, metrics: dict, video_df: pd.DataFrame,
                      forecast: dict = None) -> dict:
    """Generate a Markdown insight report.

    Returns ``{'ok': True, 'markdown': str}`` on success, or
    ``{'ok': False, 'error': str}`` on any failure (missing key, API error).
    """
    if not is_configured():
        return {"ok": False, "error": "no_key"}

    summary = _build_summary(channel_data, metrics, video_df, forecast)

    try:
        markdown = chat(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",
                 "content": f"Here are the channel's numbers:\n\n{summary}\n\nWrite the report."},
            ],
            max_tokens=1500,
            temperature=0.4,
        )
        if not markdown:
            return {"ok": False, "error": "Empty response from the model."}
        return {"ok": True, "markdown": markdown}
    except Exception as e:
        logger.error("Insight generation failed: %s", e)
        return {"ok": False, "error": str(e)}
