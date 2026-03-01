"""
Route service - business logic for route calculation.
"""

from app.engines.graph_builder import create_mock_delhi_network
from app.engines.eco_cost import EcoCostCalculator
from app.engines.pathfinding import PathfindingEngine
from app.api.schemas.route_schemas import (
    RouteOption,
    RouteSummary,
    EcoCostBreakdown,
)


class RouteService:
    """Service for route calculations."""
    
    def __init__(self):
        """Initialize with graph and calculators."""
        self.graph = create_mock_delhi_network()
        self.eco_calculator = EcoCostCalculator()
        self.pathfinder = PathfindingEngine(self.graph, self.eco_calculator)
    
    def find_nearest_node(self, latitude: float, longitude: float) -> str:
        """
        Find the nearest node in the graph to a given coordinate.
        For now, returns a hardcoded node based on proximity.
        """
        # For demo: hardcode based on coordinates
        if latitude > 28.61:
            return "connaught_place"
        elif latitude > 28.59:
            return "central_delhi"
        elif latitude > 28.55:
            return "lodhi_garden"
        elif latitude > 28.52:
            return "south_delhi"
        else:
            return "india_gate"
    
    def calculate_routes(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> list:
        """
        Calculate eco-optimal routes.
        
        Returns: List of RouteOption objects
        """
        # Find nearest nodes
        start_node = self.find_nearest_node(origin_lat, origin_lon)
        goal_node = self.find_nearest_node(dest_lat, dest_lon)
        
        # Find route
        route = self.pathfinder.find_route(start_node, goal_node)
        
        if not route:
            return []
        
        # Get route details
        details = self.pathfinder.get_route_details(route)
        
        # Get node coordinates for the route
        route_coordinates = []
        for node_id in route:
            node_data = self.graph.get_node_data(node_id)
            if node_data:
                route_coordinates.append({
                    'latitude': node_data['latitude'],
                    'longitude': node_data['longitude'],
                    'name': node_data.get('name', node_id)
                })
        
        # Build eco-cost breakdown
        breakdown = EcoCostBreakdown(
            traffic_penalty=30.0,
            aqi_penalty=25.0,
            gradient_penalty=5.0,
            carpool_bonus=-10.0,
            greenery_bonus=-12.0,
        )
        
        # Build summary
        summary = RouteSummary(
            total_distance_km=details['total_distance_km'],
            estimated_time_minutes=details['estimated_time_minutes'],
            estimated_co2_kg=details['estimated_co2_kg'],
            route_type="driving",
            eco_cost_score=details['total_eco_cost'],
        )
        
        # Build route option with coordinates
        route_option = RouteOption(
            route_id=f"route_{start_node}_{goal_node}",
            rank=1,
            summary=summary,
            eco_cost_breakdown=breakdown,
            route_coordinates=route_coordinates,
        )
        
        return [route_option]