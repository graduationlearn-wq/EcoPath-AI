"""
Pathfinding engine using Dijkstra's algorithm with eco-cost weights.
"""

import heapq
from typing import List, Tuple, Optional
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
        """
        edge_data = self.graph.get_edge_data(from_node, to_node)
        
        if not edge_data:
            return float('inf')
        
        # Get edge properties
        distance_km = edge_data.get('distance_km', 0)
        gradient_percent = edge_data.get('gradient_percent', 0)
        canopy_density_percent = edge_data.get('canopy_density_percent', 0)
        speed_limit_kmh = edge_data.get('speed_limit_kmh', 50)
        aqi_value = edge_data.get('aqi_value', 100)
        
        # Use current traffic speed or assume free-flow
        if current_traffic_speed_kmh is None:
            current_traffic_speed_kmh = speed_limit_kmh
        
        # Analyze the segment with eco-cost calculator
        eco_components = self.eco_calculator.analyze_segment(
            current_speed_kmh=current_traffic_speed_kmh,
            free_flow_speed_kmh=speed_limit_kmh,
            aqi_value=aqi_value,
            gradient_percent=gradient_percent,
            canopy_density_percent=canopy_density_percent,
            num_carpool_matches=0,  # Will be added later in routing logic
        )
        
        # Eco-cost per km
        eco_cost_per_km = eco_components.total_eco_cost / max(distance_km, 0.1)
        
        return eco_cost_per_km
    
    def heuristic(self, node: str, goal: str) -> float:
        """
        A* heuristic: Euclidean distance to goal.
        """
        node_data = self.graph.get_node_data(node)
        goal_data = self.graph.get_node_data(goal)
        
        if not node_data or not goal_data:
            return 0
        
        lat1, lon1 = node_data['latitude'], node_data['longitude']
        lat2, lon2 = goal_data['latitude'], goal_data['longitude']
        
        # Haversine formula for distance
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        earth_radius_km = 6371
        distance_km = earth_radius_km * c
        
        # Estimate eco-cost based on distance (assume average eco-cost)
        avg_eco_cost_per_km = 10  # Rough estimate
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
        # Priority queue: (f_score, counter, node)
        counter = 0
        open_set = [(0, counter, start_node)]
        counter += 1
        
        # Tracking
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: self.heuristic(start_node, goal_node)}
        closed_set = set()
        
        while open_set:
            _, _, current = heapq.heappop(open_set)
            
            if current == goal_node:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return path[::-1]
            
            if current in closed_set:
                continue
            
            closed_set.add(current)
            
            # Check neighbors
            for neighbor in self.graph.graph.neighbors(current):
                if neighbor in closed_set:
                    continue
                
                # Calculate eco-cost for this edge
                edge_eco_cost = self.calculate_edge_eco_cost(current, neighbor)
                tentative_g = g_score[current] + edge_eco_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    # Found a better path
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal_node)
                    
                    heapq.heappush(
                        open_set,
                        (f_score[neighbor], counter, neighbor)
                    )
                    counter += 1
        
        return None  # No path found
    
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
            
            # Calculate eco-cost for this segment
            eco_cost = self.calculate_edge_eco_cost(from_node, to_node)
            segment_total_cost = eco_cost * distance_km
            
            total_distance_km += distance_km
            total_eco_cost += segment_total_cost
            
            segments.append({
                'from': from_node,
                'to': to_node,
                'distance_km': distance_km,
                'eco_cost': segment_total_cost,
            })
        
        # Estimate time (assuming average 40 km/h)
        avg_speed_kmh = 40
        estimated_time_minutes = int((total_distance_km / avg_speed_kmh) * 60)
        
        # Estimate CO2 (roughly 0.2 kg per km for ICE)
        estimated_co2_kg = round(total_distance_km * 0.2, 2)
        
        return {
            'route': route,
            'segments': segments,
            'total_distance_km': total_distance_km,
            'total_eco_cost': total_eco_cost,
            'estimated_time_minutes': estimated_time_minutes,
            'estimated_co2_kg': estimated_co2_kg,
        }