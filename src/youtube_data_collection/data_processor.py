"""
Data Processing Module
Transforms raw YouTube API data into analysis-ready format
"""
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List
import re

logger = logging.getLogger(__name__)


class DataProcessor:
    @staticmethod
    def clean_description(description: str) -> str:
        """Clean and normalize video/channel description"""
        if not description:
            return ""

        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', description.strip())
        return cleaned

    @staticmethod
    def validate_channel_data(raw_channel_data: Dict) -> bool:
        """Validate raw channel data integrity"""
        required_fields = [
            'id', 'snippet', 'statistics', 'contentDetails'
        ]

        for field in required_fields:
            if field not in raw_channel_data:
                return False

        # Validate nested fields
        if not raw_channel_data['snippet'].get('title'):
            return False

        # Validate statistics exist
        stats = raw_channel_data['statistics']
        required_stats = ['viewCount', 'subscriberCount', 'videoCount']
        for stat in required_stats:
            if stat not in stats:
                return False

        return True

    @staticmethod
    def validate_video_data(video_data: Dict) -> bool:
        """Validate individual video data"""
        required_fields = [
            'video_id', 'title', 'publish_date',
            'view_count', 'like_count', 'comment_count'
        ]

        for field in required_fields:
            if field not in video_data:
                return False

        # Validate numeric values are reasonable
        if int(video_data['view_count']) < 0:
            return False
        if int(video_data['like_count']) < 0:
            return False
        if int(video_data['comment_count']) < 0:
            return False

        return True

    @staticmethod
    def process_channel_data(raw_channel_data) -> Dict:
        """Process raw channel data into structured format"""
        if not DataProcessor.validate_channel_data(raw_channel_data):
            raise ValueError("Invalid channel data format")

        snippet = raw_channel_data['snippet']
        stats = raw_channel_data['statistics']

        processed = {
        'channel_id': raw_channel_data['id'],
        'title': snippet['title'].strip(),
        'description': DataProcessor.clean_description(snippet['description']),
        'created_at': snippet['publishedAt'],
        'subscriber_count': int(stats['subscriberCount']),
        'view_count': int(stats['viewCount']),
        'video_count': int(stats['videoCount']),
        'thumbnail_url': snippet['thumbnails']['high']['url'],
        'crawl_timestamp': datetime.now().isoformat()
    }
        return processed

    @staticmethod
    def process_video_data(raw_video_data: List[Dict]) -> pd.DataFrame:
        """Convert raw video data to DataFrame with validation"""
        validated_videos = []

        for video in raw_video_data:
            # First validate the video data
            if DataProcessor.validate_video_data(video):
                processed_video = {
                    'video_id': video['video_id'],
                    'title': video['title'].strip(),
                    'description': DataProcessor.clean_description(video['description']),
                    # Convert to naive datetime
                    'publish_date': pd.to_datetime(video['publish_date']).tz_localize(None),
                    # Ensure non-negative
                    'view_count': max(0, int(video['view_count'])),
                    'like_count': max(0, int(video['like_count'])),
                    'comment_count': max(0, int(video['comment_count'])),
                    'favorite_count': max(0, int(video.get('favorite_count', 0))),
                    'engagement_rate': (int(video['like_count']) + int(video['comment_count'])) / max(int(video['view_count']), 1) * 100,
                    'crawl_timestamp': datetime.now().isoformat()
                }
                validated_videos.append(processed_video)
            else:
                logger.warning(
                    "Skipping invalid video %s", video.get('video_id', 'unknown'))

        df = pd.DataFrame(validated_videos)

        # Additional data cleaning on the DataFrame
        if not df.empty:
            # Sort by publish date (newest first)
            df = df.sort_values('publish_date', ascending=False)

            # Add calculated columns
            df['like_to_view_ratio'] = df['like_count'] / \
                df['view_count'].replace(0, 1) * 100
            df['comment_to_like_ratio'] = df['comment_count'] / \
                df['like_count'].replace(0, 1) * 100

        return df

    @staticmethod
    def filter_top_performing_videos(df: pd.DataFrame, metric: str = 'view_count', top_n: int = 10) -> pd.DataFrame:
        """Filter top performing videos based on specified metric"""
        if df.empty:
            return df

        # Validate metric exists
        if metric not in df.columns:
            raise ValueError(
                f"Metric '{metric}' not found in DataFrame columns")

        # Sort by the specified metric and return top N
        sorted_df = df.nlargest(top_n, metric)
        return sorted_df

    @staticmethod
    def calculate_engagement_metrics(processed_videos_df: pd.DataFrame) -> Dict:
        """Calculate comprehensive engagement metrics"""
        if processed_videos_df.empty:
            return {}

        # Convert the threshold date to match the DataFrame's date format
        thirty_days_ago = pd.Timestamp.now() - pd.Timedelta(days=30)

        # Ensure publish_date column is in the same format as our comparison
        publish_dates = pd.to_datetime(
            processed_videos_df['publish_date']).dt.tz_localize(None)

        # Now perform the comparison with matching formats
        recent_videos_mask = publish_dates >= thirty_days_ago
        # Count of True values
        video_growth_trend = int(recent_videos_mask.sum())

        metrics = {
            'avg_views_per_video': float(processed_videos_df['view_count'].mean()),
            'avg_likes_per_video': float(processed_videos_df['like_count'].mean()),
            'avg_comments_per_video': float(processed_videos_df['comment_count'].mean()),
            'avg_engagement_rate': float(processed_videos_df['engagement_rate'].mean()),
            'total_potential_reach': int(processed_videos_df['view_count'].sum()),
            'video_growth_trend': video_growth_trend,
            'most_viewed_video': processed_videos_df.loc[processed_videos_df['view_count'].idxmax()]['title'] if not processed_videos_df.empty else None,
            'most_liked_video': processed_videos_df.loc[processed_videos_df['like_count'].idxmax()]['title'] if not processed_videos_df.empty else None,
            'best_engagement_video': processed_videos_df.loc[processed_videos_df['engagement_rate'].idxmax()]['title'] if not processed_videos_df.empty else None,
            'engagement_efficiency': (processed_videos_df['like_count'].sum() + processed_videos_df['comment_count'].sum()) / max(processed_videos_df['view_count'].sum(), 1) * 100
        }
        return metrics
