"""
Predictive Analytics Module
Provides forecasting, recommendations, and optimization algorithms
"""
from sqlalchemy import text
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class PredictiveAnalytics:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def forecast_channel_growth(self, channel_id: str, days_ahead: int = 30) -> Dict:
        """
        Forecast channel growth based on historical video performance
        """
        query = text("""
            SELECT 
                publish_date,
                view_count,
                like_count,
                engagement_rate
            FROM videos 
            WHERE channel_id = :channel_id
            ORDER BY publish_date
        """)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={'channel_id': channel_id})
        
        if len(df) < 5:
            return {
                'forecast': [],
                'confidence': 'low',
                'message': 'Insufficient data for reliable predictions'
            }
        
        # Prepare data for modeling
        df['date_numeric'] = (df['publish_date'] - df['publish_date'].min()).dt.days
        X = df[['date_numeric']].values
        y = df['engagement_rate'].values
        
        # Create polynomial regression model (handles non-linear trends)
        model = Pipeline([
            ('poly', PolynomialFeatures(degree=2)),
            ('linear', LinearRegression())
        ])
        
        try:
            model.fit(X, y)
            
            # Generate future dates
            last_date = df['publish_date'].max()
            future_dates = []
            future_values = []
            
            for i in range(1, days_ahead + 1):
                future_date = last_date + timedelta(days=i)
                future_X = np.array([[df['date_numeric'].max() + i]])
                predicted_engagement = model.predict(future_X)[0]
                
                future_dates.append(future_date)
                future_values.append(max(0, predicted_engagement))  # Ensure non-negative
            
            return {
                'forecast': list(zip(future_dates, future_values)),
                'confidence': 'medium' if len(df) > 10 else 'low',
                'current_avg_engagement': df['engagement_rate'].mean(),
                'projected_avg_engagement': np.mean(future_values),
                'channel_id_used': channel_id  # DEBUG: Track which channel was analyzed
            }
            
        except Exception as e:
            return {
                'forecast': [],
                'confidence': 'error',
                'message': f'Model fitting failed: {str(e)}'
            }
    
    def recommend_content_strategy(self, channel_id: str) -> Dict:
        """
        Recommend content strategy based on historical performance patterns
        """
        # Get categorized performance data
        query = text("""
            SELECT 
                title,
                view_count,
                like_count,
                engagement_rate,
                publish_date,
                EXTRACT(DOW FROM publish_date) as day_of_week,
                EXTRACT(HOUR FROM publish_date) as hour_of_day
            FROM videos 
            WHERE channel_id = :channel_id
            ORDER BY publish_date DESC
        """)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={'channel_id': channel_id})
        
        if df.empty:
            return {'recommendations': [], 'message': 'No data available', 'channel_id_used': channel_id}
        
        # Content category analysis
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
            if pd.isna(title):
                return 'General'
            title_lower = title.lower()
            for category, keywords in category_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    return category
            return 'General'
        
        df['category'] = df['title'].apply(categorize_title)
        
        # Calculate performance by category
        category_performance = df.groupby('category').agg({
            'engagement_rate': ['mean', 'std', 'count'],
            'view_count': 'mean'
        }).round(2)
        
        # Flatten column names
        category_performance.columns = [
            'avg_engagement_rate', 'std_engagement_rate', 'video_count', 'avg_views'
        ]
        
        # Identify high-performing categories
        high_performers = category_performance[
            (category_performance['avg_engagement_rate'] > df['engagement_rate'].mean()) &
            (category_performance['video_count'] >= 3)  # At least 3 videos per category
        ].sort_values('avg_engagement_rate', ascending=False)
        
        recommendations = []
        
        if not high_performers.empty:
            top_category = high_performers.index[0]
            avg_performance = high_performers.iloc[0]['avg_engagement_rate']
            
            recommendations.append({
                'type': 'content_type',
                'category': top_category,
                'current_avg_engagement': avg_performance,
                'reason': f'This category performs {avg_performance:.2f}% on average'
            })
        
        # Optimal posting time analysis
        time_performance = df.groupby(['day_of_week', 'hour_of_day']).agg({
            'engagement_rate': 'mean'
        }).round(2).reset_index()
        
        if not time_performance.empty:
            best_time = time_performance.loc[time_performance['engagement_rate'].idxmax()]
            day_names = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
            
            recommendations.append({
                'type': 'posting_time',
                'optimal_day': day_names.get(best_time['day_of_week'], 'Unknown'),
                'optimal_hour': int(best_time['hour_of_day']),
                'engagement_rate': best_time['engagement_rate'],
                'reason': f'Posts at this time achieve {best_time["engagement_rate"]:.2f}% engagement'
            })
        
        return {
            'recommendations': recommendations,
            'category_performance': category_performance.to_dict('index'),
            'total_videos_analyzed': len(df),
            'channel_id_used': channel_id  # DEBUG: Track which channel was analyzed
        }
    
    def optimize_posting_schedule(self, channel_id: str, num_videos: int = 5) -> List[Dict]:
        """
        Recommend optimal posting schedule based on historical patterns
        """
        # Get historical posting patterns
        query = text("""
            SELECT 
                publish_date,
                engagement_rate
            FROM videos 
            WHERE channel_id = :channel_id
            ORDER BY publish_date DESC
            LIMIT 30
        """)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={'channel_id': channel_id})
        
        if len(df) < 5:
            return [{'date': str(datetime.now() + timedelta(days=i+1)), 'engagement_prediction': 'insufficient_data', 'channel_id_used': channel_id} 
                   for i in range(num_videos)]
        
        # Analyze day-of-week and hour-of-day patterns
        df['day_of_week'] = df['publish_date'].dt.dayofweek
        df['hour_of_day'] = df['publish_date'].dt.hour
        
        # Calculate average engagement by day and hour
        daily_avg = df.groupby('day_of_week')['engagement_rate'].mean().to_dict()
        hourly_avg = df.groupby('hour_of_day')['engagement_rate'].mean().to_dict()
        
        # Find best combinations
        best_combinations = []
        for day in range(7):
            for hour in range(24):
                day_score = daily_avg.get(day, 0)
                hour_score = hourly_avg.get(hour, 0)
                combined_score = (day_score + hour_score) / 2
                best_combinations.append((day, hour, combined_score))
        
        # Sort by score and get top slots
        best_combinations.sort(key=lambda x: x[2], reverse=True)
        
        # Generate recommended schedule
        recommendations = []
        base_date = datetime.now() + timedelta(days=1)
        
        for i in range(num_videos):
            best_day, best_hour, best_score = best_combinations[i % len(best_combinations)]
            scheduled_date = base_date.replace(
                day=base_date.day + best_day,
                hour=best_hour,
                minute=0,
                second=0
            )
            
            recommendations.append({
                'scheduled_date': scheduled_date.strftime('%Y-%m-%d %H:%M'),
                'recommended_day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][best_day],
                'recommended_hour': best_hour,
                'predicted_engagement': round(best_score, 2),
                'confidence': 'medium' if len(df) > 10 else 'low',
                'channel_id_used': channel_id  # DEBUG: Track which channel was analyzed
            })
        
        return recommendations
    
    def predict_video_performance(self, channel_id: str, video_title: str = "") -> Dict:
        """
        Predict performance of a potential video based on channel history
        """
        # Get channel's historical performance
        query = text("""
            SELECT 
                engagement_rate,
                view_count,
                like_count,
                comment_count
            FROM videos 
            WHERE channel_id = :channel_id
            ORDER BY publish_date DESC
            LIMIT 50
        """)
        
        with self.db_manager.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={'channel_id': channel_id})
        
        if df.empty:
            return {
                'predicted_engagement_rate': 'insufficient_data',
                'predicted_views': 'insufficient_data',
                'confidence': 'none',
                'channel_id_used': channel_id
            }
        
        # Calculate baseline metrics
        baseline_engagement = df['engagement_rate'].mean()
        baseline_views = df['view_count'].mean()
        baseline_likes = df['like_count'].mean()
        
        # Adjust based on content category (if title provided)
        if video_title:
            # Simple category-based adjustment
            category_multiplier = self._get_category_multiplier(video_title, df)
            predicted_engagement = baseline_engagement * category_multiplier
        else:
            predicted_engagement = baseline_engagement
        
        # Calculate predicted metrics
        predicted_views = baseline_views  # Views depend on audience size
        predicted_likes = predicted_engagement * predicted_views / 100  # Engagement formula
        
        return {
            'predicted_engagement_rate': round(predicted_engagement, 2),
            'predicted_views': int(predicted_views),
            'predicted_likes': int(predicted_likes),
            'baseline_engagement': round(baseline_engagement, 2),
            'confidence': 'medium' if len(df) > 10 else 'low',
            'channel_id_used': channel_id  # DEBUG: Track which channel was analyzed
        }
    
    def _get_category_multiplier(self, title: str, historical_df: pd.DataFrame) -> float:
        """
        Internal helper to get performance multiplier based on content category
        """
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
        
        title_lower = title.lower()
        
        # Check historical performance by category
        for category, keywords in category_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                # Return category-specific performance multiplier
                if category == 'Price Analysis':
                    return 1.2  # High engagement category
                elif category == 'Tech Reviews':
                    return 1.1
                elif category == 'Product Comparisons':
                    return 0.9
                else:
                    return 1.0  # Neutral
        
        return 1.0  # Default for general content