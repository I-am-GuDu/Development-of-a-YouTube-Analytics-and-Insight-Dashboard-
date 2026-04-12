"""
Dashboard Charts Module
Reusable Plotly visualization functions for YouTube Analytics
YouTube Studio-style theme (dark/light)
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import streamlit as st


def get_theme_colors():
    """Get colors based on current theme from session state."""
    is_dark = st.session_state.get('theme', 'dark') == 'dark'

    if is_dark:
        return {
            'bg_page': '#0f0f0f',
            'bg_card': '#272727',
            'bg_card_hover': '#333333',
            'border': 'rgba(255,255,255,0.1)',
            'text_primary': '#FFFFFF',
            'text_secondary': '#AAAAAA',
            'text_link': '#3EA6FF',
            'trend_positive': '#2BA640',
            'trend_negative': '#FF4444',
            'chart_line': '#7B68EE',
            'chart_fill': 'rgba(123,104,238,0.25)',
            'chart_bar': 'rgba(123,104,238,0.7)',
            'accent_blue': '#3EA6FF',
            'accent_purple': '#7B68EE',
            'accent_teal': '#22d3ee',
            'grid': 'rgba(255,255,255,0.05)',
            'plot_bg': 'rgba(39,39,39,0.4)',
            'template': 'plotly_dark',
        }
    else:
        return {
            'bg_page': '#f9f9f9',
            'bg_card': '#ffffff',
            'bg_card_hover': '#f0f0f0',
            'border': 'rgba(0,0,0,0.1)',
            'text_primary': '#0f0f0f',
            'text_secondary': '#606060',
            'text_link': '#065fd4',
            'trend_positive': '#2BA640',
            'trend_negative': '#FF4444',
            'chart_line': '#6366f1',
            'chart_fill': 'rgba(99,102,241,0.2)',
            'chart_bar': 'rgba(99,102,241,0.7)',
            'accent_blue': '#065fd4',
            'accent_purple': '#6366f1',
            'accent_teal': '#0891b2',
            'grid': 'rgba(0,0,0,0.06)',
            'plot_bg': 'rgba(255,255,255,0.4)',
            'template': 'plotly_white',
        }


# Keep YT_COLORS for backward compatibility
YT_COLORS = {
    'bg_page': '#0f0f0f',
    'bg_card': '#272727',
    'bg_card_hover': '#333333',
    'border': 'rgba(255,255,255,0.1)',
    'text_primary': '#FFFFFF',
    'text_secondary': '#AAAAAA',
    'text_link': '#3EA6FF',
    'trend_positive': '#2BA640',
    'trend_negative': '#FF4444',
    'chart_line': '#7B68EE',
    'chart_fill': 'rgba(123,104,238,0.25)',
    'chart_bar': 'rgba(123,104,238,0.7)',
    'accent_blue': '#3EA6FF',
    'accent_purple': '#7B68EE',
    'accent_teal': '#22d3ee',
    'grid': 'rgba(255,255,255,0.05)',
}

DONUT_PALETTE = [
    '#7B68EE', '#3EA6FF', '#22d3ee', '#a78bfa',
    '#60a5fa', '#818cf8', '#c084fc', '#38bdf8',
]

DONUT_PALETTE_LIGHT = [
    '#6366f1', '#065fd4', '#0891b2', '#8b5cf6',
    '#3b82f6', '#6366f1', '#a855f7', '#0ea5e9',
]


def _apply_yt_studio_layout(fig, height=None):
    """Apply YouTube Studio theme layout to Plotly figures (theme-aware)."""
    colors = get_theme_colors()

    layout_kwargs = dict(
        template=colors['template'],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=colors['plot_bg'],
        font=dict(family="Roboto, sans-serif", color=colors['text_secondary'], size=12),
        title=dict(font=dict(size=16, color=colors['text_primary'], family="Roboto, sans-serif"), x=0.01, y=0.97),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=colors['border'],
            borderwidth=0,
            font=dict(size=11, color=colors['text_secondary']),
        ),
        hoverlabel=dict(
            bgcolor=colors['bg_card'],
            bordercolor=colors['border'],
            font=dict(color=colors['text_primary'], family="Roboto, sans-serif"),
        ),
    )
    if height:
        layout_kwargs['height'] = height
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(showgrid=True, gridcolor=colors['grid'], zeroline=False,
                     tickfont=dict(color=colors['text_secondary'], size=10))
    fig.update_yaxes(showgrid=True, gridcolor=colors['grid'], zeroline=False,
                     tickfont=dict(color=colors['text_secondary'], size=10))
    return fig


# ─── NEW: YouTube Studio-style charts ────────────────────────────────────────

def views_area_chart(video_df):
    """Large area chart matching YT Studio 'Reach' tab — views over time with filled area."""
    colors = get_theme_colors()
    df = video_df.sort_values('publish_date').copy()
    df['rolling_views'] = df['view_count'].rolling(window=3, min_periods=1).mean()

    fig = go.Figure()

    # Filled area
    fig.add_trace(go.Scatter(
        x=df['publish_date'], y=df['view_count'],
        mode='lines',
        name='Views',
        line=dict(color=colors['chart_line'], width=2.5),
        fill='tozeroy',
        fillcolor=colors['chart_fill'],
        hovertemplate='<b>%{text}</b><br>Views: %{y:,}<extra></extra>',
        text=df['title'],
    ))

    # Video upload markers along the bottom
    fig.add_trace(go.Scatter(
        x=df['publish_date'], y=[0] * len(df),
        mode='markers',
        name='Video uploads',
        marker=dict(
            symbol='triangle-up',
            size=10,
            color=colors['text_secondary'],
            line=dict(width=1, color=colors['text_secondary']),
        ),
        hovertemplate='<b>%{text}</b><br>Published<extra></extra>',
        text=df['title'],
        showlegend=False,
    ))

    fig.update_layout(
        xaxis_title='', yaxis_title='',
        hovermode='x unified',
        showlegend=False,
    )

    return _apply_yt_studio_layout(fig, height=340)


def traffic_sources_donut(video_df):
    """Donut chart for traffic source types (simulated from video categories)."""
    colors = get_theme_colors()
    is_dark = st.session_state.get('theme', 'dark') == 'dark'
    palette = DONUT_PALETTE if is_dark else DONUT_PALETTE_LIGHT

    if 'category' not in video_df.columns:
        return None

    category_views = video_df.groupby('category')['view_count'].sum().reset_index()
    category_views.columns = ['source', 'views']
    category_views = category_views.sort_values('views', ascending=False)

    # Rename to traffic-source-like labels
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
    category_views['source'] = category_views['source'].map(
        lambda x: source_mapping.get(x, x)
    )
    # Merge duplicates
    category_views = category_views.groupby('source')['views'].sum().reset_index()
    category_views = category_views.sort_values('views', ascending=False)
    category_views['pct'] = (category_views['views'] / category_views['views'].sum() * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=category_views['source'],
        values=category_views['views'],
        hole=0.6,
        marker=dict(colors=palette[:len(category_views)],
                    line=dict(color=colors['bg_card'], width=2)),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>Views: %{value:,}<br>%{percent}<extra></extra>',
    ))

    fig.update_layout(
        title=dict(text='Traffic source types', font=dict(size=16, color=colors['text_primary'])),
        annotations=[dict(
            text='Traffic<br>Sources',
            x=0.5, y=0.5, font=dict(size=13, color=colors['text_secondary'], family='Roboto'),
            showarrow=False,
        )],
        showlegend=False,
    )

    return _apply_yt_studio_layout(fig, height=360)


def impressions_funnel(metrics, video_df):
    """Funnel-style card showing Views → Engagement Rate → Total Interactions."""
    colors = get_theme_colors()
    total_views = int(video_df['view_count'].sum()) if not video_df.empty else 0
    avg_engagement = metrics.get('avg_engagement_rate', 0)
    total_interactions = int(video_df['like_count'].sum() + video_df['comment_count'].sum()) if not video_df.empty else 0

    fig = go.Figure()

    fig.add_trace(go.Funnel(
        y=['Total Views', 'Avg Engagement Rate', 'Total Interactions'],
        x=[total_views, avg_engagement * 1000, total_interactions],
        textinfo='value',
        texttemplate='%{value:,}',
        marker=dict(
            color=[colors['accent_purple'], colors['accent_blue'], colors['accent_teal']],
            line=dict(width=0),
        ),
        connector=dict(line=dict(color=colors['border'], width=1)),
    ))

    fig.update_layout(
        title=dict(text='Impressions and how they led to watch time',
                   font=dict(size=16, color=colors['text_primary'])),
        showlegend=False,
        funnelmode='stack',
    )

    return _apply_yt_studio_layout(fig, height=360)


# ─── Existing charts (updated styling) ───────────────────────────────────────

def engagement_distribution_chart(video_df):
    """Histogram of engagement rate distribution across videos"""
    colors = get_theme_colors()
    fig = px.histogram(
        video_df,
        x='engagement_rate',
        nbins=20,
        title='Distribution of Engagement Rates',
        labels={'engagement_rate': 'Engagement Rate (%)', 'count': 'Number of Videos'},
        color_discrete_sequence=[colors['accent_purple']]
    )
    fig.update_layout(bargap=0.1)
    return _apply_yt_studio_layout(fig)


def views_vs_likes_scatter(video_df, top_n=20):
    """Scatter plot showing relationship between views and likes"""
    colors = get_theme_colors()
    df = video_df.nlargest(top_n, 'view_count')
    fig = px.scatter(
        df,
        x='view_count',
        y='like_count',
        hover_data=['title', 'engagement_rate'],
        title=f'Views vs Likes (Top {top_n} Videos)',
        labels={'view_count': 'Views', 'like_count': 'Likes'},
        size='engagement_rate',
        color='engagement_rate',
        color_continuous_scale=[[0, colors['accent_blue']], [1, colors['accent_purple']]]
    )
    return _apply_yt_studio_layout(fig)


def category_performance_bar(video_df):
    """Horizontal bar chart showing average engagement by content category"""
    colors = get_theme_colors()
    category_performance = video_df.groupby('category').agg({
        'engagement_rate': 'mean',
        'view_count': 'mean',
        'title': 'count'
    }).round(2).reset_index()
    category_performance.rename(columns={'title': 'video_count'}, inplace=True)
    category_performance = category_performance.sort_values('engagement_rate', ascending=True)

    fig = px.bar(
        category_performance,
        x='engagement_rate',
        y='category',
        orientation='h',
        title='Average Engagement Rate by Content Category',
        labels={'engagement_rate': 'Avg Engagement Rate (%)', 'category': 'Category'},
        color='engagement_rate',
        color_continuous_scale=[[0, colors['accent_blue']], [1, colors['accent_purple']]],
        hover_data=['view_count', 'video_count']
    )
    return _apply_yt_studio_layout(fig)


def category_distribution_pie(video_df):
    """Donut chart showing distribution of videos across categories"""
    colors = get_theme_colors()
    is_dark = st.session_state.get('theme', 'dark') == 'dark'
    palette = DONUT_PALETTE if is_dark else DONUT_PALETTE_LIGHT

    category_counts = video_df['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']

    fig = px.pie(
        category_counts,
        values='count',
        names='category',
        title='Content Category Distribution',
        hole=0.55,
        color_discrete_sequence=palette
    )
    fig.update_traces(textposition='inside', textinfo='percent+label',
                      marker=dict(line=dict(color=colors['bg_card'], width=2)))
    return _apply_yt_studio_layout(fig)


def engagement_over_time_line(video_df):
    """Line chart with rolling average showing engagement trend"""
    colors = get_theme_colors()
    df = video_df.sort_values('publish_date')
    df['rolling_avg'] = df['engagement_rate'].rolling(window=5, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['publish_date'], y=df['engagement_rate'],
        mode='markers', name='Individual Videos',
        marker=dict(size=7, opacity=0.65, color=colors['accent_teal']),
        hovertext=df['title']
    ))
    fig.add_trace(go.Scatter(
        x=df['publish_date'], y=df['rolling_avg'],
        mode='lines', name='5-Video Rolling Avg',
        line=dict(color=colors['accent_purple'], width=3)
    ))
    fig.update_layout(
        title='Engagement Rate Over Time',
        xaxis_title='Publish Date', yaxis_title='Engagement Rate (%)',
        hovermode='x unified'
    )
    return _apply_yt_studio_layout(fig)


def views_over_time_line(video_df):
    """Combined bar + line chart for view count trend"""
    colors = get_theme_colors()
    df = video_df.sort_values('publish_date')
    df['rolling_avg'] = df['view_count'].rolling(window=5, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['publish_date'], y=df['view_count'],
        name='Views per Video', marker_color=colors['chart_bar'],
        hovertext=df['title']
    ))
    fig.add_trace(go.Scatter(
        x=df['publish_date'], y=df['rolling_avg'],
        mode='lines', name='5-Video Rolling Avg',
        line=dict(color=colors['accent_purple'], width=3)
    ))
    fig.update_layout(
        title='View Count Over Time',
        xaxis_title='Publish Date', yaxis_title='Views',
        hovermode='x unified'
    )
    return _apply_yt_studio_layout(fig)


def posting_frequency_chart(video_df):
    """Monthly posting frequency bar chart"""
    colors = get_theme_colors()
    df = video_df.copy()
    df['month'] = df['publish_date'].dt.to_period('M').astype(str)
    monthly_counts = df.groupby('month').size().reset_index(name='video_count')

    fig = px.bar(
        monthly_counts, x='month', y='video_count',
        title='Posting Frequency (Videos per Month)',
        labels={'month': 'Month', 'video_count': 'Number of Videos'},
        color_discrete_sequence=[colors['accent_blue']]
    )
    fig.update_layout(xaxis_tickangle=-45)
    return _apply_yt_studio_layout(fig)


def optimal_posting_heatmap(video_df):
    """Heatmap showing avg engagement by day of week and hour"""
    colors = get_theme_colors()
    is_dark = st.session_state.get('theme', 'dark') == 'dark'

    df = video_df.copy()
    df['day_of_week'] = df['publish_date'].dt.day_name()
    df['hour'] = df['publish_date'].dt.hour

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = df.pivot_table(values='engagement_rate', index='day_of_week', columns='hour', aggfunc='mean')
    existing_days = [d for d in day_order if d in pivot.index]
    pivot = pivot.reindex(existing_days)

    # Different color scale for light/dark mode
    if is_dark:
        color_scale = [[0, '#1a1a2e'], [0.5, colors['accent_purple']], [1, colors['accent_teal']]]
    else:
        color_scale = [[0, '#e0e7ff'], [0.5, colors['accent_purple']], [1, colors['accent_teal']]]

    fig = px.imshow(
        pivot,
        title='Optimal Posting Times (Avg Engagement Rate)',
        labels=dict(x='Hour of Day', y='Day of Week', color='Engagement %'),
        color_continuous_scale=color_scale,
        aspect='auto'
    )
    return _apply_yt_studio_layout(fig)


def multi_channel_comparison_bar(comparison_df, metric, title, ylabel):
    """Bar chart comparing a metric across channels"""
    colors = get_theme_colors()
    fig = px.bar(
        comparison_df, x='title', y=metric,
        title=title, labels={metric: ylabel, 'title': 'Channel'},
        color=metric,
        color_continuous_scale=[[0, colors['accent_blue']], [1, colors['accent_purple']]]
    )
    return _apply_yt_studio_layout(fig)


def growth_forecast_chart(forecast_data):
    """Line chart showing predicted engagement growth"""
    colors = get_theme_colors()
    if not forecast_data.get('forecast'):
        return None

    dates, values = zip(*forecast_data['forecast'])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(dates), y=list(values),
        mode='lines+markers', name='Predicted Engagement',
        line=dict(color=colors['accent_teal'], dash='dash', width=3),
        marker=dict(size=5)
    ))
    fig.update_layout(
        title=f'Engagement Forecast (Confidence: {forecast_data.get("confidence", "N/A")})',
        xaxis_title='Date', yaxis_title='Predicted Engagement Rate (%)',
        hovermode='x unified'
    )
    return _apply_yt_studio_layout(fig)
