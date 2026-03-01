"""
Pathfinding engine using Dijkstra's algorithm with eco-cost weights.
"""

import heapq
from typing import List, Optional
import math

from app.engines.graph_builder import RoadNetworkGraph
from app.engines.eco_cost import EcoCostCalculator


class PathfindingEngine:
    """Find eco-optimal routes using Dijkstra's algorithm."""

    def __init__(self, graph: RoadNetworkGraph, eco_calculator: EcoCostCalculator):
        """Initialize the pathfinding engine."""
        self.graph = graph
        self.eco_calculator = eco_calculator

    def calculate_edge_eco_cost(
        self,
        from_node: str,
        to_node: str,
        current_traffic_speed_kmh: float = None,
    ) -> float:
        """
        Calculate eco-cost for a road segment.

        Returns total eco-cost for the segment (not per km).
        Eco-cost is scaled by distance so longer roads contribute more.
        """
        edge_data = self.graph.get_edge_data(from_node, to_node)

        if not edge_data:
            return float('inf')

        distance_km = edge_data.get('distance_km', 0)
        gradient_percent = edge_data.get('gradient_percent', 0)
        canopy_density_percent = edge_data.get('canopy_density_percent', 0)
        speed_limit_kmh = edge_data.get('speed_limit_kmh', 50)
        aqi_value = edge_data.get('aqi_value', 100)

        if current_traffic_speed_kmh is None:
            current_traffic_speed_kmh = speed_limit_kmh

        eco_components = self.eco_calculator.analyze_segment(
            current_speed_kmh=current_traffic_speed_kmh,
            free_flow_speed_kmh=speed_limit_kmh,
            aqi_value=aqi_value,
            gradient_percent=gradient_percent,
            canopy_density_percent=canopy_density_percent,
            num_carpool_matches=0,
        )

        # Multiply eco-cost by distance so the pathfinder correctly
        # penalizes longer high-pollution segments over shorter ones.
        # No per-km division — that was causing massive inflation on tiny OSM edges.
        return eco_components.total_eco_cost * distance_km

    def heuristic(self, node: str, goal: str) -> float:
        """
        A* heuristic: estimated eco-cost to goal based on straight-line distance.
        """
        node_data = self.graph.get_node_data(node)
        goal_data = self.graph.get_node_data(goal)

        if not node_data or not goal_data:
            return 0

        lat1, lon1 = node_data['latitude'], node_data['longitude']
        lat2, lon2 = goal_data['latitude'], goal_data['longitude']

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = 6371 * c

        # Use average eco-cost per km as heuristic estimate
        # Must be admissible (never overestimate) so we use a conservative value
        avg_eco_cost_per_km = 5
        return distance_km * avg_eco_cost_per_km

    def find_route(
        self,
        start_node: str,
        goal_node: str,
    ) -> Optional[List[str]]:
        """
        Find the eco-optimal route from start to goal using A* algorithm.

        Returns: List of node IDs representing the route
        """
        counter = 0
        open_set = [(0, counter, start_node)]
        counter += 1

        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: self.heuristic(start_node, goal_node)}
        closed_set = set()

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current == goal_node:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return path[::-1]

            if current in closed_set:
                continue

            closed_set.add(current)

            for neighbor in self.graph.graph.neighbors(current):
                if neighbor in closed_set:
                    continue

                edge_eco_cost = self.calculate_edge_eco_cost(current, neighbor)
                tentative_g = g_score[current] + edge_eco_cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal_node)

                    heapq.heappush(
                        open_set,
                        (f_score[neighbor], counter, neighbor)
                    )
                    counter += 1

        return None

    def get_route_details(self, route: List[str]) -> dict:
        """
        Get detailed information about a route.

        Returns: Dict with distance, time, eco-cost breakdown
        """
        if not route or len(route) < 2:
            return None

        total_distance_km = 0
        total_eco_cost = 0
        segments = []

        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]

            edge_data = self.graph.get_edge_data(from_node, to_node)
            distance_km = edge_data.get('distance_km', 0)

            # Eco-cost already includes distance scaling from calculate_edge_eco_cost
            segment_eco_cost = self.calculate_edge_eco_cost(from_node, to_node)

            total_distance_km += distance_km
            total_eco_cost += segment_eco_cost

            segments.append({
                'from': from_node,
                'to': to_node,
                'distance_km': distance_km,
                'eco_cost': segment_eco_cost,
            })

        avg_speed_kmh = 40
        estimated_time_minutes = int((total_distance_km / avg_speed_kmh) * 60)
        estimated_co2_kg = round(total_distance_km * 0.2, 2)

        # Normalize eco-cost by distance to get a meaningful 0-100 score
        # This makes scores comparable regardless of route length
        normalized_eco_score = round(total_eco_cost / max(total_distance_km, 0.1), 2)

        return {
            'route': route,
            'segments': segments,
            'total_distance_km': round(total_distance_km, 2),
            'total_eco_cost': normalized_eco_score,
            'estimated_time_minutes': estimated_time_minutes,
            'estimated_co2_kg': estimated_co2_kg,
        }