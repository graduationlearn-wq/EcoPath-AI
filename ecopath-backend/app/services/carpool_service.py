"""
Carpool matching service - finds compatible riders and drivers.
"""

from datetime import datetime, timedelta
import math
from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session

from app.db.models import CarpoolUser, CarpoolMatch

logger = logging.getLogger(__name__)


class CarpoolService:
    """Manages carpool matching and optimization."""
    
    MATCH_SCORE_THRESHOLD = 60  # Only matches >= 60 are suggested
    MAX_DISTANCE_DEVIATION = 2.0  # km, max deviation from ideal route
    MAX_TIME_DEVIATION = 15  # minutes, max time difference
    
    @staticmethod
    def get_active_users(
        db: Session,
        exclude_user_id: str = None,
    ) -> List[CarpoolUser]:
        """Get all active carpool users (excluding self)."""
        query = db.query(CarpoolUser).filter(
            CarpoolUser.is_active == True,
            CarpoolUser.expires_at > datetime.utcnow(),
        )
        
        if exclude_user_id:
            query = query.filter(CarpoolUser.user_id != exclude_user_id)
        
        return query.all()
    
    @staticmethod
    def find_matches(
        db: Session,
        user: CarpoolUser,
    ) -> List[Dict]:
        """
        Find best carpool matches for a user.
        
        Returns: List of matches with scores, sorted by quality.
        """
        
        active_users = CarpoolService.get_active_users(db, exclude_user_id=user.user_id)
        matches = []
        
        for candidate in active_users:
            # Filter: one must be driver, one must be passenger
            if user.is_driver and candidate.is_driver:
                continue  # Both drivers
            if not user.is_driver and not candidate.is_driver:
                continue  # Both passengers
            
            # Calculate match quality
            match_score = CarpoolService.calculate_match_score(
                user,
                candidate,
            )
            
            if match_score >= CarpoolService.MATCH_SCORE_THRESHOLD:
                driver = user if user.is_driver else candidate
                passenger = candidate if user.is_driver else user
                
                # Calculate savings
                co2_saved = CarpoolService.estimate_co2_savings(driver, passenger)
                cost_saved = CarpoolService.estimate_cost_savings(driver, passenger)
                
                matches.append({
                    'driver_id': driver.user_id,
                    'driver_name': driver.name,
                    'passenger_id': passenger.user_id,
                    'passenger_name': passenger.name,
                    'match_score': match_score,
                    'route_overlap': CarpoolService.calculate_route_overlap(user, candidate),
                    'time_overlap': CarpoolService.calculate_time_overlap(user, candidate),
                    'co2_saved_kg': co2_saved,
                    'cost_saved_rupees': cost_saved,
                })
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches[:5]  # Return top 5 matches
    
    @staticmethod
    def calculate_match_score(user1: CarpoolUser, user2: CarpoolUser) -> float:
        """
        Calculate overall match quality score (0-100).
        
        Factors:
        - Route overlap (how similar destinations are)
        - Time overlap (how aligned departure times are)
        - Location proximity (how close starting points are)
        """
        
        route_overlap = CarpoolService.calculate_route_overlap(user1, user2)
        time_overlap = CarpoolService.calculate_time_overlap(user1, user2)
        location_prox = CarpoolService.calculate_location_proximity(user1, user2)
        
        # Weighted average
        # Route overlap is most important (50%)
        # Time overlap is important (30%)
        # Location proximity is nice-to-have (20%)
        score = (
            route_overlap * 0.5 +
            time_overlap * 0.3 +
            location_prox * 0.2
        ) * 100
        
        return max(0, min(100, score))
    
    @staticmethod
    def calculate_route_overlap(user1: CarpoolUser, user2: CarpoolUser) -> float:
        """
        Calculate how much routes overlap (0-1).
        
        Compare destination coordinates. Closer = higher overlap.
        """
        
        # Distance between destinations (in km)
        dest_distance = CarpoolService.haversine_distance(
            user1.dest_lat, user1.dest_lon,
            user2.dest_lat, user2.dest_lon,
        )
        
        # If destinations are close, routes overlap well
        if dest_distance < 1:  # < 1 km
            return 1.0
        elif dest_distance < 3:  # < 3 km
            return 0.8
        elif dest_distance < 5:  # < 5 km
            return 0.6
        elif dest_distance < 10:  # < 10 km
            return 0.4
        else:
            return 0.0
    
    @staticmethod
    def calculate_time_overlap(user1: CarpoolUser, user2: CarpoolUser) -> float:
        """
        Calculate time alignment (0-1).
        
        How close are departure times? Closer = higher score.
        """
        
        time_diff = abs((user1.departure_time - user2.departure_time).total_seconds() / 60)
        
        # Time differences
        if time_diff < 5:  # < 5 min difference
            return 1.0
        elif time_diff < 15:  # < 15 min difference
            return 0.8
        elif time_diff < 30:  # < 30 min difference
            return 0.6
        elif time_diff < 45:  # < 45 min difference
            return 0.4
        elif time_diff < 60:  # < 60 min difference
            return 0.2
        else:
            return 0.0
    
    @staticmethod
    def calculate_location_proximity(user1: CarpoolUser, user2: CarpoolUser) -> float:
        """
        Calculate how close origins are (0-1).
        
        Closer origins = easier to meet up.
        """
        
        origin_distance = CarpoolService.haversine_distance(
            user1.origin_lat, user1.origin_lon,
            user2.origin_lat, user2.origin_lon,
        )
        
        if origin_distance < 0.5:  # < 500m
            return 1.0
        elif origin_distance < 1:  # < 1 km
            return 0.8
        elif origin_distance < 2:  # < 2 km
            return 0.6
        elif origin_distance < 5:  # < 5 km
            return 0.4
        else:
            return 0.0
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in km."""
        
        R = 6371  # Earth radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def estimate_co2_savings(driver: CarpoolUser, passenger: CarpoolUser) -> float:
        """
        Estimate CO2 saved by carpooling.
        
        Typical car: 0.2 kg CO2 per km
        Shared by 2 people: 0.1 kg CO2 per person
        """
        
        # Assume 10 km average trip
        trip_distance = 10
        
        # 1 person = 0.2 kg CO2
        # 2 people (carpool) = 0.1 kg CO2 per person
        # Savings = 0.1 kg per person
        
        savings_per_km = 0.1
        return trip_distance * savings_per_km
    
    @staticmethod
    def estimate_cost_savings(driver: CarpoolUser, passenger: CarpoolUser) -> float:
        """
        Estimate cost savings (in rupees).
        
        Typical car fuel cost: Rs 10 per km
        Carpool: Rs 5 per person
        Savings: Rs 5 per person
        """
        
        # Assume 10 km trip
        trip_distance = 10
        
        # Fuel cost per km: Rs 10
        # Shared by 2: Rs 5 per person saved
        
        savings_per_km = 5
        return trip_distance * savings_per_km
    
    @staticmethod
    def create_match(
        db: Session,
        driver_id: str,
        passenger_id: str,
        match_score: float,
        route_overlap: float,
        time_overlap: float,
        co2_saved: float,
        cost_saved: float,
    ) -> CarpoolMatch:
        """Create a new carpool match in the database."""
        
        match = CarpoolMatch(
            driver_id=driver_id,
            passenger_id=passenger_id,
            route_overlap=route_overlap,
            time_overlap=time_overlap,
            location_proximity=(route_overlap + time_overlap) / 2,
            match_score=match_score,
            co2_saved_kg=co2_saved,
            cost_saved_rupees=cost_saved,
            eco_improvement=match_score / 100,
        )
        
        db.add(match)
        db.commit()
        db.refresh(match)
        
        logger.info(f"Created carpool match: {match}")
        
        return match