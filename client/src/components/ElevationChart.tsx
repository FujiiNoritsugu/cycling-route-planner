import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import type { RouteSegment } from '../types';

interface ElevationChartProps {
  segments: RouteSegment[];
}

interface ElevationDataPoint {
  distance: number;
  elevation: number;
  gradient?: number;
}

/**
 * Calculate elevation profile from route segments
 */
function calculateElevationProfile(segments: RouteSegment[]): ElevationDataPoint[] {
  const points: ElevationDataPoint[] = [];
  let cumulativeDistance = 0;

  segments.forEach((segment) => {
    const segmentPoints = segment.coordinates.length;
    const hasElevationData = segment.elevations && segment.elevations.length === segmentPoints;

    segment.coordinates.forEach((_, idx) => {
      const distanceInSegment = (segment.distance_km * idx) / (segmentPoints - 1 || 1);

      // Use actual elevation data if available, otherwise fall back to linear interpolation
      const elevation = hasElevationData
        ? segment.elevations![idx]
        : (segment.elevation_gain_m * idx) / (segmentPoints - 1 || 1);

      const previousElevation = idx > 0
        ? (hasElevationData ? segment.elevations![idx - 1] : (segment.elevation_gain_m * (idx - 1)) / (segmentPoints - 1 || 1))
        : elevation;

      const gradient = idx > 0
        ? ((elevation - previousElevation) / (segment.distance_km / (segmentPoints - 1) || 1)) * 100
        : 0;

      points.push({
        distance: parseFloat((cumulativeDistance + distanceInSegment).toFixed(2)),
        elevation: parseFloat(elevation.toFixed(1)),
        gradient: parseFloat(gradient.toFixed(1)),
      });
    });

    cumulativeDistance += segment.distance_km;
  });

  return points;
}

/**
 * Get color based on gradient steepness
 * Note: Currently unused but kept for future gradient visualization
 */
// function getGradientColor(gradient: number): string {
//   if (gradient > 10) return '#ef4444'; // steep uphill - red
//   if (gradient > 5) return '#f59e0b'; // moderate uphill - orange
//   if (gradient > 0) return '#10b981'; // gentle uphill - green
//   if (gradient > -5) return '#3b82f6'; // gentle downhill - blue
//   if (gradient > -10) return '#6366f1'; // moderate downhill - indigo
//   return '#8b5cf6'; // steep downhill - purple
// }

export function ElevationChart({ segments }: ElevationChartProps) {
  if (segments.length === 0) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">標高プロファイル</h3>
        <p className="text-gray-500 text-sm">ルートを生成すると標高グラフが表示されます</p>
      </div>
    );
  }

  const data = calculateElevationProfile(segments);
  const elevations = data.map(d => d.elevation);
  const maxElevation = elevations.reduce((max, val) => Math.max(max, val), -Infinity);
  const minElevation = elevations.reduce((min, val) => Math.min(min, val), Infinity);

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">標高プロファイル</h3>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 rounded-md">
          <div className="text-xs text-gray-600 mb-1">総距離</div>
          <div className="text-lg font-semibold text-blue-900">
            {data[data.length - 1]?.distance.toFixed(1)} km
          </div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-md">
          <div className="text-xs text-gray-600 mb-1">最高標高</div>
          <div className="text-lg font-semibold text-green-900">
            {maxElevation.toFixed(0)} m
          </div>
        </div>
        <div className="text-center p-3 bg-orange-50 rounded-md">
          <div className="text-xs text-gray-600 mb-1">獲得標高</div>
          <div className="text-lg font-semibold text-orange-900">
            {segments.reduce((sum, s) => sum + s.elevation_gain_m, 0).toFixed(0)} m
          </div>
        </div>
      </div>

      {/* Elevation Chart */}
      <div className="w-full h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="elevationGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="distance"
              label={{ value: '距離 (km)', position: 'insideBottom', offset: -5 }}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              label={{ value: '標高 (m)', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
              domain={[Math.floor(minElevation / 100) * 100, Math.ceil(maxElevation / 100) * 100]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 border border-gray-300 rounded-md shadow-lg">
                      <p className="text-sm font-semibold">{data.distance} km</p>
                      <p className="text-sm text-gray-700">標高: {data.elevation} m</p>
                      {data.gradient !== undefined && (
                        <p className="text-sm text-gray-700">
                          勾配: {data.gradient > 0 ? '+' : ''}{data.gradient}%
                        </p>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="elevation"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#elevationGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Gradient Legend */}
      <div className="mt-6">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">勾配の目安</h4>
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
            <span>急坂 (&gt;10%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-orange-500 mr-2"></div>
            <span>中坂 (5-10%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
            <span>緩坂 (0-5%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
