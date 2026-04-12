"""
Unit Tests for YouTubeAPIHandler Module
All YouTube Data API calls are mocked — no real API key needed.
"""
import pytest
from unittest.mock import patch, MagicMock
from googleapiclient.errors import HttpError


# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPIHandlerInit:
    """Tests for YouTubeAPIHandler.__init__()"""

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': ''}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_missing_api_key_raises(self, mock_build):
        """Handler should raise ValueError when YOUTUBE_API_KEY is empty."""
        from youtube_data_collection.api_handler import YouTubeAPIHandler
        with pytest.raises(ValueError, match="YOUTUBE_API_KEY"):
            YouTubeAPIHandler()

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key_123'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_init_success(self, mock_build):
        """Handler should initialize successfully with a valid key."""
        from youtube_data_collection.api_handler import YouTubeAPIHandler
        handler = YouTubeAPIHandler()
        assert handler.api_key == 'test_key_123'
        mock_build.assert_called_once_with('youtube', 'v3', developerKey='test_key_123')


# ═══════════════════════════════════════════════════════════════════════════════
# GET CHANNEL DETAILS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetChannelDetails:
    """Tests for YouTubeAPIHandler.get_channel_details()"""

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_success(self, mock_build, raw_channel_data):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        # Mock the API chain: youtube.channels().list().execute()
        mock_execute = MagicMock(return_value={'items': [raw_channel_data]})
        mock_list = MagicMock()
        mock_list.execute = mock_execute
        mock_channels = MagicMock()
        mock_channels.list.return_value = mock_list
        mock_build.return_value.channels.return_value = mock_channels

        handler = YouTubeAPIHandler()
        result = handler.get_channel_details('UC_x5XG1OV2P6uZZ5FSM9Ttw')

        assert result['id'] == 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
        assert result['snippet']['title'] == 'Test Channel'

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_channel_not_found(self, mock_build):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        mock_execute = MagicMock(return_value={'items': []})
        mock_list = MagicMock()
        mock_list.execute = mock_execute
        mock_channels = MagicMock()
        mock_channels.list.return_value = mock_list
        mock_build.return_value.channels.return_value = mock_channels

        handler = YouTubeAPIHandler()
        with pytest.raises(ValueError, match="No channel found"):
            handler.get_channel_details('UC_nonexistent')

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_quota_exceeded(self, mock_build):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        # Simulate a 403 quotaExceeded HttpError
        resp = MagicMock()
        resp.status = 403
        error = HttpError(resp, b'quotaExceeded')

        mock_list = MagicMock()
        mock_list.execute.side_effect = error
        mock_channels = MagicMock()
        mock_channels.list.return_value = mock_list
        mock_build.return_value.channels.return_value = mock_channels

        handler = YouTubeAPIHandler()
        with pytest.raises(Exception, match="quota exceeded"):
            handler.get_channel_details('UC_any')


# ═══════════════════════════════════════════════════════════════════════════════
# GET CHANNEL BY USERNAME
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetChannelByUsername:
    """Tests for YouTubeAPIHandler.get_channel_by_username()"""

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_success(self, mock_build, raw_channel_data):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        # Mock search().list().execute() → channelId
        mock_search_execute = MagicMock(return_value={
            'items': [{'snippet': {'channelId': 'UC_x5XG1OV2P6uZZ5FSM9Ttw'}}]
        })
        mock_search_list = MagicMock()
        mock_search_list.execute = mock_search_execute
        mock_search = MagicMock()
        mock_search.list.return_value = mock_search_list

        # Mock channels().list().execute() → full channel data
        mock_channel_execute = MagicMock(return_value={'items': [raw_channel_data]})
        mock_channel_list = MagicMock()
        mock_channel_list.execute = mock_channel_execute
        mock_channels = MagicMock()
        mock_channels.list.return_value = mock_channel_list

        youtube_mock = MagicMock()
        youtube_mock.search.return_value = mock_search
        youtube_mock.channels.return_value = mock_channels
        mock_build.return_value = youtube_mock

        handler = YouTubeAPIHandler()
        result = handler.get_channel_by_username('@TestChannel')

        assert result['id'] == 'UC_x5XG1OV2P6uZZ5FSM9Ttw'

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_username_not_found(self, mock_build):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        mock_search_execute = MagicMock(return_value={'items': []})
        mock_search_list = MagicMock()
        mock_search_list.execute = mock_search_execute
        mock_search = MagicMock()
        mock_search.list.return_value = mock_search_list
        mock_build.return_value.search.return_value = mock_search

        handler = YouTubeAPIHandler()
        with pytest.raises(ValueError, match="No channel found"):
            handler.get_channel_by_username('@nobody')


# ═══════════════════════════════════════════════════════════════════════════════
# GET CHANNEL VIDEOS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetChannelVideos:
    """Tests for YouTubeAPIHandler.get_channel_videos()"""

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_success(self, mock_build):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        mock_response = {
            'items': [
                {
                    'snippet': {
                        'resourceId': {'videoId': 'vid_001'},
                        'publishedAt': '2024-01-01T12:00:00Z',
                        'title': 'Test Video 1'
                    }
                },
                {
                    'snippet': {
                        'resourceId': {'videoId': 'vid_002'},
                        'publishedAt': '2024-01-08T12:00:00Z',
                        'title': 'Test Video 2'
                    }
                }
            ]
        }
        mock_execute = MagicMock(return_value=mock_response)
        mock_list = MagicMock()
        mock_list.execute = mock_execute
        mock_playlist = MagicMock()
        mock_playlist.list.return_value = mock_list
        mock_build.return_value.playlistItems.return_value = mock_playlist

        handler = YouTubeAPIHandler()
        result = handler.get_channel_videos('UU_test_playlist')

        assert len(result) == 2
        assert result[0]['video_id'] == 'vid_001'
        assert result[1]['title'] == 'Test Video 2'

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_empty_playlist(self, mock_build):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        mock_execute = MagicMock(return_value={'items': []})
        mock_list = MagicMock()
        mock_list.execute = mock_execute
        mock_playlist = MagicMock()
        mock_playlist.list.return_value = mock_list
        mock_build.return_value.playlistItems.return_value = mock_playlist

        handler = YouTubeAPIHandler()
        result = handler.get_channel_videos('UU_empty')

        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# GET VIDEO DETAILS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetVideoDetails:
    """Tests for YouTubeAPIHandler.get_video_details()"""

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_success(self, mock_build):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        mock_response = {
            'items': [{
                'id': 'vid_001',
                'snippet': {
                    'title': 'Test',
                    'description': 'Desc',
                    'publishedAt': '2024-01-01T00:00:00Z'
                },
                'statistics': {
                    'viewCount': '5000',
                    'likeCount': '200',
                    'commentCount': '30',
                    'favoriteCount': '0'
                }
            }]
        }
        mock_execute = MagicMock(return_value=mock_response)
        mock_list = MagicMock()
        mock_list.execute = mock_execute
        mock_videos = MagicMock()
        mock_videos.list.return_value = mock_list
        mock_build.return_value.videos.return_value = mock_videos

        handler = YouTubeAPIHandler()
        result = handler.get_video_details(['vid_001'])

        assert len(result) == 1
        assert result[0]['video_id'] == 'vid_001'
        assert result[0]['view_count'] == 5000
        assert result[0]['like_count'] == 200

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test_key'}, clear=False)
    @patch('youtube_data_collection.api_handler.build')
    def test_empty_id_list(self, mock_build):
        from youtube_data_collection.api_handler import YouTubeAPIHandler

        handler = YouTubeAPIHandler()
        result = handler.get_video_details([])

        assert result == []
