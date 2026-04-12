"""
Unit Tests for Dashboard Charts Module
Verifies that each chart function returns a valid Plotly Figure.
Streamlit session state is mocked — no running Streamlit app needed.
"""
import pytest
import pandas as pd
import plotly.graph_objects as go
from unittest.mock import patch, MagicMock


# ─── Helper to mock Streamlit session state ──────────────────────────────────

def _mock_session_state(theme='dark'):
    """Return a dict-like mock for st.session_state."""
    state = {'theme': theme}
    return state


# ═══════════════════════════════════════════════════════════════════════════════
# THEME COLORS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetThemeColors:
    """Tests for charts.get_theme_colors()"""

    @patch('dashboard.charts.st')
    def test_dark_theme(self, mock_st):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import get_theme_colors
        colors = get_theme_colors()

        assert colors['text_primary'] == '#FFFFFF'
        assert colors['template'] == 'plotly_dark'

    @patch('dashboard.charts.st')
    def test_light_theme(self, mock_st):
        mock_st.session_state = _mock_session_state('light')
        from dashboard.charts import get_theme_colors
        colors = get_theme_colors()

        assert colors['text_primary'] == '#0f0f0f'
        assert colors['template'] == 'plotly_white'


# ═══════════════════════════════════════════════════════════════════════════════
# CHART FUNCTIONS — each should return a go.Figure
# ═══════════════════════════════════════════════════════════════════════════════

class TestViewsAreaChart:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import views_area_chart
        fig = views_area_chart(sample_video_df)
        assert isinstance(fig, go.Figure)

    @patch('dashboard.charts.st')
    def test_has_traces(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import views_area_chart
        fig = views_area_chart(sample_video_df)
        # Should have area trace + upload markers
        assert len(fig.data) >= 2


class TestTrafficSourcesDonut:
    @patch('dashboard.charts.st')
    def test_returns_figure_with_categories(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import traffic_sources_donut
        fig = traffic_sources_donut(sample_video_df)
        assert isinstance(fig, go.Figure)

    @patch('dashboard.charts.st')
    def test_returns_none_without_category(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import traffic_sources_donut
        df = sample_video_df.drop(columns=['category'])
        result = traffic_sources_donut(df)
        assert result is None


class TestEngagementDistribution:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import engagement_distribution_chart
        fig = engagement_distribution_chart(sample_video_df)
        assert isinstance(fig, go.Figure)


class TestViewsVsLikesScatter:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import views_vs_likes_scatter
        fig = views_vs_likes_scatter(sample_video_df, top_n=5)
        assert isinstance(fig, go.Figure)


class TestCategoryPerformanceBar:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import category_performance_bar
        fig = category_performance_bar(sample_video_df)
        assert isinstance(fig, go.Figure)


class TestCategoryDistributionPie:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import category_distribution_pie
        fig = category_distribution_pie(sample_video_df)
        assert isinstance(fig, go.Figure)


class TestEngagementOverTimeLine:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import engagement_over_time_line
        fig = engagement_over_time_line(sample_video_df)
        assert isinstance(fig, go.Figure)

    @patch('dashboard.charts.st')
    def test_has_two_traces(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import engagement_over_time_line
        fig = engagement_over_time_line(sample_video_df)
        # Individual points + rolling average line
        assert len(fig.data) == 2


class TestViewsOverTimeLine:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import views_over_time_line
        fig = views_over_time_line(sample_video_df)
        assert isinstance(fig, go.Figure)


class TestPostingFrequencyChart:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import posting_frequency_chart
        fig = posting_frequency_chart(sample_video_df)
        assert isinstance(fig, go.Figure)


class TestOptimalPostingHeatmap:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st, sample_video_df):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import optimal_posting_heatmap
        fig = optimal_posting_heatmap(sample_video_df)
        assert isinstance(fig, go.Figure)


class TestGrowthForecastChart:
    @patch('dashboard.charts.st')
    def test_returns_figure_with_data(self, mock_st):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import growth_forecast_chart
        from datetime import datetime, timedelta

        fake_forecast = {
            'forecast': [
                (datetime.now() + timedelta(days=i), 5.0 + i * 0.1)
                for i in range(7)
            ],
            'confidence': 'medium'
        }
        fig = growth_forecast_chart(fake_forecast)
        assert isinstance(fig, go.Figure)

    @patch('dashboard.charts.st')
    def test_returns_none_without_data(self, mock_st):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import growth_forecast_chart
        result = growth_forecast_chart({'forecast': []})
        assert result is None


class TestMultiChannelComparisonBar:
    @patch('dashboard.charts.st')
    def test_returns_figure(self, mock_st):
        mock_st.session_state = _mock_session_state('dark')
        from dashboard.charts import multi_channel_comparison_bar

        df = pd.DataFrame({
            'title': ['Channel A', 'Channel B'],
            'avg_engagement_rate': [5.2, 3.8]
        })
        fig = multi_channel_comparison_bar(
            df, 'avg_engagement_rate', 'Engagement Comparison', 'Engagement %'
        )
        assert isinstance(fig, go.Figure)
