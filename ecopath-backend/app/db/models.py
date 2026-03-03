"""
Database models for carpool matching.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class CarpoolUser(Base):
    """A user looking for a carpool match."""
    
    __tablename__ = "carpool_users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    
    # Current location
    origin_lat = Column(Float, nullable=False)
    origin_lon = Column(Float, nullable=False)
    origin_address = Column(String)
    
    # Destination
    dest_lat = Column(Float, nullable=False)
    dest_lon = Column(Float, nullable=False)
    dest_address = Column(String)
    
    # Timing
    departure_time = Column(DateTime, nullable=False)
    
    # Preferences
    is_driver = Column(Boolean, default=False)  # True = offering ride, False = seeking ride
    car_type = Column(String, default="sedan")  # sedan, suv, hatchback
    max_passengers = Column(Integer, default=4)  # For drivers
    
    # Eco preferences
    preferred_eco_score = Column(Float)  # Minimum acceptable eco-score
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Ride request expires after this time
    
    def __repr__(self):
        role = "Driver" if self.is_driver else "Passenger"
        return f"<CarpoolUser {role}: {self.name} ({self.user_id})>"


class CarpoolMatch(Base):
    """A successful carpool match."""
    
    __tablename__ = "carpool_matches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id = Column(String, nullable=False)
    passenger_id = Column(String, nullable=False)
    
    # Match quality metrics
    route_overlap = Column(Float)  # 0-1, how much route overlaps
    time_overlap = Column(Float)  # 0-1, how aligned departure times are
    location_proximity = Column(Float)  # 0-1, how close origins/destinations are
    match_score = Column(Float)  # Combined score 0-100
    
    # Estimated savings
    co2_saved_kg = Column(Float)  # Per passenger
    cost_saved_rupees = Column(Float)
    eco_improvement = Column(Float)  # Eco-score improvement
    
    # Status
    status = Column(String, default="pending")  # pending, accepted, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<CarpoolMatch {self.driver_id}→{self.passenger_id}: {self.match_score:.1f}>"


class CarpoolRideShare(Base):
    """A completed ride share (for history)."""
    
    __tablename__ = "carpool_ride_shares"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String, nullable=False)
    
    # Route taken
    origin_lat = Column(Float)
    origin_lon = Column(Float)
    dest_lat = Column(Float)
    dest_lon = Column(Float)
    distance_km = Column(Float)
    duration_minutes = Column(Integer)
    
    # Results
    co2_saved_kg = Column(Float)
    cost_saved_rupees = Column(Float)
    
    # Ratings
    driver_rating = Column(Integer)  # 1-5
    passenger_rating = Column(Integer)  # 1-5
    notes = Column(String)
    
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RideShare {self.match_id}: {self.distance_km:.1f}km, CO2 saved: {self.co2_saved_kg:.2f}kg>"