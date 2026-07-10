"""
YouTube API Handler Module
Handles YouTube Data API v3 interactions
"""
import os
import time
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YouTubeAPIHandler:
    def __init__(self):
        # Try st.secrets first (Streamlit Cloud), then fall back to os.getenv (local .env)
        try:
            import streamlit as st
            self.api_key = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY"))
        except Exception:
            self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable not set")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.quota_remaining = 10000  # Daily quota limit
        
    def get_channel_details(self, channel_id: str) -> Dict:
        """
        Retrieve channel details using channel ID
        """
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            )
            response = request.execute()
            
            if not response['items']:
                raise ValueError(f"No channel found with ID: {channel_id}")
            
            return response['items'][0]
            
        except HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                raise Exception("YouTube API quota exceeded")
            elif e.resp.status == 400:
                raise ValueError(f"Invalid channel ID: {channel_id}")
            else:
                raise e
    
    def get_channel_by_username(self, username: str) -> Dict:
        """
        Retrieve channel details using custom username (@handle)
        """
        try:
            # Remove @ symbol if present
            clean_username = username.lstrip('@')
            
            request = self.youtube.search().list(
                part='snippet',
                type='channel',
                q=clean_username,
                maxResults=1
            )
            response = request.execute()
            
            if not response['items']:
                raise ValueError(f"No channel found with username: {username}")
            
            # Get the actual channel ID from search result
            channel_id = response['items'][0]['snippet']['channelId']
            
            # Now get full channel details using the ID
            return self.get_channel_details(channel_id)
            
        except HttpError as e:
            raise e
    
    def get_channel_videos(self, upload_playlist_id: str, max_results: int = 50) -> List[Dict]:
        """
        Retrieve video IDs from channel's upload playlist
        """
        try:
            request = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=upload_playlist_id,
                maxResults=max_results
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video_id = item['snippet']['resourceId']['videoId']
                publish_date = item['snippet']['publishedAt']
                title = item['snippet']['title']
                
                videos.append({
                    'video_id': video_id,
                    'publish_date': publish_date,
                    'title': title
                })
            
            return videos
            
        except HttpError as e:
            raise e
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Retrieve detailed information for multiple videos
        """
        if not video_ids:
            return []
        
        # YouTube API allows max 50 video IDs per request
        chunk_size = 50
        video_chunks = [video_ids[i:i + chunk_size] for i in range(0, len(video_ids), chunk_size)]
        
        all_video_details = []
        
        for chunk in video_chunks:
            try:
                request = self.youtube.videos().list(
                    part='snippet,statistics',
                    id=','.join(chunk)
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    statistics = item.get('statistics', {})
                    
                    video_detail = {
                        'video_id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'publish_date': item['snippet']['publishedAt'],
                        'view_count': int(statistics.get('viewCount', 0)),
                        'like_count': int(statistics.get('likeCount', 0)),
                        'comment_count': int(statistics.get('commentCount', 0)),
                        'favorite_count': int(statistics.get('favoriteCount', 0))
                    }
                    all_video_details.append(video_detail)
                
                # Rate limiting - don't exceed API quota
                time.sleep(0.1)

            except HttpError as e:
                raise e

        return all_video_details

    def get_video_comments(self, video_id: str, max_results: int = 50) -> List[Dict]:
        """
        Retrieve top-level comments for a single video via the commentThreads
        endpoint. Works with an API key (no OAuth needed for reads).

        Returns a list of dicts:
            {comment_id, video_id, author, text, like_count, published_at}
        Returns an empty list if comments are disabled for the video.
        """
        comments = []
        page_token = None

        try:
            while len(comments) < max_results:
                request = self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=min(100, max_results - len(comments)),
                    textFormat='plainText',
                    order='relevance',
                    pageToken=page_token
                )
                response = request.execute()

                for item in response.get('items', []):
                    top = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'comment_id': item['id'],
                        'video_id': video_id,
                        'author': top.get('authorDisplayName', ''),
                        'text': top.get('textDisplay', ''),
                        'like_count': int(top.get('likeCount', 0)),
                        'published_at': top.get('publishedAt')
                    })

                page_token = response.get('nextPageToken')
                if not page_token:
                    break

                # Rate limiting - don't exceed API quota
                time.sleep(0.1)

            return comments[:max_results]

        except HttpError as e:
            # Comments disabled is common and expected — return what we have.
            if e.resp.status == 403 and 'commentsDisabled' in str(e):
                return comments
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                raise Exception("YouTube API quota exceeded")
            # Any other error: return whatever we collected rather than crash.
            return comments