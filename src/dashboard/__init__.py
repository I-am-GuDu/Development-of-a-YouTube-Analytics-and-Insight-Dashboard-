"""
Streamlit Dashboard Module
Interactive visualizations and UI components for YouTube Analytics
YouTube Studio-style dark theme
"""
from .charts import (
    engagement_distribution_chart,
    views_vs_likes_scatter,
    category_performance_bar,
    category_distribution_pie,
    engagement_over_time_line,
    views_over_time_line,
    posting_frequency_chart,
    optimal_posting_heatmap,
    multi_channel_comparison_bar,
    growth_forecast_chart,
    views_area_chart,
    traffic_sources_donut,
    impressions_funnel,
    sentiment_donut,
    sentiment_by_video_bar,
)
from .filters import video_search_filter, channel_search_sidebar