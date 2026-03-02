"""
Route service - business logic for route calculation.
Now uses PostgreSQL caching for road networks, AQI, elevation and NDVI.
"""

import math
import logging
from datetime import datetime

from app.engines.graph_builder import build_osm_network, create_mock_delhi_network, RoadNetworkGraph
from app.engines.eco_cost import EcoCostCalculator
from app.engines.pathfinding import PathfindingEngine
from app.services.aqi_service import AQIService
from app.services.weight_service import get_dynamic_weights
from app.api.schemas.route_schemas import (
    RouteOption,
    RouteSummary,
    EcoCostBreakdown,
)

logger = logging.getLogger(__name__)


class RouteService:
    """Service for route calculations."""

    def __init__(self):
        self.eco_calculator = EcoCostCalculator()
        self.aqi_service = AQIService()

    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371
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

    def _restore_graph_from_cache(self, nodes: dict, edges: dict) -> RoadNetworkGraph:
        """Rebuild a RoadNetworkGraph from cached node/edge dicts."""
        graph = RoadNetworkGraph()
        graph.nodes_data = nodes

        for key_str, edge_data in edges.items():
            parts = key_str.split('|')
            edge_key = (parts[0], parts[1])
            graph.edges_data[edge_key] = edge_data
            graph.graph.add_edge(parts[0], parts[1], weight=edge_data.get('distance_km', 0))

        for node_id in nodes:
            graph.graph.add_node(node_id)

        return graph

    def _enrich_with_ndvi(self, graph, db=None):
        """
        Enrich graph edges with real canopy density from NDVI service.
        Runs after both cache hits and fresh OSM builds.
        """
        try:
            from app.services.ndvi_service import NDVIService
            NDVIService().enrich_graph_with_canopy(graph, db=db)
        except Exception as e:
            logger.warning(f"NDVI enrichment failed ({e}) — canopy defaults to 40%")

    def _build_graph_for_route(self, origin_lat, origin_lon, dest_lat, dest_lon, db=None):
        """
        Build road network — checks DB cache first.
        Cache HIT: loads instantly from DB (~0.1s)
        Cache MISS: fetches from OSM, saves to DB for next time (~10s)
        NDVI enrichment runs after both cases.
        """
        center_lat = (origin_lat + dest_lat) / 2
        center_lon = (origin_lon + dest_lon) / 2

        half_distance_km = self._haversine_distance(
            center_lat, center_lon, origin_lat, origin_lon
        )
        radius_m = int(half_distance_km * 1000 * 1.5)
        radius_m = max(1000, min(radius_m, 15000))

        # 1. Check DB cache
        if db:
            try:
                from app.db.cache_service import CacheService
                cache = CacheService(db)
                cached = cache.get_road_network(center_lat, center_lon, radius_m)
                if cached:
                    nodes, edges = cached
                    graph = self._restore_graph_from_cache(nodes, edges)
                    logger.info(f"Road network loaded from DB cache: {len(graph.nodes_data)} nodes")
                    # NDVI not stored in road cache — enrich after loading
                    self._enrich_with_ndvi(graph, db=db)
                    return graph, center_lat, center_lon
            except Exception as e:
                logger.warning(f"Road network DB cache check failed: {e}")

        # 2. Fetch from OSM
        logger.info(f"Fetching OSM network: center=({center_lat:.4f},{center_lon:.4f}), radius={radius_m}m")
        try:
            graph = build_osm_network(center_lat, center_lon, radius_m)
            logger.info(f"OSM graph built: {len(graph.nodes_data)} nodes, {len(graph.edges_data)} edges")

            # Enrich with NDVI
            self._enrich_with_ndvi(graph, db=db)

            # Save to DB cache
            if db:
                try:
                    from app.db.cache_service import CacheService
                    cache = CacheService(db)
                    cache.save_road_network(
                        center_lat, center_lon, radius_m,
                        graph.nodes_data,
                        graph.edges_data,
                    )
                except Exception as e:
                    logger.warning(f"Road network DB cache save failed: {e}")

            return graph, center_lat, center_lon

        except Exception as e:
            logger.warning(f"OSM fetch failed ({e}), falling back to mock network")
            return create_mock_delhi_network(), origin_lat, origin_lon

    def _apply_real_aqi_to_graph(self, graph, center_lat, center_lon, db=None):
        aqi_value = self.aqi_service.get_aqi_for_route_area(center_lat, center_lon, db=db)
        logger.info(f"Real AQI for area: {aqi_value}")
        for edge_key in graph.edges_data:
            graph.edges_data[edge_key]['aqi_value'] = aqi_value
        return graph, aqi_value

    def calculate_routes(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: datetime = None,
        db=None,
    ) -> list:
        """
        Calculate eco-optimal routes.
        Uses DB cache for road network, AQI, elevation and NDVI.
        """

        # Build road network (cache aware, NDVI enriched)
        graph, center_lat, center_lon = self._build_graph_for_route(
            origin_lat, origin_lon, dest_lat, dest_lon, db=db
        )

        # Apply real AQI (cache aware)
        graph, aqi_value = self._apply_real_aqi_to_graph(
            graph, center_lat, center_lon, db=db
        )

        # Dynamic weights
        dynamic_weights = get_dynamic_weights(
            aqi_value=aqi_value,
            departure_time=departure_time or datetime.now(),
        )
        self.eco_calculator.update_weights(dynamic_weights)

        pathfinder = PathfindingEngine(graph, self.eco_calculator)

        start_node = self.find_nearest_node(graph, origin_lat, origin_lon)
        goal_node = self.find_nearest_node(graph, dest_lat, dest_lon)

        if not start_node or not goal_node:
            logger.error("Could not find start or goal node")
            return []

        if start_node == goal_node:
            logger.warning("Start and goal are the same node")
            return []

        route = pathfinder.find_route(start_node, goal_node)

        if not route:
            logger.warning(f"No route found from {start_node} to {goal_node}")
            return []

        details = pathfinder.get_route_details(route)

        route_coordinates = []
        for node_id in route:
            node_data = graph.get_node_data(node_id)
            if node_data:
                route_coordinates.append({
                    'latitude': node_data['latitude'],
                    'longitude': node_data['longitude'],
                    'name': node_data.get('name', node_id),
                })

        total_traffic = 0.0
        total_aqi = 0.0
        total_gradient = 0.0
        total_carpool = 0.0
        total_greenery = 0.0
        total_canyon = 0.0
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
                    canyon_penalty=edge_data.get('canyon_penalty', 0.0),
                )
                total_traffic += components.traffic_penalty
                total_aqi += components.aqi_penalty
                total_gradient += components.gradient_penalty
                total_carpool += components.carpool_bonus
                total_greenery += components.greenery_bonus
                total_canyon += components.canyon_penalty
                segment_count += 1

        # Save to route history
        if db:
            try:
                from app.db.cache_service import CacheService
                from app.services.weight_service import get_time_period
                cache = CacheService(db)
                count = max(segment_count, 1)
                cache.save_route_history(
                    origin_lat=origin_lat, origin_lon=origin_lon,
                    dest_lat=dest_lat, dest_lon=dest_lon,
                    distance_km=float(round(details['total_distance_km'], 2)),
                    duration_minutes=int(details['estimated_time_minutes']),
                    eco_score=float(round(details['total_eco_cost'], 2)),
                    co2_kg=float(details['estimated_co2_kg']),
                    aqi_penalty=round(total_aqi / count, 2),
                    gradient_penalty=round(total_gradient / count, 2),
                    canyon_penalty=round(total_canyon / count, 2),
                    greenery_bonus=round(total_greenery / count, 2),
                    aqi_value=aqi_value,
                    time_period=get_time_period((departure_time or datetime.now()).hour),
                    vehicle_type='ice',
                )
            except Exception as e:
                logger.warning(f"Route history save failed: {e}")

        count = max(segment_count, 1)
        breakdown = EcoCostBreakdown(
            traffic_penalty=round(total_traffic / count, 2),
            aqi_penalty=round(total_aqi / count, 2),
            gradient_penalty=round(total_gradient / count, 2),
            carpool_bonus=round(total_carpool / count, 2),
            greenery_bonus=round(total_greenery / count, 2),
            canyon_penalty=round(total_canyon / count, 2),
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