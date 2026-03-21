"""
YouTube Data Analysis Tool
Main Application Entry Point
"""
import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from youtube_data_collection.api_handler import YouTubeAPIHandler
from youtube_data_collection.data_processor import DataProcessor
from datetime import datetime
from data_storage.storage_service import DataStorageService
from dashboard import charts, filters

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


def inject_neo_dashboard_styles():
    """Apply a modern glassmorphism-inspired UI theme across the Streamlit app."""
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(1200px 600px at 0% 0%, rgba(124, 58, 237, 0.20), transparent 55%),
                    radial-gradient(900px 500px at 100% 0%, rgba(14, 165, 233, 0.16), transparent 50%),
                    linear-gradient(135deg, #0a1022 0%, #0e1630 50%, #0a1022 100%);
                color: #f4f7ff;
            }

            .block-container {
                padding-top: 2rem !important;
                padding-bottom: 2rem !important;
                max-width: 1200px;
            }

            .neo-hero {
                background: linear-gradient(120deg, rgba(32, 42, 78, 0.85), rgba(60, 43, 118, 0.78));
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 18px;
                padding: 1.1rem 1.3rem;
                margin-bottom: 1rem;
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
                backdrop-filter: blur(8px);
            }

            .neo-title {
                margin: 0;
                color: #f8fbff;
                font-size: 2rem;
                font-weight: 800;
                letter-spacing: 0.2px;
            }

            .neo-subtitle {
                margin-top: 0.35rem;
                color: #c9d8ff;
                font-size: 0.98rem;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(165deg, rgba(10, 18, 38, 0.95), rgba(22, 30, 56, 0.95));
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }

            [data-testid="stMetric"] {
                background: linear-gradient(145deg, rgba(30, 41, 80, 0.68), rgba(23, 30, 61, 0.66));
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 14px;
                padding: 0.75rem 0.9rem;
                box-shadow: 0 10px 24px rgba(0, 0, 0, 0.26);
            }

            [data-testid="stMetricLabel"] {
                color: #c9d8ff;
                font-weight: 600;
            }

            [data-testid="stMetricValue"] {
                color: #ffffff;
                font-weight: 750;
            }

            .stTabs [data-baseweb="tab-list"] {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 0.22rem;
            }

            .stTabs [data-baseweb="tab"] {
                border-radius: 10px;
            }

            .stTabs [aria-selected="true"] {
                background: linear-gradient(120deg, rgba(124, 58, 237, 0.7), rgba(14, 165, 233, 0.7));
                color: #ffffff !important;
            }

            .stButton > button {
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                font-weight: 600;
                padding: 0.45rem 1rem;
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.22);
            }

            .stButton > button[kind="primary"] {
                background: linear-gradient(120deg, #7c3aed, #0ea5e9);
                color: #ffffff;
            }

            [data-testid="stDataFrame"], [data-testid="stTable"] {
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                overflow: hidden;
            }

            .stAlert {
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.13);
            }
        </style>
        """,
        unsafe_allow_html=True
    )


def categorize_title(title: str) -> str:
    title_lower = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return 'General'


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
        raise ValueError("Invalid format. Use channel ID (UC...) or username (@...)")

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
        storage_service.save_analytics_summary(processed_channel['channel_id'], engagement_metrics)
        return True, "Data saved to database successfully!"
    except Exception as e:
        return False, f"Could not save to database: {str(e)}"


def render_channel_info(processed_channel):
    """Display channel overview cards"""
    st.subheader("Channel Information")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(processed_channel['thumbnail_url'], width=150)
    with col2:
        st.markdown(f"### {processed_channel['title']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Subscribers", f"{processed_channel['subscriber_count']:,}")
        c2.metric("Total Views", f"{processed_channel['view_count']:,}")
        c3.metric("Videos", f"{processed_channel['video_count']:,}")


def render_kpi_cards(metrics):
    """Display engagement KPI metric cards"""
    st.subheader("Engagement Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Views/Video", f"{metrics.get('avg_views_per_video', 0):,.0f}")
        st.metric("Avg Likes/Video", f"{metrics.get('avg_likes_per_video', 0):,.0f}")
    with col2:
        st.metric("Avg Engagement Rate", f"{metrics.get('avg_engagement_rate', 0):.2f}%")
        st.metric("Total Reach", f"{metrics.get('total_potential_reach', 0):,}")
    with col3:
        st.metric("Videos (Last 30 Days)", f"{metrics.get('video_growth_trend', 0)}")
        st.metric("Efficiency", f"{metrics.get('engagement_efficiency', 0):.2f}%")


def page_channel_overview():
    """Page: Single Channel Analysis with full dashboard"""
    st.header("📊 Channel Overview")

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or api_key == "your_actual_api_key_here":
        st.error("YouTube API Key not configured! Set YOUTUBE_API_KEY in .env file")
        return

    channel_input = st.text_input(
        "Enter YouTube Channel ID or @Username:",
        placeholder="Example: UC_x5XG1OV2P6uZZ5FSM9Ttw or @ShopiDevs"
    )

    if st.button("Analyze Channel", type="primary"):
        if not channel_input.strip():
            st.error("Please enter a valid YouTube Channel ID or @Username")
            return

        try:
            with st.spinner("Fetching channel data from YouTube..."):
                processed_channel, video_df, engagement_metrics = fetch_channel_data(api_key, channel_input)

            # Save to DB
            success, msg = save_to_database(processed_channel, video_df, engagement_metrics)
            if success:
                st.success(msg)
            else:
                st.warning(msg)

            # Store in session state for other pages
            st.session_state['channel_data'] = processed_channel
            st.session_state['video_df'] = video_df
            st.session_state['engagement_metrics'] = engagement_metrics

            # Render dashboard
            render_channel_info(processed_channel)
            render_kpi_cards(engagement_metrics)

            # Tabbed visualizations
            tab1, tab2, tab3 = st.tabs(["📈 Engagement", "👁️ Views", "📁 Categories"])

            with tab1:
                st.plotly_chart(charts.engagement_distribution_chart(video_df), width='stretch')
                st.plotly_chart(charts.views_vs_likes_scatter(video_df), width='stretch')

            with tab2:
                st.plotly_chart(charts.views_over_time_line(video_df), width='stretch')
                st.plotly_chart(charts.posting_frequency_chart(video_df), width='stretch')

            with tab3:
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(charts.category_performance_bar(video_df), width='stretch')
                with col2:
                    st.plotly_chart(charts.category_distribution_pie(video_df), width='stretch')

            # Top videos
            st.subheader("🏆 Top Performing Videos")
            top_df = video_df.nlargest(5, 'view_count')
            for _, video in top_df.iterrows():
                with st.container():
                    st.markdown(f"**{video['title']}**")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Views", f"{video['view_count']:,}")
                    c2.metric("Likes", f"{video['like_count']:,}")
                    c3.metric("Comments", f"{video['comment_count']:,}")
                    c4.metric("Engagement", f"{video['engagement_rate']:.2f}%")
                    st.divider()

        except ValueError as ve:
            st.error(f"Error: {str(ve)}")
        except Exception as e:
            st.error(f"Failed to fetch data: {str(e)}")


def page_video_explorer():
    """Page: Search, filter, and explore individual videos"""
    st.header("🔍 Video Explorer")

    if 'video_df' not in st.session_state:
        st.info("Please analyze a channel first from the **Channel Overview** page.")
        return

    video_df = st.session_state['video_df']
    channel_data = st.session_state.get('channel_data', {})

    st.markdown(f"Exploring videos from **{channel_data.get('title', 'Unknown Channel')}**")

    # Search & Filter UI
    filtered_df = filters.video_search_filter(video_df)

    if filtered_df.empty:
        st.warning("No videos match your filters.")
        return

    # Display results as interactive table
    st.subheader("Video Results")
    display_df = filtered_df[['title', 'view_count', 'like_count', 'comment_count', 'engagement_rate', 'category', 'publish_date']].copy()
    display_df['publish_date'] = display_df['publish_date'].dt.strftime('%Y-%m-%d')
    display_df.columns = ['Title', 'Views', 'Likes', 'Comments', 'Engagement %', 'Category', 'Published']

    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        column_config={
            "Views": st.column_config.NumberColumn(format="%d"),
            "Likes": st.column_config.NumberColumn(format="%d"),
            "Comments": st.column_config.NumberColumn(format="%d"),
            "Engagement %": st.column_config.NumberColumn(format="%.2f%%"),
        }
    )

    # Summary stats of filtered results
    st.subheader("Filtered Results Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Videos", len(filtered_df))
    c2.metric("Avg Views", f"{filtered_df['view_count'].mean():,.0f}")
    c3.metric("Avg Engagement", f"{filtered_df['engagement_rate'].mean():.2f}%")
    c4.metric("Total Views", f"{filtered_df['view_count'].sum():,}")

    # Visualize filtered data
    st.plotly_chart(charts.views_vs_likes_scatter(filtered_df, top_n=len(filtered_df)), width='stretch')


def page_trend_analysis():
    """Page: Time-series trends, posting patterns, optimal times"""
    st.header("📈 Trend Analysis")

    if 'video_df' not in st.session_state:
        st.info("Please analyze a channel first from the **Channel Overview** page.")
        return

    video_df = st.session_state['video_df']
    channel_data = st.session_state.get('channel_data', {})

    st.markdown(f"Trends for **{channel_data.get('title', 'Unknown Channel')}**")

    tab1, tab2, tab3 = st.tabs(["📊 Engagement Trends", "📅 Posting Patterns", "🎯 Predictive Insights"])

    with tab1:
        st.plotly_chart(charts.engagement_over_time_line(video_df), width='stretch')
        st.plotly_chart(charts.views_over_time_line(video_df), width='stretch')

    with tab2:
        st.plotly_chart(charts.posting_frequency_chart(video_df), width='stretch')
        st.plotly_chart(charts.optimal_posting_heatmap(video_df), width='stretch')

    with tab3:
        st.subheader("Growth Forecast")
        try:
            storage_service = DataStorageService()
            predictive = storage_service.get_predictive_analytics()
            channel_id = channel_data.get('channel_id')

            if channel_id:
                forecast = predictive.forecast_channel_growth(channel_id, days_ahead=30)
                fig = charts.growth_forecast_chart(forecast)
                if fig:
                    st.plotly_chart(fig, width='stretch')
                    c1, c2 = st.columns(2)
                    c1.metric("Current Avg Engagement", f"{forecast.get('current_avg_engagement', 0):.2f}%")
                    c2.metric("Projected Avg Engagement", f"{forecast.get('projected_avg_engagement', 0):.2f}%")
                else:
                    st.info("Not enough data for growth forecasting (need at least 5 videos in database).")

                st.subheader("Content Strategy Recommendations")
                strategy = predictive.recommend_content_strategy(channel_id)
                for rec in strategy.get('recommendations', []):
                    if rec['type'] == 'content_type':
                        st.success(f"**Best Content Type:** {rec['category']} — {rec['reason']}")
                    elif rec['type'] == 'posting_time':
                        st.success(f"**Best Posting Time:** {rec['optimal_day']} at {rec['optimal_hour']}:00 — {rec['reason']}")

                if not strategy.get('recommendations'):
                    st.info("Not enough data to generate content strategy recommendations.")
        except Exception as e:
            st.warning(f"Predictive analytics unavailable: {str(e)}")


def page_multi_channel():
    """Page: Multi-channel comparison and competitive benchmarking"""
    st.header("⚔️ Multi-Channel Comparison")
    st.write("Compare multiple YouTube channels side by side")

    channel_ids_input = st.text_area(
        "Enter Channel IDs (one per line):",
        placeholder="UC_x5XG1OV2P6uZZ5FSM9Ttw\nUCanotherchannelid\n@username",
        height=120
    )

    if st.button("Compare Channels", type="primary"):
        if not channel_ids_input.strip():
            st.error("Please enter at least one channel ID")
            return

        channel_ids = [cid.strip() for cid in channel_ids_input.split('\n') if cid.strip()]

        if len(channel_ids) < 2:
            st.error("Please enter at least 2 channels for comparison")
            return

        try:
            with st.spinner("Analyzing channels..."):
                storage_service = DataStorageService()
                analytics = storage_service.get_analytics_queries()

                comparison_df = analytics.compare_multiple_channels(channel_ids)

                if comparison_df.empty:
                    st.warning("No data found. Please analyze these channels individually first.")
                    return

                # Comparison table
                st.subheader("Channel Comparison")
                st.dataframe(
                    comparison_df[['title', 'subscriber_count', 'view_count', 'video_count', 'avg_engagement_rate', 'engagement_efficiency']],
                    width='stretch', hide_index=True
                )

                # Charts
                tab1, tab2, tab3 = st.tabs(["📊 Metrics", "📁 Content Strategy", "🏆 Benchmarking"])

                with tab1:
                    st.plotly_chart(
                        charts.multi_channel_comparison_bar(comparison_df, 'avg_engagement_rate', 'Engagement Rate Comparison', 'Avg Engagement Rate (%)'),
                        width='stretch'
                    )
                    st.plotly_chart(
                        charts.multi_channel_comparison_bar(comparison_df, 'subscriber_count', 'Subscriber Count Comparison', 'Subscribers'),
                        width='stretch'
                    )

                with tab2:
                    strategy_df = analytics.get_content_strategy_comparison(channel_ids)
                    if not strategy_df.empty:
                        category_comparison = strategy_df.groupby(['channel_title', 'category']).size().unstack(fill_value=0)
                        st.write("**Content Category Distribution by Channel:**")
                        st.dataframe(category_comparison, width='stretch')
                    else:
                        st.info("No content strategy data available.")

                with tab3:
                    report = analytics.get_competitive_benchmarking_report(
                        primary_channel_id=channel_ids[0],
                        competitor_channel_ids=channel_ids[1:]
                    )

                    primary_title = report['primary_channel_metrics'].get('title', 'Primary Channel')
                    st.markdown(f"**Primary Channel:** {primary_title}")

                    if report['benchmarks'].get('avg_engagement_rate'):
                        st.metric("Benchmark Avg Engagement", f"{report['benchmarks']['avg_engagement_rate']:.2f}%")

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


def main():
    st.set_page_config(
        page_title="YouTube Analytics Dashboard",
        page_icon="📊",
        layout="wide"
    )
    inject_neo_dashboard_styles()

    st.markdown(
        """
        <div class="neo-hero">
            <h1 class="neo-title">📊 YouTube Analytics & Insight Dashboard</h1>
            <div class="neo-subtitle">Modern intelligence view for channel growth, engagement, and competitive strategy.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to:",
        ["Channel Overview", "Video Explorer", "Trend Analysis", "Multi-Channel Comparison"],
        label_visibility="collapsed"
    )

    # Show channel info in sidebar if loaded
    if 'channel_data' in st.session_state:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Active Channel:**")
        st.sidebar.markdown(f"{st.session_state['channel_data'].get('title', 'N/A')}")
        st.sidebar.caption(f"{st.session_state['channel_data'].get('subscriber_count', 0):,} subscribers")

    # Route to pages
    if page == "Channel Overview":
        page_channel_overview()
    elif page == "Video Explorer":
        page_video_explorer()
    elif page == "Trend Analysis":
        page_trend_analysis()
    elif page == "Multi-Channel Comparison":
        page_multi_channel()


if __name__ == "__main__":
    main()
