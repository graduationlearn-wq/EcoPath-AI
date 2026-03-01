from app.engines.graph_builder import create_mock_delhi_network
from app.engines.eco_cost import EcoCostCalculator
from app.engines.pathfinding import PathfindingEngine

# Create mock network
graph = create_mock_delhi_network()

# Create calculators
eco_calc = EcoCostCalculator()
pathfinder = PathfindingEngine(graph, eco_calc)

# Find route from Connaught Place to India Gate
start = "connaught_place"
goal = "india_gate"

print(f"Finding eco-optimal route from {start} to {goal}...\n")

route = pathfinder.find_route(start, goal)

if route:
    print(f"Route found: {' → '.join(route)}\n")
    
    details = pathfinder.get_route_details(route)
    
    print(f"Route Details:")
    print(f"  Distance: {details['total_distance_km']:.2f} km")
    print(f"  Time: {details['estimated_time_minutes']} minutes")
    print(f"  CO2: {details['estimated_co2_kg']} kg")
    print(f"  Total Eco-Cost: {details['total_eco_cost']:.2f}\n")
    
    print("Segments:")
    for seg in details['segments']:
        print(f"  {seg['from']} → {seg['to']}: {seg['distance_km']} km, Eco-Cost: {seg['eco_cost']:.2f}")
else:   
    print("No route found!")