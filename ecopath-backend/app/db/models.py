"""
Database models for EcoPath AI.

Tables:
    - road_networks   : Cached OSM road graphs per area (expires 7 days)
    - aqi_cache       : Cached AQI readings per location (expires 30 mins)
    - elevation_cache : Cached elevation per coordinate (never expires)
    - route_history   : Every route calculated (for future ML training)
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean
from app.db.database import Base


class RoadNetwork(Base):
    """
    Cached OSM road network for a geographic area.
    Keyed by center lat/lon rounded to 3dp and radius.
    Stores full node/edge data as JSON string.
    """
    __tablename__ = "road_networks"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Area identifier
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    radius_m = Column(Integer, nullable=False)

    # Stored graph data as JSON
    nodes_json = Column(Text, nullable=False)   # JSON string of all nodes
    edges_json = Column(Text, nullable=False)   # JSON string of all edges

    # Metadata
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # 7 days from creation


class AQICache(Base):
    """
    Cached AQI reading for a geographic area.
    Keyed by lat/lon rounded to 2dp (~1km grid).
    Expires after 30 minutes.
    """
    __tablename__ = "aqi_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Location (rounded to 2dp)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    # AQI value on our 0-500 scale
    aqi_value = Column(Integer, nullable=False)

    # Metadata
    fetched_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # 30 mins from fetch


class ElevationCache(Base):
    """
    Cached elevation for a coordinate.
    Keyed by lat/lon rounded to 4dp (~11m grid).
    Never expires — elevation doesn't change.
    """
    __tablename__ = "elevation_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Location (rounded to 4dp)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    # Elevation in meters
    elevation_m = Column(Float, nullable=False)

    # Metadata
    fetched_at = Column(DateTime, default=datetime.utcnow)


class RouteHistory(Base):
    """
    Every route calculated by the system.
    Stored for analytics and future ML training data.
    """
    __tablename__ = "route_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Request
    origin_lat = Column(Float, nullable=False)
    origin_lon = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lon = Column(Float, nullable=False)

    # Result
    distance_km = Column(Float)
    duration_minutes = Column(Integer)
    eco_score = Column(Float)
    co2_kg = Column(Float)

    # Eco breakdown
    aqi_penalty = Column(Float)
    gradient_penalty = Column(Float)
    canyon_penalty = Column(Float)
    greenery_bonus = Column(Float)

    # Context
    aqi_value = Column(Integer)
    time_period = Column(String(20))   # morning_peak, evening_peak, night, normal
    vehicle_type = Column(String(10))  # ice, ev, hybrid

    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)