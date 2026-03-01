"""
API endpoints for route calculation.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.api.schemas.route_schemas import (
    RouteCalculationRequest,
    RouteCalculationResponse,
    RouteOption,
    RouteSummary,
    EcoCostBreakdown,
)
from app.engines.eco_cost import EcoCostCalculator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/routes",
    tags=["routes"],
)


@router.post("/calculate", response_model=RouteCalculationResponse)
async def calculate_routes(request: RouteCalculationRequest):
    """Calculate eco-optimal routes."""
    
    try:
        logger.info(f"Route calculation: {request.origin.address} → {request.destination.address}")
        
        # Create eco-cost calculator
        calc = EcoCostCalculator()
        
        # For now, return a mock route (we'll implement real pathfinding later)
        mock_eco_cost = EcoCostBreakdown(
            traffic_penalty=30.0,
            aqi_penalty=25.0,
            gradient_penalty=5.0,
            carpool_bonus=-10.0,
            greenery_bonus=-12.0,
        )
        
        mock_summary = RouteSummary(
            total_distance_km=12.5,
            estimated_time_minutes=28,
            estimated_co2_kg=2.8,
            route_type="driving",
            eco_cost_score=45.3,
        )
        
        mock_route = RouteOption(
            route_id="route_001",
            rank=1,
            summary=mock_summary,
            eco_cost_breakdown=mock_eco_cost,
        )
        
        return RouteCalculationResponse(
            status="success",
            routes=[mock_route],
            message="Route calculated successfully",
        )
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Route service health check."""
    return {"status": "healthy", "service": "routes"}