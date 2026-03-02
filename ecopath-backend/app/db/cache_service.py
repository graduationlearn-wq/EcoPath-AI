"""
Cache Service — reads and writes to PostgreSQL cache tables.

This is what makes EcoPath AI fast on repeat requests:
- Road networks cached for 7 days (OSM data rarely changes)
- AQI cached for 30 minutes (changes frequently)
- Elevation cached forever (never changes)
- Every route saved to history for future ML training
"""

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from app.db.models import RoadNetwork, AQICache, ElevationCache, RouteHistory

logger = logging.getLogger(__name__)

# Cache expiry durations
ROAD_NETWORK_EXPIRY_DAYS = 7
AQI_EXPIRY_MINUTES = 30


class CacheService:
    """Handles all database cache operations."""

    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────────────────────────
    # ROAD NETWORK CACHE
    # ─────────────────────────────────────────

    def _road_network_key(self, lat: float, lon: float, radius_m: int) -> tuple:
        """Round lat/lon to 3dp for cache key (~111m grid)."""
        return (round(lat, 3), round(lon, 3), radius_m)

    def get_road_network(self, lat: float, lon: float, radius_m: int):
        """
        Get cached road network if it exists and hasn't expired.
        Returns (nodes_dict, edges_dict) or None if not cached.
        """
        key_lat, key_lon, key_radius = self._road_network_key(lat, lon, radius_m)

        try:
            record = self.db.query(RoadNetwork).filter(
                RoadNetwork.center_lat == key_lat,
                RoadNetwork.center_lon == key_lon,
                RoadNetwork.radius_m == key_radius,
                RoadNetwork.expires_at > datetime.utcnow(),
            ).first()

            if record:
                logger.info(
                    f"Road network cache HIT: "
                    f"({key_lat},{key_lon}) r={key_radius}m — "
                    f"{record.node_count} nodes, {record.edge_count} edges"
                )
                nodes = json.loads(record.nodes_json)
                edges = json.loads(record.edges_json)
                return nodes, edges

            logger.info(f"Road network cache MISS: ({key_lat},{key_lon}) r={key_radius}m")
            return None

        except Exception as e:
            logger.warning(f"Road network cache read failed: {e}")
            return None

    def save_road_network(
        self,
        lat: float, lon: float, radius_m: int,
        nodes: dict, edges: dict,
    ):
        """
        Save a road network to cache.
        Replaces existing record if one exists for this area.
        """
        key_lat, key_lon, key_radius = self._road_network_key(lat, lon, radius_m)

        try:
            # Delete existing record for this area if any
            self.db.query(RoadNetwork).filter(
                RoadNetwork.center_lat == key_lat,
                RoadNetwork.center_lon == key_lon,
                RoadNetwork.radius_m == key_radius,
            ).delete()

            # Convert edge keys from tuples to strings for JSON serialization
            # Tuple keys like ('123', '456') become "123|456"
            serializable_edges = {
                f"{k[0]}|{k[1]}": v for k, v in edges.items()
            }

            record = RoadNetwork(
                center_lat=key_lat,
                center_lon=key_lon,
                radius_m=key_radius,
                nodes_json=json.dumps(nodes),
                edges_json=json.dumps(serializable_edges),
                node_count=len(nodes),
                edge_count=len(edges),
                expires_at=datetime.utcnow() + timedelta(days=ROAD_NETWORK_EXPIRY_DAYS),
            )

            self.db.add(record)
            self.db.commit()

            logger.info(
                f"Road network cached: ({key_lat},{key_lon}) r={key_radius}m — "
                f"{len(nodes)} nodes, {len(edges)} edges — "
                f"expires in {ROAD_NETWORK_EXPIRY_DAYS} days"
            )

        except Exception as e:
            logger.warning(f"Road network cache write failed: {e}")
            self.db.rollback()

    def restore_road_network(self, nodes: dict, edges_serialized: dict):
        """
        Restore edge keys from serialized "from|to" strings back to tuples.
        Called after loading from cache.
        """
        restored_edges = {}
        for key_str, edge_data in edges_serialized.items():
            parts = key_str.split('|')
            restored_edges[(parts[0], parts[1])] = edge_data
        return nodes, restored_edges

    # ─────────────────────────────────────────
    # AQI CACHE
    # ─────────────────────────────────────────

    def _aqi_key(self, lat: float, lon: float) -> tuple:
        """Round to 2dp for AQI cache key (~1km grid)."""
        return (round(lat, 2), round(lon, 2))

    def get_aqi(self, lat: float, lon: float):
        """
        Get cached AQI if not expired.
        Returns aqi_value int or None.
        """
        key_lat, key_lon = self._aqi_key(lat, lon)

        try:
            record = self.db.query(AQICache).filter(
                AQICache.lat == key_lat,
                AQICache.lon == key_lon,
                AQICache.expires_at > datetime.utcnow(),
            ).first()

            if record:
                logger.debug(f"AQI cache HIT: ({key_lat},{key_lon}) = {record.aqi_value}")
                return record.aqi_value

            logger.debug(f"AQI cache MISS: ({key_lat},{key_lon})")
            return None

        except Exception as e:
            logger.warning(f"AQI cache read failed: {e}")
            return None

    def save_aqi(self, lat: float, lon: float, aqi_value: int):
        """Save AQI reading to cache. Expires in 30 minutes."""
        key_lat, key_lon = self._aqi_key(lat, lon)

        try:
            self.db.query(AQICache).filter(
                AQICache.lat == key_lat,
                AQICache.lon == key_lon,
            ).delete()

            record = AQICache(
                lat=key_lat,
                lon=key_lon,
                aqi_value=aqi_value,
                expires_at=datetime.utcnow() + timedelta(minutes=AQI_EXPIRY_MINUTES),
            )

            self.db.add(record)
            self.db.commit()
            logger.debug(f"AQI cached: ({key_lat},{key_lon}) = {aqi_value}")

        except Exception as e:
            logger.warning(f"AQI cache write failed: {e}")
            self.db.rollback()

    # ─────────────────────────────────────────
    # ELEVATION CACHE
    # ─────────────────────────────────────────

    def _elevation_key(self, lat: float, lon: float) -> tuple:
        """Round to 4dp for elevation cache key (~11m grid)."""
        return (round(lat, 4), round(lon, 4))

    def get_elevation_batch(self, locations: list) -> dict:
        """
        Get cached elevations for a list of (lat, lon) tuples.
        Returns dict of (lat, lon) → elevation_m for all cached locations.
        """
        results = {}

        try:
            for lat, lon in locations:
                key_lat, key_lon = self._elevation_key(lat, lon)
                record = self.db.query(ElevationCache).filter(
                    ElevationCache.lat == key_lat,
                    ElevationCache.lon == key_lon,
                ).first()

                if record:
                    results[(lat, lon)] = record.elevation_m

        except Exception as e:
            logger.warning(f"Elevation cache read failed: {e}")

        return results

    def save_elevation_batch(self, elevation_map: dict):
        """
        Save a batch of elevation readings.
        elevation_map: dict of (lat, lon) → elevation_m
        """
        try:
            for (lat, lon), elevation_m in elevation_map.items():
                key_lat, key_lon = self._elevation_key(lat, lon)

                # Skip if already cached
                existing = self.db.query(ElevationCache).filter(
                    ElevationCache.lat == key_lat,
                    ElevationCache.lon == key_lon,
                ).first()

                if not existing:
                    record = ElevationCache(
                        lat=key_lat,
                        lon=key_lon,
                        elevation_m=elevation_m,
                    )
                    self.db.add(record)

            self.db.commit()
            logger.debug(f"Saved {len(elevation_map)} elevation readings to cache")

        except Exception as e:
            logger.warning(f"Elevation cache write failed: {e}")
            self.db.rollback()

    # ─────────────────────────────────────────
    # ROUTE HISTORY
    # ─────────────────────────────────────────

    def save_route_history(
        self,
        origin_lat: float, origin_lon: float,
        dest_lat: float, dest_lon: float,
        distance_km: float,
        duration_minutes: int,
        eco_score: float,
        co2_kg: float,
        aqi_penalty: float,
        gradient_penalty: float,
        canyon_penalty: float,
        greenery_bonus: float,
        aqi_value: int,
        time_period: str,
        vehicle_type: str,
        success: bool = True,
    ):
        """Save a completed route calculation to history."""
        try:
            record = RouteHistory(
                origin_lat=origin_lat,
                origin_lon=origin_lon,
                dest_lat=dest_lat,
                dest_lon=dest_lon,
                distance_km=distance_km,
                duration_minutes=duration_minutes,
                eco_score=eco_score,
                co2_kg=co2_kg,
                aqi_penalty=aqi_penalty,
                gradient_penalty=gradient_penalty,
                canyon_penalty=canyon_penalty,
                greenery_bonus=greenery_bonus,
                aqi_value=aqi_value,
                time_period=time_period,
                vehicle_type=vehicle_type,
                success=success,
            )

            self.db.add(record)
            self.db.commit()
            logger.debug(f"Route history saved: {origin_lat},{origin_lon} → {dest_lat},{dest_lon}")

        except Exception as e:
            logger.warning(f"Route history save failed: {e}")
            self.db.rollback()