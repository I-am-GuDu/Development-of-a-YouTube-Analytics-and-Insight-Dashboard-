"""
Streamlit Dashboard Module
Interactive visualizations and UI components for YouTube Analytics
YouTube Studio-style dark theme
"""
from .charts import (
    category_distribution_pie,
    category_performance_bar,
    engagement_distribution_chart,
    engagement_over_time_line,
    growth_forecast_chart,
    impressions_funnel,
    multi_channel_comparison_bar,
    optimal_posting_heatmap,
    posting_frequency_chart,
    sentiment_by_video_bar,
    sentiment_donut,
    traffic_sources_donut,
    views_area_chart,
    views_over_time_line,
    views_vs_likes_scatter,
)
from .filters import channel_search_sidebar, video_search_filter
