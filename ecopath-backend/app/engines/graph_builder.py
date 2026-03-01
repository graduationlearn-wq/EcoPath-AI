"""
Graph builder for road networks.
For now, creates a mock network for testing pathfinding.
"""

import networkx as nx
from typing import Dict, Tuple


class RoadNetworkGraph:
    """Represents a road network as a graph."""
    
    def __init__(self):
        """Initialize the graph."""
        self.graph = nx.DiGraph()
        self.nodes_data = {}
        self.edges_data = {}
    
    def add_node(
        self, 
        node_id: str, 
        latitude: float, 
        longitude: float, 
        name: str = ""
    ):
        """Add a node (intersection) to the graph."""
        self.graph.add_node(node_id)
        self.nodes_data[node_id] = {
            'latitude': latitude,
            'longitude': longitude,
            'name': name,
        }
    
    def add_edge(
        self,
        from_node: str,
        to_node: str,
        distance_km: float,
        gradient_percent: float = 0.0,
        canopy_density_percent: float = 0.0,
        speed_limit_kmh: float = 50.0,
        aqi_value: int = 100,
    ):
        """Add an edge (road segment) to the graph."""
        self.graph.add_edge(from_node, to_node, weight=distance_km)
        
        edge_key = (from_node, to_node)
        self.edges_data[edge_key] = {
            'distance_km': distance_km,
            'gradient_percent': gradient_percent,
            'canopy_density_percent': canopy_density_percent,
            'speed_limit_kmh': speed_limit_kmh,
            'aqi_value': aqi_value,
        }
    
    def get_edge_data(self, from_node: str, to_node: str) -> Dict:
        """Get data for a specific edge."""
        edge_key = (from_node, to_node)
        return self.edges_data.get(edge_key, {})
    
    def get_node_data(self, node_id: str) -> Dict:
        """Get data for a specific node."""
        return self.nodes_data.get(node_id, {})


def create_mock_delhi_network() -> RoadNetworkGraph:
    """
    Create a mock Delhi road network for testing.
    This is a simplified network with key intersections.
    """
    graph = RoadNetworkGraph()
    
    # Add nodes (key locations in Delhi)
    graph.add_node("connaught_place", 28.6139, 77.2090, "Connaught Place")
    graph.add_node("central_delhi", 28.6050, 77.2300, "Central Delhi")
    graph.add_node("south_delhi", 28.5200, 77.2000, "South Delhi")
    graph.add_node("green_park", 28.5450, 77.2050, "Green Park")
    graph.add_node("lodhi_garden", 28.5932, 77.2197, "Lodhi Garden")
    graph.add_node("india_gate", 28.5244, 77.1855, "India Gate")
    
    # Add intermediate nodes for better route visualization
    graph.add_node("node_1", 28.6000, 77.2150, "Intersection 1")
    graph.add_node("node_2", 28.5850, 77.2100, "Intersection 2")
    graph.add_node("node_3", 28.5700, 77.2050, "Intersection 3")
    graph.add_node("node_4", 28.5550, 77.2000, "Intersection 4")
    graph.add_node("node_5", 28.5350, 77.1950, "Intersection 5")
    
    # Main route: Connaught Place → Central Delhi → Intermediate nodes → South Delhi → Green Park → India Gate
    graph.add_edge(
        "connaught_place", "node_1",
        distance_km=0.8,
        gradient_percent=0.5,
        canopy_density_percent=60,
        speed_limit_kmh=50,
        aqi_value=150,
    )
    
    graph.add_edge(
        "node_1", "central_delhi",
        distance_km=0.7,
        gradient_percent=0.3,
        canopy_density_percent=65,
        speed_limit_kmh=50,
        aqi_value=140,
    )
    
    graph.add_edge(
        "central_delhi", "lodhi_garden",
        distance_km=0.6,
        gradient_percent=1.5,
        canopy_density_percent=80,
        speed_limit_kmh=40,
        aqi_value=120,
    )
    
    graph.add_edge(
        "lodhi_garden", "node_2",
        distance_km=0.8,
        gradient_percent=-1.0,
        canopy_density_percent=75,
        speed_limit_kmh=45,
        aqi_value=130,
    )
    
    graph.add_edge(
        "node_2", "node_3",
        distance_km=0.7,
        gradient_percent=0.2,
        canopy_density_percent=50,
        speed_limit_kmh=50,
        aqi_value=150,
    )
    
    graph.add_edge(
        "node_3", "node_4",
        distance_km=0.8,
        gradient_percent=-0.5,
        canopy_density_percent=55,
        speed_limit_kmh=50,
        aqi_value=160,
    )
    
    graph.add_edge(
        "node_4", "south_delhi",
        distance_km=0.7,
        gradient_percent=0.0,
        canopy_density_percent=50,
        speed_limit_kmh=50,
        aqi_value=165,
    )
    
    graph.add_edge(
        "south_delhi", "green_park",
        distance_km=0.8,
        gradient_percent=0.3,
        canopy_density_percent=70,
        speed_limit_kmh=50,
        aqi_value=140,
    )
    
    graph.add_edge(
        "green_park", "node_5",
        distance_km=0.7,
        gradient_percent=-0.2,
        canopy_density_percent=60,
        speed_limit_kmh=50,
        aqi_value=155,
    )
    
    graph.add_edge(
        "node_5", "india_gate",
        distance_km=0.8,
        gradient_percent=0.1,
        canopy_density_percent=55,
        speed_limit_kmh=50,
        aqi_value=170,
    )
    
    # Alternative shorter route (steeper, less green)
    graph.add_edge(
        "connaught_place", "south_delhi",
        distance_km=2.8,
        gradient_percent=5.0,
        canopy_density_percent=30,
        speed_limit_kmh=60,
        aqi_value=200,
    )
    
    return graph