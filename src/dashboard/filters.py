"""
Dashboard Filters Module
Search and filter UI components for YouTube Analytics
"""
import streamlit as st
import pandas as pd


def video_search_filter(video_df):
    """Render search and filter controls, return filtered DataFrame"""
    st.subheader("Search & Filter Videos")

    col1, col2 = st.columns(2)

    with col1:
        search_query = st.text_input(
            "Search by video title:",
            placeholder="Enter keywords...",
            key="video_search"
        )

    with col2:
        sort_metric = st.selectbox(
            "Sort by:",
            options=['view_count', 'like_count', 'comment_count', 'engagement_rate', 'publish_date'],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="sort_metric"
        )

    col3, col4, col5 = st.columns(3)

    with col3:
        min_views = st.number_input("Min Views:", min_value=0, value=0, step=1000, key="min_views")

    with col4:
        min_engagement = st.slider(
            "Min Engagement Rate (%):",
            min_value=0.0,
            max_value=float(video_df['engagement_rate'].max()) if not video_df.empty else 100.0,
            value=0.0, step=0.1, key="min_engagement"
        )

    with col5:
        if 'category' in video_df.columns:
            categories = ['All'] + sorted(video_df['category'].unique().tolist())
            selected_category = st.selectbox("Category:", options=categories, key="category_filter")
        else:
            selected_category = 'All'

    # Date range filter
    if not video_df.empty:
        col6, col7 = st.columns(2)
        min_date = video_df['publish_date'].min().date()
        max_date = video_df['publish_date'].max().date()
        with col6:
            start_date = st.date_input("From date:", value=min_date, min_value=min_date, max_value=max_date, key="start_date")
        with col7:
            end_date = st.date_input("To date:", value=max_date, min_value=min_date, max_value=max_date, key="end_date")
    else:
        start_date = None
        end_date = None

    # Apply filters
    filtered_df = video_df.copy()

    if search_query:
        filtered_df = filtered_df[
            filtered_df['title'].str.contains(search_query, case=False, na=False)
        ]

    if min_views > 0:
        filtered_df = filtered_df[filtered_df['view_count'] >= min_views]

    if min_engagement > 0:
        filtered_df = filtered_df[filtered_df['engagement_rate'] >= min_engagement]

    if selected_category != 'All' and 'category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['category'] == selected_category]

    if start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df['publish_date'].dt.date >= start_date) &
            (filtered_df['publish_date'].dt.date <= end_date)
        ]

    # Sort
    ascending = sort_metric == 'publish_date'
    filtered_df = filtered_df.sort_values(sort_metric, ascending=ascending)

    st.caption(f"Showing {len(filtered_df)} of {len(video_df)} videos")

    return filtered_df


def channel_search_sidebar():
    """Sidebar component for channel ID/username input"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Channel Lookup")
    quick_channel = st.sidebar.text_input(
        "Channel ID or @Username:",
        placeholder="@MrBeast",
        key="sidebar_channel"
    )
    return quick_channel