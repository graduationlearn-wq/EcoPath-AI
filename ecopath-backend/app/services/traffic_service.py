"""
Traffic data service - estimates congestion based on time of day.
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TrafficService:
    """Manages traffic data and congestion estimation."""
    
    @staticmethod
    def get_congestion_ratio(departure_time: datetime = None) -> float:
        """
        Get traffic congestion ratio based on time of day.
        
        Returns: 0.5 (free flow) to 1.0+ (congested)
        """
        
        if departure_time is None:
            departure_time = datetime.now()
        
        hour = departure_time.hour
        
        # Get congestion based on time
        if 23 <= hour or hour < 6:
            # Night (11 PM - 6 AM): very light
            return 0.5
        
        elif 6 <= hour < 7:
            # Early morning (6-7 AM): light
            return 0.6
        
        elif 7 <= hour < 9:
            # Morning peak (7-9 AM): HEAVY
            return 1.0
        
        elif 9 <= hour < 12:
            # Mid-morning (9 AM-12 PM): moderate
            return 0.7
        
        elif 12 <= hour < 17:
            # Afternoon (12-5 PM): light to moderate
            return 0.65
        
        elif 17 <= hour < 19:
            # Evening peak (5-7 PM): HEAVY
            return 0.95
        
        else:  # 19 <= hour < 23
            # Evening (7-11 PM): light to moderate
            return 0.65
    
    @staticmethod
    def calculate_traffic_penalty(
        free_flow_speed_kmh: float,
        congestion_ratio: float,
    ) -> float:
        """
        Calculate traffic penalty based on congestion.
        
        Returns: Penalty 0-100
        """
        
        # Speed reduction from congestion
        # congestion_ratio 0.5 = no reduction
        # congestion_ratio 1.0 = 50% speed reduction
        
        speed_reduction_percent = (congestion_ratio - 0.5) * 100
        
        # Convert to penalty (0-100 scale)
        penalty = speed_reduction_percent * 1.5
        
        # Clamp to 0-100
        return max(0, min(100, penalty))


# Create singleton instance
traffic_service = TrafficService()