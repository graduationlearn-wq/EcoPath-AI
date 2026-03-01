"""
Route service - business logic for route calculation.
"""

import math
import logging

from app.engines.graph_builder import build_osm_network, create_mock_delhi_network
from app.engines.eco_cost import EcoCostCalculator
from app.engines.pathfinding import PathfindingEngine
from app.api.schemas.route_schemas import (
    RouteOption,
    RouteSummary,
    EcoCostBreakdown,
)

logger = logging.getLogger(__name__)


class RouteService:
    """Service for route calculations."""

    def __init__(self):
        """Initialize calculators. Graph is built per-request based on user coordinates."""
        self.eco_calculator = EcoCostCalculator()

    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
    ) -> float:
        """
        Calculate straight-line distance between two lat/lon points in km.
        Used to find the nearest graph node to a given coordinate.
        """
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def find_nearest_node(self, graph, latitude: float, longitude: float) -> str:
        """
        Find the nearest node in the graph to a given coordinate.
        Uses haversine distance — works for any location in the world.
        """
        nearest_node = None
        min_distance = float('inf')

        for node_id, node_data in graph.nodes_data.items():
            dist = self._haversine_distance(
                latitude, longitude,
                node_data['latitude'], node_data['longitude'],
            )
            if dist < min_distance:
                min_distance = dist
                nearest_node = node_id

        return nearest_node

    def _build_graph_for_route(
        self,
        origin_lat: float, origin_lon: float,
        dest_lat: float, dest_lon: float,
    ):
        """
        Build an OSM road network that covers the area between origin and destination.

        The radius is calculated so the circle always contains both points,
        plus a 20% buffer so the pathfinder has room to find alternate routes.
        """
        # Center point between origin and destination
        center_lat = (origin_lat + dest_lat) / 2
        center_lon = (origin_lon + dest_lon) / 2

        # Distance from center to either endpoint (in meters)
        half_distance_km = self._haversine_distance(
            center_lat, center_lon,
            origin_lat, origin_lon,
        )
        radius_m = int(half_distance_km * 1000 * 1.5)  # 1.5x buffer for alternate roads

        # Clamp radius: min 1km (short trips), max 15km (avoid huge downloads)
        radius_m = max(1000, min(radius_m, 15000))

        logger.info(f"Fetching OSM network: center=({center_lat:.4f},{center_lon:.4f}), radius={radius_m}m")

        try:
            graph = build_osm_network(center_lat, center_lon, radius_m)
            logger.info(f"OSM graph built: {len(graph.nodes_data)} nodes, {len(graph.edges_data)} edges")
            return graph
        except Exception as e:
            logger.warning(f"OSM fetch failed ({e}), falling back to mock network")
            return create_mock_delhi_network()

    def calculate_routes(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> list:
        """
        Calculate eco-optimal routes between two coordinates.
        Works globally — fetches real OSM roads for the given area.

        Returns: List of RouteOption objects
        """
        # Build road network for this specific origin/destination pair
        graph = self._build_graph_for_route(origin_lat, origin_lon, dest_lat, dest_lon)
        pathfinder = PathfindingEngine(graph, self.eco_calculator)

        # Find nearest graph nodes to the user's exact coordinates
        start_node = self.find_nearest_node(graph, origin_lat, origin_lon)
        goal_node = self.find_nearest_node(graph, dest_lat, dest_lon)

        if not start_node or not goal_node:
            logger.error("Could not find start or goal node in graph")
            return []

        if start_node == goal_node:
            logger.warning("Start and goal are the same node — route too short or coordinates too close")
            return []

        # Run pathfinding
        route = pathfinder.find_route(start_node, goal_node)

        if not route:
            logger.warning(f"No route found from {start_node} to {goal_node}")
            return []

        # Get full route details
        details = pathfinder.get_route_details(route)

        # Build coordinate list for map rendering
        route_coordinates = []
        for node_id in route:
            node_data = graph.get_node_data(node_id)
            if node_data:
                route_coordinates.append({
                    'latitude': node_data['latitude'],
                    'longitude': node_data['longitude'],
                    'name': node_data.get('name', node_id),
                })

        # Build real eco-cost breakdown by re-running the calculator on the full route
        # (instead of the old hardcoded 30.0, 25.0 placeholder values)
        total_traffic = 0.0
        total_aqi = 0.0
        total_gradient = 0.0
        total_carpool = 0.0
        total_greenery = 0.0
        segment_count = 0

        for i in range(len(route) - 1):
            edge_data = graph.get_edge_data(route[i], route[i + 1])
            if edge_data:
                components = self.eco_calculator.analyze_segment(
                    current_speed_kmh=edge_data.get('speed_limit_kmh', 50),
                    free_flow_speed_kmh=edge_data.get('speed_limit_kmh', 50),
                    aqi_value=edge_data.get('aqi_value', 100),
                    gradient_percent=edge_data.get('gradient_percent', 0),
                    canopy_density_percent=edge_data.get('canopy_density_percent', 40),
                )
                total_traffic += components.traffic_penalty
                total_aqi += components.aqi_penalty
                total_gradient += components.gradient_penalty
                total_carpool += components.carpool_bonus
                total_greenery += components.greenery_bonus
                segment_count += 1

        # Average across all segments for the breakdown display
        count = max(segment_count, 1)
        breakdown = EcoCostBreakdown(
            traffic_penalty=round(total_traffic / count, 2),
            aqi_penalty=round(total_aqi / count, 2),
            gradient_penalty=round(total_gradient / count, 2),
            carpool_bonus=round(total_carpool / count, 2),
            greenery_bonus=round(total_greenery / count, 2),
        )

        summary = RouteSummary(
            total_distance_km=round(details['total_distance_km'], 2),
            estimated_time_minutes=details['estimated_time_minutes'],
            estimated_co2_kg=details['estimated_co2_kg'],
            route_type="driving",
            eco_cost_score=round(details['total_eco_cost'], 2),
        )

        route_option = RouteOption(
            route_id=f"route_{start_node}_{goal_node}",
            rank=1,
            summary=summary,
            eco_cost_breakdown=breakdown,
            route_coordinates=route_coordinates,
        )

        return [route_option]
