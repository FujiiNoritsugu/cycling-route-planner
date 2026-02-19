"""Route history API endpoint.

This module provides the GET /api/history endpoint for retrieving
past route planning history.
"""

from fastapi import APIRouter, HTTPException, Query

from ..database import get_route_history, get_route_plan_by_id
from ..schemas import HistoryResponse, RoutePlan

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of plans to retrieve"),
) -> HistoryResponse:
    """Retrieve route planning history.

    Args:
        limit: Maximum number of plans to return (1-100).

    Returns:
        HistoryResponse with list of past route plans.

    Raises:
        HTTPException: If database query fails.
    """
    try:
        plans = get_route_history(limit=limit)
        return HistoryResponse(data=plans)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}",
        ) from e


@router.get("/history/{plan_id}", response_model=RoutePlan)
async def get_plan_by_id(plan_id: str) -> RoutePlan:
    """Retrieve a specific route plan by ID.

    Args:
        plan_id: Route plan UUID.

    Returns:
        RoutePlan if found.

    Raises:
        HTTPException: If plan not found or database query fails.
    """
    try:
        plan = get_route_plan_by_id(plan_id)
        if plan is None:
            raise HTTPException(
                status_code=404,
                detail=f"Route plan not found: {plan_id}",
            )
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve plan: {str(e)}",
        ) from e
