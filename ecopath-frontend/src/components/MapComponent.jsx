// src/components/MapComponent.jsx

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { reverseGeocode } from '../services/api';

// Fix Leaflet default icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

export default function MapComponent({
  originLat,
  originLng,
  destLat,
  destLng,
  routeCoordinates,
  onLocationSelect,
  selectingMode,
}) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef({});
  const polylineRef = useRef(null);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current) return;

    // Create map
    map.current = L.map(mapContainer.current).setView([28.6139, 77.2090], 12);

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map.current);

    // Handle map clicks for location selection
    map.current.on('click', async (e) => {
      if (!onLocationSelect) return;

      const { lat, lng } = e.latlng;

      try {
        // Try to get address from coordinates
        const geocodeResult = await reverseGeocode(lat, lng);
        const address = geocodeResult?.address?.country
          ? `${geocodeResult.address.road || ''}, ${geocodeResult.address.city || ''}`
          : `${lat.toFixed(4)}, ${lng.toFixed(4)}`;

        onLocationSelect({
          lat,
          lng,
          address: address.trim(),
        });
      } catch (error) {
        console.error('Geocoding error:', error);
        onLocationSelect({
          lat,
          lng,
          address: `${lat.toFixed(4)}, ${lng.toFixed(4)}`,
        });
      }
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [onLocationSelect]);

  // Update origin marker
  useEffect(() => {
    if (!map.current || !originLat || !originLng) return;

    // Remove old origin marker
    if (markersRef.current.origin) {
      map.current.removeLayer(markersRef.current.origin);
    }

    // Add new origin marker
    markersRef.current.origin = L.circleMarker([originLat, originLng], {
      radius: 10,
      fillColor: '#22c55e',
      color: '#fff',
      weight: 3,
      opacity: 1,
      fillOpacity: 0.9,
    })
      .addTo(map.current)
      .bindPopup('<b>📍 Origin</b>')
      .openPopup();
  }, [originLat, originLng]);

  // Update destination marker
  useEffect(() => {
    if (!map.current || !destLat || !destLng) return;

    // Remove old destination marker
    if (markersRef.current.destination) {
      map.current.removeLayer(markersRef.current.destination);
    }

    // Add new destination marker
    markersRef.current.destination = L.circleMarker([destLat, destLng], {
      radius: 10,
      fillColor: '#ef4444',
      color: '#fff',
      weight: 3,
      opacity: 1,
      fillOpacity: 0.9,
    })
      .addTo(map.current)
      .bindPopup('<b>🎯 Destination</b>')
      .openPopup();

    // Fit bounds to show both markers
    if (markersRef.current.origin && markersRef.current.destination) {
      const group = L.featureGroup([
        markersRef.current.origin,
        markersRef.current.destination,
      ]);
      map.current.fitBounds(group.getBounds(), { padding: [50, 50] });
    }
  }, [destLat, destLng]);

  // Draw route polyline
  useEffect(() => {
    if (!map.current || !routeCoordinates || routeCoordinates.length === 0) return;

    // Remove old polyline
    if (polylineRef.current) {
      map.current.removeLayer(polylineRef.current);
    }

    // Create route coordinates array
    const routeLatLngs = routeCoordinates.map((coord) => [
      coord.latitude,
      coord.longitude,
    ]);

    // Draw polyline
    polylineRef.current = L.polyline(routeLatLngs, {
      color: '#2563eb',
      weight: 5,
      opacity: 0.8,
      dashArray: '5, 10',
      smoothFactor: 1.0,
    }).addTo(map.current);

    // Fit bounds to route
    if (polylineRef.current) {
      map.current.fitBounds(polylineRef.current.getBounds(), { padding: [50, 50] });
    }
  }, [routeCoordinates]);

  return (
    <div className="relative mb-6 rounded-lg shadow-lg overflow-hidden">
      <div
        ref={mapContainer}
        className="w-full h-96 bg-gray-200"
      />
      
      {selectingMode && (
        <div className="absolute top-4 left-4 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-semibold">
          📍 Click on map to select location
        </div>
      )}

      {/* Zoom controls info */}
      <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow p-2 text-xs text-gray-600">
        <p>Use + / - to zoom</p>
        <p>Drag to pan</p>
      </div>
    </div>
  );
}