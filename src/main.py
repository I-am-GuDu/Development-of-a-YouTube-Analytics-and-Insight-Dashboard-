"""
YouTube Data Analysis Tool
Main Application Entry Point
"""
import streamlit as st
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from youtube_data_collection.api_handler import YouTubeAPIHandler
from youtube_data_collection.data_processor import DataProcessor
from datetime import datetime
from data_storage.storage_service import DataStorageService

def main():
    st.title("YouTube Channel Data Analyzer")
    st.write("Welcome to the YouTube Data Analysis Tool")
    
    # Get YouTube API key from environment variable
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or api_key == "your_actual_api_key_here":
        st.error("YouTube API Key not configured! Please set YOUTUBE_API_KEY in .env file")
        st.info("To get an API key: Go to Google Cloud Console → Enable YouTube Data API v3 → Create credentials")
        return
    
    # Sidebar for navigation
    page = st.sidebar.selectbox("Choose Analysis Type", ["Single Channel Analysis", "Multi-Channel Comparison"])
    
    if page == "Single Channel Analysis":
        single_channel_analysis(api_key)
    elif page == "Multi-Channel Comparison":
        multi_channel_analysis()

def single_channel_analysis(api_key):
    st.header("Single Channel Analysis")
    
    # Input for YouTube channel ID
    channel_id = st.text_input("Enter YouTube Channel ID or @Username:", placeholder="Example: UC_x5XG1OV2P6uZZ5FSM9Ttw or @ShopiDevs")
    
    if st.button("Analyze Channel"):
        if not channel_id.strip():
            st.error("Please enter a valid YouTube Channel ID or @Username")
        else:
            try:
                with st.spinner("Fetching and processing channel data..."):
                    handler = YouTubeAPIHandler()
                    processor = DataProcessor()
                    
                    # Determine input type and get channel info accordingly
                    input_text = channel_id.strip()
                    
                    if input_text.startswith('@'):
                        # Handle @username format
                        raw_channel_info = handler.get_channel_by_username(input_text)
                    elif input_text.startswith('UC') and len(input_text) == 24:
                        # Handle standard channel ID format
                        raw_channel_info = handler.get_channel_details(input_text)
                    else:
                        # Invalid format
                        st.error("Invalid format. Use channel ID (UC...) or username (@...)")
                        return
                    
                    # Process channel data
                    processed_channel = processor.process_channel_data(raw_channel_info)
                    
                    # Get video details
                    upload_playlist_id = raw_channel_info['contentDetails']['relatedPlaylists']['uploads']
                    raw_videos = handler.get_channel_videos(upload_playlist_id, max_results=50)
                    video_ids = [video['video_id'] for video in raw_videos]
                    
                    # Get detailed stats for videos
                    raw_video_details = handler.get_video_details(video_ids)
                    
                    # Process video data
                    video_df = processor.process_video_data(raw_video_details)
                    
                    # Calculate engagement metrics
                    engagement_metrics = processor.calculate_engagement_metrics(video_df)
                    
                    # DATABASE INTEGRATION: Save processed data to PostgreSQL
                    try:
                        storage_service = DataStorageService()
                        storage_service.save_channel_data(processed_channel)
                        
                        # Add channel_id to video dataframe
                        video_df['channel_id'] = processed_channel['channel_id']
                        storage_service.save_video_data(video_df)
                        storage_service.save_analytics_summary(processed_channel['channel_id'], engagement_metrics)
                        
                        st.success("Data saved to database successfully!")
                        
                    except Exception as db_error:
                        st.warning(f"Warning: Could not save data to database: {str(db_error)}")
                    
                    # Display processed results
                    st.subheader("Channel Information")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.image(processed_channel['thumbnail_url'], width=200)
                    
                    with col2:
                        st.write(f"**Title:** {processed_channel['title']}")
                        st.write(f"**Subscribers:** {processed_channel['subscriber_count']:,}")
                        st.write(f"**Total Views:** {processed_channel['view_count']:,}")
                        st.write(f"**Video Count:** {processed_channel['video_count']:,}")
                        st.write(f"**Crawled:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Display engagement metrics
                    st.subheader("Engagement Metrics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Avg Views/Video", f"{engagement_metrics.get('avg_views_per_video', 0):,.0f}")
                        st.metric("Avg Likes/Video", f"{engagement_metrics.get('avg_likes_per_video', 0):,.0f}")
                    with col2:
                        st.metric("Avg Engagement Rate", f"{engagement_metrics.get('avg_engagement_rate', 0):.2f}%")
                        st.metric("Total Reach", f"{engagement_metrics.get('total_potential_reach', 0):,}")
                    with col3:
                        st.metric("Videos This Month", f"{engagement_metrics.get('video_growth_trend', 0)}")
                        st.metric("Efficiency", f"{engagement_metrics.get('engagement_efficiency', 0):.2f}%")
                    
                    # Visualizations
                    st.subheader("Performance Visualizations")
                    
                    # Engagement Rate Distribution
                    fig_engagement = px.histogram(
                        video_df, 
                        x='engagement_rate', 
                        title='Distribution of Engagement Rates',
                        labels={'engagement_rate': 'Engagement Rate (%)'}
                    )
                    st.plotly_chart(fig_engagement, use_container_width=True)
                    
                    # Views vs Likes Scatter Plot
                    fig_scatter = px.scatter(
                        video_df.head(20), 
                        x='view_count', 
                        y='like_count', 
                        hover_data=['title'],
                        title='Views vs Likes Relationship (Top 20 Videos)'
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    # Content Category Analysis
                    st.subheader("Content Category Analysis")
                    
                    # Simulate content categorization (since we don't have real categories yet)
                    category_keywords = {
                        'Tech Reviews': ['review', 'unbox', 'test', 'spec', 'performance'],
                        'Product Comparisons': ['vs', 'versus', 'comparison', 'battle', 'faceoff'],
                        'News Updates': ['news', 'update', 'leak', 'rumor', 'announcement'],
                        'Tutorials': ['how to', 'tutorial', 'guide', 'tips', 'tricks'],
                        'Unboxings': ['unboxing', 'unpack', 'first look'],
                        'Price Analysis': ['price', 'cost', 'affordable', 'expensive', 'deal'],
                        'Software Updates': ['update', 'android', 'software', 'features'],
                        'Accessories': ['accessory', 'gadget', 'must have', 'buy', 'recommend']
                    }
                    
                    def categorize_title(title: str) -> str:
                        title_lower = title.lower()
                        for category, keywords in category_keywords.items():
                            if any(keyword in title_lower for keyword in keywords):
                                return category
                        return 'General'
                    
                    video_df['category'] = video_df['title'].apply(categorize_title)
                    category_performance = video_df.groupby('category').agg({
                        'engagement_rate': 'mean',
                        'view_count': 'mean'
                    }).round(2).reset_index()
                    
                    fig_category = px.bar(
                        category_performance,
                        x='category',
                        y='engagement_rate',
                        title='Average Engagement Rate by Content Category',
                        labels={'engagement_rate': 'Avg Engagement Rate (%)', 'category': 'Content Category'}
                    )
                    st.plotly_chart(fig_category, use_container_width=True)
                    
                    # Display top performing videos
                    st.subheader("Top Performing Videos")
                    top_videos = processor.filter_top_performing_videos(video_df, 'view_count', 5)
                    
                    for _, video in top_videos.iterrows():
                        st.write(f"**{video['title']}**")
                        st.write(f"Views: {video['view_count']:,} | Likes: {video['like_count']:,} | Engagement: {video['engagement_rate']:.2f}%")
                        st.write(f"Published: {video['publish_date'].strftime('%Y-%m-%d')}")
                        st.divider()
                    
            except ValueError as ve:
                st.error(f"Error: {str(ve)}")
            except Exception as e:
                st.error(f"Failed to fetch data: {str(e)}")

def multi_channel_analysis():
    st.header("Multi-Channel Comparison")
    
    st.write("Compare multiple YouTube channels simultaneously")
    
    # Input for multiple channel IDs
    channel_ids_input = st.text_area(
        "Enter multiple Channel IDs (one per line):",
        placeholder="Example:\nUC_x5XG1OV2P6uZZ5FSM9Ttw\nUCanotherchannelid\n@username"
    )
    
    if st.button("Compare Channels"):
        if not channel_ids_input.strip():
            st.error("Please enter at least one channel ID")
        else:
            try:
                channel_ids = [cid.strip() for cid in channel_ids_input.split('\n') if cid.strip()]
                
                if len(channel_ids) < 2:
                    st.error("Please enter at least 2 channels for comparison")
                    return
                
                with st.spinner("Analyzing channels..."):
                    storage_service = DataStorageService()
                    analytics = storage_service.get_analytics_queries()
                    
                    # Get multi-channel comparison
                    comparison_df = analytics.compare_multiple_channels(channel_ids)
                    
                    if comparison_df.empty:
                        st.warning("No data found for the specified channels. Please analyze these channels first.")
                        return
                    
                    st.subheader("Channel Comparison")
                    st.dataframe(comparison_df[['title', 'subscriber_count', 'avg_engagement_rate', 'engagement_efficiency']], use_container_width=True)
                    
                    # Visualization: Engagement Rate Comparison
                    fig_comparison = px.bar(
                        comparison_df,
                        x='title',
                        y='avg_engagement_rate',
                        title='Average Engagement Rate Comparison',
                        labels={'avg_engagement_rate': 'Avg Engagement Rate (%)', 'title': 'Channel'},
                        color='avg_engagement_rate'
                    )
                    st.plotly_chart(fig_comparison, use_container_width=True)
                    
                    # Visualization: Subscriber Count Comparison
                    fig_subs = px.bar(
                        comparison_df,
                        x='title',
                        y='subscriber_count',
                        title='Subscriber Count Comparison',
                        labels={'subscriber_count': 'Subscribers', 'title': 'Channel'},
                        color='subscriber_count'
                    )
                    st.plotly_chart(fig_subs, use_container_width=True)
                    
                    # Content Strategy Comparison
                    st.subheader("Content Strategy Comparison")
                    strategy_df = analytics.get_content_strategy_comparison(channel_ids)
                    
                    if not strategy_df.empty:
                        category_comparison = strategy_df.groupby(['channel_title', 'category']).size().unstack(fill_value=0)
                        st.write("Content Category Distribution by Channel:")
                        st.dataframe(category_comparison, use_container_width=True)
                    
                    # Competitive Analysis
                    st.subheader("Competitive Benchmarking")
                    report = analytics.get_competitive_benchmarking_report(
                        primary_channel_id=channel_ids[0],
                        competitor_channel_ids=channel_ids[1:]
                    )
                    
                    st.write(f"**Primary Channel:** {report['primary_channel_metrics'].get('title', 'N/A')}")
                    st.write(f"**Benchmark Average Engagement:** {report['benchmarks']['avg_engagement_rate']:.2f}%")
                    
                    if report['advantages']:
                        st.success("**Strengths:**")
                        for advantage in report['advantages']:
                            st.write(f"- {advantage}")
                    
                    if report['disadvantages']:
                        st.error("**Areas for Improvement:**")
                        for disadvantage in report['disadvantages']:
                            st.write(f"- {disadvantage}")
                    
            except Exception as e:
                st.error(f"Failed to compare channels: {str(e)}")

if __name__ == "__main__":
    main()