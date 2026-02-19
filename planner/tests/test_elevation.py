"""Tests for elevation module."""

import pytest
from unittest.mock import patch, MagicMock
import httpx
from planner.elevation import ElevationService, ElevationAPIError


@pytest.fixture
def elevation_service():
    """Create an ElevationService instance."""
    return ElevationService()


@pytest.fixture
def mock_elevation_response():
    """Mock OpenMeteo elevation API response."""
    return {"elevation": [100.0, 150.0, 200.0, 250.0, 300.0]}


class TestElevationService:
    """Tests for ElevationService class."""

    @pytest.mark.asyncio
    async def test_get_elevation_profile_success(
        self, elevation_service, mock_elevation_response
    ):
        """Test successful elevation profile retrieval."""
        coordinates = [
            (34.573, 135.483),
            (34.560, 135.500),
            (34.550, 135.520),
            (34.540, 135.540),
            (34.530, 135.560),
        ]

        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elevation_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            elevations = await elevation_service.get_elevation_profile(coordinates)

            assert len(elevations) == 5
            assert elevations[0] == 100.0
            assert elevations[4] == 300.0

    @pytest.mark.asyncio
    async def test_get_elevation_profile_empty_coordinates(self, elevation_service):
        """Test elevation profile with empty coordinates."""
        elevations = await elevation_service.get_elevation_profile([])
        assert elevations == []

    @pytest.mark.asyncio
    async def test_get_elevation_profile_api_error_fallback(self, elevation_service):
        """Test elevation profile with API error triggers fallback."""
        coordinates = [(34.573, 135.483), (34.560, 135.500)]

        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock API error
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=mock_response
            )
            mock_get.return_value = mock_response

            # Should fall back to estimation
            elevations = await elevation_service.get_elevation_profile(coordinates)

            assert len(elevations) == 2
            # Fallback returns estimated values
            assert all(isinstance(e, float) for e in elevations)

    @pytest.mark.asyncio
    async def test_get_elevation_profile_sampling(
        self, elevation_service, mock_elevation_response
    ):
        """Test elevation profile sampling for large coordinate lists."""
        # Create 200 coordinates (exceeds max_points of 100)
        coordinates = [(34.0 + i * 0.001, 135.0 + i * 0.001) for i in range(200)]

        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elevation_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            elevations = await elevation_service.get_elevation_profile(coordinates)

            # Should interpolate back to 200 points
            assert len(elevations) == 200

    @pytest.mark.asyncio
    async def test_calculate_elevation_stats_gains_and_losses(self, elevation_service):
        """Test elevation statistics calculation."""
        elevations = [100.0, 150.0, 200.0, 180.0, 220.0, 200.0, 250.0]

        gain, loss = await elevation_service.calculate_elevation_stats(elevations)

        # Gains: 50 + 50 + 40 + 50 = 190
        # Losses: 20 + 20 = 40
        assert gain == pytest.approx(190.0)
        assert loss == pytest.approx(40.0)

    @pytest.mark.asyncio
    async def test_calculate_elevation_stats_empty(self, elevation_service):
        """Test elevation statistics with empty list."""
        gain, loss = await elevation_service.calculate_elevation_stats([])
        assert gain == 0.0
        assert loss == 0.0

    @pytest.mark.asyncio
    async def test_calculate_elevation_stats_single_point(self, elevation_service):
        """Test elevation statistics with single point."""
        gain, loss = await elevation_service.calculate_elevation_stats([100.0])
        assert gain == 0.0
        assert loss == 0.0

    def test_sample_coordinates_within_limit(self, elevation_service):
        """Test coordinate sampling when within limit."""
        coordinates = [(34.0 + i * 0.01, 135.0 + i * 0.01) for i in range(50)]
        sampled = elevation_service._sample_coordinates(coordinates, 100)

        # Should return original coordinates
        assert len(sampled) == 50
        assert sampled == coordinates

    def test_sample_coordinates_exceeds_limit(self, elevation_service):
        """Test coordinate sampling when exceeding limit."""
        coordinates = [(34.0 + i * 0.001, 135.0 + i * 0.001) for i in range(200)]
        sampled = elevation_service._sample_coordinates(coordinates, 100)

        # Should sample down to 100 points
        assert len(sampled) == 100
        # Should include first and last points
        assert sampled[0] == coordinates[0]
        assert sampled[-1] == coordinates[-1]

    def test_interpolate_elevations(self, elevation_service):
        """Test elevation interpolation."""
        original_elevations = [100.0, 200.0, 300.0]
        interpolated = elevation_service._interpolate_elevations(original_elevations, 3, 5)

        assert len(interpolated) == 5
        assert interpolated[0] == pytest.approx(100.0)
        assert interpolated[2] == pytest.approx(200.0)
        assert interpolated[4] == pytest.approx(300.0)
        # Middle values should be interpolated
        assert 100.0 < interpolated[1] < 200.0
        assert 200.0 < interpolated[3] < 300.0

    def test_interpolate_elevations_same_count(self, elevation_service):
        """Test interpolation with same count returns original."""
        elevations = [100.0, 200.0, 300.0]
        result = elevation_service._interpolate_elevations(elevations, 3, 3)
        assert result == elevations

    @pytest.mark.asyncio
    async def test_fallback_elevation_fetch(self, elevation_service):
        """Test fallback elevation estimation."""
        coordinates = [
            (30.0, 135.0),  # Low latitude
            (35.0, 135.0),  # Mid latitude
            (40.0, 135.0),  # Higher latitude
        ]

        elevations = await elevation_service._fallback_elevation_fetch(coordinates)

        assert len(elevations) == 3
        # Fallback estimates based on latitude
        # Higher latitude should generally have higher estimated elevation
        assert all(e >= 0.0 for e in elevations)
