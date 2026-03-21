"""
Dashboard Charts Module
Reusable Plotly visualization functions for YouTube Analytics
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def _apply_neo_layout(fig):
    """Apply a consistent modern dark-glass visual style to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(12, 20, 40, 0.55)",
        font=dict(color="#e8efff"),
        title=dict(font=dict(size=20, color="#f5f8ff")),
        margin=dict(l=24, r=24, t=68, b=28),
        legend=dict(
            bgcolor="rgba(12, 20, 40, 0.45)",
            bordercolor="rgba(255,255,255,0.12)",
            borderwidth=1
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.09)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.09)", zeroline=False)
    return fig


def engagement_distribution_chart(video_df):
    """Histogram of engagement rate distribution across videos"""
    fig = px.histogram(
        video_df,
        x='engagement_rate',
        nbins=20,
        title='Distribution of Engagement Rates',
        labels={'engagement_rate': 'Engagement Rate (%)', 'count': 'Number of Videos'},
        color_discrete_sequence=['#22d3ee']
    )
    fig.update_layout(bargap=0.1)
    return _apply_neo_layout(fig)


def views_vs_likes_scatter(video_df, top_n=20):
    """Scatter plot showing relationship between views and likes"""
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
        color_continuous_scale='Turbo'
    )
    return _apply_neo_layout(fig)


def category_performance_bar(video_df):
    """Horizontal bar chart showing average engagement by content category"""
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
        color_continuous_scale='Turbo',
        hover_data=['view_count', 'video_count']
    )
    return _apply_neo_layout(fig)


def category_distribution_pie(video_df):
    """Donut chart showing distribution of videos across categories"""
    category_counts = video_df['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']

    fig = px.pie(
        category_counts,
        values='count',
        names='category',
        title='Content Category Distribution',
        hole=0.5,
        color_discrete_sequence=px.colors.sequential.Plasma_r
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return _apply_neo_layout(fig)


def engagement_over_time_line(video_df):
    """Line chart with rolling average showing engagement trend"""
    df = video_df.sort_values('publish_date')
    df['rolling_avg'] = df['engagement_rate'].rolling(window=5, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['publish_date'], y=df['engagement_rate'],
        mode='markers', name='Individual Videos',
        marker=dict(size=7, opacity=0.65, color="#22d3ee"), hovertext=df['title']
    ))
    fig.add_trace(go.Scatter(
        x=df['publish_date'], y=df['rolling_avg'],
        mode='lines', name='5-Video Rolling Avg',
        line=dict(color='#a78bfa', width=3)
    ))
    fig.update_layout(
        title='Engagement Rate Over Time',
        xaxis_title='Publish Date', yaxis_title='Engagement Rate (%)',
        hovermode='x unified'
    )
    return _apply_neo_layout(fig)


def views_over_time_line(video_df):
    """Combined bar + line chart for view count trend"""
    df = video_df.sort_values('publish_date')
    df['rolling_avg'] = df['view_count'].rolling(window=5, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['publish_date'], y=df['view_count'],
        name='Views per Video', marker_color='rgba(34, 211, 238, 0.55)',
        hovertext=df['title']
    ))
    fig.add_trace(go.Scatter(
        x=df['publish_date'], y=df['rolling_avg'],
        mode='lines', name='5-Video Rolling Avg',
        line=dict(color='#a78bfa', width=3)
    ))
    fig.update_layout(
        title='View Count Over Time',
        xaxis_title='Publish Date', yaxis_title='Views',
        hovermode='x unified'
    )
    return _apply_neo_layout(fig)


def posting_frequency_chart(video_df):
    """Monthly posting frequency bar chart"""
    df = video_df.copy()
    df['month'] = df['publish_date'].dt.to_period('M').astype(str)
    monthly_counts = df.groupby('month').size().reset_index(name='video_count')

    fig = px.bar(
        monthly_counts, x='month', y='video_count',
        title='Posting Frequency (Videos per Month)',
        labels={'month': 'Month', 'video_count': 'Number of Videos'},
        color_discrete_sequence=['#60a5fa']
    )
    fig.update_layout(xaxis_tickangle=-45)
    return _apply_neo_layout(fig)


def optimal_posting_heatmap(video_df):
    """Heatmap showing avg engagement by day of week and hour"""
    df = video_df.copy()
    df['day_of_week'] = df['publish_date'].dt.day_name()
    df['hour'] = df['publish_date'].dt.hour

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = df.pivot_table(values='engagement_rate', index='day_of_week', columns='hour', aggfunc='mean')
    existing_days = [d for d in day_order if d in pivot.index]
    pivot = pivot.reindex(existing_days)

    fig = px.imshow(
        pivot,
        title='Optimal Posting Times (Avg Engagement Rate)',
        labels=dict(x='Hour of Day', y='Day of Week', color='Engagement %'),
        color_continuous_scale='Turbo', aspect='auto'
    )
    return _apply_neo_layout(fig)


def multi_channel_comparison_bar(comparison_df, metric, title, ylabel):
    """Bar chart comparing a metric across channels"""
    fig = px.bar(
        comparison_df, x='title', y=metric,
        title=title, labels={metric: ylabel, 'title': 'Channel'},
        color=metric, color_continuous_scale='Turbo'
    )
    return _apply_neo_layout(fig)


def growth_forecast_chart(forecast_data):
    """Line chart showing predicted engagement growth"""
    if not forecast_data.get('forecast'):
        return None

    dates, values = zip(*forecast_data['forecast'])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(dates), y=list(values),
        mode='lines+markers', name='Predicted Engagement',
        line=dict(color='#22d3ee', dash='dash', width=3), marker=dict(size=5)
    ))
    fig.update_layout(
        title=f'Engagement Forecast (Confidence: {forecast_data.get("confidence", "N/A")})',
        xaxis_title='Date', yaxis_title='Predicted Engagement Rate (%)',
        hovermode='x unified'
    )
    return _apply_neo_layout(fig)
