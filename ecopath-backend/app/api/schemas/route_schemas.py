"""
Pydantic schemas for route API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class LocationPoint(BaseModel):
    """A geographic location."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None


class RoutePreferences(BaseModel):
    """User preferences for routing."""
    allow_carpool: bool = True
    allow_multimodal: bool = True
    vehicle_type: str = "ice"  # ice, ev, hybrid


class RouteCalculationRequest(BaseModel):
    """User request for route calculation."""
    origin: LocationPoint
    destination: LocationPoint
    departure_time: datetime
    preferences: Optional[RoutePreferences] = None


class EcoCostBreakdown(BaseModel):
    """Breakdown of eco-cost for a segment."""
    traffic_penalty: float
    aqi_penalty: float
    gradient_penalty: float
    carpool_bonus: float
    greenery_bonus: float


class RouteSummary(BaseModel):
    """High-level route summary."""
    total_distance_km: float
    estimated_time_minutes: int
    estimated_co2_kg: float
    route_type: str  # driving, carpool, multimodal
    eco_cost_score: float


class RouteOption(BaseModel):
    """A single route option."""
    route_id: str
    rank: int
    summary: RouteSummary
    eco_cost_breakdown: EcoCostBreakdown
    route_coordinates: Optional[List[Dict]] = Field(default_factory=list, description="Route waypoints with lat/lon")


class RouteCalculationResponse(BaseModel):
    """Response with route options."""
    status: str  # success or error
    routes: List[RouteOption] = []
    message: Optional[str] = None