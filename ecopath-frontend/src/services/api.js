// src/services/api.js

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const calculateRoute = async (origin, destination, preferences = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}/routes/calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        origin: {
          latitude: origin.lat,
          longitude: origin.lng,
          address: origin.address || `${origin.lat}, ${origin.lng}`,
        },
        destination: {
          latitude: destination.lat,
          longitude: destination.lng,
          address: destination.address || `${destination.lat}, ${destination.lng}`,
        },
        departure_time: new Date().toISOString(),
        preferences: {
          allow_carpool: preferences.carpool !== false,
          allow_multimodal: preferences.multimodal !== false,
          vehicle_type: preferences.vehicleType || 'ice',
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Route calculation error:', error);
    throw error;
  }
};

export const getHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/routes/health`);
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};

// Nominatim API for address search (free, uses OpenStreetMap)
export const searchAddress = async (query) => {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`
    );
    return await response.json();
  } catch (error) {
    console.error('Address search error:', error);
    return [];
  }
};

export const reverseGeocode = async (lat, lng) => {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`
    );
    return await response.json();
  } catch (error) {
    console.error('Reverse geocode error:', error);
    return null;
  }
};