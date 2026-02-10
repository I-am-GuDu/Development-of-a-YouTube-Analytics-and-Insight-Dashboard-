"""
Historical Trend Analysis Queries
Provides analytical functions for time-series data and performance trends
"""
from sqlalchemy import text
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class AnalyticsQueries:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_video_performance_over_time(self, channel_id: str, days_back: int = 90) -> pd.DataFrame:
        """
        Get video performance metrics over time period
        """
        query = text("""
            SELECT 
                video_id,
                title,
                publish_date,
                view_count,
                like_count,
                comment_count,
                engagement_rate
            FROM videos 
            WHERE channel_id = :channel_id 
                AND publish_date >= :start_date
            ORDER BY publish_date DESC
        """)
        
        start_date = datetime.now() - timedelta(days=days_back)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(
                query, 
                conn, 
                params={'channel_id': channel_id, 'start_date': start_date}
            )
        
        return df
    
    def get_posting_frequency_trends(self, channel_id: str, days_back: int = 90) -> pd.DataFrame:
        """
        Analyze posting frequency patterns (videos per day/week/month)
        """
        query = text("""
            SELECT 
                DATE_TRUNC('day', publish_date) as date,
                COUNT(*) as videos_per_day
            FROM videos 
            WHERE channel_id = :channel_id 
                AND publish_date >= :start_date
            GROUP BY DATE_TRUNC('day', publish_date)
            ORDER BY date DESC
        """)
        
        start_date = datetime.now() - timedelta(days=days_back)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(
                query, 
                conn, 
                params={'channel_id': channel_id, 'start_date': start_date}
            )
        
        return df
    
    def get_engagement_trends(self, channel_id: str, days_back: int = 90) -> pd.DataFrame:
        """
        Analyze engagement rate trends over time
        """
        query = text("""
            SELECT 
                DATE_TRUNC('week', publish_date) as week,
                AVG(engagement_rate) as avg_engagement_rate,
                AVG(view_count) as avg_views,
                AVG(like_count) as avg_likes,
                COUNT(*) as videos_this_week
            FROM videos 
            WHERE channel_id = :channel_id 
                AND publish_date >= :start_date
            GROUP BY DATE_TRUNC('week', publish_date)
            ORDER BY week DESC
        """)
        
        start_date = datetime.now() - timedelta(days=days_back)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(
                query, 
                conn, 
                params={'channel_id': channel_id, 'start_date': start_date}
            )
        
        return df
    
    def get_best_performing_content_types(self, channel_id: str) -> pd.DataFrame:
        """
        Identify content types based on video titles/topics and their performance
        """
        query = text("""
            SELECT 
                title,
                view_count,
                like_count,
                comment_count,
                engagement_rate,
                publish_date
            FROM videos 
            WHERE channel_id = :channel_id
            ORDER BY engagement_rate DESC, view_count DESC
            LIMIT 20
        """)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(
                query, 
                conn, 
                params={'channel_id': channel_id}
            )
        
        return df
    
    def get_optimal_posting_times(self, channel_id: str) -> Dict:
        """
        Analyze best days and times for posting based on engagement
        """
        query = text("""
            SELECT 
                EXTRACT(DOW FROM publish_date) as day_of_week,
                EXTRACT(HOUR FROM publish_date) as hour_of_day,
                AVG(engagement_rate) as avg_engagement,
                AVG(view_count) as avg_views,
                COUNT(*) as video_count
            FROM videos 
            WHERE channel_id = :channel_id
            GROUP BY EXTRACT(DOW FROM publish_date), EXTRACT(HOUR FROM publish_date)
            ORDER BY avg_engagement DESC
            LIMIT 10
        """)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(
                query, 
                conn, 
                params={'channel_id': channel_id}
            )
        
        # Find best day and hour
        if not df.empty:
            best_row = df.loc[df['avg_engagement'].idxmax()]
            best_day_hour = {
                'day_of_week': best_row['day_of_week'],
                'hour_of_day': best_row['hour_of_day'],
                'avg_engagement': best_row['avg_engagement'],
                'avg_views': best_row['avg_views'],
                'video_count': best_row['video_count']
            }
            return {
                'best_day_hour': best_day_hour,
                'full_analysis': df.to_dict('records')
            }
        
        return {'best_day_hour': {}, 'full_analysis': []}
    
    def get_content_growth_trends(self, channel_id: str) -> Dict:
        """
        Analyze overall content growth and performance trends
        """
        query = text("""
            SELECT 
                MIN(publish_date) as first_video_date,
                MAX(publish_date) as latest_video_date,
                COUNT(*) as total_videos,
                AVG(view_count) as avg_views_per_video,
                AVG(engagement_rate) as avg_engagement_rate,
                SUM(view_count) as total_channel_views,
                SUM(like_count) as total_channel_likes
            FROM videos 
            WHERE channel_id = :channel_id
        """)
        
        with self.db_manager.engine.connect() as conn:
            result = conn.execute(
                query, 
                {'channel_id': channel_id}
            ).fetchone()
        
        return dict(result._mapping) if result else {}