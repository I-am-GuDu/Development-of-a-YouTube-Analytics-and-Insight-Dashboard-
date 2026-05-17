-- database: :memory:

-- Create users table (authentication)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL DEFAULT '',
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create channels table
CREATE TABLE IF NOT EXISTS channels (
    channel_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP,
    subscriber_count BIGINT,
    view_count BIGINT,
    video_count INT,
    thumbnail_url VARCHAR(500),
    crawl_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create videos table
CREATE TABLE IF NOT EXISTS videos (
    video_id VARCHAR(50) PRIMARY KEY,
    channel_id VARCHAR(50) REFERENCES channels(channel_id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    publish_date TIMESTAMP,
    view_count BIGINT,
    like_count BIGINT,
    comment_count BIGINT,
    favorite_count BIGINT,
    engagement_rate DECIMAL(10,4),
    like_to_view_ratio DECIMAL(10,4),
    comment_to_like_ratio DECIMAL(10,4),
    crawl_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create analytics_summary table for pre-computed metrics
CREATE TABLE IF NOT EXISTS analytics_summary (
    channel_id VARCHAR(50) PRIMARY KEY REFERENCES channels(channel_id) ON DELETE CASCADE,
    avg_views_per_video DECIMAL(15,2),
    avg_likes_per_video DECIMAL(15,2),
    avg_engagement_rate DECIMAL(10,4),
    total_potential_reach BIGINT,
    video_growth_trend INT,
    most_viewed_video VARCHAR(500),
    most_liked_video VARCHAR(500),
    best_engagement_video VARCHAR(500),
    engagement_efficiency DECIMAL(10,4),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_publish_date ON videos(publish_date);
CREATE INDEX IF NOT EXISTS idx_videos_engagement_rate ON videos(engagement_rate DESC);