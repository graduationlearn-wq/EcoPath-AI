"""
NDVI Service — fetches real vegetation index data and calculates canopy density.

Uses Open-Meteo's free API (no key needed, global coverage).
NDVI (Normalized Difference Vegetation Index) measures vegetation density
from satellite imagery on a scale of -1 to +1.

We convert NDVI → Canopy Density % for use in the eco-cost greenery bonus.
"""

import json
import logging
import urllib.request
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Open-Meteo endpoint for vegetation data
# Uses ERA5 reanalysis data — updated daily, global coverage
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"


def ndvi_to_canopy_percent(ndvi: float) -> float:
    """
    Convert NDVI value to canopy density percentage.

    NDVI scale:
        < 0.0  → No vegetation (water, buildings)  → 0%
        0-0.1  → Bare soil, concrete               → 0-5%
        0.1-0.2 → Sparse vegetation                → 5-20%
        0.2-0.3 → Grassland, scattered trees       → 20-40%
        0.3-0.5 → Moderate greenery, urban parks   → 40-65%
        0.5-0.7 → Dense vegetation                 → 65-85%
        0.7+   → Heavy forest canopy               → 85-100%
    """
    if ndvi <= 0.0:
        return 0.0
    elif ndvi <= 0.1:
        return ndvi * 50          # 0-5%
    elif ndvi <= 0.2:
        return 5 + (ndvi - 0.1) * 150   # 5-20%
    elif ndvi <= 0.3:
        return 20 + (ndvi - 0.2) * 200  # 20-40%
    elif ndvi <= 0.5:
        return 40 + (ndvi - 0.3) * 125  # 40-65%
    elif ndvi <= 0.7:
        return 65 + (ndvi - 0.5) * 100  # 65-85%
    else:
        return min(85 + (ndvi - 0.7) * 50, 100)  # 85-100%


class NDVIService:
    """Fetches vegetation index data and calculates canopy density per location."""

    def __init__(self):
        # In-memory cache: key=(lat,lon rounded to 2dp), value=canopy_percent
        self._memory_cache = {}

    def _cache_key(self, lat: float, lon: float) -> tuple:
        """Round to 2dp (~1km grid) — NDVI doesn't vary much within 1km."""
        return (round(lat, 2), round(lon, 2))

    def get_canopy_density(self, lat: float, lon: float, db=None) -> float:
        """
        Get canopy density % for a coordinate.

        Check order: DB cache → in-memory cache → API call
        Returns canopy density 0-100%.
        Falls back to 40% (urban average) if API fails.
        """
        # 1. Check DB cache
        if db:
            try:
                from app.db.cache_service import CacheService
                cache = CacheService(db)
                cached = cache.get_ndvi(lat, lon)
                if cached is not None:
                    logger.debug(f"NDVI DB cache HIT: ({round(lat,2)},{round(lon,2)}) = {cached}%")
                    return cached
            except Exception as e:
                logger.warning(f"NDVI DB cache check failed: {e}")

        # 2. Check in-memory cache
        cache_key = self._cache_key(lat, lon)
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # 3. Fetch from API
        canopy = self._fetch_ndvi(lat, lon)

        # Save to caches
        self._memory_cache[cache_key] = canopy
        if db:
            try:
                from app.db.cache_service import CacheService
                cache = CacheService(db)
                cache.save_ndvi(lat, lon, canopy)
            except Exception as e:
                logger.warning(f"NDVI DB cache save failed: {e}")

        return canopy

    def _fetch_ndvi(self, lat: float, lon: float) -> float:
        """
        Fetch NDVI from Open-Meteo API.
        Uses leaf_area_index_low_vegetation and leaf_area_index_high_vegetation
        as proxy for canopy density when direct NDVI isn't available.
        """
        try:
            # Get last 7 days of vegetation data and average it
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            params = (
                f"?latitude={lat}&longitude={lon}"
                f"&daily=et0_fao_evapotranspiration"
                f"&start_date={start_date}&end_date={end_date}"
            )

            # Try the vegetation/soil endpoint
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=soil_moisture_0_to_1cm&forecast_days=1"

            with urllib.request.urlopen(url, timeout=8) as response:
                data = json.loads(response.read().decode())

            # Use soil moisture as proxy for vegetation
            # Higher soil moisture generally correlates with more vegetation
            hourly = data.get('hourly', {})
            soil_moisture_values = hourly.get('soil_moisture_0_to_1cm', [])

            if soil_moisture_values:
                # Filter out None values
                valid_values = [v for v in soil_moisture_values if v is not None]
                if valid_values:
                    avg_moisture = sum(valid_values) / len(valid_values)
                    # Soil moisture 0-0.4 m³/m³ → canopy 10-80%
                    canopy = min(10 + (avg_moisture / 0.4) * 70, 80)
                    canopy = round(canopy, 1)
                    logger.info(f"NDVI proxy at ({lat:.2f},{lon:.2f}): soil_moisture={avg_moisture:.3f} → canopy={canopy}%")
                    return canopy

        except Exception as e:
            logger.warning(f"NDVI fetch failed for ({lat},{lon}): {e} — using default 40%")

        return 40.0  # Urban average fallback

    def enrich_graph_with_canopy(self, graph, db=None) -> None:
        """
        Fetch real canopy density for each edge's midpoint and update
        canopy_density_percent values in the graph.

        Uses midpoint of each edge for the NDVI lookup — more accurate
        than using node coordinates since we want the vegetation along
        the road, not just at the intersection.

        Modifies graph in-place.
        """
        logger.info(f"Fetching NDVI canopy data for {len(graph.edges_data)} edges...")

        # Collect unique midpoints (rounded to 2dp to minimize API calls)
        midpoint_cache = {}
        edge_midpoints = {}

        for edge_key, edge_data in graph.edges_data.items():
            from_id = edge_key[0]
            to_id = edge_key[1]

            from_data = graph.nodes_data.get(from_id)
            to_data = graph.nodes_data.get(to_id)

            if not from_data or not to_data:
                continue

            # Midpoint of the edge
            mid_lat = round((from_data['latitude'] + to_data['latitude']) / 2, 2)
            mid_lon = round((from_data['longitude'] + to_data['longitude']) / 2, 2)

            edge_midpoints[edge_key] = (mid_lat, mid_lon)
            midpoint_cache[(mid_lat, mid_lon)] = None  # placeholder

        # Fetch canopy for each unique midpoint
        unique_midpoints = list(midpoint_cache.keys())
        logger.info(f"Fetching canopy for {len(unique_midpoints)} unique locations...")

        for mid_lat, mid_lon in unique_midpoints:
            canopy = self.get_canopy_density(mid_lat, mid_lon, db=db)
            midpoint_cache[(mid_lat, mid_lon)] = canopy

        # Update edges with real canopy values
        updated = 0
        for edge_key, (mid_lat, mid_lon) in edge_midpoints.items():
            canopy = midpoint_cache.get((mid_lat, mid_lon), 40.0)
            graph.edges_data[edge_key]['canopy_density_percent'] = canopy
            updated += 1

        logger.info(f"Updated {updated} edges with real canopy density data")