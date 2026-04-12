"""
Shared Pytest Fixtures for YouTube Analytics Dashboard Tests
Provides reusable sample data, mock objects, and test utilities.
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Make 'src/' importable so tests can do:
#   from youtube_data_collection.api_handler import YouTubeAPIHandler
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ═══════════════════════════════════════════════════════════════════════════════
# RAW API RESPONSE FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def raw_channel_data():
    """
    Simulates the raw JSON returned by YouTube Data API v3
    for a single channel (channels().list() → items[0]).
    """
    return {
        'id': 'UC_x5XG1OV2P6uZZ5FSM9Ttw',
        'snippet': {
            'title': 'Test Channel',
            'description': 'A channel   for   testing\n\npurposes.',
            'publishedAt': '2020-01-15T10:30:00Z',
            'thumbnails': {
                'high': {
                    'url': 'https://example.com/thumb_high.jpg'
                }
            }
        },
        'statistics': {
            'viewCount': '5000000',
            'subscriberCount': '100000',
            'videoCount': '250'
        },
        'contentDetails': {
            'relatedPlaylists': {
                'uploads': 'UU_x5XG1OV2P6uZZ5FSM9Ttw'
            }
        }
    }


@pytest.fixture
def raw_channel_data_missing_stats():
    """Channel data with a required statistic field removed."""
    return {
        'id': 'UC_missing',
        'snippet': {
            'title': 'Bad Channel',
            'description': '',
            'publishedAt': '2021-06-01T00:00:00Z',
            'thumbnails': {'high': {'url': ''}}
        },
        'statistics': {
            'viewCount': '100',
            # 'subscriberCount' intentionally missing
            'videoCount': '5'
        },
        'contentDetails': {
            'relatedPlaylists': {'uploads': 'UU_missing'}
        }
    }


@pytest.fixture
def raw_video_list():
    """
    A list of raw video detail dicts as returned after
    YouTubeAPIHandler.get_video_details() post-processing.
    """
    base = datetime(2024, 1, 1, 12, 0, 0)
    videos = []
    for i in range(10):
        videos.append({
            'video_id': f'vid_{i:03d}',
            'title': f'Test Video {i} review' if i % 3 == 0 else f'Test Video {i}',
            'description': f'Description for video {i}.',
            'publish_date': (base + timedelta(days=i * 7)).isoformat() + 'Z',
            'view_count': (i + 1) * 1000,
            'like_count': (i + 1) * 50,
            'comment_count': (i + 1) * 10,
            'favorite_count': 0
        })
    return videos


@pytest.fixture
def raw_video_invalid():
    """A single video dict that is intentionally invalid (negative views)."""
    return {
        'video_id': 'vid_bad',
        'title': 'Bad Video',
        'description': 'Should be rejected.',
        'publish_date': '2024-03-01T00:00:00Z',
        'view_count': -100,
        'like_count': 10,
        'comment_count': 5,
        'favorite_count': 0
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSED DATA FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def processed_channel(raw_channel_data):
    """
    A processed channel dict as returned by
    DataProcessor.process_channel_data().
    """
    return {
        'channel_id': raw_channel_data['id'],
        'title': 'Test Channel',
        'description': 'A channel for testing purposes.',
        'created_at': '2020-01-15T10:30:00Z',
        'subscriber_count': 100000,
        'view_count': 5000000,
        'video_count': 250,
        'thumbnail_url': 'https://example.com/thumb_high.jpg',
        'crawl_timestamp': datetime.now().isoformat()
    }


@pytest.fixture
def sample_video_df():
    """
    A ready-to-use Pandas DataFrame simulating processed video data
    with all calculated columns present. Contains 10 rows.
    """
    base = pd.Timestamp('2024-01-01 12:00:00')
    n = 10
    data = {
        'video_id': [f'vid_{i:03d}' for i in range(n)],
        'title': [
            'Phone review test',     # Tech Reviews
            'Tutorial how to code',  # Tutorials
            'A vs B comparison',     # Product Comparisons
            'Latest news update',    # News Updates
            'Unboxing new gadget',   # Unboxings
            'Price analysis deal',   # Price Analysis
            'Software update tips',  # Software Updates
            'Best accessory buy',    # Accessories
            'General video one',     # General
            'General video two',     # General
        ],
        'description': [f'Desc {i}' for i in range(n)],
        'publish_date': [base + pd.Timedelta(days=i * 7) for i in range(n)],
        'view_count': [5000, 12000, 8000, 3000, 15000, 7000, 4000, 6000, 9000, 11000],
        'like_count': [200, 600, 350, 120, 800, 280, 150, 250, 400, 500],
        'comment_count': [30, 80, 50, 20, 100, 40, 25, 35, 60, 70],
        'favorite_count': [0] * n,
        'crawl_timestamp': [datetime.now().isoformat()] * n,
    }
    df = pd.DataFrame(data)

    # Calculated columns (mirroring DataProcessor output)
    df['engagement_rate'] = (df['like_count'] + df['comment_count']) / df['view_count'].replace(0, 1) * 100
    df['like_to_view_ratio'] = df['like_count'] / df['view_count'].replace(0, 1) * 100
    df['comment_to_like_ratio'] = df['comment_count'] / df['like_count'].replace(0, 1) * 100
    df['category'] = [
        'Tech Reviews', 'Tutorials', 'Product Comparisons', 'News Updates',
        'Unboxings', 'Price Analysis', 'Software Updates', 'Accessories',
        'General', 'General'
    ]
    df['channel_id'] = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'

    return df


@pytest.fixture
def sample_engagement_metrics():
    """Pre-computed engagement metrics dict."""
    return {
        'avg_views_per_video': 8000.0,
        'avg_likes_per_video': 365.0,
        'avg_comments_per_video': 51.0,
        'avg_engagement_rate': 5.25,
        'total_potential_reach': 80000,
        'video_growth_trend': 3,
        'most_viewed_video': 'Unboxing new gadget',
        'most_liked_video': 'Unboxing new gadget',
        'best_engagement_video': 'Phone review test',
        'engagement_efficiency': 5.20
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_db_session():
    """A MagicMock that mimics a SQLAlchemy Session."""
    session = MagicMock()
    session.execute = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_db_manager(mock_db_session):
    """A MagicMock DatabaseManager that returns the mock session."""
    manager = MagicMock()
    manager.get_session.return_value = mock_db_session
    manager.engine = MagicMock()
    return manager
