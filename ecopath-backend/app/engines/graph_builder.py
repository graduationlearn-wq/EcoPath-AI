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
    graph.add_node("india_gate", 28.5244, 77.1855, "India Gate")
    graph.add_node("central_delhi", 28.6050, 77.2300, "Central Delhi")
    graph.add_node("south_delhi", 28.5200, 77.2000, "South Delhi")
    graph.add_node("green_park", 28.5450, 77.2050, "Green Park")
    graph.add_node("lodhi_garden", 28.5932, 77.2197, "Lodhi Garden")
    
    # Add edges with various properties
    # Connaught Place → Central Delhi (flat, good trees)
    graph.add_edge(
        "connaught_place", "central_delhi",
        distance_km=1.5,
        gradient_percent=0.5,
        canopy_density_percent=60,
        speed_limit_kmh=50,
        aqi_value=150,
    )
    
    # Central Delhi → Lodhi Garden (slight uphill, very green)
    graph.add_edge(
        "central_delhi", "lodhi_garden",
        distance_km=2.0,
        gradient_percent=2.5,
        canopy_density_percent=80,
        speed_limit_kmh=40,
        aqi_value=120,
    )
    
    # Lodhi Garden → South Delhi (downhill, moderate green)
    graph.add_edge(
        "lodhi_garden", "south_delhi",
        distance_km=2.5,
        gradient_percent=-1.5,
        canopy_density_percent=50,
        speed_limit_kmh=50,
        aqi_value=160,
    )
    
    # South Delhi → Green Park (flat, green)
    graph.add_edge(
        "south_delhi", "green_park",
        distance_km=1.2,
        gradient_percent=0.0,
        canopy_density_percent=70,
        speed_limit_kmh=50,
        aqi_value=140,
    )
    
    # Green Park → India Gate (flat, moderate green)
    graph.add_edge(
        "green_park", "india_gate",
        distance_km=1.8,
        gradient_percent=0.2,
        canopy_density_percent=55,
        speed_limit_kmh=50,
        aqi_value=170,
    )
    
    # Alternative route: Connaught Place → South Delhi (steeper, less green)
    graph.add_edge(
        "connaught_place", "south_delhi",
        distance_km=2.8,
        gradient_percent=5.0,
        canopy_density_percent=30,
        speed_limit_kmh=60,
        aqi_value=200,
    )
    
    # Alternative route: Central Delhi → Green Park (direct)
    graph.add_edge(
        "central_delhi", "green_park",
        distance_km=3.5,
        gradient_percent=1.0,
        canopy_density_percent=40,
        speed_limit_kmh=50,
        aqi_value=180,
    )
    
    return graph