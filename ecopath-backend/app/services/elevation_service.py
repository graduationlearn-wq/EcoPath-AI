"""
Elevation Service — fetches real elevation data and calculates road gradients.

Uses the Open-Elevation API (free, no API key needed, global coverage).
Calculates gradient % for each road segment using:
    gradient % = (elevation_end - elevation_start) / distance_m × 100
"""

import json
import math
import logging
import urllib.request

logger = logging.getLogger(__name__)

# Open-Elevation API endpoint (free, no key needed)
OPEN_ELEVATION_API = "https://api.open-elevation.com/api/v1/lookup"

# Max locations per API call (Open-Elevation recommends batching)
BATCH_SIZE = 100


class ElevationService:
    """Fetches elevation data and calculates road gradients."""

    def __init__(self):
        # Cache: key=rounded (lat, lon), value=elevation in meters
        self._cache = {}

    def _cache_key(self, lat: float, lon: float) -> tuple:
        """Round to 4 decimal places (~11m grid) for caching."""
        return (round(lat, 4), round(lon, 4))

    def get_elevations_batch(self, locations: list) -> dict:
        """
        Fetch elevations for a list of (lat, lon) tuples in one API call.

        Args:
            locations: List of (lat, lon) tuples

        Returns:
            Dict mapping (lat, lon) → elevation_meters
        """
        uncached = [loc for loc in locations if self._cache_key(*loc) not in self._cache]

        if uncached:
            for i in range(0, len(uncached), BATCH_SIZE):
                batch = uncached[i:i + BATCH_SIZE]
                self._fetch_batch(batch)

        results = {}
        for loc in locations:
            key = self._cache_key(*loc)
            results[loc] = self._cache.get(key, 0)

        return results

    def _fetch_batch(self, locations: list):
        """Fetch a batch of elevations from Open-Elevation API."""
        try:
            payload = {
                "locations": [
                    {"latitude": lat, "longitude": lon}
                    for lat, lon in locations
                ]
            }

            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                OPEN_ELEVATION_API,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())

            for item in result.get('results', []):
                key = self._cache_key(item['latitude'], item['longitude'])
                self._cache[key] = item['elevation']

            logger.debug(f"Fetched {len(locations)} elevations from Open-Elevation API")

        except Exception as e:
            logger.warning(f"Elevation batch fetch failed: {e} — gradients will default to 0")
            for lat, lon in locations:
                key = self._cache_key(lat, lon)
                if key not in self._cache:
                    self._cache[key] = 0

    def calculate_gradient(
        self,
        lat1: float, lon1: float, elev1: float,
        lat2: float, lon2: float, elev2: float,
    ) -> float:
        """
        Calculate gradient % between two points.
        gradient % = rise / run × 100
        """
        R = 6371000
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )
        distance_m = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        if distance_m < 1:
            return 0.0

        rise = elev2 - elev1
        gradient = (rise / distance_m) * 100
        return max(-30.0, min(30.0, round(gradient, 2)))

    def enrich_graph_with_gradients(self, graph) -> None:
        """
        Fetch real elevation for all nodes in the graph and update
        edge gradient_percent values with real calculated gradients.
        Modifies the graph in-place.
        """
        # Skip for very large graphs — too slow for real-time routing
        # Will be enabled with Redis caching in a future step
        if len(graph.nodes_data) > 500:
            logger.warning(
                f"Graph has {len(graph.nodes_data)} nodes — "
                f"skipping elevation enrichment (too large for real-time). "
                f"Will be enabled with caching layer."
            )
            return

        logger.info(f"Fetching elevation for {len(graph.nodes_data)} nodes...")

        node_locations = []
        for node_id, node_data in graph.nodes_data.items():
            node_locations.append((node_data['latitude'], node_data['longitude']))

        unique_locations = list(set(node_locations))
        elevation_map = self.get_elevations_batch(unique_locations)

        node_elevations = {}
        for node_id, node_data in graph.nodes_data.items():
            loc = (node_data['latitude'], node_data['longitude'])
            node_elevations[node_id] = elevation_map.get(loc, 0)

        updated = 0
        for (from_id, to_id), edge_data in graph.edges_data.items():
            from_data = graph.nodes_data.get(from_id)
            to_data = graph.nodes_data.get(to_id)

            if not from_data or not to_data:
                continue

            elev_from = node_elevations.get(from_id, 0)
            elev_to = node_elevations.get(to_id, 0)

            gradient = self.calculate_gradient(
                from_data['latitude'], from_data['longitude'], elev_from,
                to_data['latitude'], to_data['longitude'], elev_to,
            )

            graph.edges_data[(from_id, to_id)]['gradient_percent'] = gradient
            updated += 1

        logger.info(f"Updated {updated} edges with real gradient data")