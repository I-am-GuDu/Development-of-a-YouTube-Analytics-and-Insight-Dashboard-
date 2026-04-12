"""
Unit Tests for DataProcessor Module
Tests data cleaning, validation, processing, filtering, and engagement metrics.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from youtube_data_collection.data_processor import DataProcessor


# ═══════════════════════════════════════════════════════════════════════════════
# DESCRIPTION CLEANING
# ═══════════════════════════════════════════════════════════════════════════════

class TestCleanDescription:
    """Tests for DataProcessor.clean_description()"""

    def test_removes_extra_whitespace(self):
        result = DataProcessor.clean_description("Hello   world   test")
        assert result == "Hello world test"

    def test_removes_newlines(self):
        result = DataProcessor.clean_description("Line one\n\nLine two\nLine three")
        assert result == "Line one Line two Line three"

    def test_strips_leading_trailing_spaces(self):
        result = DataProcessor.clean_description("   padded text   ")
        assert result == "padded text"

    def test_empty_string_returns_empty(self):
        result = DataProcessor.clean_description("")
        assert result == ""

    def test_none_returns_empty(self):
        result = DataProcessor.clean_description(None)
        assert result == ""


# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateChannelData:
    """Tests for DataProcessor.validate_channel_data()"""

    def test_valid_channel_data(self, raw_channel_data):
        assert DataProcessor.validate_channel_data(raw_channel_data) is True

    def test_missing_required_field(self, raw_channel_data):
        del raw_channel_data['statistics']
        assert DataProcessor.validate_channel_data(raw_channel_data) is False

    def test_missing_snippet_title(self, raw_channel_data):
        raw_channel_data['snippet']['title'] = ''
        assert DataProcessor.validate_channel_data(raw_channel_data) is False

    def test_missing_subscriber_count(self, raw_channel_data_missing_stats):
        assert DataProcessor.validate_channel_data(raw_channel_data_missing_stats) is False


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateVideoData:
    """Tests for DataProcessor.validate_video_data()"""

    def test_valid_video(self, raw_video_list):
        assert DataProcessor.validate_video_data(raw_video_list[0]) is True

    def test_missing_required_field(self):
        incomplete = {'video_id': 'v1', 'title': 'Test'}
        assert DataProcessor.validate_video_data(incomplete) is False

    def test_negative_view_count(self, raw_video_invalid):
        assert DataProcessor.validate_video_data(raw_video_invalid) is False

    def test_negative_like_count(self, raw_video_list):
        video = raw_video_list[0].copy()
        video['like_count'] = -5
        assert DataProcessor.validate_video_data(video) is False

    def test_negative_comment_count(self, raw_video_list):
        video = raw_video_list[0].copy()
        video['comment_count'] = -1
        assert DataProcessor.validate_video_data(video) is False


# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL DATA PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

class TestProcessChannelData:
    """Tests for DataProcessor.process_channel_data()"""

    def test_processes_valid_data(self, raw_channel_data):
        result = DataProcessor.process_channel_data(raw_channel_data)

        assert result['channel_id'] == 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
        assert result['title'] == 'Test Channel'
        assert result['subscriber_count'] == 100000
        assert result['view_count'] == 5000000
        assert result['video_count'] == 250
        assert result['thumbnail_url'] == 'https://example.com/thumb_high.jpg'
        assert 'crawl_timestamp' in result

    def test_cleans_description(self, raw_channel_data):
        result = DataProcessor.process_channel_data(raw_channel_data)
        # Original has double spaces and newlines
        assert '  ' not in result['description']
        assert '\n' not in result['description']

    def test_invalid_data_raises_value_error(self, raw_channel_data_missing_stats):
        with pytest.raises(ValueError, match="Invalid channel data format"):
            DataProcessor.process_channel_data(raw_channel_data_missing_stats)


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO DATA PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

class TestProcessVideoData:
    """Tests for DataProcessor.process_video_data()"""

    def test_creates_dataframe(self, raw_video_list):
        df = DataProcessor.process_video_data(raw_video_list)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10

    def test_skips_invalid_videos(self, raw_video_list, raw_video_invalid):
        mixed = raw_video_list + [raw_video_invalid]
        df = DataProcessor.process_video_data(mixed)
        # Invalid video should be skipped
        assert len(df) == 10
        assert 'vid_bad' not in df['video_id'].values

    def test_adds_calculated_columns(self, raw_video_list):
        df = DataProcessor.process_video_data(raw_video_list)
        assert 'engagement_rate' in df.columns
        assert 'like_to_view_ratio' in df.columns
        assert 'comment_to_like_ratio' in df.columns

    def test_sorted_by_publish_date_descending(self, raw_video_list):
        df = DataProcessor.process_video_data(raw_video_list)
        dates = df['publish_date'].tolist()
        assert dates == sorted(dates, reverse=True)

    def test_engagement_rate_calculation(self, raw_video_list):
        df = DataProcessor.process_video_data(raw_video_list)
        # For the first video (vid_000): likes=50, comments=10, views=1000
        row = df[df['video_id'] == 'vid_000'].iloc[0]
        expected = (50 + 10) / 1000 * 100  # 6.0%
        assert abs(row['engagement_rate'] - expected) < 0.01

    def test_empty_list_returns_empty_dataframe(self):
        df = DataProcessor.process_video_data([])
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# ═══════════════════════════════════════════════════════════════════════════════
# TOP PERFORMING FILTER
# ═══════════════════════════════════════════════════════════════════════════════

class TestFilterTopPerforming:
    """Tests for DataProcessor.filter_top_performing_videos()"""

    def test_returns_top_n_by_views(self, sample_video_df):
        result = DataProcessor.filter_top_performing_videos(
            sample_video_df, metric='view_count', top_n=3
        )
        assert len(result) == 3
        assert result.iloc[0]['view_count'] == sample_video_df['view_count'].max()

    def test_invalid_metric_raises(self, sample_video_df):
        with pytest.raises(ValueError, match="not found"):
            DataProcessor.filter_top_performing_videos(
                sample_video_df, metric='nonexistent_column'
            )

    def test_empty_df_returns_empty(self):
        empty = pd.DataFrame()
        result = DataProcessor.filter_top_performing_videos(empty)
        assert result.empty


# ═══════════════════════════════════════════════════════════════════════════════
# ENGAGEMENT METRICS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateEngagementMetrics:
    """Tests for DataProcessor.calculate_engagement_metrics()"""

    def test_returns_all_expected_keys(self, sample_video_df):
        metrics = DataProcessor.calculate_engagement_metrics(sample_video_df)
        expected_keys = [
            'avg_views_per_video', 'avg_likes_per_video',
            'avg_comments_per_video', 'avg_engagement_rate',
            'total_potential_reach', 'video_growth_trend',
            'most_viewed_video', 'most_liked_video',
            'best_engagement_video', 'engagement_efficiency'
        ]
        for key in expected_keys:
            assert key in metrics, f"Missing key: {key}"

    def test_avg_views_is_correct(self, sample_video_df):
        metrics = DataProcessor.calculate_engagement_metrics(sample_video_df)
        expected = sample_video_df['view_count'].mean()
        assert abs(metrics['avg_views_per_video'] - expected) < 0.01

    def test_total_potential_reach(self, sample_video_df):
        metrics = DataProcessor.calculate_engagement_metrics(sample_video_df)
        expected = int(sample_video_df['view_count'].sum())
        assert metrics['total_potential_reach'] == expected

    def test_empty_df_returns_empty_dict(self):
        empty = pd.DataFrame()
        metrics = DataProcessor.calculate_engagement_metrics(empty)
        assert metrics == {}

    def test_most_viewed_video(self, sample_video_df):
        metrics = DataProcessor.calculate_engagement_metrics(sample_video_df)
        max_idx = sample_video_df['view_count'].idxmax()
        expected_title = sample_video_df.loc[max_idx, 'title']
        assert metrics['most_viewed_video'] == expected_title
