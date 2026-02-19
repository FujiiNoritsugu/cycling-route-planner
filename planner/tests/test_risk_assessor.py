"""Tests for risk_assessor module."""

import pytest
from datetime import datetime
from planner.risk_assessor import RiskAssessor
from planner.schemas import RouteSegment, WeatherForecast, RoutePreferences


@pytest.fixture
def risk_assessor():
    """Create a RiskAssessor instance."""
    return RiskAssessor()


@pytest.fixture
def high_wind_forecast():
    """Weather forecast with high wind."""
    return [
        WeatherForecast(
            time=datetime(2025, 3, 15, 8, 0),
            temperature=15.0,
            wind_speed=12.0,  # High wind
            wind_direction=180.0,
            precipitation_probability=20.0,
            weather_code=1,
            description="Mainly clear",
        )
    ]


@pytest.fixture
def rainy_forecast():
    """Weather forecast with high rain probability."""
    return [
        WeatherForecast(
            time=datetime(2025, 3, 15, 8, 0),
            temperature=15.0,
            wind_speed=5.0,
            wind_direction=180.0,
            precipitation_probability=75.0,  # High rain probability
            weather_code=61,
            description="Slight rain",
        )
    ]


@pytest.fixture
def cold_forecast():
    """Weather forecast with cold temperature."""
    return [
        WeatherForecast(
            time=datetime(2025, 3, 15, 8, 0),
            temperature=2.0,  # Cold
            wind_speed=5.0,
            wind_direction=180.0,
            precipitation_probability=10.0,
            weather_code=0,
            description="Clear sky",
        )
    ]


@pytest.fixture
def hot_forecast():
    """Weather forecast with hot temperature."""
    return [
        WeatherForecast(
            time=datetime(2025, 3, 15, 13, 0),
            temperature=38.0,  # Hot
            wind_speed=5.0,
            wind_direction=180.0,
            precipitation_probability=10.0,
            weather_code=0,
            description="Clear sky",
        )
    ]


@pytest.fixture
def high_elevation_segments():
    """Route segments with high elevation gain."""
    return [
        RouteSegment(
            coordinates=[(34.0, 135.0), (34.1, 135.1)],
            distance_km=50.0,
            elevation_gain_m=2500.0,  # Very high
            elevation_loss_m=500.0,
            estimated_duration_min=300,
            surface_type="paved",
        )
    ]


