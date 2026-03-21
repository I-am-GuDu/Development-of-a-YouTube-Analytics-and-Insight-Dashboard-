"""
Streamlit Dashboard Module
Interactive visualizations and UI components for YouTube Analytics
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
)
from .filters import video_search_filter, channel_search_sidebar