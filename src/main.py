"""
YouTube Data Analysis Tool
Main Application Entry Point
YouTube Studio-style Analytics Dashboard
"""
import streamlit as st
import os
import base64
import html
import pandas as pd
from dotenv import load_dotenv
from youtube_data_collection.api_handler import YouTubeAPIHandler
from youtube_data_collection.data_processor import DataProcessor
from datetime import datetime, timedelta
from data_storage.storage_service import DataStorageService
from dashboard import charts, filters
from dashboard import theme as theme_tokens
from auth import is_logged_in, logout, get_current_user
from login_page import render_login_page
from ai_analysis import insights as ai_insights
from ai_analysis import sentiment as ai_sentiment
from ai_analysis.client import is_configured as ai_configured

load_dotenv()

CATEGORY_KEYWORDS = {
    'Tech Reviews': ['review', 'unbox', 'test', 'spec', 'performance'],
    'Product Comparisons': ['vs', 'versus', 'comparison', 'battle', 'faceoff'],
    'News Updates': ['news', 'update', 'leak', 'rumor', 'announcement'],
    'Tutorials': ['how to', 'tutorial', 'guide', 'tips', 'tricks'],
    'Unboxings': ['unboxing', 'unpack', 'first look'],
    'Price Analysis': ['price', 'cost', 'affordable', 'expensive', 'deal'],
    'Software Updates': ['update', 'android', 'software', 'features'],
    'Accessories': ['accessory', 'gadget', 'must have', 'buy', 'recommend']
}


# ═══════════════════════════════════════════════════════════════════════════════
# YOUTUBE STUDIO CSS THEME
# ═══════════════════════════════════════════════════════════════════════════════

