"""
Elevation Service — fetches real elevation data and calculates road gradients.
Checks PostgreSQL cache before making API calls.
Elevation never expires — geography doesn't change.
Now works for graphs of ANY size thanks to DB caching.
"""

import json
import math
import logging
import urllib.request

logger = logging.getLogger(__name__)

OPEN_ELEVATION_API = "https://api.open-elevation.com/api/v1/lookup"
BATCH_SIZE = 100


class ElevationService:
    """Fetches elevation data and calculates road gradients."""

    def __init__(self):
        # In-memory cache as fallback
        self._memory_cache = {}

    def _cache_key(self, lat: float, lon: float) -> tuple:
        return (round(lat, 4), round(lon, 4))

    def get_elevations_batch(self, locations: list, db=None) -> dict:
        """
        Fetch elevations for a list of (lat, lon) tuples.
        Check order: DB cache → API call
        """
        results = {}
        uncached = []

        # 1. Check DB cache first
        if db:
            try:
                from app.db.cache_service import CacheService
                cache = CacheService(db)
                db_results = cache.get_elevation_batch(locations)
                results.update(db_results)
                uncached = [loc for loc in locations if loc not in results]
                if db_results:
                    logger.debug(f"Elevation DB cache: {len(db_results)} hits, {len(uncached)} misses")
            except Exception as e:
                logger.warning(f"Elevation DB cache check failed: {e}")
                uncached = locations
        else:
            uncached = locations

        # 2. Check in-memory cache for remaining
        still_uncached = []
        for loc in uncached:
            key = self._cache_key(*loc)
            if key in self._memory_cache:
                results[loc] = self._memory_cache[key]
            else:
                still_uncached.append(loc)

        # 3. Fetch from API for remaining
        if still_uncached:
            fetched = {}
            for i in range(0, len(still_uncached), BATCH_SIZE):
                batch = still_uncached[i:i + BATCH_SIZE]
                batch_result = self._fetch_batch(batch)
                fetched.update(batch_result)

            results.update(fetched)

            # Save to DB cache
            if db and fetched:
                try:
                    from app.db.cache_service import CacheService
                    cache = CacheService(db)
                    cache.save_elevation_batch(fetched)
                except Exception as e:
                    logger.warning(f"Elevation DB cache save failed: {e}")

        return results

    def _fetch_batch(self, locations: list) -> dict:
        """Fetch a batch of elevations from Open-Elevation API."""
        results = {}
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
                loc = (item['latitude'], item['longitude'])
                results[loc] = item['elevation']
                key = self._cache_key(item['latitude'], item['longitude'])
                self._memory_cache[key] = item['elevation']

            logger.debug(f"Fetched {len(locations)} elevations from API")

        except Exception as e:
            logger.warning(f"Elevation batch fetch failed: {e} — defaulting to 0")
            for loc in locations:
                results[loc] = 0

        return results

    def calculate_gradient(
        self,
        lat1: float, lon1: float, elev1: float,
        lat2: float, lon2: float, elev2: float,
    ) -> float:
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

    def enrich_graph_with_gradients(self, graph, db=None) -> None:
        """
        Fetch real elevation for all nodes and update edge gradients.
        Now works for ANY graph size — DB cache handles large graphs.
        """
        node_count = len(graph.nodes_data)
        logger.info(f"Fetching elevation for {node_count} nodes...")

        node_locations = []
        for node_id, node_data in graph.nodes_data.items():
            node_locations.append((node_data['latitude'], node_data['longitude']))

        unique_locations = list(set(node_locations))
        elevation_map = self.get_elevations_batch(unique_locations, db=db)

        node_elevations = {}
        for node_id, node_data in graph.nodes_data.items():
            loc = (node_data['latitude'], node_data['longitude'])
            node_elevations[node_id] = elevation_map.get(loc, 0)

        updated = 0
        for edge_key, edge_data in graph.edges_data.items():
            from_id = edge_key[0]
            to_id = edge_key[1]
            from_data = graph.nodes_data.get(from_id)
            to_data = graph.nodes_data.get(to_id)

            if not from_data or not to_data:
                continue

            gradient = self.calculate_gradient(
                from_data['latitude'], from_data['longitude'],
                node_elevations.get(from_id, 0),
                to_data['latitude'], to_data['longitude'],
                node_elevations.get(to_id, 0),
            )

            graph.edges_data[edge_key]['gradient_percent'] = gradient
            updated += 1

        logger.info(f"Updated {updated} edges with real gradient data")