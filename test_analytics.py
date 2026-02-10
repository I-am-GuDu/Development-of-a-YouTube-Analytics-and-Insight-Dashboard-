#!/usr/bin/env python3
"""
Test analytics functionality
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_storage.storage_service import DataStorageService

# Initialize storage service
print("Initializing storage service...")
storage = DataStorageService()

# Get analytics queries object
analytics = storage.get_analytics_queries()

# Test with your channel ID
channel_id = "UCxVjtTQJ1oFkQ3iGhOngU3g"  # Techy Pathshala

try:
    # Test different analytics functions
    print("=== Video Performance Over Time ===")
    trends = analytics.get_video_performance_over_time(channel_id, days_back=30)
    print(f"Found {len(trends)} videos in last 30 days")
    if not trends.empty:
        print(f"Latest video: {trends.iloc[0]['title']}")
        print(f"Average views: {trends['view_count'].mean():.0f}")
    
    print("\n=== Engagement Trends ===")
    engagement_trends = analytics.get_engagement_trends(channel_id, days_back=90)
    print(f"Weekly engagement trends for {len(engagement_trends)} weeks")
    if not engagement_trends.empty:
        print(f"Average engagement rate: {engagement_trends['avg_engagement_rate'].mean():.2f}%")
    
    print("\n=== Optimal Posting Times ===")
    posting_times = analytics.get_optimal_posting_times(channel_id)
    if posting_times['best_day_hour']:
        best = posting_times['best_day_hour']
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_name = days[int(best['day_of_week'])]
        print(f"Best posting time: {day_name} at {int(best['hour_of_day'])}:00")
        print(f"Average engagement: {best['avg_engagement']:.2f}%")
    else:
        print("No optimal posting time data available")
    
    print("\n=== Content Growth ===")
    growth = analytics.get_content_growth_trends(channel_id)
    if growth:
        print(f"Total videos: {growth.get('total_videos', 0)}")
        print(f"Average views per video: {growth.get('avg_views_per_video', 0):.0f}")
        print(f"Total channel views: {growth.get('total_channel_views', 0):,}")
        print(f"Average engagement rate: {growth.get('avg_engagement_rate', 0):.2f}%")
    else:
        print("No growth data available")
        
except Exception as e:
    print(f"❌ Error during analytics testing: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Clean up
    if hasattr(storage, 'session'):
        storage.session.close()