"""
Dynamic Weight Service — adjusts eco-cost weights based on time of day and AQI levels.

Base weights:
    W1 Traffic:  0.30
    W2 AQI:      0.40
    W3 Gradient: 0.20
    W4 Carpool:  0.10
    W5 Greenery: 0.15

These shift dynamically depending on:
    - Time of day (peak hours vs off-peak vs night)
    - AQI emergency level (if AQI > 300, W2 gets boosted hard)
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Time periods (24hr format)
MORNING_PEAK_START = 7    # 7:00 AM
MORNING_PEAK_END = 9      # 9:00 AM
EVENING_PEAK_START = 17   # 5:00 PM
EVENING_PEAK_END = 19     # 7:00 PM
NIGHT_START = 22          # 10:00 PM
NIGHT_END = 6             # 6:00 AM

# AQI emergency threshold
AQI_EMERGENCY = 300


def get_time_period(hour: int) -> str:
    """
    Classify the current hour into a time period.

    Args:
        hour: Hour of day (0-23)

    Returns:
        'morning_peak', 'evening_peak', 'night', or 'normal'
    """
    if MORNING_PEAK_START <= hour < MORNING_PEAK_END:
        return 'morning_peak'
    elif EVENING_PEAK_START <= hour < EVENING_PEAK_END:
        return 'evening_peak'
    elif hour >= NIGHT_START or hour < NIGHT_END:
        return 'night'
    else:
        return 'normal'


def get_dynamic_weights(aqi_value: int = 100, departure_time: datetime = None) -> dict:
    """
    Calculate dynamic eco-cost weights based on time of day and AQI.

    Args:
        aqi_value: Current AQI at the route area (0-500 scale)
        departure_time: When the user wants to depart (defaults to now)

    Returns:
        Dict of weights: W1_traffic, W2_aqi, W3_gradient, W4_carpool, W5_greenery
    """
    # Use current time if no departure time given
    if departure_time is None:
        departure_time = datetime.now()

    hour = departure_time.hour
    time_period = get_time_period(hour)

    # Start from base weights
    weights = {
        'W1_traffic': 0.30,
        'W2_aqi': 0.40,
        'W3_gradient': 0.20,
        'W4_carpool': 0.10,
        'W5_greenery': 0.15,
    }

    # --- TIME-BASED ADJUSTMENTS ---

    if time_period == 'morning_peak':
        # Roads are congested, pollution is rising with traffic
        # Prioritize avoiding high-traffic and high-AQI roads
        weights['W1_traffic'] = 0.45   # Up from 0.30 — traffic is the main problem
        weights['W2_aqi'] = 0.50       # Up from 0.40 — pollution peaks with morning traffic
        weights['W3_gradient'] = 0.15  # Down slightly — gradient less critical vs congestion
        weights['W4_carpool'] = 0.15   # Up from 0.10 — peak hour = best time to carpool
        weights['W5_greenery'] = 0.10  # Down slightly
        logger.info(f"Morning peak weights applied (hour={hour})")

    elif time_period == 'evening_peak':
        # Heaviest congestion of the day, pollution worst in evening
        weights['W1_traffic'] = 0.50   # Highest traffic weight of the day
        weights['W2_aqi'] = 0.55       # Highest AQI weight — evening pollution is worst
        weights['W3_gradient'] = 0.15
        weights['W4_carpool'] = 0.20   # Highest carpool weight — evening commute carpooling
        weights['W5_greenery'] = 0.10
        logger.info(f"Evening peak weights applied (hour={hour})")

    elif time_period == 'night':
        # Low traffic, better air quality — gradient and greenery matter more
        weights['W1_traffic'] = 0.15   # Down from 0.30 — roads are clear
        weights['W2_aqi'] = 0.25       # Down from 0.40 — air is cleaner at night
        weights['W3_gradient'] = 0.35  # Up from 0.20 — fuel efficiency matters more
        weights['W4_carpool'] = 0.05   # Down — fewer carpool opportunities at night
        weights['W5_greenery'] = 0.20  # Up slightly
        logger.info(f"Night weights applied (hour={hour})")

    else:
        # Normal hours — use base weights as-is
        logger.info(f"Normal hours weights applied (hour={hour})")

    # --- AQI EMERGENCY OVERRIDE ---
    # If AQI is dangerously high (>300), boost W2 regardless of time
    # This forces the pathfinder to strongly prefer lower-AQI roads
    if aqi_value > AQI_EMERGENCY:
        original_w2 = weights['W2_aqi']
        weights['W2_aqi'] = min(weights['W2_aqi'] * 1.5, 0.80)
        logger.warning(
            f"AQI EMERGENCY: AQI={aqi_value} > {AQI_EMERGENCY}. "
            f"W2_aqi boosted: {original_w2:.2f} → {weights['W2_aqi']:.2f}"
        )

    logger.info(
        f"Dynamic weights → "
        f"W1={weights['W1_traffic']:.2f} "
        f"W2={weights['W2_aqi']:.2f} "
        f"W3={weights['W3_gradient']:.2f} "
        f"W4={weights['W4_carpool']:.2f} "
        f"W5={weights['W5_greenery']:.2f} "
        f"| period={time_period}, AQI={aqi_value}"
    )

    return weights