def inject_yt_studio_styles(mode='light'):
    """Inject the full design system. Single token source = theme.py.

    Premium violet "creator console" identity. Space Grotesk for display +
    tabular metric numerals, Inter for body/UI.
    """
    t = theme_tokens.get_tokens(mode)

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            --bg-page: {t['bg_page']};
            --bg-card: {t['bg_card']};
            --bg-card-hover: {t['bg_card_hover']};
            --bg-sidebar: {t['bg_sidebar']};
            --bg-subtle: {t['bg_subtle']};
            --border: {t['border']};
            --border-strong: {t['border_strong']};
            --divider: {t['divider']};
            --ink: {t['text_primary']};
            --muted: {t['text_secondary']};
            --body: {t['text_body']};
            --faint: {t['text_faint']};
            --brand: {t['brand']};
            --brand-hover: {t['brand_hover']};
            --brand-soft: {t['brand_soft']};
            --brand-on: {t['brand_on']};
            --focus-ring: {t['focus_ring']};
            --pos: {t['pos']};
            --neg: {t['neg']};
            --input-bg: {t['input_bg']};
            --input-border: {t['input_border']};
            --font-display: 'Space Grotesk', sans-serif;
            --font-body: 'Inter', sans-serif;
        }}

        /* ── Page shell ──────────────────────────────────── */
        .stApp {{
            background: var(--bg-page) !important;
            color: var(--body) !important;
            font-family: var(--font-body);
        }}
        /* Native Streamlit header: transparent so no leftover dark bar
           collides with the fixed theme toggle. Token-independent — page
           bg shows through, reads correctly in both modes. */
        [data-testid="stHeader"], .stApp > header {{
            background: transparent !important;
        }}
        .stApp, [data-testid="stSidebar"], .yt-metric-card, .yt-chart-card,
        .yt-video-card, [data-testid="stMetric"], .stButton > button,
        .stTextInput input {{
            transition: background-color 0.25s ease, color 0.25s ease, border-color 0.25s ease;
        }}
        .block-container {{
            padding-top: 1.6rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 1280px;
        }}
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {{ color: var(--body); }}
        [data-testid="stCaptionContainer"], .stCaption,
        [data-testid="stWidgetLabel"] label,
        .stSelectbox label, .stMultiSelect label, .stDateInput label,
        .stTextInput label, .stNumberInput label, .stTextArea label,
        .stRadio > label, .stSlider label {{
            color: var(--muted) !important;
            font-family: var(--font-body) !important;
        }}
        h1, h2, h3, h4 {{ color: var(--ink) !important; font-family: var(--font-display); }}

        /* ── Sidebar ─────────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background: var(--bg-sidebar) !important;
            border-right: 1px solid var(--border);
            width: 248px !important;
        }}
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3 {{
            color: var(--ink) !important;
            font-family: var(--font-body) !important;
        }}
        [data-testid="stSidebar"] .stRadio label {{
            color: var(--muted) !important;
            font-family: var(--font-body) !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            padding: 9px 14px !important;
            border-radius: 10px;
            transition: all 0.18s ease;
        }}
        [data-testid="stSidebar"] .stRadio label:hover {{
            background: var(--brand-soft) !important;
            color: var(--ink) !important;
        }}
        [data-testid="stSidebar"] [aria-checked="true"] + div,
        [data-testid="stSidebar"] .stRadio [aria-checked="true"] ~ div {{
            color: var(--brand) !important;
        }}

        /* ── Page header ─────────────────────────────────── */
        .page-head {{ margin: 0 0 1.4rem; }}
        .page-eyebrow {{
            display: inline-flex; align-items: center; gap: 8px;
            font-family: var(--font-body);
            font-size: 0.7rem; font-weight: 600; letter-spacing: 0.14em;
            text-transform: uppercase; color: var(--brand);
            margin-bottom: 8px;
        }}
        .page-eyebrow::before {{
            content: ''; width: 22px; height: 2px; border-radius: 2px;
            background: var(--brand);
        }}
        .page-title {{
            font-family: var(--font-display);
            font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em;
            color: var(--ink); margin: 0; line-height: 1.1;
        }}
        .page-subtitle {{
            font-family: var(--font-body);
            font-size: 0.92rem; color: var(--muted); margin: 6px 0 0;
        }}
        .yt-page-title {{
            font-family: var(--font-display);
            font-size: 1.5rem; font-weight: 700; color: var(--ink);
            margin: 0; padding: 0;
        }}

        /* ── Tab bar ──────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {{
            background: transparent !important;
            border: none !important;
            border-bottom: 1px solid var(--border) !important;
            border-radius: 0 !important;
            padding: 0 !important; gap: 4px !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 0 !important;
            background: transparent !important;
            color: var(--muted) !important;
            font-family: var(--font-body) !important;
            font-size: 14px !important; font-weight: 600 !important;
            padding: 12px 20px !important;
            border-bottom: 2.5px solid transparent !important;
            transition: all 0.18s ease;
        }}
        .stTabs [data-baseweb="tab"]:hover {{ color: var(--ink) !important; }}
        .stTabs [aria-selected="true"] {{
            background: transparent !important;
            color: var(--brand) !important;
            border-bottom: 2.5px solid var(--brand) !important;
        }}
        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

        /* ── Metric cards ─────────────────────────────────── */
        .yt-metric-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px 22px;
            min-height: 104px;
            position: relative;
            transition: all 0.2s cubic-bezier(0.23,1,0.32,1);
        }}
        .yt-metric-card::before {{
            content: ''; position: absolute; left: 0; top: 16px; bottom: 16px;
            width: 3px; border-radius: 0 3px 3px 0;
            background: var(--brand); opacity: 0;
            transition: opacity 0.2s ease;
        }}
        .yt-metric-card:hover {{
            border-color: var(--border-strong);
            transform: translateY(-2px);
            box-shadow: 0 10px 30px {('rgba(0,0,0,0.35)' if mode=='dark' else 'rgba(79,70,229,0.10)')};
        }}
        .yt-metric-card:hover::before {{ opacity: 1; }}
        .yt-metric-label {{
            font-family: var(--font-body);
            font-size: 0.76rem; font-weight: 500;
            color: var(--muted); margin-bottom: 8px;
        }}
        .yt-metric-value {{
            font-family: var(--font-display);
            font-size: 1.9rem; font-weight: 600;
            color: var(--ink); line-height: 1.1;
            font-feature-settings: 'tnum' 1; font-variant-numeric: tabular-nums;
            letter-spacing: -0.01em;
        }}
        .yt-metric-trend {{
            font-family: var(--font-body);
            font-size: 0.76rem; font-weight: 600; margin-top: 8px;
        }}
        .yt-trend-up {{ color: var(--pos); }}
        .yt-trend-down {{ color: var(--neg); }}
        .yt-trend-neutral {{ color: var(--muted); font-weight: 500; }}

        /* ── Chart cards ──────────────────────────────────── */
        .yt-chart-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 1rem;
        }}
        .yt-chart-title {{
            font-family: var(--font-display);
            font-size: 1.02rem; font-weight: 600;
            color: var(--ink); margin-bottom: 4px;
        }}
        .yt-chart-subtitle {{
            font-family: var(--font-body);
            font-size: 0.78rem; color: var(--muted); margin-bottom: 12px;
        }}

        /* ── Native st.metric ─────────────────────────────── */
        [data-testid="stMetric"] {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 20px;
        }}
        [data-testid="stMetric"]:hover {{ border-color: var(--border-strong); }}
        [data-testid="stMetricLabel"] {{
            color: var(--muted) !important; font-weight: 500 !important;
            font-family: var(--font-body) !important; font-size: 0.76rem !important;
        }}
        [data-testid="stMetricValue"] {{
            color: var(--ink) !important; font-weight: 600 !important;
            font-family: var(--font-display) !important;
            font-variant-numeric: tabular-nums;
        }}
        [data-testid="stMetricDelta"] {{ font-family: var(--font-body) !important; }}

        /* ── Buttons ──────────────────────────────────────── */
        .stButton > button {{
            background: transparent !important;
            border: 1px solid var(--input-border) !important;
            border-radius: 10px !important;
            color: var(--brand) !important;
            font-family: var(--font-body) !important;
            font-weight: 600 !important; font-size: 14px !important;
            padding: 9px 22px !important;
            transition: all 0.18s ease;
        }}
        .stButton > button:hover {{
            background: var(--brand-soft) !important;
            border-color: var(--brand) !important;
        }}
        .stButton > button[kind="primary"] {{
            background: var(--brand) !important;
            color: var(--brand-on) !important;
            border-color: var(--brand) !important;
            box-shadow: 0 4px 14px var(--focus-ring) !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: var(--brand-hover) !important;
            border-color: var(--brand-hover) !important;
            transform: translateY(-1px);
        }}

        /* ── Inputs ───────────────────────────────────────── */
        .stTextInput input, .stNumberInput input, .stTextArea textarea {{
            background: var(--input-bg) !important;
            border: 1px solid var(--input-border) !important;
            border-radius: 10px !important;
            color: var(--body) !important;
            font-family: var(--font-body) !important;
        }}
        .stTextInput input:focus, .stNumberInput input:focus,
        .stTextArea textarea:focus {{
            border-color: var(--brand) !important;
            box-shadow: 0 0 0 3px var(--focus-ring) !important;
        }}
        [data-baseweb="select"] > div {{
            background: var(--input-bg) !important;
            border-color: var(--input-border) !important;
            border-radius: 10px !important;
        }}
        /* Select selected-value + option-list text follow tokens (both modes) */
        [data-baseweb="select"] div {{ color: var(--body) !important; }}
        [data-baseweb="popover"] [role="option"] {{
            background: var(--bg-card) !important;
            color: var(--body) !important;
        }}
        [data-baseweb="popover"] [role="option"]:hover {{
            background: var(--brand-soft) !important;
        }}
        /* Placeholder text — token-driven so it is visible in light mode */
        .stTextInput input::placeholder,
        .stNumberInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: var(--faint) !important;
            opacity: 1;
        }}
        /* Date inputs: field + calendar popover follow tokens (fix dark-default
           chrome bleeding into light mode) */
        .stDateInput [data-baseweb="input"],
        .stDateInput input {{
            background: var(--input-bg) !important;
            color: var(--body) !important;
            border-color: var(--input-border) !important;
        }}
        [data-baseweb="calendar"] {{
            background: var(--bg-card) !important;
            color: var(--body) !important;
        }}

        [data-testid="stDataFrame"], [data-testid="stTable"] {{
            border: 1px solid var(--border);
            border-radius: 12px; overflow: hidden;
        }}
        .stAlert {{ border-radius: 12px; border: 1px solid var(--border); }}

        /* ── Sidebar channel info ─────────────────────────── */
        .sidebar-channel-info {{ text-align: center; padding: 14px 12px; margin-bottom: 8px; }}
        .sidebar-channel-avatar {{
            width: 76px; height: 76px; border-radius: 50%;
            margin: 0 auto 10px; display: block;
            border: 2px solid var(--brand-soft);
        }}
        .sidebar-channel-name {{
            font-family: var(--font-display); font-size: 0.92rem; font-weight: 600;
            color: var(--ink); margin-top: 4px;
        }}
        .sidebar-channel-label {{
            font-family: var(--font-body); font-size: 0.7rem;
            color: var(--muted); margin-top: 2px;
            text-transform: uppercase; letter-spacing: 0.08em;
        }}

        /* ── Top video cards ──────────────────────────────── */
        .yt-video-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 15px 18px; margin-bottom: 8px;
            transition: all 0.18s ease;
        }}
        .yt-video-card:hover {{
            border-color: var(--border-strong);
            background: var(--bg-card-hover);
        }}
        .yt-video-title {{
            font-family: var(--font-body); font-size: 0.9rem; font-weight: 600;
            color: var(--ink); margin-bottom: 8px; line-height: 1.35;
        }}
        .yt-video-stats {{ display: flex; gap: 22px; flex-wrap: wrap; }}
        .yt-video-stat {{ font-family: var(--font-body); font-size: 0.78rem; }}
        .yt-video-stat-label {{ color: var(--muted); }}
        .yt-video-stat-value {{
            color: var(--ink); font-weight: 600; margin-left: 4px;
            font-variant-numeric: tabular-nums;
        }}

        /* ── Category mix bars ────────────────────────────── */
        .yt-traffic-row {{ display: flex; align-items: center; margin-bottom: 10px; gap: 12px; }}
        .yt-traffic-label {{
            font-family: var(--font-body); font-size: 0.8rem;
            color: var(--muted); min-width: 130px;
        }}
        .yt-traffic-bar-bg {{
            flex: 1; height: 7px; background: var(--bg-subtle);
            border-radius: 4px; overflow: hidden;
        }}
        .yt-traffic-bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.6s ease; }}
        .yt-traffic-pct {{
            font-family: var(--font-display); font-size: 0.8rem;
            color: var(--ink); font-weight: 500; min-width: 48px; text-align: right;
            font-variant-numeric: tabular-nums;
        }}

        .yt-divider {{ border: none; border-top: 1px solid var(--divider); margin: 16px 0; }}

        /* ── Scrollbar ────────────────────────────────────── */
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: {t['scrollbar_track']}; }}
        ::-webkit-scrollbar-thumb {{ background: {t['scrollbar_thumb']}; border-radius: 4px; }}

        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        /* ── Sidebar buttons ──────────────────────────────── */
        [data-testid="stSidebar"] .stButton > button {{
            background: transparent !important;
            border: 1px solid var(--border) !important;
            color: var(--muted) !important; width: 100%;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            background: var(--brand-soft) !important;
            color: var(--brand) !important;
            border-color: var(--brand) !important;
        }}

        /* ── Sidebar collapse control ─────────────────────── */
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="collapsedControl"] button {{
            background: var(--bg-card) !important;
            color: var(--ink) !important;
            border: 1px solid var(--border-strong) !important;
            border-radius: 10px !important;
        }}
        [data-testid="stSidebarCollapseButton"] button:hover,
        [data-testid="collapsedControl"] button:hover {{
            border-color: var(--brand) !important;
        }}
        [data-testid="stSidebarCollapseButton"] button svg,
        [data-testid="collapsedControl"] button svg {{
            fill: var(--ink) !important; stroke: var(--ink) !important;
        }}

        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)


