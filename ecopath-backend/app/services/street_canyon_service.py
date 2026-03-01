"""
Street Canyon Service — detects urban trap zones where exhaust concentrates.

A "street canyon" occurs when tall buildings on both sides of a narrow street
trap vehicle exhaust at ground level, making real pollution far worse than
open-air AQI readings suggest.

Street Canyon Index (SCI) = Average Building Height / Street Width
    SCI < 1.0  → Open street, pollution disperses freely
    SCI 1-2    → Moderate canyon, some trapping
    SCI > 2.0  → Severe canyon — TRAP ZONE, avoid if possible

Data sources (all free, from OSM):
    - Building heights: 'building:height' or 'height' tag on OSM buildings
    - Street widths: 'width' tag, or estimated from road type (highway tag)
"""

import logging

logger = logging.getLogger(__name__)

HIGHWAY_WIDTH_DEFAULTS = {
    'motorway': 14.0,
    'trunk': 12.0,
    'primary': 10.0,
    'secondary': 8.0,
    'tertiary': 7.0,
    'residential': 6.0,
    'service': 4.0,
    'unclassified': 6.0,
    'living_street': 4.5,
    'pedestrian': 5.0,
}

DEFAULT_STREET_WIDTH = 7.0
DEFAULT_BUILDING_HEIGHT = 10.0

SCI_MODERATE = 1.0
SCI_SEVERE = 2.0


def estimate_street_width(highway_type: str, explicit_width=None) -> float:
    if explicit_width:
        try:
            return float(str(explicit_width).replace('m', '').strip())
        except (ValueError, TypeError):
            pass
    return HIGHWAY_WIDTH_DEFAULTS.get(highway_type, DEFAULT_STREET_WIDTH)


def calculate_canyon_index(building_height: float, street_width: float) -> float:
    if street_width <= 0:
        return 0.0
    return round(building_height / street_width, 2)


def classify_canyon(sci: float) -> str:
    if sci < SCI_MODERATE:
        return 'open'
    elif sci < SCI_SEVERE:
        return 'moderate'
    else:
        return 'trap_zone'


def calculate_canyon_penalty(sci: float) -> float:
    if sci < SCI_MODERATE:
        return 0.0
    elif sci < SCI_SEVERE:
        return round((sci - SCI_MODERATE) / (SCI_SEVERE - SCI_MODERATE) * 25, 2)
    else:
        return round(min(25 + (sci - SCI_SEVERE) * 12.5, 50), 2)


class StreetCanyonService:
    """Analyzes urban geometry to detect street canyon trap zones."""

    def enrich_graph_with_canyon_data(self, road_graph, osm_graph) -> None:
        """
        Analyze building heights and street widths from OSM data
        and enrich road_graph edges with canyon index and penalty.
        Modifies road_graph in-place.
        """
        enriched = 0
        trap_zones = 0

        for edge_key, edge_data in road_graph.edges_data.items():
            from_id = edge_key[0]
            to_id = edge_key[1]

            # Get OSM edge attributes
            osm_edge = {}
            if osm_graph is not None:
                try:
                    osm_edge = osm_graph.edges.get((int(from_id), int(to_id), 0), {})
                except (ValueError, TypeError):
                    osm_edge = {}

            # Get street width
            highway_type = osm_edge.get('highway', 'unclassified')
            if isinstance(highway_type, list):
                highway_type = highway_type[0]
            street_width = estimate_street_width(highway_type, osm_edge.get('width'))

            # Get building height
            building_height = DEFAULT_BUILDING_HEIGHT
            raw_height = osm_edge.get('building:height') or osm_edge.get('height')
            if raw_height:
                try:
                    building_height = float(str(raw_height).replace('m', '').strip())
                except (ValueError, TypeError):
                    building_height = DEFAULT_BUILDING_HEIGHT

            # Calculate canyon metrics
            sci = calculate_canyon_index(building_height, street_width)
            canyon_class = classify_canyon(sci)
            canyon_penalty = calculate_canyon_penalty(sci)

            # Write back using the original edge_key (not a new tuple)
            road_graph.edges_data[edge_key]['canyon_index'] = sci
            road_graph.edges_data[edge_key]['canyon_class'] = canyon_class
            road_graph.edges_data[edge_key]['canyon_penalty'] = canyon_penalty

            enriched += 1
            if canyon_class == 'trap_zone':
                trap_zones += 1

        logger.info(
            f"Street canyon analysis complete: "
            f"{enriched} edges analyzed, {trap_zones} trap zones detected"
        )