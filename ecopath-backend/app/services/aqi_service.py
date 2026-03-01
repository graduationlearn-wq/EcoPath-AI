"""
AQI Service — fetches real air quality data from OpenWeatherMap.

OpenWeatherMap Air Pollution API returns AQI on a 1-5 scale plus
individual pollutant concentrations (PM2.5, PM10, NO2, O3, etc).
We convert their scale to our 0-500 AQI scale that eco_cost.py expects.
"""

import logging
import urllib.request
import urllib.parse
import json

from app.config import settings

logger = logging.getLogger(__name__)

# OpenWeatherMap AQI scale → our AQI scale mapping
# OWM uses: 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
OWM_TO_AQI = {
    1: 25,    # Good       → 0-50
    2: 75,    # Fair       → 51-100
    3: 150,   # Moderate   → 101-200
    4: 250,   # Poor       → 201-300
    5: 400,   # Very Poor  → 301-500
}


class AQIService:
    """Fetches and caches real AQI data from OpenWeatherMap."""

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        # Simple in-memory cache: key=(lat,lon rounded to 2dp), value=aqi_int
        # Rounds coordinates to ~1km grid so nearby streets share the same AQI call
        self._cache = {}

    def _cache_key(self, lat: float, lon: float) -> tuple:
        """Round to 2 decimal places (~1.1km grid) to avoid redundant API calls."""
        return (round(lat, 2), round(lon, 2))

    def get_aqi(self, lat: float, lon: float) -> int:
        """
        Get AQI value for a coordinate.

        Returns AQI on 0-500 scale (matching eco_cost.py expectations).
        Falls back to 100 (moderate) if API call fails.
        """
        if not self.api_key:
            logger.warning("No OpenWeatherMap API key set — using default AQI 100")
            return 100

        cache_key = self._cache_key(lat, lon)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            url = (
                f"http://api.openweathermap.org/data/2.5/air_pollution"
                f"?lat={lat}&lon={lon}&appid={self.api_key}"
            )
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())

            # OWM response: {"list": [{"main": {"aqi": 1-5}, "components": {...}}]}
            owm_aqi = data["list"][0]["main"]["aqi"]
            aqi_value = OWM_TO_AQI.get(owm_aqi, 100)

            self._cache[cache_key] = aqi_value
            logger.debug(f"AQI at ({lat:.2f},{lon:.2f}): OWM={owm_aqi} → {aqi_value}")
            return aqi_value

        except Exception as e:
            logger.warning(f"AQI fetch failed for ({lat},{lon}): {e} — using default 100")
            return 100

    def get_aqi_for_route_area(self, lat: float, lon: float) -> int:
        """
        Get a single AQI value representing the general area of a route.
        Used to assign AQI to all edges in the graph as a baseline.
        Will be replaced with per-edge AQI in a future step.
        """
        return self.get_aqi(lat, lon)