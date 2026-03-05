import { useState, useMemo } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMapEvents } from 'react-leaflet';
import { LatLngExpression, Icon } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Location, RouteSegment } from '../types';
import { GradientPolyline } from './GradientPolyline';
import { GradientLegend } from './GradientLegend';

// Fix Leaflet default marker icon issue with Vite
// Use CDN links instead of importing from node_modules to avoid TypeScript issues
const markerIcon2x = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png';
const markerIcon = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png';
const markerShadow = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png';

delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

interface RouteMapProps {
  origin: Location | null;
  destination: Location | null;
  segments: RouteSegment[];
  onMapClick?: (location: Location) => void;
}

/**
 * Component for clicking on map to set origin/destination
 */
function MapClickHandler({ onClick }: { onClick?: (location: Location) => void }) {
  useMapEvents({
    click: (e) => {
      if (onClick) {
        onClick({
          lat: e.latlng.lat,
          lng: e.latlng.lng,
        });
      }
    },
  });
  return null;
}

export function RouteMap({ origin, destination, segments, onMapClick }: RouteMapProps) {
  const [showGradient, setShowGradient] = useState(false);

  // Default center: Osaka area [34.6, 135.5]
  const defaultCenter: LatLngExpression = [34.6, 135.5];
  const defaultZoom = 10;

  // Calculate route center and bounds
  let mapCenter = defaultCenter;
  let mapZoom = defaultZoom;

  if (origin && destination) {
    mapCenter = [
      (origin.lat + destination.lat) / 2,
      (origin.lng + destination.lng) / 2,
    ];
    mapZoom = 11;
  } else if (origin) {
    mapCenter = [origin.lat, origin.lng];
  } else if (destination) {
    mapCenter = [destination.lat, destination.lng];
  }

  // Check if all segments have elevation data
  const hasElevationData = useMemo(
    () =>
      segments.length > 0 &&
      segments.every(
        (s) => s.elevations && s.elevations.length === s.coordinates.length,
      ),
    [segments],
  );

  const effectiveGradient = showGradient && hasElevationData;

  // Color based on segment type: outbound = blue, return = green
  const getRouteColor = (segmentType?: string) => {
    return segmentType === 'return' ? '#10b981' : '#3b82f6';
  };

  return (
    <div className="h-full w-full relative">
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        className="h-full w-full"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapClickHandler onClick={onMapClick} />

        {/* Origin marker */}
        {origin && (
          <Marker position={[origin.lat, origin.lng]}>
            <Popup>
              <div>
                <strong>出発地</strong>
                {origin.name && <div>{origin.name}</div>}
              </div>
            </Popup>
          </Marker>
        )}

        {/* Destination marker */}
        {destination && (
          <Marker position={[destination.lat, destination.lng]}>
            <Popup>
              <div>
                <strong>目的地</strong>
                {destination.name && <div>{destination.name}</div>}
              </div>
            </Popup>
          </Marker>
        )}

        {/* Route segments */}
        {segments.map((segment, idx) => {
          if (effectiveGradient) {
            return (
              <GradientPolyline key={idx} segment={segment} segmentIndex={idx} />
            );
          }

          const positions: LatLngExpression[] = segment.coordinates.map((coord) => [
            coord[0],
            coord[1],
          ]);

          const segmentLabel = segment.segment_type === 'return' ? '復路' : '往路';

          return (
            <Polyline
              key={idx}
              positions={positions}
              pathOptions={{
                color: getRouteColor(segment.segment_type),
                weight: 4,
                opacity: 0.7,
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div>
                    <strong>{segmentLabel} - 区間 {idx + 1}</strong>
                  </div>
                  <div>距離: {segment.distance_km.toFixed(2)} km</div>
                  <div>獲得標高: {segment.elevation_gain_m.toFixed(0)} m</div>
                  <div>路面: {segment.surface_type}</div>
                  <div>所要時間: {segment.estimated_duration_min} 分</div>
                </div>
              </Popup>
            </Polyline>
          );
        })}
      </MapContainer>

      {/* Gradient toggle button */}
      {segments.length > 0 && (
        <button
          onClick={() => setShowGradient((v) => !v)}
          disabled={!hasElevationData}
          className={`absolute top-4 right-4 px-3 py-2 rounded-lg shadow-md text-sm font-medium transition-colors ${
            effectiveGradient
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          } ${!hasElevationData ? 'opacity-50 cursor-not-allowed' : ''}`}
          style={{ zIndex: 1000 }}
          title={hasElevationData ? '勾配ヒートマップ表示を切り替え' : '標高データがありません'}
        >
          {effectiveGradient ? '勾配表示 ON' : '勾配表示 OFF'}
        </button>
      )}

      {/* Gradient legend */}
      {effectiveGradient && <GradientLegend />}
    </div>
  );
}