class TestRiskAssessor:
    """Tests for RiskAssessor class."""

    def test_assess_route_basic(
        self,
        risk_assessor,
        sample_route_segments,
        sample_weather_forecasts,
        sample_preferences,
    ):
        """Test basic route assessment."""
        warnings, gear = risk_assessor.assess_route(
            sample_route_segments, sample_weather_forecasts, sample_preferences
        )

        # Should have basic gear
        assert "Helmet" in gear
        assert "Water bottles (at least 2)" in gear
        assert "Repair kit (spare tube, tire levers, pump)" in gear
        assert "Bike lights (front and rear)" in gear

        # Warnings list should exist (may be empty for mild conditions)
        assert isinstance(warnings, list)

    def test_assess_high_wind(
        self, risk_assessor, sample_route_segments, high_wind_forecast, sample_preferences
    ):
        """Test assessment with high wind conditions."""
        warnings, gear = risk_assessor.assess_route(
            sample_route_segments, high_wind_forecast, sample_preferences
        )

        # Should warn about wind
        wind_warnings = [w for w in warnings if "wind" in w.lower()]
        assert len(wind_warnings) > 0

        # Should recommend wind gear
        assert any("wind" in g.lower() for g in gear)

    def test_assess_rain(
        self, risk_assessor, sample_route_segments, rainy_forecast, sample_preferences
    ):
        """Test assessment with rainy conditions."""
        warnings, gear = risk_assessor.assess_route(
            sample_route_segments, rainy_forecast, sample_preferences
        )

        # Should warn about rain
        rain_warnings = [w for w in warnings if "rain" in w.lower()]
        assert len(rain_warnings) > 0

        # Should recommend rain gear
        assert any("rain" in g.lower() for g in gear)

    def test_assess_cold_weather(
        self, risk_assessor, sample_route_segments, cold_forecast, sample_preferences
    ):
        """Test assessment with cold weather."""
        warnings, gear = risk_assessor.assess_route(
            sample_route_segments, cold_forecast, sample_preferences
        )

        # Should warn about cold
        cold_warnings = [w for w in warnings if "cold" in w.lower() or "temperature" in w.lower()]
        assert len(cold_warnings) > 0

        # Should recommend warm gear
        assert any("thermal" in g.lower() or "gloves" in g.lower() for g in gear)

    def test_assess_hot_weather(
        self, risk_assessor, sample_route_segments, hot_forecast, sample_preferences
    ):
        """Test assessment with hot weather."""
        warnings, gear = risk_assessor.assess_route(
            sample_route_segments, hot_forecast, sample_preferences
        )

        # Should warn about heat
        heat_warnings = [w for w in warnings if "temperature" in w.lower() or "high" in w.lower()]
        assert len(heat_warnings) > 0

        # Should recommend sun protection
        assert any("sun" in g.lower() or "water" in g.lower() for g in gear)

    def test_assess_high_elevation(
        self,
        risk_assessor,
        high_elevation_segments,
        sample_weather_forecasts,
        sample_preferences,
    ):
        """Test assessment with high elevation gain."""
        warnings, gear = risk_assessor.assess_route(
            high_elevation_segments, sample_weather_forecasts, sample_preferences
        )

        # Should warn about elevation
        elevation_warnings = [w for w in warnings if "elevation" in w.lower() or "challenging" in w.lower()]
        assert len(elevation_warnings) > 0

        # Should recommend energy supplies
        assert any("energy" in g.lower() or "gel" in g.lower() or "bar" in g.lower() for g in gear)

    def test_assess_difficulty_mismatch(
        self, risk_assessor, high_elevation_segments, sample_weather_forecasts
    ):
        """Test assessment when route difficulty doesn't match preference."""
        easy_prefs = RoutePreferences(
            difficulty="easy",
            avoid_traffic=True,
            prefer_scenic=True,
        )

        warnings, gear = risk_assessor.assess_route(
            high_elevation_segments, sample_weather_forecasts, easy_prefs
        )

        # Should warn about difficulty mismatch
        mismatch_warnings = [w for w in warnings if "difficulty" in w.lower() or "preference" in w.lower()]
        assert len(mismatch_warnings) > 0

    def test_assess_long_distance(self, risk_assessor, sample_weather_forecasts, sample_preferences):
        """Test assessment with long distance route."""
        long_segments = [
            RouteSegment(
                coordinates=[(34.0, 135.0), (34.5, 135.5)],
                distance_km=120.0,  # Long distance
                elevation_gain_m=500.0,
                elevation_loss_m=500.0,
                estimated_duration_min=480,
                surface_type="paved",
            )
        ]

        warnings, gear = risk_assessor.assess_route(
            long_segments, sample_weather_forecasts, sample_preferences
        )

        # Should warn about distance
        distance_warnings = [w for w in warnings if "distance" in w.lower() or "long" in w.lower()]
        assert len(distance_warnings) > 0

        # Should recommend supplies for long ride
        assert any("energy" in g.lower() or "cash" in g.lower() or "charger" in g.lower() for g in gear)

    def test_assess_gravel_surface(self, risk_assessor, sample_weather_forecasts, sample_preferences):
        """Test assessment with gravel surface."""
        gravel_segments = [
            RouteSegment(
                coordinates=[(34.0, 135.0), (34.1, 135.1)],
                distance_km=40.0,
                elevation_gain_m=300.0,
                elevation_loss_m=300.0,
                estimated_duration_min=180,
                surface_type="gravel",
            ),
            RouteSegment(
                coordinates=[(34.1, 135.1), (34.2, 135.2)],
                distance_km=10.0,
                elevation_gain_m=100.0,
                elevation_loss_m=100.0,
                estimated_duration_min=50,
                surface_type="paved",
            ),
        ]

        warnings, gear = risk_assessor.assess_route(
            gravel_segments, sample_weather_forecasts, sample_preferences
        )

        # Should warn about unpaved surface
        surface_warnings = [w for w in warnings if "unpaved" in w.lower() or "gravel" in w.lower()]
        assert len(surface_warnings) > 0

        # Should recommend appropriate tires
        assert any("tire" in g.lower() for g in gear)

    def test_calculate_risk_score_low(
        self, risk_assessor, sample_route_segments, sample_weather_forecasts
    ):
        """Test risk score calculation for low-risk route."""
        score = risk_assessor.calculate_risk_score(
            sample_route_segments, sample_weather_forecasts
        )

        # Should be low to moderate risk
        assert 0 <= score <= 50

    def test_calculate_risk_score_high(
        self, risk_assessor, high_elevation_segments, high_wind_forecast
    ):
        """Test risk score calculation for high-risk route."""
        score = risk_assessor.calculate_risk_score(
            high_elevation_segments, high_wind_forecast
        )

        # Should be higher risk
        assert score > 30
        assert score <= 100

    def test_calculate_risk_score_boundaries(self, risk_assessor):
        """Test that risk score stays within 0-100 bounds."""
        # Create extreme conditions
        extreme_segments = [
            RouteSegment(
                coordinates=[(34.0, 135.0), (35.0, 136.0)],
                distance_km=200.0,
                elevation_gain_m=5000.0,
                elevation_loss_m=1000.0,
                estimated_duration_min=1000,
                surface_type="dirt",
            )
        ]

        extreme_weather = [
            WeatherForecast(
                time=datetime(2025, 3, 15, 8, 0),
                temperature=40.0,
                wind_speed=20.0,
                wind_direction=180.0,
                precipitation_probability=95.0,
                weather_code=95,
                description="Thunderstorm",
            )
        ]

        score = risk_assessor.calculate_risk_score(extreme_segments, extreme_weather)

        # Should not exceed 100
        assert 0 <= score <= 100

    def test_assess_weather_no_forecasts(
        self, risk_assessor
    ):
        """Test weather assessment with no forecasts."""
        warnings, gear = risk_assessor._assess_weather([])

        assert warnings == []
        assert gear == []

    def test_assess_elevation_exceeds_preference(self, risk_assessor):
        """Test elevation assessment when it exceeds user preference."""
        segments = [
            RouteSegment(
                coordinates=[(34.0, 135.0), (34.1, 135.1)],
                distance_km=30.0,
                elevation_gain_m=1200.0,
                elevation_loss_m=200.0,
                estimated_duration_min=180,
                surface_type="paved",
            )
        ]

        prefs = RoutePreferences(
            difficulty="moderate",
            avoid_traffic=True,
            prefer_scenic=True,
            max_elevation_gain_m=1000.0,  # Less than actual
        )

        warnings, gear = risk_assessor._assess_elevation(segments, prefs)

        # Should warn about exceeding preference
        exceed_warnings = [w for w in warnings if "exceeds" in w.lower()]
        assert len(exceed_warnings) > 0

    def test_assess_steep_segments(self, risk_assessor, sample_preferences):
        """Test assessment detects steep segments."""
        steep_segment = RouteSegment(
            coordinates=[(34.0, 135.0), (34.01, 135.01)],
            distance_km=1.0,
            elevation_gain_m=100.0,  # 10% gradient
            elevation_loss_m=10.0,
            estimated_duration_min=30,
            surface_type="paved",
        )

        warnings, gear = risk_assessor._assess_elevation([steep_segment], sample_preferences)

        # Should warn about steep climb
        steep_warnings = [w for w in warnings if "steep" in w.lower() or "gradient" in w.lower()]
        assert len(steep_warnings) > 0
