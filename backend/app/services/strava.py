"""Strava API integration service for athlete data and fitness analysis.

This module provides OAuth2 token exchange, activity fetching, and fitness
profile generation from Strava cycling data.
"""

import os
from datetime import datetime, timedelta, timezone

import httpx

STRAVA_API_BASE = "https://www.strava.com/api/v3"
STRAVA_AUTH_URL = "https://www.strava.com/oauth/token"


class StravaService:
    """Service for interacting with the Strava API."""

    def __init__(self) -> None:
        """Initialize Strava service with credentials from environment."""
        self.client_id = os.getenv("STRAVA_CLIENT_ID", "")
        self.client_secret = os.getenv("STRAVA_CLIENT_SECRET", "")

    async def exchange_token(self, code: str) -> dict:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Strava OAuth callback.

        Returns:
            Token response including access_token, refresh_token, and athlete data.

        Raises:
            httpx.HTTPStatusError: If the token exchange request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                STRAVA_AUTH_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh expired access token.

        Args:
            refresh_token: Refresh token from previous authentication.

        Returns:
            New token response including access_token and refresh_token.

        Raises:
            httpx.HTTPStatusError: If the refresh request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                STRAVA_AUTH_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_athlete(self, access_token: str) -> dict:
        """Get authenticated athlete profile.

        Args:
            access_token: Valid Strava access token.

        Returns:
            Athlete profile data from Strava.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{STRAVA_API_BASE}/athlete",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_activities(
        self, access_token: str, per_page: int = 50, page: int = 1
    ) -> list[dict]:
        """Get athlete's recent activities.

        Args:
            access_token: Valid Strava access token.
            per_page: Number of activities per page (max 200).
            page: Page number for pagination.

        Returns:
            List of activity summaries from Strava.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{STRAVA_API_BASE}/athlete/activities",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"per_page": per_page, "page": page},
            )
            response.raise_for_status()
            return response.json()

    def build_fitness_profile(self, activities: list[dict]) -> dict:
        """Build a fitness profile from Strava activities.

        Analyzes recent cycling activities to determine average/max distance,
        speed, elevation gain, ride frequency, and estimated fitness level.

        Args:
            activities: List of Strava activity summaries.

        Returns:
            Fitness profile dictionary with activity statistics.
        """
        # Filter to cycling activities only
        cycling = [
            a
            for a in activities
            if a.get("type") in ("Ride", "VirtualRide", "EBikeRide")
        ]

        if not cycling:
            return {
                "has_data": False,
                "message": "サイクリングアクティビティが見つかりませんでした",
            }

        distances_km = [a["distance"] / 1000 for a in cycling]
        speeds_kmh = [
            a["average_speed"] * 3.6 for a in cycling if a.get("average_speed")
        ]
        elevations_m = [
            a["total_elevation_gain"]
            for a in cycling
            if a.get("total_elevation_gain")
        ]
        durations_min = [
            a["moving_time"] / 60 for a in cycling if a.get("moving_time")
        ]

        # Calculate ride frequency (rides per week over last 3 months)
        now = datetime.now(tz=timezone.utc)
        three_months_ago = now - timedelta(days=90)
        recent = [
            a
            for a in cycling
            if datetime.fromisoformat(
                a["start_date_local"].replace("Z", "+00:00")
            )
            > three_months_ago
        ]
        weeks = max(1, (now - three_months_ago).days / 7)
        rides_per_week = len(recent) / weeks

        # Compute averages
        avg_distance = (
            sum(distances_km) / len(distances_km) if distances_km else 0
        )
        avg_elevation = (
            sum(elevations_m) / len(elevations_m) if elevations_m else 0
        )
        avg_speed = sum(speeds_kmh) / len(speeds_kmh) if speeds_kmh else 0

        # Estimate fitness level based on activity metrics
        if avg_distance > 80 and avg_elevation > 800 and rides_per_week >= 3:
            fitness_level = "advanced"
        elif avg_distance > 40 and avg_elevation > 400 and rides_per_week >= 2:
            fitness_level = "intermediate"
        else:
            fitness_level = "beginner"

        return {
            "has_data": True,
            "total_activities": len(cycling),
            "avg_distance_km": round(avg_distance, 1),
            "max_distance_km": (
                round(max(distances_km), 1) if distances_km else 0
            ),
            "avg_speed_kmh": round(avg_speed, 1),
            "max_speed_kmh": (
                round(max(speeds_kmh), 1) if speeds_kmh else 0
            ),
            "avg_elevation_gain_m": round(avg_elevation, 0),
            "max_elevation_gain_m": (
                round(max(elevations_m), 0) if elevations_m else 0
            ),
            "avg_duration_min": (
                round(sum(durations_min) / len(durations_min), 0)
                if durations_min
                else 0
            ),
            "rides_per_week": round(rides_per_week, 1),
            "fitness_level": fitness_level,
        }
