// src/components/RouteResults.jsx

import { Leaf, Wind, Mountain, Users, Car } from 'lucide-react';

export default function RouteResults({ routes, loading }) {
  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-green-200 border-t-green-600"></div>
        </div>
        <p className="mt-4 text-gray-600">Calculating eco-optimal routes...</p>
      </div>
    );
  }

  if (!routes || routes.length === 0) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <p className="text-blue-800">No routes found. Try different locations!</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">
        🌍 Eco-Optimal Routes ({routes.length})
      </h2>

      {routes.map((route, index) => (
        <div
          key={route.route_id}
          className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition"
        >
          {/* Route Header */}
          <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="bg-white bg-opacity-20 rounded-full w-10 h-10 flex items-center justify-center font-bold text-lg">
                  #{route.rank}
                </div>
                <div>
                  <h3 className="text-xl font-bold">
                    {route.summary.route_type.toUpperCase()}
                  </h3>
                  <p className="text-green-100">
                    {route.summary.total_distance_km.toFixed(2)} km ·{' '}
                    {route.summary.estimated_time_minutes} min
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-green-100">Eco-Score</div>
                <div className="text-3xl font-bold">
                  {route.summary.eco_cost_score.toFixed(1)}
                </div>
              </div>
            </div>
          </div>

          {/* Route Details Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 border-b border-gray-200">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-xs text-gray-600 mb-1">Distance</div>
              <div className="text-lg font-bold text-gray-800">
                {route.summary.total_distance_km.toFixed(2)} km
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-xs text-gray-600 mb-1">Time</div>
              <div className="text-lg font-bold text-gray-800">
                {route.summary.estimated_time_minutes} min
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-xs text-gray-600 mb-1">CO₂ Emissions</div>
              <div className="text-lg font-bold text-gray-800">
                {route.summary.estimated_co2_kg.toFixed(2)} kg
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-xs text-gray-600 mb-1">Route Type</div>
              <div className="text-lg font-bold text-gray-800 capitalize">
                {route.summary.route_type}
              </div>
            </div>
          </div>

          {/* Eco-Cost Breakdown */}
          <div className="p-6 bg-gray-50">
            <h4 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Leaf className="w-5 h-5 text-green-600" />
              Eco-Cost Breakdown
            </h4>
            <div className="space-y-3">
              {/* Traffic Penalty */}
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <div className="flex items-center gap-3">
                  <Car className="w-5 h-5 text-red-500" />
                  <span className="text-gray-700">Traffic Penalty</span>
                </div>
                <span className="font-semibold text-red-500">
                  +{route.eco_cost_breakdown.traffic_penalty.toFixed(2)}
                </span>
              </div>

              {/* AQI Penalty */}
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <div className="flex items-center gap-3">
                  <Wind className="w-5 h-5 text-orange-500" />
                  <span className="text-gray-700">Air Quality Penalty</span>
                </div>
                <span className="font-semibold text-orange-500">
                  +{route.eco_cost_breakdown.aqi_penalty.toFixed(2)}
                </span>
              </div>

              {/* Gradient Penalty */}
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <div className="flex items-center gap-3">
                  <Mountain className="w-5 h-5 text-gray-600" />
                  <span className="text-gray-700">Gradient Penalty</span>
                </div>
                <span className="font-semibold text-gray-600">
                  +{route.eco_cost_breakdown.gradient_penalty.toFixed(2)}
                </span>
              </div>

              {/* Carpool Bonus */}
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <div className="flex items-center gap-3">
                  <Users className="w-5 h-5 text-green-600" />
                  <span className="text-gray-700">Carpool Bonus</span>
                </div>
                <span className="font-semibold text-green-600">
                  {route.eco_cost_breakdown.carpool_bonus.toFixed(2)}
                </span>
              </div>

              {/* Greenery Bonus */}
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <div className="flex items-center gap-3">
                  <Leaf className="w-5 h-5 text-emerald-600" />
                  <span className="text-gray-700">Greenery Bonus</span>
                </div>
                <span className="font-semibold text-emerald-600">
                  {route.eco_cost_breakdown.greenery_bonus.toFixed(2)}
                </span>
              </div>

              {/* Canyon Penalty (if exists) */}
              {route.eco_cost_breakdown.canyon_penalty !== 0 && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div className="flex items-center gap-3">
                    <Wind className="w-5 h-5 text-yellow-600" />
                    <span className="text-gray-700">Street Canyon Penalty</span>
                  </div>
                  <span className="font-semibold text-yellow-600">
                    +{route.eco_cost_breakdown.canyon_penalty.toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="p-6 bg-white border-t border-gray-200 flex gap-3">
            <button className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition">
              📍 View on Map
            </button>
            <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition">
              ▶️ Start Navigation
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}