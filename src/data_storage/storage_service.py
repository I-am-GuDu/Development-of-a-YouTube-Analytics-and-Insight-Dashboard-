"""
Data Storage Service for YouTube Analytics
Handles CRUD operations and data persistence
"""
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from .database import DatabaseManager
from datetime import datetime
from .analytics_queries import AnalyticsQueries

class DataStorageService:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
    
    def __del__(self):
        """Cleanup database session"""
        if hasattr(self, 'session'):
            self.session.close()

    def get_analytics_queries(self):
        """Get analytics query object for trend analysis"""
        return AnalyticsQueries(self.db_manager)
    
    def save_channel_data(self, channel_data: dict):
        """Save processed channel data to database"""
        try:
            from sqlalchemy import text
            
            query = text("""
                INSERT INTO channels (
                    channel_id, title, description, created_at, 
                    subscriber_count, view_count, video_count, thumbnail_url, crawl_timestamp
                ) VALUES (
                    :channel_id, :title, :description, :created_at,
                    :subscriber_count, :view_count, :video_count, :thumbnail_url, :crawl_timestamp
                )
                ON CONFLICT (channel_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    subscriber_count = EXCLUDED.subscriber_count,
                    view_count = EXCLUDED.view_count,
                    video_count = EXCLUDED.video_count,
                    thumbnail_url = EXCLUDED.thumbnail_url,
                    crawl_timestamp = EXCLUDED.crawl_timestamp
            """)
            
            self.session.execute(query, {
                'channel_id': channel_data['channel_id'],
                'title': channel_data['title'],
                'description': channel_data['description'],
                'created_at': channel_data['created_at'],
                'subscriber_count': channel_data['subscriber_count'],
                'view_count': channel_data['view_count'],
                'video_count': channel_data['video_count'],
                'thumbnail_url': channel_data['thumbnail_url'],
                'crawl_timestamp': channel_data.get('crawl_timestamp', datetime.now())
            })
            
            self.session.commit()
            print(f"Channel data saved for {channel_data['channel_id']}")
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error saving channel data: {e}")
            raise e
    
    def save_video_data(self, video_df: pd.DataFrame):
        """Save processed video data to database"""
        try:
            from sqlalchemy import text
            import numpy as np
            
            # Helper function to convert numpy types to native Python types
            def convert_numpy_types(value):
                if value is None or pd.isna(value):
                    return None
                if isinstance(value, (np.integer, np.floating)):
                    return value.item()
                if isinstance(value, np.ndarray):
                    return value.tolist()
                return value
            
            # Convert DataFrame to list of dictionaries
            video_records = video_df.to_dict('records')
            
            query = text("""
                INSERT INTO videos (
                    video_id, channel_id, title, description, publish_date,
                    view_count, like_count, comment_count, favorite_count,
                    engagement_rate, like_to_view_ratio, comment_to_like_ratio, crawl_timestamp
                ) VALUES (
                    :video_id, :channel_id, :title, :description, :publish_date,
                    :view_count, :like_count, :comment_count, :favorite_count,
                    :engagement_rate, :like_to_view_ratio, :comment_to_like_ratio, :crawl_timestamp
                )
                ON CONFLICT (video_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    publish_date = EXCLUDED.publish_date,
                    view_count = EXCLUDED.view_count,
                    like_count = EXCLUDED.like_count,
                    comment_count = EXCLUDED.comment_count,
                    engagement_rate = EXCLUDED.engagement_rate,
                    like_to_view_ratio = EXCLUDED.like_to_view_ratio,
                    comment_to_like_ratio = EXCLUDED.comment_to_like_ratio,
                    crawl_timestamp = EXCLUDED.crawl_timestamp
            """)
            
            for record in video_records:
                self.session.execute(query, {
                    'video_id': record['video_id'],
                    'channel_id': record.get('channel_id'),
                    'title': record['title'],
                    'description': record['description'],
                    'publish_date': record['publish_date'],
                    'view_count': int(convert_numpy_types(record['view_count'])),
                    'like_count': int(convert_numpy_types(record['like_count'])),
                    'comment_count': int(convert_numpy_types(record['comment_count'])),
                    'favorite_count': int(convert_numpy_types(record.get('favorite_count', 0))),
                    'engagement_rate': float(convert_numpy_types(record['engagement_rate'])),
                    'like_to_view_ratio': float(convert_numpy_types(record.get('like_to_view_ratio', 0))),
                    'comment_to_like_ratio': float(convert_numpy_types(record.get('comment_to_like_ratio', 0))),
                    'crawl_timestamp': record.get('crawl_timestamp', datetime.now())
                })
            
            self.session.commit()
            print(f"Saved {len(video_records)} videos to database")
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error saving video data: {e}")
            raise e
    
    def save_analytics_summary(self, channel_id: str, metrics: dict):
        """Save pre-computed analytics summary"""
        try:
            from sqlalchemy import text
            import numpy as np
            
            # Helper function to convert numpy types to native Python types
            def convert_numpy_types(value):
                if value is None:
                    return None
                if isinstance(value, (np.integer, np.floating)):
                    return value.item()
                if isinstance(value, np.ndarray):
                    return value.tolist()
                return value
            
            query = text("""
                INSERT INTO analytics_summary (
                    channel_id, avg_views_per_video, avg_likes_per_video, avg_engagement_rate,
                    total_potential_reach, video_growth_trend, most_viewed_video,
                    most_liked_video, best_engagement_video, engagement_efficiency
                ) VALUES (
                    :channel_id, :avg_views_per_video, :avg_likes_per_video, :avg_engagement_rate,
                    :total_potential_reach, :video_growth_trend, :most_viewed_video,
                    :most_liked_video, :best_engagement_video, :engagement_efficiency
                )
                ON CONFLICT (channel_id) DO UPDATE SET
                    avg_views_per_video = EXCLUDED.avg_views_per_video,
                    avg_likes_per_video = EXCLUDED.avg_likes_per_video,
                    avg_engagement_rate = EXCLUDED.avg_engagement_rate,
                    total_potential_reach = EXCLUDED.total_potential_reach,
                    video_growth_trend = EXCLUDED.video_growth_trend,
                    most_viewed_video = EXCLUDED.most_viewed_video,
                    most_liked_video = EXCLUDED.most_liked_video,
                    best_engagement_video = EXCLUDED.best_engagement_video,
                    engagement_efficiency = EXCLUDED.engagement_efficiency,
                    last_updated = CURRENT_TIMESTAMP
            """)
            
            self.session.execute(query, {
                'channel_id': channel_id,
                'avg_views_per_video': convert_numpy_types(metrics.get('avg_views_per_video')),
                'avg_likes_per_video': convert_numpy_types(metrics.get('avg_likes_per_video')),
                'avg_engagement_rate': convert_numpy_types(metrics.get('avg_engagement_rate')),
                'total_potential_reach': convert_numpy_types(metrics.get('total_potential_reach')),
                'video_growth_trend': convert_numpy_types(metrics.get('video_growth_trend')),
                'most_viewed_video': convert_numpy_types(metrics.get('most_viewed_video')),
                'most_liked_video': convert_numpy_types(metrics.get('most_liked_video')),
                'best_engagement_video': convert_numpy_types(metrics.get('best_engagement_video')),
                'engagement_efficiency': convert_numpy_types(metrics.get('engagement_efficiency'))
            })
            
            self.session.commit()
            print(f"Analytics summary saved for channel {channel_id}")
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error saving analytics summary: {e}")
            raise e