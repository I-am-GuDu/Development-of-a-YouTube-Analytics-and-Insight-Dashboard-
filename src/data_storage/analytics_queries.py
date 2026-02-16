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

    # NEW METHODS FOR CONTENT ANALYSIS (ADD THESE TO THE END)
    def categorize_video_topics(self, channel_id: str) -> pd.DataFrame:
        """
        Analyze video titles/descriptions to identify content categories and their performance
        """
        query = text("""
            SELECT 
                video_id,
                title,
                description,
                view_count,
                like_count,
                comment_count,
                engagement_rate,
                publish_date
            FROM videos 
            WHERE channel_id = :channel_id
            ORDER BY publish_date DESC
        """)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(
                query, 
                conn, 
                params={'channel_id': channel_id}
            )
        
        # Simple keyword-based categorization
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
        
        df['category'] = df['title'].apply(categorize_title)
        return df

    def get_category_performance_analysis(self, channel_id: str) -> pd.DataFrame:
        """
        Analyze performance by content category
        """
        # First get categorized data
        categorized_df = self.categorize_video_topics(channel_id)
        
        # Group by category and calculate metrics
        category_analysis = categorized_df.groupby('category').agg({
            'view_count': ['count', 'mean', 'sum'],
            'like_count': 'mean',
            'comment_count': 'mean', 
            'engagement_rate': 'mean'
        }).round(2)
        
        # Flatten column names
        category_analysis.columns = [
            'video_count', 'avg_views', 'total_views', 
            'avg_likes', 'avg_comments', 'avg_engagement_rate'
        ]
        
        # Sort by engagement rate
        category_analysis = category_analysis.sort_values('avg_engagement_rate', ascending=False)
        
        return category_analysis.reset_index()

    def get_top_performing_videos_by_category(self, channel_id: str) -> pd.DataFrame:
        """
        Get top performing videos within each category
        """
        categorized_df = self.categorize_video_topics(channel_id)
        
        # Get top video by engagement rate for each category
        top_videos = categorized_df.loc[
            categorized_df.groupby('category')['engagement_rate'].idxmax()
        ][['category', 'title', 'engagement_rate', 'view_count', 'like_count']]
        
        return top_videos.sort_values('engagement_rate', ascending=False)

    def get_seasonal_content_patterns(self, channel_id: str) -> pd.DataFrame:
        """
        Analyze content performance by month/season to identify patterns
        """
        query = text("""
            SELECT 
                video_id,
                title,
                view_count,
                engagement_rate,
                EXTRACT(MONTH FROM publish_date) as month,
                EXTRACT(YEAR FROM publish_date) as year
            FROM videos 
            WHERE channel_id = :channel_id
            ORDER BY publish_date
        """)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(
                query, 
                conn, 
                params={'channel_id': channel_id}
            )
        
        # Group by month and calculate average performance
        grouped = df.groupby('month')
        monthly_performance = pd.DataFrame({
            'engagement_rate': grouped['engagement_rate'].mean(),
            'view_count': grouped['view_count'].mean(),
            'video_count': grouped.size()  # Use grouped.size() separately
        }).round(2)
        
        # Add month names
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        monthly_performance.index = monthly_performance.index.map(month_names)
        
        return monthly_performance
    

    def compare_multiple_channels(self, channel_ids: List[str]) -> pd.DataFrame:
        """
        Compare performance metrics across multiple channels
        """
        if not channel_ids:
            return pd.DataFrame()
            
        placeholders = ','.join([f':channel_id_{i}' for i in range(len(channel_ids))])
        
        query = text(f"""
            SELECT 
                c.channel_id,
                c.title,
                c.subscriber_count,
                c.view_count,
                c.video_count,
                a.avg_views_per_video,
                a.avg_engagement_rate,
                a.total_potential_reach,
                a.video_growth_trend,
                a.engagement_efficiency
            FROM channels c
            LEFT JOIN analytics_summary a ON c.channel_id = a.channel_id
            WHERE c.channel_id IN ({placeholders})
            ORDER BY c.subscriber_count DESC
        """)
        
        # Prepare parameters dynamically
        params = {f'channel_id_{i}': channel_id for i, channel_id in enumerate(channel_ids)}
        
        try:
            with self.db_manager.engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            print(f"Error comparing channels: {e}")
            return pd.DataFrame()

    def get_cross_channel_performance_rankings(self, channel_ids: List[str], metric: str = 'engagement_rate') -> pd.DataFrame:
        """
        Rank channels by specific performance metric
        """
        if not channel_ids:
            return pd.DataFrame()
            
        valid_metrics = {
            'engagement_rate': 'a.avg_engagement_rate',
            'avg_views': 'a.avg_views_per_video', 
            'subscribers': 'c.subscriber_count',
            'efficiency': 'a.engagement_efficiency'
        }
        
        if metric not in valid_metrics:
            raise ValueError(f"Invalid metric. Choose from: {list(valid_metrics.keys())}")
        
        column_name = valid_metrics[metric]
        placeholders = ','.join([f':channel_id_{i}' for i in range(len(channel_ids))])
        
        query = text(f"""
            SELECT 
                c.channel_id,
                c.title,
                {column_name} as {metric},
                c.subscriber_count
            FROM channels c
            LEFT JOIN analytics_summary a ON c.channel_id = a.channel_id
            WHERE c.channel_id IN ({placeholders})
            AND {column_name} IS NOT NULL
            ORDER BY {column_name} DESC
        """)
        
        # Prepare parameters dynamically
        params = {f'channel_id_{i}': channel_id for i, channel_id in enumerate(channel_ids)}
        
        try:
            with self.db_manager.engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            print(f"Error ranking channels: {e}")
            return pd.DataFrame()

    def get_competitive_benchmarking_report(self, primary_channel_id: str, competitor_channel_ids: List[str]) -> Dict:
        """
        Generate competitive analysis report comparing one channel against competitors
        """
        if not primary_channel_id or not competitor_channel_ids:
            return {
                'comparison_table': [],
                'primary_channel_metrics': {},
                'benchmarks': {},
                'advantages': [],
                'disadvantages': [],
                'rankings': []
            }
            
        all_channel_ids = [primary_channel_id] + competitor_channel_ids
        
        try:
            # Get overall comparison
            comparison_df = self.compare_multiple_channels(all_channel_ids)
            
            if comparison_df.empty:
                return {
                    'comparison_table': [],
                    'primary_channel_metrics': {},
                    'benchmarks': {},
                    'advantages': [],
                    'disadvantages': [],
                    'rankings': []
                }
            
            # Get primary channel metrics
            primary_mask = comparison_df['channel_id'] == primary_channel_id
            primary_metrics = comparison_df[primary_mask].iloc[0].to_dict() if not comparison_df[primary_mask].empty else {}
            
            # Calculate benchmarks (excluding null values)
            benchmarks = {
                'avg_subscribers': comparison_df['subscriber_count'].mean(),
                'avg_engagement_rate': comparison_df['avg_engagement_rate'].mean(),
                'avg_views_per_video': comparison_df['avg_views_per_video'].mean(),
                'avg_efficiency': comparison_df['engagement_efficiency'].mean()
            }
            
            # Competitive advantages/disadvantages
            advantages = []
            disadvantages = []
            
            if primary_metrics and not pd.isna(primary_metrics.get('avg_engagement_rate')):
                if primary_metrics['avg_engagement_rate'] > benchmarks['avg_engagement_rate']:
                    advantages.append(f"Higher engagement rate ({primary_metrics['avg_engagement_rate']:.2f}% vs {benchmarks['avg_engagement_rate']:.2f}%)")
                else:
                    disadvantages.append(f"Lower engagement rate ({primary_metrics['avg_engagement_rate']:.2f}% vs {benchmarks['avg_engagement_rate']:.2f}%)")
                
                if not pd.isna(primary_metrics.get('engagement_efficiency')) and not pd.isna(benchmarks['avg_efficiency']):
                    if primary_metrics['engagement_efficiency'] > benchmarks['avg_efficiency']:
                        advantages.append(f"Better engagement efficiency ({primary_metrics['engagement_efficiency']:.2f} vs {benchmarks['avg_efficiency']:.2f})")
                    else:
                        disadvantages.append(f"Lower engagement efficiency ({primary_metrics['engagement_efficiency']:.2f} vs {benchmarks['avg_efficiency']:.2f})")
            
            return {
                'comparison_table': comparison_df.to_dict('records'),
                'primary_channel_metrics': primary_metrics,
                'benchmarks': benchmarks,
                'advantages': advantages,
                'disadvantages': disadvantages,
                'rankings': self.get_cross_channel_performance_rankings(all_channel_ids, 'engagement_rate').to_dict('records')
            }
            
        except Exception as e:
            print(f"Error generating benchmarking report: {e}")
            return {
                'comparison_table': [],
                'primary_channel_metrics': {},
                'benchmarks': {},
                'advantages': [],
                'disadvantages': [],
                'rankings': []
            }

    def get_content_strategy_comparison(self, channel_ids: List[str]) -> pd.DataFrame:
        """
        Compare content strategies across channels (categories, posting patterns, etc.)
        """
        if not channel_ids:
            return pd.DataFrame()
            
        # First get all videos for all channels
        placeholders = ','.join([f':channel_id_{i}' for i in range(len(channel_ids))])
        
        query = text(f"""
            SELECT 
                v.channel_id,
                c.title as channel_title,
                v.title as video_title,
                v.engagement_rate,
                v.view_count,
                v.publish_date,
                EXTRACT(DOW FROM v.publish_date) as day_of_week,
                EXTRACT(HOUR FROM v.publish_date) as hour_of_day
            FROM videos v
            JOIN channels c ON v.channel_id = c.channel_id
            WHERE v.channel_id IN ({placeholders})
            ORDER BY v.channel_id, v.publish_date DESC
        """)
        
        params = {f'channel_id_{i}': channel_id for i, channel_id in enumerate(channel_ids)}
        
        try:
            with self.db_manager.engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
            
            # Add content categorization
            if not df.empty:
                df_with_categories = self._add_content_categories(df)
                return df_with_categories
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error comparing content strategies: {e}")
            return pd.DataFrame()

    def _add_content_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Helper method to add content categories to video dataframe
        """
        if df.empty:
            return df
            
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
            if pd.isna(title) or not isinstance(title, str):
                return 'General'
            title_lower = title.lower()
            for category, keywords in category_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    return category
            return 'General'
        
        df['category'] = df['video_title'].apply(categorize_title)
        return df