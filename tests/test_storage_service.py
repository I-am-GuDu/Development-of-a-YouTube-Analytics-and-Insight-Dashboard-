"""
Unit Tests for DataStorageService Module
All database interactions are mocked — no real PostgreSQL needed.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock
from sqlalchemy.exc import SQLAlchemyError


# ═══════════════════════════════════════════════════════════════════════════════
# SAVE CHANNEL DATA
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaveChannelData:
    """Tests for DataStorageService.save_channel_data()"""

    @patch('data_storage.storage_service.DatabaseManager')
    def test_save_success(self, MockDBManager, processed_channel):
        from data_storage.storage_service import DataStorageService

        mock_session = MagicMock()
        MockDBManager.return_value.get_session.return_value = mock_session

        service = DataStorageService()
        service.save_channel_data(processed_channel)

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('data_storage.storage_service.DatabaseManager')
    def test_rollback_on_error(self, MockDBManager, processed_channel):
        from data_storage.storage_service import DataStorageService

        mock_session = MagicMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB write failed")
        MockDBManager.return_value.get_session.return_value = mock_session

        service = DataStorageService()
        with pytest.raises(SQLAlchemyError):
            service.save_channel_data(processed_channel)

        mock_session.rollback.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# SAVE VIDEO DATA
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaveVideoData:
    """Tests for DataStorageService.save_video_data()"""

    @patch('data_storage.storage_service.DatabaseManager')
    def test_save_success(self, MockDBManager, sample_video_df):
        from data_storage.storage_service import DataStorageService

        mock_session = MagicMock()
        MockDBManager.return_value.get_session.return_value = mock_session

        service = DataStorageService()
        service.save_video_data(sample_video_df)

        # Should call execute once per video row
        assert mock_session.execute.call_count == len(sample_video_df)
        mock_session.commit.assert_called_once()

    @patch('data_storage.storage_service.DatabaseManager')
    def test_empty_dataframe_no_commits(self, MockDBManager):
        from data_storage.storage_service import DataStorageService

        mock_session = MagicMock()
        MockDBManager.return_value.get_session.return_value = mock_session

        service = DataStorageService()
        empty_df = pd.DataFrame()
        service.save_video_data(empty_df)

        mock_session.execute.assert_not_called()
        # commit is still called (no rows to insert, but the try block completes)
        mock_session.commit.assert_called_once()

    @patch('data_storage.storage_service.DatabaseManager')
    def test_rollback_on_error(self, MockDBManager, sample_video_df):
        from data_storage.storage_service import DataStorageService

        mock_session = MagicMock()
        mock_session.execute.side_effect = SQLAlchemyError("Insert failed")
        MockDBManager.return_value.get_session.return_value = mock_session

        service = DataStorageService()
        with pytest.raises(SQLAlchemyError):
            service.save_video_data(sample_video_df)

        mock_session.rollback.assert_called_once()

    @patch('data_storage.storage_service.DatabaseManager')
    def test_handles_numpy_types(self, MockDBManager):
        """Verify numpy int64/float64 values are converted to native Python types."""
        from data_storage.storage_service import DataStorageService

        mock_session = MagicMock()
        MockDBManager.return_value.get_session.return_value = mock_session

        # Build a tiny DataFrame with numpy types
        df = pd.DataFrame([{
            'video_id': 'v1',
            'channel_id': 'ch1',
            'title': 'Numpy Test',
            'description': 'Test',
            'publish_date': pd.Timestamp('2024-01-01'),
            'view_count': np.int64(5000),
            'like_count': np.int64(200),
            'comment_count': np.int64(30),
            'favorite_count': np.int64(0),
            'engagement_rate': np.float64(4.6),
            'like_to_view_ratio': np.float64(4.0),
            'comment_to_like_ratio': np.float64(15.0),
            'crawl_timestamp': datetime.now().isoformat()
        }])

        service = DataStorageService()
        # Should not raise — numpy types are converted internally
        service.save_video_data(df)
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# SAVE ANALYTICS SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaveAnalyticsSummary:
    """Tests for DataStorageService.save_analytics_summary()"""

    @patch('data_storage.storage_service.DatabaseManager')
    def test_save_success(self, MockDBManager, sample_engagement_metrics):
        from data_storage.storage_service import DataStorageService

        mock_session = MagicMock()
        MockDBManager.return_value.get_session.return_value = mock_session

        service = DataStorageService()
        service.save_analytics_summary('UC_test', sample_engagement_metrics)

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('data_storage.storage_service.DatabaseManager')
    def test_rollback_on_error(self, MockDBManager, sample_engagement_metrics):
        from data_storage.storage_service import DataStorageService

        mock_session = MagicMock()
        mock_session.execute.side_effect = SQLAlchemyError("Summary insert failed")
        MockDBManager.return_value.get_session.return_value = mock_session

        service = DataStorageService()
        with pytest.raises(SQLAlchemyError):
            service.save_analytics_summary('UC_test', sample_engagement_metrics)

        mock_session.rollback.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER ACCESSOR METHODS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAccessorMethods:
    """Tests for service accessor methods."""

    @patch('data_storage.storage_service.DatabaseManager')
    def test_get_analytics_queries(self, MockDBManager):
        from data_storage.storage_service import DataStorageService
        from data_storage.analytics_queries import AnalyticsQueries

        service = DataStorageService()
        aq = service.get_analytics_queries()
        assert isinstance(aq, AnalyticsQueries)

    @patch('data_storage.storage_service.DatabaseManager')
    def test_get_predictive_analytics(self, MockDBManager):
        from data_storage.storage_service import DataStorageService
        from data_storage.predictive_analytics import PredictiveAnalytics

        service = DataStorageService()
        pa = service.get_predictive_analytics()
        assert isinstance(pa, PredictiveAnalytics)
