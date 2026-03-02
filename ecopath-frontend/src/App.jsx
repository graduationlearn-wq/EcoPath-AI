// src/App.jsx

import { useState, useEffect } from 'react';
import { Leaf } from 'lucide-react';
import RouteForm from './components/RouteForm';
import MapComponent from './components/MapComponent';
import RouteResults from './components/RouteResults';
import { calculateRoute } from './services/api';
import './App.css';

export default function App() {
  const [origin, setOrigin] = useState({
    address: 'Connaught Place, Delhi',
    lat: 28.6139,
    lng: 77.2090,
  });

  const [destination, setDestination] = useState({
    address: 'India Gate, Delhi',
    lat: 28.5244,
    lng: 77.1855,
  });

  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectingOrigin, setSelectingOrigin] = useState(false);
  const [selectingDestination, setSelectingDestination] = useState(false);

  // Handle form submission
  const handleRouteSubmit = async (formData) => {
    setLoading(true);
    setError(null);
    setRoutes([]);

    try {
      const response = await calculateRoute(
        formData.origin,
        formData.destination,
        {
          vehicleType: formData.vehicleType,
          carpool: formData.carpool,
          multimodal: formData.multimodal,
        }
      );

      if (response.status === 'success') {
        setRoutes(response.routes);
        setOrigin(formData.origin);
        setDestination(formData.destination);
      } else {
        setError(response.message || 'Failed to calculate routes');
      }
    } catch (err) {
      setError(err.message || 'An error occurred. Please try again.');
      console.error('Route calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle map location selection
  const handleLocationSelect = (location, isOrigin) => {
    if (isOrigin) {
      setOrigin(location);
      setSelectingOrigin(false);
    } else {
      setDestination(location);
      setSelectingDestination(false);
    }
  };

  // Get route coordinates from first route
  const routeCoordinates =
    routes.length > 0 ? routes[0].route_coordinates : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-green-600 to-green-700 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6 flex items-center gap-3">
          <Leaf className="w-8 h-8" />
          <div>
            <h1 className="text-3xl font-bold">🌱 EcoPath AI</h1>
            <p className="text-green-100 text-sm">Navigate for a Greener Tomorrow</p>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Form */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <RouteForm onSubmit={handleRouteSubmit} loading={loading} />
            </div>
          </div>

          {/* Right Column - Map & Results */}
          <div className="lg:col-span-2">
            {/* Map */}
            <MapComponent
              originLat={origin.lat}
              originLng={origin.lng}
              destLat={destination.lat}
              destLng={destination.lng}
              routeCoordinates={routeCoordinates}
              onLocationSelect={handleLocationSelect}
              selectingMode={selectingOrigin || selectingDestination}
            />

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-800">
                <p className="font-semibold">❌ Error</p>
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Route Results */}
            <RouteResults routes={routes} loading={loading} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-300 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          <p>
            🌍 EcoPath AI - Optimizing routes for environmental health and carbon
            minimization
          </p>
          <p className="mt-2">Made with 💚 for a sustainable future</p>
        </div>
      </footer>
    </div>
  );
}