def render_page_header(eyebrow, title, subtitle=''):
    """Clean page header — replaces the old 3D hero banner."""
    sub = f'<p class="page-subtitle">{html.escape(subtitle)}</p>' if subtitle else ''
    st.markdown(f"""
    <div class="page-head">
        <div class="page-eyebrow">{html.escape(eyebrow)}</div>
        <h1 class="page-title">{html.escape(title)}</h1>
        {sub}
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def categorize_title(title: str) -> str:
    title_lower = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return 'General'


def format_number(n):
    """Format large numbers like YouTube (e.g. 52.6K, 1.2M)."""
    if n is None:
        return '0'
    n = float(n)
    if n >= 1_000_000_000:
        return f'{n/1_000_000_000:.1f}B'
    if n >= 1_000_000:
        return f'{n/1_000_000:.1f}M'
    if n >= 1_000:
        return f'{n/1_000:.1f}K'
    return f'{n:,.0f}'


@st.cache_data(ttl=600, show_spinner=False)
def fetch_channel_data(api_key, channel_input):
    """Fetch and process channel + video data from YouTube API"""
    handler = YouTubeAPIHandler()
    processor = DataProcessor()

    input_text = channel_input.strip()
    if input_text.startswith('@'):
        raw_channel_info = handler.get_channel_by_username(input_text)
    elif input_text.startswith('UC') and len(input_text) == 24:
        raw_channel_info = handler.get_channel_details(input_text)
    else:
        raise ValueError(
            "Invalid format. Use channel ID (UC...) or username (@...)")

    processed_channel = processor.process_channel_data(raw_channel_info)

    upload_playlist_id = raw_channel_info['contentDetails']['relatedPlaylists']['uploads']
    raw_videos = handler.get_channel_videos(upload_playlist_id, max_results=50)
    video_ids = [video['video_id'] for video in raw_videos]
    raw_video_details = handler.get_video_details(video_ids)

    video_df = processor.process_video_data(raw_video_details)
    engagement_metrics = processor.calculate_engagement_metrics(video_df)

    # Add category column
    video_df['category'] = video_df['title'].apply(categorize_title)
    video_df['channel_id'] = processed_channel['channel_id']

    return processed_channel, video_df, engagement_metrics


def save_to_database(processed_channel, video_df, engagement_metrics):
    """Save data to PostgreSQL, return success status"""
    try:
        storage_service = DataStorageService()
        storage_service.save_channel_data(processed_channel)
        storage_service.save_video_data(video_df)
        storage_service.save_analytics_summary(
            processed_channel['channel_id'], engagement_metrics)
        return True, "Data saved to database successfully!"
    except Exception as e:
        return False, f"Could not save to database: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# YT STUDIO METRIC CARD COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════

def render_metric_card(label, value, trend_value=None, trend_direction=None, trend_text=None):
    """Render a YouTube Studio-style metric card with HTML."""
    trend_html = ''
    if trend_value is not None and trend_direction:
        arrow = '↑' if trend_direction == 'up' else '↓'
        css_class = 'yt-trend-up' if trend_direction == 'up' else 'yt-trend-down'
        trend_html = f'<div class="yt-metric-trend {css_class}">{arrow} {trend_value}</div>'
    elif trend_text:
        trend_html = f'<div class="yt-metric-trend yt-trend-neutral">{trend_text}</div>'

    st.markdown(f"""
    <div class="yt-metric-card">
        <div class="yt-metric-label">{label}</div>
        <div class="yt-metric-value">{value}</div>
        {trend_html}
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# YT STUDIO TRAFFIC SOURCE BARS
# ═══════════════════════════════════════════════════════════════════════════════

def render_traffic_source_bars(video_df):
    """Render views-by-category breakdown as styled HTML bars."""
    if 'category' not in video_df.columns or video_df.empty:
        return

    category_views = video_df.groupby('category')['view_count'].sum()
    total = category_views.sum()
    if total == 0:
        return

    colors = charts.get_theme_colors()['viz']
    sources = [(cat, views / total * 100)
               for cat, views in category_views.sort_values(ascending=False).items()]

    html_rows = ''
    for i, (name, pct) in enumerate(sources[:6]):
        color = colors[i % len(colors)]
        html_rows += f"""
        <div class="yt-traffic-row">
            <span class="yt-traffic-label">{html.escape(str(name))}</span>
            <div class="yt-traffic-bar-bg">
                <div class="yt-traffic-bar-fill" style="width:{pct:.1f}%; background:{color};"></div>
            </div>
            <span class="yt-traffic-pct">{pct:.1f}%</span>
        </div>
        """

    st.markdown(html_rows, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    """Render YT Studio-style sidebar with channel info and navigation."""
    text_secondary = charts.get_theme_colors()['text_secondary']

    with st.sidebar:
        # Channel info at top
        if 'channel_data' in st.session_state:
            ch = st.session_state['channel_data']
            safe_title = html.escape(ch.get('title', 'Unknown'))
            safe_thumb = html.escape(ch.get('thumbnail_url', ''))
            st.markdown(f"""
            <div class="sidebar-channel-info">
                <img src="{safe_thumb}" class="sidebar-channel-avatar" alt="Channel Avatar"/>
                <div class="sidebar-channel-label">Your channel</div>
                <div class="sidebar-channel-name">{safe_title}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            intro_video_path = 'Profile_Pic.mp4'
            if os.path.exists(intro_video_path):
                with open(intro_video_path, 'rb') as video_file:
                    video_b64 = base64.b64encode(
                        video_file.read()).decode('ascii')

                st.markdown(f"""
                <div class="sidebar-channel-info">
                    <div style="width:80px;height:80px;border-radius:50%;overflow:hidden;background:var(--bg-subtle);margin:0 auto 10px;">
                        <video autoplay loop muted playsinline style="width:100%;height:100%;object-fit:cover;display:block;">
                            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                        </video>
                    </div>
                    <div class="sidebar-channel-label">Your channel</div>
                    <div class="sidebar-channel-name">YouTube Analytics</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="sidebar-channel-info">
                    <div style="width:80px;height:80px;border-radius:50%;background:var(--bg-subtle);margin:0 auto 10px;display:flex;align-items:center;justify-content:center;">
                        <span style="font-size:2rem;color:{text_secondary};">❤️</span>
                    </div>
                    <div class="sidebar-channel-label">Your channel</div>
                    <div class="sidebar-channel-name">YouTube Analytics</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)

        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Analytics", "🔍 Video Explorer",
                "📈 Trend Analysis", "⚔️ Multi-Channel",
                "🤖 AI Insights", "💬 Comment Sentiment"],
            label_visibility="collapsed"
        )

        st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)

        # Subscriber count
        if 'channel_data' in st.session_state:
            ch = st.session_state['channel_data']
            st.caption(f"📢 {ch.get('subscriber_count', 0):,} subscribers")
            st.caption(f"🎬 {ch.get('video_count', 0):,} videos")
            st.caption(f"👁️ {ch.get('view_count', 0):,} total views")

        # ── Theme follows OS/browser automatically (theme.resolve_mode) ──

        # ── User info & Logout ──────────────────────────────
        st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)
        user = get_current_user()
        if user:
            st.caption(f"👤 {user['display_name']}")
            st.caption(f"✉️ {user['email']}")
        if st.button("🚪 Logout", key="logout_btn"):
            logout()
            st.rerun()

    return page


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CHANNEL ANALYTICS (main page matching YT Studio)
# ═══════════════════════════════════════════════════════════════════════════════

