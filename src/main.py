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
from dashboard.effects_3d import inject_3d_effects, inject_3d_javascript, render_floating_orbs, render_hero_section
from auth import is_logged_in, logout, get_current_user
from login_page import render_login_page

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

def inject_yt_studio_styles(theme='dark'):
    """Apply YouTube Studio theme CSS across the Streamlit app."""
    is_dark = theme == 'dark'

    # Theme-dependent tokens
    bg_page = '#030712' if is_dark else '#FAF5FF'
    bg_card = '#272727' if is_dark else '#ffffff'
    bg_card_hover = '#333333' if is_dark else '#f0f0f0'
    bg_sidebar = '#202020' if is_dark else '#FCE7F3'
    border_color = 'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.1)'
    text_primary = '#FFFFFF' if is_dark else '#0f0f0f'
    text_secondary = '#AAAAAA' if is_dark else '#606060'
    text_body = '#f1f1f1' if is_dark else '#0f0f0f'
    sidebar_hover = 'rgba(255,255,255,0.08)' if is_dark else 'rgba(0,0,0,0.05)'
    input_bg = '#272727' if is_dark else '#ffffff'
    input_border = 'rgba(255,255,255,0.15)' if is_dark else 'rgba(0,0,0,0.15)'
    scrollbar_track = '#0f0f0f' if is_dark else '#f9f9f9'
    scrollbar_thumb = '#555' if is_dark else '#ccc'
    metric_delta_up = '#2BA640'
    metric_delta_down = '#FF4444'
    accent_blue = '#3EA6FF'
    grid_color = 'rgba(255,255,255,0.05)' if is_dark else 'rgba(0,0,0,0.06)'
    divider_color = 'rgba(255,255,255,0.08)' if is_dark else 'rgba(0,0,0,0.08)'
    traffic_bar_bg = 'rgba(255,255,255,0.08)' if is_dark else 'rgba(0,0,0,0.06)'
    btn_bg = '#272727' if is_dark else '#f0f0f0'
    btn_hover_bg = '#333333' if is_dark else '#e0e0e0'
    btn_primary_bg = '#3EA6FF'
    btn_primary_text = '#0f0f0f'
    toggle_bg = 'rgba(255,255,255,0.08)' if is_dark else 'rgba(0,0,0,0.05)'
    sidebar_ctrl_bg = '#272727' if is_dark else '#1f1f1f'
    sidebar_ctrl_hover_bg = '#3a3a3a' if is_dark else '#111111'
    sidebar_ctrl_text = '#f1f1f1' if is_dark else '#ffffff'
    sidebar_ctrl_border = 'rgba(255,255,255,0.2)' if is_dark else 'rgba(0,0,0,0.4)'
    light_mode_text_overrides = ""

    if not is_dark:
        light_mode_text_overrides = f"""
        /* ── Light Mode Text Readability Guard ──────────── */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stCaptionContainer"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        .stText,
        .stSelectbox label,
        .stMultiSelect label,
        .stDateInput label,
        .stTextInput label,
        .stNumberInput label,
        .stTextArea label,
        .stRadio > label,
        .stCheckbox > label,
        .stToggle > label {{
            color: {text_body} !important;
        }}

        .yt-chart-subtitle,
        .yt-date-range,
        .yt-metric-label,
        .yt-video-stat-label {{
            color: {text_secondary} !important;
        }}
        """

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700;800;900&display=swap');

        /* ── Smooth Theme Transitions ─────────────────────── */
        .stApp, [data-testid="stSidebar"], .yt-metric-card, .yt-chart-card,
        .yt-video-card, [data-testid="stMetric"], .stButton > button,
        .stTextInput input, .sidebar-channel-info, .yt-theme-toggle {{
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease !important;
        }}

        /* ── Page Background ─────────────────────────────── */
        .stApp {{
            background: {bg_page} !important;
            color: {text_body} !important;
            font-family: 'Roboto', sans-serif;
        }}
        {light_mode_text_overrides}
        .block-container {{
            padding-top: 1.2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1300px;
        }}

        /* ── Sidebar ─────────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background: {bg_sidebar} !important;
            border-right: 1px solid {border_color};
            width: 240px !important;
        }}
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3 {{
            color: {text_primary} !important;
            font-family: 'Roboto', sans-serif !important;
        }}
        [data-testid="stSidebar"] .stRadio label {{
            color: {text_secondary} !important;
            font-family: 'Roboto', sans-serif !important;
            font-size: 14px !important;
            font-weight: 400 !important;
            padding: 8px 16px !important;
            border-radius: 10px;
            transition: all 0.2s ease;
        }}
        [data-testid="stSidebar"] .stRadio label:hover {{
            background: {sidebar_hover} !important;
            color: {text_primary} !important;
        }}
        [data-testid="stSidebar"] .stRadio label[data-checked="true"],
        [data-testid="stSidebar"] [aria-checked="true"] + label {{
            color: {accent_blue} !important;
            font-weight: 500 !important;
        }}

        /* ── Section Headings ────────────────────────────── */
        .yt-page-title {{
            font-family: 'Roboto', sans-serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: {text_primary};
            margin: 0;
            padding: 0;
        }}
        .yt-header-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.8rem;
        }}
        .yt-date-range {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.8rem;
            color: {text_secondary};
            text-align: right;
        }}
        .yt-date-range strong {{
            display: block;
            color: {text_primary};
            font-size: 0.85rem;
            font-weight: 500;
        }}

        /* ── Tab Bar ─────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {{
            background: transparent !important;
            border: none !important;
            border-bottom: 1px solid {border_color} !important;
            border-radius: 0 !important;
            padding: 0 !important;
            gap: 0 !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 0 !important;
            background: transparent !important;
            color: {text_secondary} !important;
            font-family: 'Roboto', sans-serif !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            padding: 12px 24px !important;
            border-bottom: 3px solid transparent !important;
            transition: all 0.2s ease;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {text_primary} !important;
        }}
        .stTabs [aria-selected="true"] {{
            background: transparent !important;
            color: {accent_blue} !important;
            border-bottom: 3px solid {accent_blue} !important;
        }}
        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {{
            display: none !important;
        }}

        /* ── Metric Cards ────────────────────────────────── */
        .yt-metric-card {{
            background: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 20px 24px;
            transition: all 0.25s ease;
            min-height: 100px;
        }}
        .yt-metric-card:hover {{
            background: {bg_card_hover};
            border-color: {border_color};
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }}
        .yt-metric-label {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.78rem;
            font-weight: 400;
            color: {text_secondary};
            margin-bottom: 6px;
            text-transform: none;
        }}
        .yt-metric-value {{
            font-family: 'Roboto', sans-serif;
            font-size: 1.75rem;
            font-weight: 700;
            color: {text_primary};
            line-height: 1.2;
        }}
        .yt-metric-trend {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.78rem;
            font-weight: 500;
            margin-top: 6px;
        }}
        .yt-trend-up {{ color: {metric_delta_up}; }}
        .yt-trend-down {{ color: {metric_delta_down}; }}
        .yt-trend-neutral {{ color: {text_secondary}; }}

        /* ── Chart Cards ─────────────────────────────────── */
        .yt-chart-card {{
            background: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 1rem;
            transition: all 0.25s ease;
        }}
        .yt-chart-card:hover {{
            border-color: {border_color};
        }}
        .yt-chart-title {{
            font-family: 'Roboto', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            color: {text_primary};
            margin-bottom: 4px;
        }}
        .yt-chart-subtitle {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.78rem;
            color: {text_secondary};
            margin-bottom: 12px;
        }}

        /* ── See More Link ───────────────────────────────── */
        .yt-see-more {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.85rem;
            font-weight: 500;
            color: {accent_blue};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            cursor: pointer;
            margin-top: 8px;
            display: inline-block;
        }}
        .yt-see-more:hover {{
            color: #69b8ff;
        }}

        /* ── Streamlit Overrides ─────────────────────────── */
        [data-testid="stMetric"] {{
            background: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px 20px;
            transition: all 0.25s ease;
        }}
        [data-testid="stMetric"]:hover {{
            background: {bg_card_hover};
            border-color: {border_color};
            transform: translateY(-1px);
        }}
        [data-testid="stMetricLabel"] {{
            color: {text_secondary} !important;
            font-weight: 400 !important;
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.78rem !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {text_primary} !important;
            font-weight: 700 !important;
            font-family: 'Roboto', sans-serif !important;
        }}
        [data-testid="stMetricDelta"] {{
            font-family: 'Roboto', sans-serif !important;
        }}

        .stButton > button {{
            background: {btn_bg} !important;
            border: 1px solid {input_border} !important;
            border-radius: 20px !important;
            color: {accent_blue} !important;
            font-family: 'Roboto', sans-serif !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            padding: 8px 24px !important;
            transition: all 0.2s ease;
        }}
        .stButton > button:hover {{
            background: {btn_hover_bg} !important;
            border-color: {accent_blue} !important;
        }}
        .stButton > button[kind="primary"] {{
            background: {btn_primary_bg} !important;
            color: {btn_primary_text} !important;
            border-color: {btn_primary_bg} !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: #69b8ff !important;
        }}

        .stTextInput input, .stSelectbox select, .stNumberInput input {{
            background: {input_bg} !important;
            border: 1px solid {input_border} !important;
            border-radius: 8px !important;
            color: {text_body} !important;
            font-family: 'Roboto', sans-serif !important;
        }}
        .stTextInput input:focus {{
            border-color: {accent_blue} !important;
            box-shadow: 0 0 0 1px {accent_blue} !important;
        }}

        [data-testid="stDataFrame"], [data-testid="stTable"] {{
            border: 1px solid {border_color};
            border-radius: 12px;
            overflow: hidden;
        }}

        .stAlert {{
            border-radius: 12px;
            border: 1px solid {border_color};
        }}

        /* ── Sidebar Channel Info ────────────────────────── */
        .sidebar-channel-info {{
            text-align: center;
            padding: 16px 12px;
            margin-bottom: 12px;
        }}
        .sidebar-channel-avatar {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            margin: 0 auto 10px;
            display: block;
            border: 2px solid {border_color};
        }}
        .sidebar-channel-name {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.85rem;
            font-weight: 600;
            color: {text_primary};
            margin-top: 4px;
        }}
        .sidebar-channel-label {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.72rem;
            color: {text_secondary};
            margin-top: 2px;
        }}

        /* ── Top Video Cards ─────────────────────────────── */
        .yt-video-card {{
            background: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 8px;
            transition: all 0.2s ease;
        }}
        .yt-video-card:hover {{
            background: {bg_card_hover};
            border-color: {border_color};
        }}
        .yt-video-title {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.9rem;
            font-weight: 500;
            color: {text_primary};
            margin-bottom: 8px;
            line-height: 1.3;
        }}
        .yt-video-stats {{
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
        }}
        .yt-video-stat {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.78rem;
        }}
        .yt-video-stat-label {{
            color: {text_secondary};
        }}
        .yt-video-stat-value {{
            color: {text_primary};
            font-weight: 600;
            margin-left: 4px;
        }}

        /* ── Progress bars for traffic sources ───────────── */
        .yt-traffic-row {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            gap: 12px;
        }}
        .yt-traffic-label {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.8rem;
            color: {text_secondary};
            min-width: 130px;
        }}
        .yt-traffic-bar-bg {{
            flex: 1;
            height: 6px;
            background: {traffic_bar_bg};
            border-radius: 3px;
            overflow: hidden;
        }}
        .yt-traffic-bar-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.6s ease;
        }}
        .yt-traffic-pct {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.8rem;
            color: {text_primary};
            font-weight: 500;
            min-width: 50px;
            text-align: right;
        }}

        /* ── Divider ─────────────────────────────────────── */
        .yt-divider {{
            border: none;
            border-top: 1px solid {divider_color};
            margin: 16px 0;
        }}

        /* ── Theme Toggle ────────────────────────────────── */
        .yt-theme-toggle {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: {toggle_bg};
            border-radius: 10px;
            margin-top: 0;
        }}
        .yt-theme-toggle-label {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.78rem;
            color: {text_secondary};
        }}

        /* ── Toggle Switch Styling ───────────────────────── */
        [data-testid="stSidebar"] .stToggle > label {{
            display: none !important;
        }}
        [data-testid="stSidebar"] .stToggle {{
            margin-top: 0 !important;
            display: flex;
            justify-content: flex-end;
        }}
        [data-testid="stSidebar"] .stToggle > div {{
            margin-top: 0 !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="checkbox"] > div {{
            background: {toggle_bg} !important;
            border-color: {border_color} !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="checkbox"] > div[aria-checked="true"] {{
            background: {accent_blue} !important;
            border-color: {accent_blue} !important;
        }}

        /* ── Scrollbar ───────────────────────────────────── */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: {scrollbar_track}; }}
        ::-webkit-scrollbar-thumb {{ background: {scrollbar_thumb}; border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #777; }}

        /* ── Hide Streamlit branding ─────────────────────── */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        /* ── Sidebar Buttons ─────────────────────────────── */
        [data-testid="stSidebar"] .stButton > button {{
            background: {toggle_bg} !important;
            border: 1px solid {border_color} !important;
            color: {text_secondary} !important;
            width: 100%;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            background: {sidebar_hover} !important;
            color: {text_primary} !important;
            border-color: {accent_blue} !important;
        }}

        /* ── Sidebar Collapse/Expand Control ───────────── */
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="collapsedControl"] button,
        button[aria-label="Close sidebar"],
        button[aria-label="Open sidebar"] {{
            background: {sidebar_ctrl_bg} !important;
            color: {sidebar_ctrl_text} !important;
            border: 1px solid {sidebar_ctrl_border} !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }}

        [data-testid="stSidebarCollapseButton"] button:hover,
        [data-testid="collapsedControl"] button:hover,
        button[aria-label="Close sidebar"]:hover,
        button[aria-label="Open sidebar"]:hover {{
            background: {sidebar_ctrl_hover_bg} !important;
            color: {sidebar_ctrl_text} !important;
            border-color: {accent_blue} !important;
        }}

        [data-testid="stSidebarCollapseButton"] button svg,
        [data-testid="collapsedControl"] button svg,
        button[aria-label="Close sidebar"] svg,
        button[aria-label="Open sidebar"] svg {{
            fill: {sidebar_ctrl_text} !important;
            stroke: {sidebar_ctrl_text} !important;
        }}
    </style>
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
    """Render traffic source breakdown as styled HTML bars (simulated from categories)."""
    if 'category' not in video_df.columns or video_df.empty:
        return

    category_views = video_df.groupby('category')['view_count'].sum()
    total = category_views.sum()
    if total == 0:
        return

    source_mapping = {
        'General': 'External',
        'Tech Reviews': 'YouTube search',
        'Tutorials': 'Browse features',
        'Product Comparisons': 'Suggested videos',
        'News Updates': 'Channel pages',
        'Unboxings': 'Direct or unknown',
        'Software Updates': 'Notifications',
        'Accessories': 'Playlists',
        'Price Analysis': 'Other',
    }

    colors = ['#7B68EE', '#3EA6FF', '#22d3ee', '#a78bfa',
              '#60a5fa', '#818cf8', '#c084fc', '#38bdf8', '#6366f1']
    sources = []
    for cat, views in category_views.sort_values(ascending=False).items():
        pct = views / total * 100
        sources.append((source_mapping.get(cat, cat), pct))

    # Merge duplicates
    merged = {}
    for name, pct in sources:
        merged[name] = merged.get(name, 0) + pct
    sources = sorted(merged.items(), key=lambda x: x[1], reverse=True)

    html_rows = ''
    for i, (name, pct) in enumerate(sources[:6]):
        color = colors[i % len(colors)]
        html_rows += f"""
        <div class="yt-traffic-row">
            <span class="yt-traffic-label">{name}</span>
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
                    <div style="width:80px;height:80px;border-radius:50%;overflow:hidden;background:#111;margin:0 auto 10px;">
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
                    <div style="width:80px;height:80px;border-radius:50%;background:#333;margin:0 auto 10px;display:flex;align-items:center;justify-content:center;">
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
                "📈 Trend Analysis", "⚔️ Multi-Channel"],
            label_visibility="collapsed"
        )

        st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)

        # Subscriber count
        if 'channel_data' in st.session_state:
            ch = st.session_state['channel_data']
            st.caption(f"📢 {ch.get('subscriber_count', 0):,} subscribers")
            st.caption(f"🎬 {ch.get('video_count', 0):,} videos")
            st.caption(f"👁️ {ch.get('view_count', 0):,} total views")

        # st.markdown('<hr class="yt-divider">', unsafe_allow_html=True)

        # Dark / Light mode toggle
        current_theme = st.session_state.get('theme', 'dark')
        theme_icon = '🌙' if current_theme == 'dark' else '☀️'
        theme_label = 'Dark mode' if current_theme == 'dark' else 'Light mode'

        # Theme toggle with callback for instant update
        def toggle_theme():
            st.session_state['theme'] = 'dark' if st.session_state.get(
                'theme_toggle_key') else 'light'

        col_label, col_toggle = st.columns([5, 2])
        with col_label:
            st.markdown(
                f'<div class="yt-theme-toggle"><span>{theme_icon}</span><span class="yt-theme-toggle-label">{theme_label}</span></div>',
                unsafe_allow_html=True
            )

        with col_toggle:
            st.toggle(
                'Toggle theme',
                value=(current_theme == 'dark'),
                key='theme_toggle_key',
                label_visibility='collapsed',
                on_change=toggle_theme
            )

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

    # 3D Hero Section
    render_hero_section(
        title="Channel Analytics",
        subtitle="Deep-dive performance metrics · Powered by YouTube Data API"
    )

    # Header row
    st.markdown("""
    <div class="yt-header-row">
        <h1 class="yt-page-title">Channel analytics</h1>
        <div class="yt-date-range">
            <strong>Last 28 days</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
            <div style="font-family:Roboto,sans-serif;font-size:1.1rem;color:{text_secondary};">
                Enter a YouTube Channel ID or @Username above to start analyzing
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    video_df = st.session_state['video_df']
    engagement_metrics = st.session_state['engagement_metrics']
    channel_data = st.session_state['channel_data']

    # ─── Tab Bar (Overview / Reach / Engagement / Audience / Revenue) ───
    tab_overview, tab_reach, tab_engagement, tab_audience, tab_revenue = st.tabs(
        ["Overview", "Reach", "Engagement", "Audience", "Revenue"]
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
        st.markdown('<span class="yt-see-more">SEE MORE</span>',
                    unsafe_allow_html=True)

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        # Bottom two cards
        col_traffic, col_funnel = st.columns(2)

        with col_traffic:
            st.markdown("""
            <div class="yt-chart-card">
                <div class="yt-chart-title">Traffic source types</div>
                <div class="yt-chart-subtitle">Views · Last 28 days</div>
            """, unsafe_allow_html=True)
            st.plotly_chart(charts.traffic_sources_donut(
                video_df), use_container_width=True)
            render_traffic_source_bars(video_df)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_funnel:
            st.markdown("""
            <div class="yt-chart-card">
                <div class="yt-chart-title">Impressions and how they led to watch time</div>
                <div class="yt-chart-subtitle">Data available · Last 28 days</div>
            """, unsafe_allow_html=True)

            # Funnel-style metrics
            total_v = int(video_df['view_count'].sum())
            total_likes = int(video_df['like_count'].sum())
            total_comments = int(video_df['comment_count'].sum())
            total_interactions = total_likes + total_comments
            ctr = (total_interactions / max(total_v, 1)) * 100

            render_metric_card("Total Views (Impressions)",
                               format_number(total_v))
            st.markdown(f"""
            <div style="text-align:center;padding:8px 0;color:{text_secondary};font-size:0.8rem;font-family:Roboto,sans-serif;">
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

    # ═══════════════════════ REVENUE TAB ══════════════════════════════════
    with tab_revenue:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:2.5rem;margin-bottom:12px;">💰</div>
            <div class="yt-chart-title" style="text-align:center;">Revenue analytics</div>
            <div class="yt-chart-subtitle" style="text-align:center;">Growth forecast based on current engagement trends</div>
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
    st.markdown('<h1 class="yt-page-title">🔍 Video Explorer</h1>',
                unsafe_allow_html=True)

    # 3D Hero Section
    render_hero_section(
        title="Video Explorer",
        subtitle="Search, filter and discover top-performing content"
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
    <div style="color:{text_secondary};font-family:Roboto,sans-serif;font-size:0.9rem;margin-bottom:16px;">
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
    st.markdown('<h1 class="yt-page-title">📈 Trend Analysis</h1>',
                unsafe_allow_html=True)

    # 3D Hero Section
    render_hero_section(
        title="Trend Analysis",
        subtitle="Time-series insights · Posting patterns · Predictive forecasting"
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
    <div style="color:{text_secondary};font-family:Roboto,sans-serif;font-size:0.9rem;margin-bottom:16px;">
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
    st.markdown('<h1 class="yt-page-title">⚔️ Multi-Channel Comparison</h1>',
                unsafe_allow_html=True)

    # 3D Hero Section
    render_hero_section(
        title="Multi-Channel Battle",
        subtitle="Compare channels side by side · Competitive benchmarking"
    )

    theme_colors = charts.get_theme_colors()
    text_primary = theme_colors['text_primary']
    text_secondary = theme_colors['text_secondary']

    st.markdown(f"""
    <div style="color:{text_secondary};font-family:Roboto,sans-serif;font-size:0.9rem;margin-bottom:16px;">
        Compare multiple YouTube channels side by side
    </div>
    """, unsafe_allow_html=True)

    channel_ids_input = st.text_area(
        "Enter Channel IDs or @Usernames (one per line):",
        placeholder="UC_x5XG1OV2P6uZZ5FSM9Ttw\n@chaiaurcode\n@username",
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
                    <div style="color:{text_primary};font-family:Roboto,sans-serif;font-weight:600;font-size:1rem;margin-bottom:12px;">
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

    # Initialize theme in session state if not exists
    if 'theme' not in st.session_state:
        st.session_state['theme'] = 'dark'

    # Apply theme based on session state
    theme = st.session_state.get('theme', 'dark')
    inject_yt_studio_styles(theme)

    # ── Inject 3D interactive effects ──
    inject_3d_effects(theme)
    render_floating_orbs()
    inject_3d_javascript()

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


if __name__ == "__main__":
    main()
