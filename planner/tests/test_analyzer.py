"""Tests for analyzer module."""

import pytest
from datetime import datetime
from planner.analyzer import RouteAnalyzer


@pytest.fixture
def analyzer():
    """Create a RouteAnalyzer instance."""
    return RouteAnalyzer()


class TestRouteAnalyzer:
    """Tests for RouteAnalyzer class."""

    def test_build_context_complete(
        self,
        analyzer,
        sample_location_origin,
        sample_location_destination,
        sample_route_segments,
        sample_weather_forecasts,
        sample_elevation_profile,
        sample_preferences,
    ):
        """Test building complete context for Claude."""
        warnings = ["High wind speeds expected", "Steep climbs ahead"]
        gear = ["Windbreaker", "Extra water"]

        context = analyzer.build_context(
            sample_location_origin,
            sample_location_destination,
            sample_route_segments,
            sample_weather_forecasts,
            sample_elevation_profile,
            sample_preferences,
            warnings,
            gear,
        )

        # Check that context contains key sections
        assert "Route Overview" in context
        assert "User Preferences" in context
        assert "Elevation Profile" in context
        assert "Weather Forecast" in context
        assert "Route Segments" in context
        assert "Warnings" in context
        assert "Recommended Gear" in context
        assert "Analysis Request" in context

        # Check that data is included
        assert "Sakai City" in context
        assert "Yoshino Mountain" in context
        assert "50.0 km" in context  # Total distance
        assert "moderate" in context  # Difficulty
        assert "High wind speeds expected" in context
        assert "Windbreaker" in context

    def test_build_route_summary(
        self, analyzer, sample_location_origin, sample_location_destination
    ):
        """Test route summary building."""
        summary = analyzer._build_route_summary(
            sample_location_origin,
            sample_location_destination,
            total_distance=75.5,
            total_elevation_gain=1200.0,
            total_elevation_loss=350.0,
            total_duration=240,
        )

        assert "Sakai City" in summary
        assert "Yoshino Mountain" in summary
        assert "75.5 km" in summary
        assert "1200 m" in summary
        assert "350 m" in summary
        assert "4h 0m" in summary

    def test_build_route_summary_no_names(self, analyzer):
        """Test route summary with locations without names."""
        origin = type("Location", (), {"lat": 34.573, "lng": 135.483, "name": None})()
        dest = type("Location", (), {"lat": 34.396, "lng": 135.757, "name": None})()

        summary = analyzer._build_route_summary(
            origin, dest, 50.0, 800.0, 200.0, 180
        )

        # Should use coordinates when no name
        assert "34.573" in summary
        assert "135.483" in summary

    def test_build_preferences_summary(self, analyzer, sample_preferences):
        """Test preferences summary building."""
        summary = analyzer._build_preferences_summary(sample_preferences)

        assert "moderate" in summary
        assert "Avoid Traffic:** Yes" in summary
        assert "Prefer Scenic Routes:** Yes" in summary
        assert "100.0 km" in summary
        assert "1500.0 m" in summary

    def test_build_preferences_summary_minimal(self, analyzer):
        """Test preferences summary with minimal preferences."""
        from planner.schemas import RoutePreferences

        prefs = RoutePreferences(
            difficulty="easy",
            avoid_traffic=False,
            prefer_scenic=False,
        )

        summary = analyzer._build_preferences_summary(prefs)

        assert "easy" in summary
        assert "Avoid Traffic:** No" in summary
        assert "Prefer Scenic Routes:** No" in summary
        assert "Max Distance" not in summary
        assert "Max Elevation Gain" not in summary

    def test_build_elevation_analysis(
        self, analyzer, sample_elevation_profile, sample_route_segments
    ):
        """Test elevation analysis building."""
        analysis = analyzer._build_elevation_analysis(
            sample_elevation_profile, sample_route_segments
        )

        assert "Elevation Profile" in analysis
        assert "Minimum Elevation" in analysis
        assert "Maximum Elevation" in analysis
        assert "Average Elevation" in analysis
        assert "Steepest Climb" in analysis

    def test_build_elevation_analysis_empty(self, analyzer):
        """Test elevation analysis with no data."""
        analysis = analyzer._build_elevation_analysis([], [])
        assert "No elevation data available" in analysis

    def test_build_weather_summary(self, analyzer, sample_weather_forecasts):
        """Test weather summary building."""
        summary = analyzer._build_weather_summary(sample_weather_forecasts)

        assert "Weather Forecast" in summary
        assert "Average Temperature" in summary
        assert "Maximum Wind Speed" in summary
        assert "Average Precipitation Probability" in summary
        assert "Expected Conditions" in summary

    def test_build_weather_summary_empty(self, analyzer):
        """Test weather summary with no data."""
        summary = analyzer._build_weather_summary([])
        assert "No weather data available" in summary

    def test_build_segments_detail(self, analyzer, sample_route_segments):
        """Test segments detail building."""
        detail = analyzer._build_segments_detail(sample_route_segments)

        assert "Route Segments" in detail
        assert "10.0 km" in detail
        assert "15.0 km" in detail
        assert "25.0 km" in detail
        assert "paved" in detail
        assert "gravel" in detail

    def test_build_warnings_and_gear(self, analyzer):
        """Test warnings and gear section building."""
        warnings = ["High winds", "Steep climbs"]
        gear = ["Windbreaker", "Extra food"]

        section = analyzer._build_warnings_and_gear(warnings, gear)

        assert "Warnings" in section
        assert "High winds" in section
        assert "Steep climbs" in section
        assert "Recommended Gear" in section
        assert "Windbreaker" in section
        assert "Extra food" in section

    def test_build_warnings_and_gear_empty(self, analyzer):
        """Test warnings and gear with empty lists."""
        section = analyzer._build_warnings_and_gear([], [])

        assert "None" in section
        assert "Standard cycling gear" in section

    def test_build_analysis_prompt(self, analyzer):
        """Test analysis prompt building."""
        prompt = analyzer._build_analysis_prompt()

        assert "Analysis Request" in prompt
        assert "Overall Assessment" in prompt
        assert "Highlights" in prompt
        assert "Challenges" in prompt
        assert "Timing Recommendations" in prompt
        assert "Safety Considerations" in prompt
        assert "Alternative Suggestions" in prompt

    def test_summarize_route_stats(self, analyzer, sample_route_segments):
        """Test route statistics summary."""
        stats = analyzer.summarize_route_stats(sample_route_segments)

        assert stats["total_distance_km"] == 50.0
        assert stats["total_elevation_gain_m"] == 900.0
        assert stats["total_elevation_loss_m"] == 170.0
        assert stats["total_duration_min"] == 235
        assert stats["num_segments"] == 3

        # Check surface distribution
        assert "paved" in stats["surface_distribution"]
        assert "gravel" in stats["surface_distribution"]
        assert stats["surface_distribution"]["paved"] == 35.0  # 10 + 25
        assert stats["surface_distribution"]["gravel"] == 15.0

    def test_summarize_route_stats_empty(self, analyzer):
        """Test route statistics with empty segments."""
        stats = analyzer.summarize_route_stats([])

        assert stats["total_distance_km"] == 0.0
        assert stats["total_elevation_gain_m"] == 0.0
        assert stats["total_elevation_loss_m"] == 0.0
        assert stats["total_duration_min"] == 0
        assert stats["num_segments"] == 0
        assert stats["surface_distribution"] == {}