def page_channel_analytics():
    """Main analytics page matching YouTube Studio screenshot."""
    text_secondary = charts.get_theme_colors()['text_secondary']

    render_page_header(
        "Channel Analytics",
        "Channel analytics",
        "Deep-dive performance metrics · Powered by YouTube Data API"
    )

    # Read API key — st.secrets (Cloud) or os.getenv (local .env)
    try:
        api_key = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY"))
    except Exception:
        api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or api_key == "your_actual_api_key_here":
        st.error("YouTube API Key not configured! Set YOUTUBE_API_KEY in .env file")
        return

    # Channel input
    channel_input = st.text_input(
        "Enter YouTube Channel ID or @Username:",
        placeholder="Example: UC_x5XG1OV2P6uZZ5FSM9Ttw or @ShopiDevs",
        label_visibility="collapsed"
    )

    if st.button("🔍  Analyze Channel", type="primary"):
        if not channel_input.strip():
            st.error("Please enter a valid YouTube Channel ID or @Username")
            return

        try:
            with st.spinner("Fetching channel data from YouTube..."):
                processed_channel, video_df, engagement_metrics = fetch_channel_data(
                    api_key, channel_input)

            # Save to DB
            success, msg = save_to_database(
                processed_channel, video_df, engagement_metrics)
            if success:
                st.success(msg)
            else:
                st.warning(msg)

            # Store in session state
            st.session_state['channel_data'] = processed_channel
            st.session_state['video_df'] = video_df
            st.session_state['engagement_metrics'] = engagement_metrics
            st.rerun()

        except ValueError as ve:
            st.error(f"Error: {str(ve)}")
        except Exception as e:
            st.error(f"Failed to fetch data: {str(e)}")

    # If data is loaded, show the analytics dashboard
    if 'video_df' not in st.session_state:
        st.markdown(f"""
        <div style="text-align:center;padding:80px 20px;">
            <div style="font-size:3rem;margin-bottom:16px;">🧐</div>
            <div style="font-family:Inter,sans-serif;font-size:1.1rem;color:{text_secondary};">
                Enter a YouTube Channel ID or @Username above to start analyzing
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    video_df = st.session_state['video_df']
    engagement_metrics = st.session_state['engagement_metrics']
    channel_data = st.session_state['channel_data']

    # ─── Tab Bar ───
    tab_overview, tab_reach, tab_engagement, tab_audience, tab_revenue = st.tabs(
        ["Overview", "Reach", "Engagement", "Audience", "Growth Forecast"]
    )

    # ══════════════════════════ OVERVIEW TAB ══════════════════════════════
    with tab_overview:
        # Channel info
        col_avatar, col_info = st.columns([1, 4])
        with col_avatar:
            st.image(channel_data['thumbnail_url'], width=120)
        with col_info:
            st.markdown(f"### {channel_data['title']}")
            st.caption(f"Channel ID: {channel_data['channel_id']}")

        st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)

        # KPI Metrics Row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card(
                "Subscribers",
                format_number(channel_data['subscriber_count']),
                trend_text="Total subscribers"
            )
        with c2:
            render_metric_card(
                "Total views",
                format_number(channel_data['view_count']),
                trend_text="Lifetime views"
            )
        with c3:
            render_metric_card(
                "Videos",
                format_number(channel_data['video_count']),
                trend_text="Total uploads"
            )
        with c4:
            render_metric_card(
                "Avg engagement rate",
                f"{engagement_metrics.get('avg_engagement_rate', 0):.2f}%",
                trend_text="Across all videos"
            )

        st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)

        # Top performing videos
        st.markdown(
            '<div class="yt-chart-title">🏆 Top Performing Videos</div>', unsafe_allow_html=True)
        top_df = video_df.nlargest(5, 'view_count')
        for _, video in top_df.iterrows():
            safe_video_title = html.escape(str(video['title']))
            st.markdown(f"""
            <div class="yt-video-card">
                <div class="yt-video-title">{safe_video_title}</div>
                <div class="yt-video-stats">
                    <span class="yt-video-stat"><span class="yt-video-stat-label">Views</span> <span class="yt-video-stat-value">{video['view_count']:,}</span></span>
                    <span class="yt-video-stat"><span class="yt-video-stat-label">Likes</span> <span class="yt-video-stat-value">{video['like_count']:,}</span></span>
                    <span class="yt-video-stat"><span class="yt-video-stat-label">Comments</span> <span class="yt-video-stat-value">{video['comment_count']:,}</span></span>
                    <span class="yt-video-stat"><span class="yt-video-stat-label">Engagement</span> <span class="yt-video-stat-value">{video['engagement_rate']:.2f}%</span></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ════════════════════════════ REACH TAB ═══════════════════════════════
    with tab_reach:
        # 4 Metric Cards (matching screenshot)
        avg_views = video_df['view_count'].mean()
        total_views = video_df['view_count'].sum()
        avg_engagement = engagement_metrics.get('avg_engagement_rate', 0)
        unique_videos = len(video_df)

        # Calculate trends (compare first half vs second half of videos)
        half = len(video_df) // 2
        if half > 0:
            recent = video_df.head(half)
            older = video_df.tail(half)
            view_trend = ((recent['view_count'].mean(
            ) - older['view_count'].mean()) / max(older['view_count'].mean(), 1)) * 100
            eng_trend = ((recent['engagement_rate'].mean(
            ) - older['engagement_rate'].mean()) / max(older['engagement_rate'].mean(), 1)) * 100
        else:
            view_trend = 0
            eng_trend = 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card(
                "Total Views",
                format_number(total_views),
                trend_value=f"{abs(view_trend):.0f}%",
                trend_direction='up' if view_trend >= 0 else 'down'
            )
        with c2:
            render_metric_card(
                "Avg Engagement Rate",
                f"{avg_engagement:.1f}%",
                trend_value=f"{abs(eng_trend):.0f}%",
                trend_direction='up' if eng_trend >= 0 else 'down'
            )
        with c3:
            render_metric_card(
                "Avg Views per Video",
                format_number(avg_views),
                trend_text=f"{format_number(avg_views - video_df['view_count'].median())} vs median"
            )
        with c4:
            render_metric_card(
                "Total Videos Analyzed",
                str(unique_videos),
                trend_text=f"{engagement_metrics.get('video_growth_trend', 0)} in last 30 days"
            )

        # Large area chart
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.views_area_chart(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        # Bottom two cards
        col_traffic, col_funnel = st.columns(2)

        with col_traffic:
            st.markdown("""
            <div class="yt-chart-card">
                <div class="yt-chart-title">Content category mix</div>
                <div class="yt-chart-subtitle">Views grouped by inferred category</div>
            """, unsafe_allow_html=True)
            st.plotly_chart(charts.traffic_sources_donut(
                video_df), use_container_width=True)
            render_traffic_source_bars(video_df)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_funnel:
            st.markdown("""
            <div class="yt-chart-card">
                <div class="yt-chart-title">Engagement breakdown</div>
                <div class="yt-chart-subtitle">Across all analyzed videos</div>
            """, unsafe_allow_html=True)

            # Funnel-style metrics
            total_v = int(video_df['view_count'].sum())
            total_likes = int(video_df['like_count'].sum())
            total_comments = int(video_df['comment_count'].sum())
            total_interactions = total_likes + total_comments
            ctr = (total_interactions / max(total_v, 1)) * 100

            render_metric_card("Total Views",
                               format_number(total_v))
            st.markdown(f"""
            <div style="text-align:center;padding:8px 0;color:{text_secondary};font-size:0.8rem;font-family:'Inter',sans-serif;">
                {ctr:.1f}% engagement rate
            </div>
            """, unsafe_allow_html=True)
            render_metric_card("Total Interactions", format_number(total_interactions),
                               trend_text=f"{format_number(total_likes)} likes + {format_number(total_comments)} comments")
            st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════ ENGAGEMENT TAB ═══════════════════════════════
    with tab_engagement:
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card(
                "Avg Likes per Video",
                format_number(engagement_metrics.get('avg_likes_per_video', 0))
            )
        with c2:
            render_metric_card(
                "Avg Comments per Video",
                format_number(engagement_metrics.get(
                    'avg_comments_per_video', 0))
            )
        with c3:
            render_metric_card(
                "Engagement Efficiency",
                f"{engagement_metrics.get('engagement_efficiency', 0):.2f}%"
            )

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.engagement_distribution_chart(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.views_vs_likes_scatter(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ════════════════════════ AUDIENCE TAB ════════════════════════════════
    with tab_audience:
        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.posting_frequency_chart(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.optimal_posting_heatmap(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Category breakdown
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
            st.plotly_chart(charts.category_performance_bar(
                video_df), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
            st.plotly_chart(charts.category_distribution_pie(
                video_df), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════ GROWTH FORECAST TAB ══════════════════════════
    with tab_revenue:
        st.markdown("""
        <div style="text-align:center;padding:48px 20px;">
            <div style="font-size:2.2rem;margin-bottom:12px;">📈</div>
            <div class="yt-chart-title" style="text-align:center;">Growth forecast</div>
            <div class="yt-chart-subtitle" style="text-align:center;">Projected engagement based on current trends</div>
        </div>
        """, unsafe_allow_html=True)

        try:
            storage_service = DataStorageService()
            predictive = storage_service.get_predictive_analytics()
            channel_id = channel_data.get('channel_id')

            if channel_id:
                forecast = predictive.forecast_channel_growth(
                    channel_id, days_ahead=30)
                fig = charts.growth_forecast_chart(forecast)
                if fig:
                    st.markdown('<div class="yt-chart-card">',
                                unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        render_metric_card(
                            "Current Avg Engagement",
                            f"{forecast.get('current_avg_engagement', 0):.2f}%"
                        )
                    with c2:
                        render_metric_card(
                            "Projected Avg Engagement",
                            f"{forecast.get('projected_avg_engagement', 0):.2f}%"
                        )
                else:
                    st.info(
                        "Not enough data for growth forecasting (need at least 5 videos in database).")

                st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="yt-chart-title">Content Strategy Recommendations</div>', unsafe_allow_html=True)
                strategy = predictive.recommend_content_strategy(channel_id)
                for rec in strategy.get('recommendations', []):
                    if rec['type'] == 'content_type':
                        st.success(
                            f"**Best Content Type:** {rec['category']} — {rec['reason']}")
                    elif rec['type'] == 'posting_time':
                        st.success(
                            f"**Best Posting Time:** {rec['optimal_day']} at {rec['optimal_hour']}:00 — {rec['reason']}")

                if not strategy.get('recommendations'):
                    st.info(
                        "Not enough data to generate content strategy recommendations.")
        except Exception as e:
            st.warning(f"Predictive analytics unavailable: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: VIDEO EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════

def page_video_explorer():
    """Page: Search, filter, and explore individual videos"""
    render_page_header(
        "Video Explorer",
        "Video explorer",
        "Search, filter and discover top-performing content"
    )

    if 'video_df' not in st.session_state:
        st.info("Please analyze a channel first from the **Analytics** page.")
        return

    video_df = st.session_state['video_df']
    channel_data = st.session_state.get('channel_data', {})
    theme_colors = charts.get_theme_colors()
    text_primary = theme_colors['text_primary']
    text_secondary = theme_colors['text_secondary']

    st.markdown(f"""
    <div style="color:{text_secondary};font-family:Inter,sans-serif;font-size:0.9rem;margin-bottom:16px;">
        Exploring videos from <strong style="color:{text_primary};">{channel_data.get('title', 'Unknown Channel')}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Search & Filter UI
    filtered_df = filters.video_search_filter(video_df)

    if filtered_df.empty:
        st.warning("No videos match your filters.")
        return

    # Display results as interactive table
    st.markdown('<div class="yt-chart-title">Video Results</div>',
                unsafe_allow_html=True)
    display_df = filtered_df[['title', 'view_count', 'like_count',
                              'comment_count', 'engagement_rate', 'category', 'publish_date']].copy()
    display_df['publish_date'] = display_df['publish_date'].dt.strftime(
        '%Y-%m-%d')
    display_df.columns = ['Title', 'Views', 'Likes',
                          'Comments', 'Engagement %', 'Category', 'Published']

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Views": st.column_config.NumberColumn(format="%d"),
            "Likes": st.column_config.NumberColumn(format="%d"),
            "Comments": st.column_config.NumberColumn(format="%d"),
            "Engagement %": st.column_config.NumberColumn(format="%.2f%%"),
        }
    )

    # Summary stats
    st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Videos Found", str(len(filtered_df)))
    with c2:
        render_metric_card("Avg Views", format_number(
            filtered_df['view_count'].mean()))
    with c3:
        render_metric_card(
            "Avg Engagement", f"{filtered_df['engagement_rate'].mean():.2f}%")
    with c4:
        render_metric_card("Total Views", format_number(
            filtered_df['view_count'].sum()))

    st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
    st.plotly_chart(charts.views_vs_likes_scatter(
        filtered_df, top_n=len(filtered_df)), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def page_trend_analysis():
    """Page: Time-series trends, posting patterns, optimal times"""
    render_page_header(
        "Trend Analysis",
        "Trend analysis",
        "Time-series insights · Posting patterns · Predictive forecasting"
    )

    if 'video_df' not in st.session_state:
        st.info("Please analyze a channel first from the **Analytics** page.")
        return

    video_df = st.session_state['video_df']
    channel_data = st.session_state.get('channel_data', {})
    theme_colors = charts.get_theme_colors()
    text_primary = theme_colors['text_primary']
    text_secondary = theme_colors['text_secondary']

    st.markdown(f"""
    <div style="color:{text_secondary};font-family:Inter,sans-serif;font-size:0.9rem;margin-bottom:16px;">
        Trends for <strong style="color:{text_primary};">{channel_data.get('title', 'Unknown Channel')}</strong>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(
        ["📊 Engagement Trends", "📅 Posting Patterns", "🎯 Predictive Insights"])

    with tab1:
        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.engagement_over_time_line(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.views_over_time_line(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.posting_frequency_chart(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.optimal_posting_heatmap(
            video_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown(
            '<div class="yt-chart-title">Growth Forecast</div>', unsafe_allow_html=True)
        try:
            storage_service = DataStorageService()
            predictive = storage_service.get_predictive_analytics()
            channel_id = channel_data.get('channel_id')

            if channel_id:
                forecast = predictive.forecast_channel_growth(
                    channel_id, days_ahead=30)
                fig = charts.growth_forecast_chart(forecast)
                if fig:
                    st.markdown('<div class="yt-chart-card">',
                                unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    with c1:
                        render_metric_card("Current Avg Engagement",
                                           f"{forecast.get('current_avg_engagement', 0):.2f}%")
                    with c2:
                        render_metric_card("Projected Avg Engagement",
                                           f"{forecast.get('projected_avg_engagement', 0):.2f}%")
                else:
                    st.info(
                        "Not enough data for growth forecasting (need at least 5 videos in database).")

                st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="yt-chart-title">Content Strategy Recommendations</div>', unsafe_allow_html=True)
                strategy = predictive.recommend_content_strategy(channel_id)
                for rec in strategy.get('recommendations', []):
                    if rec['type'] == 'content_type':
                        st.success(
                            f"**Best Content Type:** {rec['category']} — {rec['reason']}")
                    elif rec['type'] == 'posting_time':
                        st.success(
                            f"**Best Posting Time:** {rec['optimal_day']} at {rec['optimal_hour']}:00 — {rec['reason']}")

                if not strategy.get('recommendations'):
                    st.info(
                        "Not enough data to generate content strategy recommendations.")
        except Exception as e:
            st.warning(f"Predictive analytics unavailable: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MULTI-CHANNEL COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════

def page_multi_channel():
    """Page: Multi-channel comparison and competitive benchmarking"""
    render_page_header(
        "Multi-Channel",
        "Multi-channel comparison",
        "Compare channels side by side · Competitive benchmarking"
    )

    theme_colors = charts.get_theme_colors()
    text_primary = theme_colors['text_primary']
    text_secondary = theme_colors['text_secondary']

    st.markdown(f"""
    <div style="color:{text_secondary};font-family:Inter,sans-serif;font-size:0.9rem;margin-bottom:16px;">
        Compare multiple YouTube channels side by side
    </div>
    """, unsafe_allow_html=True)

    st.info("💡 Use **Channel IDs** (e.g. `UC_x5XG1OV2P6uZZ5FSM9Ttw`) for multi-channel analysis. You can find a channel's ID on the **Analytics** page after analyzing it.")

    channel_ids_input = st.text_area(
        "Enter Channel IDs (one per line):",
        placeholder="UC_x5XG1OV2P6uZZ5FSM9Ttw\nUCXgGY0wkgOzynnHvSEVmE3A",
        height=120
    )

    if st.button("Compare Channels", type="primary"):
        if not channel_ids_input.strip():
            st.error("Please enter at least one channel ID or @username")
            return

        raw_inputs = [cid.strip()
                      for cid in channel_ids_input.split('\n') if cid.strip()]

        if len(raw_inputs) < 2:
            st.error("Please enter at least 2 channels for comparison")
            return

        try:
            with st.spinner("Resolving channel identifiers & analyzing..."):
                # Resolve @usernames to actual channel IDs
                handler = YouTubeAPIHandler()
                channel_ids = []
                for entry in raw_inputs:
                    if entry.startswith('@'):
                        try:
                            channel_info = handler.get_channel_by_username(
                                entry)
                            resolved_id = channel_info['id']
                            channel_ids.append(resolved_id)
                            st.caption(f"✅ Resolved {entry} → {resolved_id}")
                        except Exception as resolve_err:
                            st.warning(
                                f"⚠️ Could not resolve {entry}: {resolve_err}")
                    elif entry.startswith('UC') and len(entry) == 24:
                        channel_ids.append(entry)
                    else:
                        st.warning(
                            f"⚠️ Skipping invalid input: {entry} (use UC... channel ID or @username)")

                if len(channel_ids) < 2:
                    st.error(
                        "Need at least 2 valid channels after resolving. Make sure the channels have been analyzed individually first.")
                    return

                storage_service = DataStorageService()
                analytics = storage_service.get_analytics_queries()

                comparison_df = analytics.compare_multiple_channels(
                    channel_ids)

                if comparison_df.empty:
                    st.warning(
                        "No data found. Please analyze these channels individually first.")
                    return

                # Comparison table
                st.markdown(
                    '<div class="yt-chart-title">Channel Comparison</div>', unsafe_allow_html=True)
                st.dataframe(
                    comparison_df[['title', 'subscriber_count', 'view_count',
                                   'video_count', 'avg_engagement_rate', 'engagement_efficiency']],
                    use_container_width=True, hide_index=True
                )

                # Charts
                tab1, tab2, tab3 = st.tabs(
                    ["📊 Metrics", "📁 Content Strategy", "🏆 Benchmarking"])

                with tab1:
                    st.markdown('<div class="yt-chart-card">',
                                unsafe_allow_html=True)
                    st.plotly_chart(
                        charts.multi_channel_comparison_bar(
                            comparison_df, 'avg_engagement_rate', 'Engagement Rate Comparison', 'Avg Engagement Rate (%)'),
                        use_container_width=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="yt-chart-card">',
                                unsafe_allow_html=True)
                    st.plotly_chart(
                        charts.multi_channel_comparison_bar(
                            comparison_df, 'subscriber_count', 'Subscriber Count Comparison', 'Subscribers'),
                        use_container_width=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

                with tab2:
                    strategy_df = analytics.get_content_strategy_comparison(
                        channel_ids)
                    if not strategy_df.empty:
                        category_comparison = strategy_df.groupby(
                            ['channel_title', 'category']).size().unstack(fill_value=0)
                        st.markdown(
                            '<div class="yt-chart-title">Content Category Distribution by Channel</div>', unsafe_allow_html=True)
                        st.dataframe(category_comparison,
                                     use_container_width=True)
                    else:
                        st.info("No content strategy data available.")

                with tab3:
                    report = analytics.get_competitive_benchmarking_report(
                        primary_channel_id=channel_ids[0],
                        competitor_channel_ids=channel_ids[1:]
                    )

                    primary_title = report['primary_channel_metrics'].get(
                        'title', 'Primary Channel')
                    st.markdown(f"""
                    <div style="color:{text_primary};font-family:Inter,sans-serif;font-weight:600;font-size:1rem;margin-bottom:12px;">
                        Primary Channel: {primary_title}
                    </div>
                    """, unsafe_allow_html=True)

                    if report['benchmarks'].get('avg_engagement_rate'):
                        render_metric_card("Benchmark Avg Engagement",
                                           f"{report['benchmarks']['avg_engagement_rate']:.2f}%")

                    col1, col2 = st.columns(2)
                    with col1:
                        if report['advantages']:
                            st.success("**Strengths:**")
                            for adv in report['advantages']:
                                st.write(f"✅ {adv}")
                    with col2:
                        if report['disadvantages']:
                            st.error("**Areas for Improvement:**")
                            for dis in report['disadvantages']:
                                st.write(f"⚠️ {dis}")

        except Exception as e:
            st.error(f"Failed to compare channels: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: AI INSIGHTS (LLM-generated analysis)
# ═══════════════════════════════════════════════════════════════════════════════

def page_ai_insights():
    """Page: Claude reads the computed metrics and writes a performance report."""
    render_page_header(
        "AI Insights",
        "AI insights",
        "Plain-English analysis of your channel · Powered by Claude"
    )

    if 'video_df' not in st.session_state:
        st.info("Please analyze a channel first from the **Analytics** page.")
        return

    if not ai_configured():
        st.info("🔑 Add your **CLOUDFLARE_API_TOKEN** to `.env` (or Streamlit Cloud secrets) "
                "to enable AI features. See the README for where to put it.")
        return

    video_df = st.session_state['video_df']
    channel_data = st.session_state.get('channel_data', {})
    engagement_metrics = st.session_state.get('engagement_metrics', {})

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        generate = st.button("✨  Generate AI insights", type="primary")

    if generate:
        # Best-effort forecast from the DB to enrich the prompt.
        forecast = None
        try:
            storage_service = DataStorageService()
            predictive = storage_service.get_predictive_analytics()
            cid = channel_data.get('channel_id')
            if cid:
                forecast = predictive.forecast_channel_growth(cid, days_ahead=30)
        except Exception:
            forecast = None

        with st.spinner("Claude is analyzing your channel..."):
            result = ai_insights.generate_insights(
                channel_data, engagement_metrics, video_df, forecast)
        st.session_state['ai_insights_result'] = result

    result = st.session_state.get('ai_insights_result')
    if result:
        if result.get('ok'):
            st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
            st.markdown(result['markdown'])
            st.markdown('</div>', unsafe_allow_html=True)
        elif result.get('error') == 'no_key':
            st.info("🔑 Add your CLOUDFLARE_API_TOKEN to enable AI features.")
        else:
            st.error(f"Could not generate insights: {result.get('error')}")
    else:
        st.caption("Click **Generate AI insights** to get an LLM-written performance "
                   "report and specific action tips based on your channel's numbers.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COMMENT SENTIMENT (AI classification of viewer comments)
# ═══════════════════════════════════════════════════════════════════════════════

def page_comment_sentiment():
    """Page: fetch viewer comments and classify sentiment with Claude."""
    render_page_header(
        "Comment Sentiment",
        "Comment sentiment",
        "AI reads your viewers' comments · Powered by Claude"
    )

    if 'video_df' not in st.session_state:
        st.info("Please analyze a channel first from the **Analytics** page.")
        return

    if not ai_configured():
        st.info("🔑 Add your **CLOUDFLARE_API_TOKEN** to `.env` (or Streamlit Cloud secrets) "
                "to enable AI features. See the README for where to put it.")
        return

    video_df = st.session_state['video_df']
    channel_data = st.session_state.get('channel_data', {})

    col_a, _ = st.columns([1, 3])
    with col_a:
        max_videos = st.number_input(
            "Top videos to scan", min_value=3, max_value=20, value=8, step=1)
    st.caption("Fetches recent comments from your top videos by views, then classifies "
               "each as positive / neutral / negative.")

    if st.button("💬  Analyze comments", type="primary"):
        try:
            handler = YouTubeAPIHandler()
        except Exception as e:
            st.error(f"YouTube API not configured: {e}")
            return

        top_videos = video_df.nlargest(int(max_videos), 'view_count')
        rows = list(top_videos.iterrows())
        all_comments = []
        progress = st.progress(0.0, text="Fetching comments...")
        for i, (_, v) in enumerate(rows):
            try:
                raw = handler.get_video_comments(v['video_id'], max_results=30)
                all_comments.extend(raw)
            except Exception:
                pass
            progress.progress((i + 1) / max(len(rows), 1),
                              text=f"Fetching comments... ({i + 1}/{len(rows)})")
        progress.empty()

        if not all_comments:
            st.warning("No comments found (comments may be disabled on these videos).")
            return

        comments_df = DataProcessor().process_comment_data(all_comments)
        if comments_df.empty:
            st.warning("No usable comments to analyze.")
            return

        comments_df['channel_id'] = channel_data.get('channel_id')

        with st.spinner(f"Claude is classifying {len(comments_df)} comments..."):
            comments_df = ai_sentiment.analyze_comment_sentiment(comments_df)

        # Best-effort persistence — charts render from memory regardless.
        try:
            storage_service = DataStorageService()
            storage_service.save_comment_data(comments_df)
        except Exception as e:
            st.caption(f"(Saved to session only — database write skipped: {e})")

        st.session_state['comments_df'] = comments_df

    comments_df = st.session_state.get('comments_df')
    if comments_df is None or comments_df.empty:
        st.caption("Click **Analyze comments** to fetch and classify viewer comments.")
        return

    # ─── Summary metric cards ───
    total = len(comments_df)
    pos = int((comments_df['sentiment_label'] == 'positive').sum())
    neg = int((comments_df['sentiment_label'] == 'negative').sum())
    avg_score = float(comments_df['sentiment_score'].mean())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Comments Analyzed", str(total))
    with c2:
        render_metric_card("Positive", f"{pos / total * 100:.0f}%",
                           trend_text=f"{pos} comments")
    with c3:
        render_metric_card("Negative", f"{neg / total * 100:.0f}%",
                           trend_text=f"{neg} comments")
    with c4:
        render_metric_card("Avg Sentiment", f"{avg_score:+.2f}",
                           trend_text="-1 to +1 scale")

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    # ─── Charts ───
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.sentiment_donut(comments_df),
                        use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="yt-chart-card">', unsafe_allow_html=True)
        st.plotly_chart(charts.sentiment_by_video_bar(comments_df, video_df),
                        use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── Top positive / negative comments ───
    col_p, col_n = st.columns(2)
    with col_p:
        st.markdown('<div class="yt-chart-title">😊 Most positive comments</div>',
                    unsafe_allow_html=True)
        for _, row in comments_df.nlargest(5, 'sentiment_score').iterrows():
            st.markdown(f"> {html.escape(str(row['text'])[:200])}  \n"
                        f"`{row['sentiment_score']:+.2f}`")
    with col_n:
        st.markdown('<div class="yt-chart-title">😠 Most negative comments</div>',
                    unsafe_allow_html=True)
        for _, row in comments_df.nsmallest(5, 'sentiment_score').iterrows():
            st.markdown(f"> {html.escape(str(row['text'])[:200])}  \n"
                        f"`{row['sentiment_score']:+.2f}`")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="YouTube Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ══════════════════════════════════════════════════════════════════════
    # AUTHENTICATION GATE — show login page if not logged in
    # ══════════════════════════════════════════════════════════════════════
    if not is_logged_in():
        render_login_page()
        return

    # ══════════════════════════════════════════════════════════════════════
    # AUTHENTICATED — render the full dashboard
    # ══════════════════════════════════════════════════════════════════════

    # Resolve theme: corner toggle override → system preference → light
    mode = theme_tokens.resolve_mode()
    inject_yt_studio_styles(mode)

    # Theme toggle — injected globally
    theme_tokens.inject_theme_toggle()

    # Initialize sidebar state
    if 'sidebar_visible' not in st.session_state:
        st.session_state['sidebar_visible'] = True

    # Hide sidebar completely when not visible
    if not st.session_state.get('sidebar_visible', True):
        st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            .stApp > header { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

        # Floating button to show sidebar
        col_btn, col_space = st.columns([1, 10])
        with col_btn:
            if st.button("▶ Menu", key="show_sidebar"):
                st.session_state['sidebar_visible'] = True
                st.rerun()

        # Use stored page
        page = st.session_state.get('current_page', "📊 Analytics")
    else:
        # Render sidebar normally
        page = render_sidebar()

    # Store current page
    st.session_state['current_page'] = page

    # Route to pages
    if page == "📊 Analytics":
        page_channel_analytics()
    elif page == "🔍 Video Explorer":
        page_video_explorer()
    elif page == "📈 Trend Analysis":
        page_trend_analysis()
    elif page == "⚔️ Multi-Channel":
        page_multi_channel()
    elif page == "🤖 AI Insights":
        page_ai_insights()
    elif page == "💬 Comment Sentiment":
        page_comment_sentiment()


if __name__ == "__main__":
    main()
