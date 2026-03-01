"""
Graph builder for road networks.
Supports both mock network (for testing) and real OSM network (for production).
"""

import math
import networkx as nx
from typing import Dict


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


def build_osm_network(
    lat: float,
    lon: float,
    radius_m: int = 2000,
) -> RoadNetworkGraph:
    """
    Build a real road network from OpenStreetMap data.

    Fetches all drivable roads within radius_m meters of the given
    lat/lon coordinate. Works for any location in the world.

    Args:
        lat: Center latitude
        lon: Center longitude
        radius_m: Radius in meters to fetch roads for (default 2km)

    Returns:
        RoadNetworkGraph populated with real OSM nodes and edges
    """
    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx is required for real road networks. "
            "Install it with: pip install osmnx"
        )

    # Fetch the drivable road network from OSM around the given point
    # network_type='drive' gets roads cars can use (no footpaths, no private roads)
    osm_graph = ox.graph_from_point(
        (lat, lon),
        dist=radius_m,
        network_type='drive',
        simplify=True,        # Merge redundant nodes (straight segments) for cleaner graph
        retain_all=False,     # Only keep the largest connected component
    )

    # Convert to undirected to get edges in both directions for routing flexibility
    # then back to directed so our pathfinding engine works correctly
    osm_graph = ox.convert.to_digraph(osm_graph, weight='length')

    road_graph = RoadNetworkGraph()

    # --- ADD NODES ---
    # OSM nodes are intersections. Each has a numeric ID, lat, and lon.
    for node_id, node_data in osm_graph.nodes(data=True):
        node_lat = node_data.get('y', 0)   # osmnx uses 'y' for latitude
        node_lon = node_data.get('x', 0)   # osmnx uses 'x' for longitude
        node_name = str(node_id)            # OSM node IDs are large integers

        road_graph.add_node(
            node_id=str(node_id),
            latitude=node_lat,
            longitude=node_lon,
            name=node_name,
        )

    # --- ADD EDGES ---
    # OSM edges are road segments between intersections.
    # We fill in eco fields with realistic defaults since OSM doesn't have AQI/canopy.
    # These will be replaced with real API data in a future step.
    for from_id, to_id, edge_data in osm_graph.edges(data=True):
        # Distance: OSM gives length in meters, convert to km
        length_m = edge_data.get('length', 100)
        distance_km = length_m / 1000.0

        # Speed limit: OSM sometimes has maxspeed tag, default to 50 if missing
        raw_speed = edge_data.get('maxspeed', 50)
        if isinstance(raw_speed, list):
            raw_speed = raw_speed[0]  # Some edges have multiple speed values
        try:
            speed_limit_kmh = float(str(raw_speed).replace(' mph', '').replace(' kmh', '').strip())
            # Convert mph to kmh if needed (some countries use mph)
            if 'mph' in str(raw_speed):
                speed_limit_kmh = speed_limit_kmh * 1.60934
        except (ValueError, TypeError):
            speed_limit_kmh = 50.0

        # Gradient: OSM rarely has elevation data — default to flat (0%)
        # Will be replaced with real elevation API (e.g. Open-Elevation) later
        gradient_percent = 0.0

        # Canopy density: OSM doesn't have this — default to 40% (urban average)
        # Will be replaced with satellite/NDVI data later
        canopy_density_percent = 40.0

        # AQI: OSM doesn't have this — default to 100 (moderate, urban average)
        # Will be replaced with real AQI API later
        aqi_value = 100

        road_graph.add_edge(
            from_node=str(from_id),
            to_node=str(to_id),
            distance_km=distance_km,
            gradient_percent=gradient_percent,
            canopy_density_percent=canopy_density_percent,
            speed_limit_kmh=speed_limit_kmh,
            aqi_value=aqi_value,
        )

    return road_graph


def create_mock_delhi_network() -> RoadNetworkGraph:
    """
    Create a mock Delhi road network for offline testing.
    Used as fallback when OSM fetch fails or for unit tests.
    """
    graph = RoadNetworkGraph()
    
    graph.add_node("connaught_place", 28.6139, 77.2090, "Connaught Place")
    graph.add_node("central_delhi", 28.6050, 77.2300, "Central Delhi")
    graph.add_node("south_delhi", 28.5200, 77.2000, "South Delhi")
    graph.add_node("green_park", 28.5450, 77.2050, "Green Park")
    graph.add_node("lodhi_garden", 28.5932, 77.2197, "Lodhi Garden")
    graph.add_node("india_gate", 28.5244, 77.1855, "India Gate")
    graph.add_node("node_1", 28.6000, 77.2150, "Intersection 1")
    graph.add_node("node_2", 28.5850, 77.2100, "Intersection 2")
    graph.add_node("node_3", 28.5700, 77.2050, "Intersection 3")
    graph.add_node("node_4", 28.5550, 77.2000, "Intersection 4")
    graph.add_node("node_5", 28.5350, 77.1950, "Intersection 5")

    graph.add_edge("connaught_place", "node_1", distance_km=0.8, gradient_percent=0.5, canopy_density_percent=60, speed_limit_kmh=50, aqi_value=150)
    graph.add_edge("node_1", "central_delhi", distance_km=0.7, gradient_percent=0.3, canopy_density_percent=65, speed_limit_kmh=50, aqi_value=140)
    graph.add_edge("central_delhi", "lodhi_garden", distance_km=0.6, gradient_percent=1.5, canopy_density_percent=80, speed_limit_kmh=40, aqi_value=120)
    graph.add_edge("lodhi_garden", "node_2", distance_km=0.8, gradient_percent=-1.0, canopy_density_percent=75, speed_limit_kmh=45, aqi_value=130)
    graph.add_edge("node_2", "node_3", distance_km=0.7, gradient_percent=0.2, canopy_density_percent=50, speed_limit_kmh=50, aqi_value=150)
    graph.add_edge("node_3", "node_4", distance_km=0.8, gradient_percent=-0.5, canopy_density_percent=55, speed_limit_kmh=50, aqi_value=160)
    graph.add_edge("node_4", "south_delhi", distance_km=0.7, gradient_percent=0.0, canopy_density_percent=50, speed_limit_kmh=50, aqi_value=165)
    graph.add_edge("south_delhi", "green_park", distance_km=0.8, gradient_percent=0.3, canopy_density_percent=70, speed_limit_kmh=50, aqi_value=140)
    graph.add_edge("green_park", "node_5", distance_km=0.7, gradient_percent=-0.2, canopy_density_percent=60, speed_limit_kmh=50, aqi_value=155)
    graph.add_edge("node_5", "india_gate", distance_km=0.8, gradient_percent=0.1, canopy_density_percent=55, speed_limit_kmh=50, aqi_value=170)
    graph.add_edge("connaught_place", "south_delhi", distance_km=2.8, gradient_percent=5.0, canopy_density_percent=30, speed_limit_kmh=60, aqi_value=200)

    return graph