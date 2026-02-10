#!/usr/bin/env python3
"""
Comprehensive analytics testing with error handling and edge cases
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_storage.storage_service import DataStorageService

def test_analytics_for_channel(channel_id, channel_name):
    """Test analytics for a specific channel"""
    print(f"\n{'='*60}")
    print(f"Testing Analytics for: {channel_name}")
    print(f"Channel ID: {channel_id}")
    print(f"{'='*60}")
    
    try:
        storage = DataStorageService()
        analytics = storage.get_analytics_queries()
        
        # Test 1: Video Performance Over Time
        print("\n📊 Video Performance Over Time (Last 30 days)")
        trends = analytics.get_video_performance_over_time(channel_id, days_back=30)
        if not trends.empty:
            print(f"  ✅ Found {len(trends)} videos")
            print(f"  📈 Average views: {trends['view_count'].mean():.0f}")
            print(f"  👍 Average likes: {trends['like_count'].mean():.0f}")
            print(f"  💬 Average comments: {trends['comment_count'].mean():.0f}")
            print(f"  🎯 Average engagement: {trends['engagement_rate'].mean():.2f}%")
        else:
            print("  ⚠️  No videos found in the last 30 days")
        
        # Test 2: Engagement Trends
        print("\n📈 Engagement Trends (Last 90 days)")
        engagement_trends = analytics.get_engagement_trends(channel_id, days_back=90)
        if not engagement_trends.empty:
            print(f"  ✅ Found data for {len(engagement_trends)} weeks")
            print(f"  📊 Average weekly engagement: {engagement_trends['avg_engagement_rate'].mean():.2f}%")
            print(f"  📹 Average videos per week: {engagement_trends['videos_this_week'].mean():.1f}")
        else:
            print("  ⚠️  No engagement trend data available")
        
        # Test 3: Best Performing Content
        print("\n🏆 Best Performing Content")
        best_content = analytics.get_best_performing_content_types(channel_id)
        if not best_content.empty:
            print(f"  ✅ Found {len(best_content)} top videos")
            top_video = best_content.iloc[0]
            print(f"  🥇 Top video: {top_video['title'][:50]}...")
            print(f"     Views: {top_video['view_count']:,}")
            print(f"     Engagement: {top_video['engagement_rate']:.2f}%")
        else:
            print("  ⚠️  No content performance data available")
        
        # Test 4: Optimal Posting Times
        print("\n⏰ Optimal Posting Times")
        posting_times = analytics.get_optimal_posting_times(channel_id)
        if posting_times['best_day_hour']:
            best = posting_times['best_day_hour']
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            day_name = days[int(best['day_of_week'])]
            print(f"  ✅ Best posting time: {day_name} at {int(best['hour_of_day'])}:00")
            print(f"  📊 Average engagement at this time: {best['avg_engagement']:.2f}%")
            print(f"  📹 Videos posted at this time: {best['video_count']}")
        else:
            print("  ⚠️  No optimal posting time data available")
        
        # Test 5: Content Growth Trends
        print("\n📈 Content Growth Overview")
        growth = analytics.get_content_growth_trends(channel_id)
        if growth:
            print(f"  ✅ Total videos: {growth.get('total_videos', 0)}")
            print(f"  👀 Total channel views: {growth.get('total_channel_views', 0):,}")
            print(f"  📊 Average views per video: {growth.get('avg_views_per_video', 0):.0f}")
            print(f"  👍 Total channel likes: {growth.get('total_channel_likes', 0):,}")
            print(f"  🎯 Average engagement rate: {growth.get('avg_engagement_rate', 0):.2f}%")
            
            if growth.get('first_video_date') and growth.get('latest_video_date'):
                print(f"  📅 First video: {growth['first_video_date']}")
                print(f"  📅 Latest video: {growth['latest_video_date']}")
        else:
            print("  ⚠️  No growth data available")
        
        # Clean up
        storage.session.close()
        print(f"\n✅ Analytics testing completed for {channel_name}")
        
    except Exception as e:
        print(f"\n❌ Error testing analytics for {channel_name}: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Analytics Testing")
    
    # Test channels (add more as needed)
    test_channels = [
        ("UCxVjtTQJ1oFkQ3iGhOngU3g", "Techy Pathshala"),
        ("UCKnNrlSJF_hWoBSz1lY_D7g", "Another Channel")  # Replace with actual channel name
    ]
    
    for channel_id, channel_name in test_channels:
        test_analytics_for_channel(channel_id, channel_name)
    
    print(f"\n{'='*60}")
    print("🎉 All analytics tests completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()