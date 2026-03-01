from app.engines.eco_cost import EcoCostCalculator

# Create calculator
calc = EcoCostCalculator()

# Test scenario: sitting in traffic, bad AQI, flat road, some trees, 2 carpool matches
result = calc.analyze_segment(
    current_speed_kmh=15,      # Slow traffic
    free_flow_speed_kmh=50,    # Normal speed is 50
    aqi_value=300,             # Poor air quality
    gradient_percent=2.0,      # Slight uphill
    canopy_density_percent=60, # Good tree coverage
    num_carpool_matches=2      # 2 carpool riders available
)

print(f"Total Eco-Cost: {result.total_eco_cost:.2f}")
print(f"  Traffic Penalty: {result.traffic_penalty:.2f}")
print(f"  AQI Penalty: {result.aqi_penalty:.2f}")
print(f"  Gradient Penalty: {result.gradient_penalty:.2f}")
print(f"  Carpool Bonus: {result.carpool_bonus:.2f}")
print(f"  Greenery Bonus: {result.greenery_bonus:.2f}")