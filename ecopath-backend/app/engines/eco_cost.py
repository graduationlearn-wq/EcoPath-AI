"""
Eco-Cost Heuristic Calculator

Computes the eco-cost score for any route using the formula:
Eco_Score = (Traffic × W₁) + (AQI × W₂) + (Gradient × W₃) - (Carpool × W₄) - (Greenery × W₅)
"""

from dataclasses import dataclass


@dataclass
class EcoCostComponents:
    """Breakdown of eco-cost components."""
    traffic_penalty: float
    aqi_penalty: float
    gradient_penalty: float
    carpool_bonus: float
    greenery_bonus: float
    total_eco_cost: float


class EcoCostCalculator:
    """Core eco-cost heuristic engine."""

    def __init__(self, base_weights: dict = None):
        """Initialize with base weights."""
        self.base_weights = base_weights or {
            'W1_traffic': 0.3,
            'W2_aqi': 0.4,
            'W3_gradient': 0.2,
            'W4_carpool': 0.1,
            'W5_greenery': 0.15,
        }

    def update_weights(self, new_weights: dict):
        """
        Update weights dynamically.
        Called by route service with time/AQI adjusted weights before pathfinding.
        """
        self.base_weights.update(new_weights)

    @staticmethod
    def calculate_traffic_penalty(current_speed_kmh: float, free_flow_speed_kmh: float) -> float:
        """Calculate traffic penalty (0-100)."""
        if free_flow_speed_kmh <= 0:
            return 0

        congestion_ratio = max(0, 1 - (current_speed_kmh / free_flow_speed_kmh))
        penalty = congestion_ratio * 100

        # Amplify heavy congestion
        if congestion_ratio > 0.7:
            penalty *= 1.3

        return min(penalty, 100)

    @staticmethod
    def calculate_aqi_penalty(aqi_value: int) -> float:
        """Calculate AQI penalty (0-100)."""
        if aqi_value <= 50:
            return 5
        elif aqi_value <= 100:
            return 10
        elif aqi_value <= 200:
            return 30
        elif aqi_value <= 300:
            return 50
        elif aqi_value <= 400:
            return 75
        else:
            return 100

    @staticmethod
    def calculate_gradient_penalty(gradient_percent: float) -> float:
        """Calculate gradient penalty (0-100)."""
        gradient_abs = abs(gradient_percent)

        if gradient_abs <= 1:
            return 0
        elif gradient_abs <= 3:
            return gradient_abs * 5
        elif gradient_abs <= 6:
            return 15 + (gradient_abs - 3) * 8
        else:
            return min(39 + (gradient_abs - 6) * 10, 100)

    @staticmethod
    def calculate_carpool_bonus(num_matched_riders: int) -> float:
        """Calculate carpool bonus (negative reduces cost)."""
        if num_matched_riders == 0:
            return 0
        elif num_matched_riders == 1:
            return -5
        elif num_matched_riders == 2:
            return -12
        else:
            return -20

    @staticmethod
    def calculate_greenery_bonus(canopy_density_percent: float) -> float:
        """Calculate greenery bonus (negative reduces cost)."""
        if canopy_density_percent < 30:
            return 0
        elif canopy_density_percent < 50:
            return -(canopy_density_percent - 30) * 0.5
        elif canopy_density_percent < 70:
            return -10 - (canopy_density_percent - 50) * 0.5
        else:
            return -20

    def calculate_segment_eco_cost(
        self,
        traffic_penalty: float,
        aqi_penalty: float,
        gradient_penalty: float,
        carpool_bonus: float,
        greenery_bonus: float,
    ) -> float:
        """Calculate overall eco-cost for a segment using current weights."""
        W1 = self.base_weights['W1_traffic']
        W2 = self.base_weights['W2_aqi']
        W3 = self.base_weights['W3_gradient']
        W4 = self.base_weights['W4_carpool']
        W5 = self.base_weights['W5_greenery']

        eco_cost = (
            traffic_penalty * W1 +
            aqi_penalty * W2 +
            gradient_penalty * W3 -
            carpool_bonus * W4 -
            greenery_bonus * W5
        )

        return max(0, eco_cost)

    def analyze_segment(
        self,
        current_speed_kmh: float,
        free_flow_speed_kmh: float,
        aqi_value: int,
        gradient_percent: float,
        canopy_density_percent: float,
        num_carpool_matches: int = 0,
    ) -> EcoCostComponents:
        """Analyze a single road segment."""
        traffic_penalty = self.calculate_traffic_penalty(current_speed_kmh, free_flow_speed_kmh)
        aqi_penalty = self.calculate_aqi_penalty(aqi_value)
        gradient_penalty = self.calculate_gradient_penalty(gradient_percent)
        carpool_bonus = self.calculate_carpool_bonus(num_carpool_matches)
        greenery_bonus = self.calculate_greenery_bonus(canopy_density_percent)

        total_eco_cost = self.calculate_segment_eco_cost(
            traffic_penalty, aqi_penalty, gradient_penalty, carpool_bonus, greenery_bonus
        )

        return EcoCostComponents(
            traffic_penalty=traffic_penalty,
            aqi_penalty=aqi_penalty,
            gradient_penalty=gradient_penalty,
            carpool_bonus=carpool_bonus,
            greenery_bonus=greenery_bonus,
            total_eco_cost=total_eco_cost,
        )