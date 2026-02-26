import { useState } from 'react';
import type { PlanRequest, Location, Difficulty, RoutePreferences } from '../types';
import { useGeocode } from '../hooks/useGeocode';

interface PlanFormProps {
  onSubmit: (request: PlanRequest) => void;
  isLoading: boolean;
  origin: Location | null;
  destination: Location | null;
  onOriginChange: (location: Location | null) => void;
  onDestinationChange: (location: Location | null) => void;
}

export function PlanForm({
  onSubmit,
  isLoading,
  origin,
  destination,
  onOriginChange,
  onDestinationChange,
}: PlanFormProps) {
  const [difficulty, setDifficulty] = useState<Difficulty>('moderate');
  const [avoidTraffic, setAvoidTraffic] = useState(true);
  const [preferScenic, setPreferScenic] = useState(true);
  const [maxDistance, setMaxDistance] = useState<string>('');
  const [maxElevation, setMaxElevation] = useState<string>('');
  const [departureTime, setDepartureTime] = useState(() => {
    // Get current time in JST (local timezone)
    const now = new Date();
    // Format for datetime-local input (YYYY-MM-DDTHH:mm) in local timezone
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  });

  // Location name inputs
  const [originName, setOriginName] = useState('');
  const [destName, setDestName] = useState('');
  const [geocodeError, setGeocodeError] = useState<string | null>(null);

  // Geocoding candidates
  const [originCandidates, setOriginCandidates] = useState<Location[]>([]);
  const [destCandidates, setDestCandidates] = useState<Location[]>([]);

  // Geocoding hook
  const { geocode, isLoading: isGeocoding, error: geocodeApiError } = useGeocode();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!origin || !destination) {
      alert('出発地と目的地を設定してください');
      return;
    }

    const preferences: RoutePreferences = {
      difficulty,
      avoid_traffic: avoidTraffic,
      prefer_scenic: preferScenic,
      max_distance_km: maxDistance ? parseFloat(maxDistance) : undefined,
      max_elevation_gain_m: maxElevation ? parseFloat(maxElevation) : undefined,
    };

    // Parse datetime-local value as local time (JST) and convert to ISO string
    // datetime-local format: "2026-02-28T07:00"
    // This will be interpreted as JST and converted to UTC in ISO format
    const localDateTime = new Date(departureTime);

    const request: PlanRequest = {
      origin,
      destination,
      preferences,
      departure_time: localDateTime.toISOString(),
    };

    onSubmit(request);
  };

  const handleSetOriginByName = async () => {
    if (originName.trim()) {
      setGeocodeError(null);
      setOriginCandidates([]);
      const results = await geocode(originName);
      console.log('Origin search results:', results);
      if (results.length > 0) {
        if (results.length === 1) {
          // Only one result, use it directly
          onOriginChange(results[0]);
        } else {
          // Multiple results, show candidates
          setOriginCandidates(results);
        }
      } else if (!geocodeApiError) {
        setGeocodeError('場所が見つかりませんでした');
      }
    }
  };

  const handleSetDestByName = async () => {
    if (destName.trim()) {
      setGeocodeError(null);
      setDestCandidates([]);
      const results = await geocode(destName);
      console.log('Destination search results:', results);
      if (results.length > 0) {
        if (results.length === 1) {
          // Only one result, use it directly
          onDestinationChange(results[0]);
        } else {
          // Multiple results, show candidates
          setDestCandidates(results);
        }
      } else if (!geocodeApiError) {
        setGeocodeError('場所が見つかりませんでした');
      }
    }
  };

  const handleSelectOriginCandidate = (location: Location) => {
    onOriginChange(location);
    setOriginCandidates([]);
  };

  const handleSelectDestCandidate = (location: Location) => {
    onDestinationChange(location);
    setDestCandidates([]);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800">ルート設定</h2>

      {/* Geocode Error */}
      {(geocodeError || geocodeApiError) && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-800">
            {geocodeError || geocodeApiError}
          </p>
          <p className="text-xs text-yellow-700 mt-1">
            ヒント: 「上野芝」「大阪城」など、シンプルな地名を入力してください
          </p>
        </div>
      )}

      {/* Origin */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">出発地</label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={originName}
              onChange={(e) => setOriginName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSetOriginByName();
                }
              }}
              placeholder="例: 上野芝、大阪城（シンプルな地名）"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isGeocoding}
            />
            <button
              type="button"
              onClick={handleSetOriginByName}
              disabled={isGeocoding || !originName.trim()}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isGeocoding ? '検索中...' : '検索'}
            </button>
          </div>
          {originCandidates.length > 0 && (
            <div className="mt-2 border border-gray-300 rounded-md bg-white shadow-sm max-h-48 overflow-y-auto">
              <div className="p-2 text-xs font-semibold text-gray-700 bg-gray-50 border-b">
                複数の候補が見つかりました（{originCandidates.length}件）:
              </div>
              {originCandidates.map((candidate, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectOriginCandidate(candidate)}
                  className="w-full text-left px-3 py-2 hover:bg-blue-50 border-b last:border-b-0 text-sm"
                >
                  <div className="font-medium">{candidate.name}</div>
                  <div className="text-xs text-gray-500">
                    ({candidate.lat.toFixed(4)}, {candidate.lng.toFixed(4)})
                  </div>
                </button>
              ))}
            </div>
          )}
          {origin && (
            <div className="text-sm text-gray-600">
              {origin.name || '未設定'}
              <span className="ml-2 text-xs">
                ({origin.lat.toFixed(4)}, {origin.lng.toFixed(4)})
              </span>
              <button
                type="button"
                onClick={() => onOriginChange(null)}
                className="ml-2 text-red-600 hover:text-red-800"
              >
                クリア
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Destination */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">目的地</label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={destName}
              onChange={(e) => setDestName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSetDestByName();
                }
              }}
              placeholder="例: 上野芝、大阪城（シンプルな地名）"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isGeocoding}
            />
            <button
              type="button"
              onClick={handleSetDestByName}
              disabled={isGeocoding || !destName.trim()}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isGeocoding ? '検索中...' : '検索'}
            </button>
          </div>
          {destCandidates.length > 0 && (
            <div className="mt-2 border border-gray-300 rounded-md bg-white shadow-sm max-h-48 overflow-y-auto">
              <div className="p-2 text-xs font-semibold text-gray-700 bg-gray-50 border-b">
                複数の候補が見つかりました（{destCandidates.length}件）:
              </div>
              {destCandidates.map((candidate, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectDestCandidate(candidate)}
                  className="w-full text-left px-3 py-2 hover:bg-blue-50 border-b last:border-b-0 text-sm"
                >
                  <div className="font-medium">{candidate.name}</div>
                  <div className="text-xs text-gray-500">
                    ({candidate.lat.toFixed(4)}, {candidate.lng.toFixed(4)})
                  </div>
                </button>
              ))}
            </div>
          )}
          {destination && (
            <div className="text-sm text-gray-600">
              {destination.name || '未設定'}
              <span className="ml-2 text-xs">
                ({destination.lat.toFixed(4)}, {destination.lng.toFixed(4)})
              </span>
              <button
                type="button"
                onClick={() => onDestinationChange(null)}
                className="ml-2 text-red-600 hover:text-red-800"
              >
                クリア
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Difficulty */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">難易度</label>
        <select
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value as Difficulty)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="easy">初級 (Easy)</option>
          <option value="moderate">中級 (Moderate)</option>
          <option value="hard">上級 (Hard)</option>
        </select>
      </div>

      {/* Preferences */}
      <div className="space-y-3">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="avoidTraffic"
            checked={avoidTraffic}
            onChange={(e) => setAvoidTraffic(e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="avoidTraffic" className="ml-2 block text-sm text-gray-700">
            交通量の多い道を避ける
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="preferScenic"
            checked={preferScenic}
            onChange={(e) => setPreferScenic(e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="preferScenic" className="ml-2 block text-sm text-gray-700">
            景色の良いルートを優先
          </label>
        </div>
      </div>

      {/* Max Distance */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          最大距離 (km) - 任意
        </label>
        <input
          type="number"
          value={maxDistance}
          onChange={(e) => setMaxDistance(e.target.value)}
          placeholder="例: 100"
          min="0"
          step="0.1"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Max Elevation */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          最大獲得標高 (m) - 任意
        </label>
        <input
          type="number"
          value={maxElevation}
          onChange={(e) => setMaxElevation(e.target.value)}
          placeholder="例: 1500"
          min="0"
          step="1"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Departure Time */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">出発時刻</label>
        <input
          type="datetime-local"
          value={departureTime}
          onChange={(e) => setDepartureTime(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !origin || !destination}
        className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
      >
        {isLoading ? 'ルート生成中...' : 'ルート生成'}
      </button>
    </form>
  );
}
