import streamlit as st
import os
from dotenv import load_dotenv
from youtube_data_collection.api_handler import YouTubeAPIHandler
from youtube_data_collection.data_processor import DataProcessor
from datetime import datetime
from data_storage.storage_service import DataStorageService

# Load environment variables
load_dotenv()

def main():
    st.title("YouTube Channel Data Analyzer")
    st.write("Welcome to the YouTube Data Analysis Tool")
    
    # Get YouTube API key from environment variable
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or api_key == "your_actual_api_key_here":
        st.error("YouTube API Key not configured! Please set YOUTUBE_API_KEY in .env file")
        st.info("To get an API key: Go to Google Cloud Console → Enable YouTube Data API v3 → Create credentials")
        return
    
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
                    if 'created_at' not in processed_channel:
                        processed_channel['created_at'] = raw_channel_info['snippet']['publishedAt']
                    
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
                        storage_service = DataStorageService()  # Define here
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


if __name__ == "__main__":
    main()