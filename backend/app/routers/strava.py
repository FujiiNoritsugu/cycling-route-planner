"""Strava integration API endpoints.

Provides OAuth2 authentication and activity data retrieval from Strava.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

from ..schemas import StravaFitnessProfile, StravaTokenResponse
from ..services.strava import StravaService

# Load environment variables from .env file
_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(dotenv_path=_project_root / ".env")

router = APIRouter(prefix="/api/strava", tags=["strava"])


@router.get("/auth-url")
async def get_auth_url() -> dict[str, str]:
    """Get Strava OAuth authorization URL.

    Returns:
        URL to redirect user to for Strava authorization.

    Raises:
        HTTPException: If STRAVA_CLIENT_ID is not configured.
    """
    client_id = os.getenv("STRAVA_CLIENT_ID", "")
    redirect_uri = os.getenv(
        "STRAVA_REDIRECT_URI", "http://localhost:5173/strava/callback"
    )

    if not client_id:
        raise HTTPException(
            status_code=500, detail="STRAVA_CLIENT_ID not configured"
        )

    url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=read,activity:read"
    )
    return {"url": url}


@router.post("/token")
async def exchange_token(code: str) -> StravaTokenResponse:
    """Exchange Strava authorization code for access token.

    Args:
        code: Authorization code from Strava OAuth callback.

    Returns:
        Access token and athlete information.

    Raises:
        HTTPException: If token exchange fails.
    """
    service = StravaService()
    try:
        data = await service.exchange_token(code)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Token exchange failed: {e}"
        )

    athlete = data.get("athlete", {})
    return StravaTokenResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=data["expires_at"],
        athlete_id=athlete.get("id", 0),
        athlete_name=f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip(),
    )


@router.post("/refresh")
async def refresh_token(refresh_token: str) -> StravaTokenResponse:
    """Refresh expired Strava access token.

    Args:
        refresh_token: Refresh token from previous authentication.

    Returns:
        New access token and athlete information.

    Raises:
        HTTPException: If token refresh fails.
    """
    service = StravaService()
    try:
        data = await service.refresh_token(refresh_token)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Token refresh failed: {e}"
        )

    return StravaTokenResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=data["expires_at"],
        athlete_id=0,
        athlete_name="",
    )


@router.get("/profile")
async def get_fitness_profile(
    access_token: str,
) -> StravaFitnessProfile:
    """Get fitness profile derived from Strava activities.

    Fetches recent cycling activities and analyzes them to build
    a fitness profile for personalized route recommendations.

    Args:
        access_token: Valid Strava access token.

    Returns:
        Fitness profile with activity statistics.

    Raises:
        HTTPException: If fetching activities fails.
    """
    service = StravaService()
    try:
        activities = await service.get_activities(access_token, per_page=50)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch activities: {e}"
        )

    profile_data = service.build_fitness_profile(activities)
    return StravaFitnessProfile(**profile_data)
