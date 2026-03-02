"""
AQI Service — fetches real air quality data from OpenWeatherMap.
Checks PostgreSQL cache before making API calls.
Cache expires every 30 minutes.
"""

import logging
import urllib.request
import json

from app.config import settings

logger = logging.getLogger(__name__)

OWM_TO_AQI = {
    1: 25,
    2: 75,
    3: 150,
    4: 250,
    5: 400,
}


class AQIService:
    """Fetches and caches real AQI data from OpenWeatherMap."""

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        # In-memory cache as fallback if DB is unavailable
        self._memory_cache = {}

    def _cache_key(self, lat: float, lon: float) -> tuple:
        return (round(lat, 2), round(lon, 2))

    def get_aqi(self, lat: float, lon: float, db=None) -> int:
        """
        Get AQI value for a coordinate.
        Check order: DB cache → in-memory cache → API call
        """
        if not self.api_key:
            logger.warning("No OpenWeatherMap API key — using default AQI 100")
            return 100

        # 1. Check PostgreSQL cache first
        if db:
            try:
                from app.db.cache_service import CacheService
                cache = CacheService(db)
                cached = cache.get_aqi(lat, lon)
                if cached is not None:
                    logger.info(f"AQI DB cache HIT: ({round(lat,2)},{round(lon,2)}) = {cached}")
                    return cached
            except Exception as e:
                logger.warning(f"AQI DB cache check failed: {e}")

        # 2. Check in-memory cache
        cache_key = self._cache_key(lat, lon)
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # 3. Fetch from API
        try:
            url = (
                f"http://api.openweathermap.org/data/2.5/air_pollution"
                f"?lat={lat}&lon={lon}&appid={self.api_key}"
            )
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())

            owm_aqi = data["list"][0]["main"]["aqi"]
            aqi_value = OWM_TO_AQI.get(owm_aqi, 100)

            # Save to in-memory cache
            self._memory_cache[cache_key] = aqi_value

            # Save to DB cache
            if db:
                try:
                    from app.db.cache_service import CacheService
                    cache = CacheService(db)
                    cache.save_aqi(lat, lon, aqi_value)
                except Exception as e:
                    logger.warning(f"AQI DB cache save failed: {e}")

            logger.debug(f"AQI fetched from API: ({lat:.2f},{lon:.2f}) = {aqi_value}")
            return aqi_value

        except Exception as e:
            logger.warning(f"AQI fetch failed for ({lat},{lon}): {e} — using default 100")
            return 100

    def get_aqi_for_route_area(self, lat: float, lon: float, db=None) -> int:
        return self.get_aqi(lat, lon, db=db)