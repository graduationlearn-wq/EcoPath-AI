// src/components/RouteForm.jsx

import { useState } from 'react';
import { MapPin, Loader } from 'lucide-react';
import AddressSearch from './AddressSearch';

export default function RouteForm({ onSubmit, loading }) {
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

  const [vehicleType, setVehicleType] = useState('ice');
  const [allowCarpool, setAllowCarpool] = useState(true);
  const [allowMultimodal, setAllowMultimodal] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!origin.lat || !origin.lng || !destination.lat || !destination.lng) {
      alert('Please select both origin and destination');
      return;
    }

    onSubmit({
      origin,
      destination,
      vehicleType,
      carpool: allowCarpool,
      multimodal: allowMultimodal,
    });
  };

  const swapLocations = () => {
  const temp = origin;
  setOrigin(destination);
  setDestination(temp);
};

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-6 mb-6">
      {/* Origin Section */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          <MapPin className="inline w-4 h-4 mr-2" />
          From
        </label>
        <AddressSearch
          value={origin.address}
          onChange={(selected) => setOrigin(selected)}
          placeholder="Enter origin address"
        />
        <div className="text-xs text-gray-500 mt-1">
          Lat: {origin.lat?.toFixed(4)}, Lng: {origin.lng?.toFixed(4)}
        </div>
      </div>

      {/* Swap Button */}
      <div className="flex justify-center mb-6">
        <button
          type="button"
          onClick={swapLocations}
          className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold py-2 px-4 rounded-full transition"
        >
          ⇅ Swap
        </button>
      </div>

      {/* Destination Section */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          <MapPin className="inline w-4 h-4 mr-2" />
          To
        </label>
        <AddressSearch
          value={destination.address}
          onChange={(selected) => setDestination(selected)}
          placeholder="Enter destination address"
        />
        <div className="text-xs text-gray-500 mt-1">
          Lat: {destination.lat?.toFixed(4)}, Lng: {destination.lng?.toFixed(4)}
        </div>
      </div>

      {/* Vehicle Type */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Vehicle Type
        </label>
        <select
          value={vehicleType}
          onChange={(e) => setVehicleType(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          <option value="ice">🚗 Gas (ICE)</option>
          <option value="ev">⚡ Electric (EV)</option>
          <option value="hybrid">🔄 Hybrid</option>
        </select>
      </div>

      {/* Preferences */}
      <div className="mb-6 space-y-3">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={allowCarpool}
            onChange={(e) => setAllowCarpool(e.target.checked)}
            className="w-4 h-4 text-green-600 rounded focus:ring-2 focus:ring-green-500"
          />
          <span className="ml-3 text-sm text-gray-700">🤝 Allow Carpool Matching</span>
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={allowMultimodal}
            onChange={(e) => setAllowMultimodal(e.target.checked)}
            className="w-4 h-4 text-green-600 rounded focus:ring-2 focus:ring-green-500"
          />
          <span className="ml-3 text-sm text-gray-700">🚌 Allow Multi-modal Routes</span>
        </label>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition ${
          loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-green-600 hover:bg-green-700'
        }`}
      >
        {loading ? (
          <>
            <Loader className="inline w-4 h-4 mr-2 animate-spin" />
            Calculating...
          </>
        ) : (
          '🌱 Calculate Eco-Optimal Route'
        )}
      </button>
    </form>
  );
}