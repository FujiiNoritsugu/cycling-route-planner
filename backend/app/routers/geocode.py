"""Geocoding API endpoint.

This module provides the GET /api/geocode endpoint for converting
addresses and place names to geographic coordinates.
"""

from fastapi import APIRouter, HTTPException, Query

from planner.geocode import Geocoder, GeocodingError

from ..schemas import GeocodeResponse, Location

router = APIRouter(prefix="/api", tags=["geocode"])


@router.get("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    query: str = Query(..., min_length=1, description="Address or place name to search"),
    country: str = Query("JP", description="Country code (default: JP for Japan)"),
) -> GeocodeResponse:
    """Geocode an address or place name to coordinates.

    This endpoint uses OpenRouteService Geocoding API to convert
    addresses or place names into geographic coordinates.

    Args:
        query: Address or place name to search.
        country: Country code for filtering results (default: JP).

    Returns:
        GeocodeResponse with list of matching locations.

    Raises:
        HTTPException: If geocoding fails or no results found.
    """
    try:
        geocoder = Geocoder()
        planner_locations = await geocoder.geocode(query, country)

        # Convert planner.schemas.Location to backend.app.schemas.Location
        locations = [
            Location(lat=loc.lat, lng=loc.lng, name=loc.name)
            for loc in planner_locations
        ]

        return GeocodeResponse(data=locations)

    except GeocodingError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e
    except ValueError as e:
        # API key not configured
        raise HTTPException(
            status_code=500,
            detail=f"Geocoding service not configured: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geocoding failed: {str(e)}",
        ) from e
