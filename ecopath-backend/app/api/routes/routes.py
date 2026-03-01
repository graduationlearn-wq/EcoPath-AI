"""
API endpoints for route calculation.
"""

from fastapi import APIRouter, HTTPException
import logging

from app.api.schemas.route_schemas import (
    RouteCalculationRequest,
    RouteCalculationResponse,
)
from app.services.route_service import RouteService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/routes",
    tags=["routes"],
)

# Initialize service
route_service = RouteService()


@router.post("/calculate", response_model=RouteCalculationResponse)
async def calculate_routes(request: RouteCalculationRequest):
    """Calculate eco-optimal routes."""
    
    try:
        logger.info(f"Route calculation: {request.origin.address} → {request.destination.address}")
        
        # Calculate routes using the service
        routes = route_service.calculate_routes(
            origin_lat=request.origin.latitude,
            origin_lon=request.origin.longitude,
            dest_lat=request.destination.latitude,
            dest_lon=request.destination.longitude,
        )
        
        if not routes:
            return RouteCalculationResponse(
                status="error",
                message="No route found between these locations",
            )
        
        return RouteCalculationResponse(
            status="success",
            routes=routes,
            message="Routes calculated successfully",
        )
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Route service health check."""
    return {"status": "healthy", "service": "routes"}