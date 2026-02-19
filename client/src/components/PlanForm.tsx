import { useState } from 'react';
import type { PlanRequest, Location, Difficulty, RoutePreferences } from '../types';

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
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(7, 0, 0, 0);
    return tomorrow.toISOString().slice(0, 16);
  });

  // Location name inputs
  const [originName, setOriginName] = useState('');
  const [destName, setDestName] = useState('');

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

    const request: PlanRequest = {
      origin,
      destination,
      preferences,
      departure_time: new Date(departureTime).toISOString(),
    };

    onSubmit(request);
  };

  const handleSetOriginByName = () => {
    if (originName.trim()) {
      // In a real app, this would geocode the address
      // For now, just set the name
      if (origin) {
        onOriginChange({ ...origin, name: originName });
      }
    }
  };

  const handleSetDestByName = () => {
    if (destName.trim()) {
      if (destination) {
        onDestinationChange({ ...destination, name: destName });
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800">ルート設定</h2>

      {/* Origin */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">出発地</label>
        <div className="space-y-2">
          <input
            type="text"
            value={originName}
            onChange={(e) => setOriginName(e.target.value)}
            onBlur={handleSetOriginByName}
            placeholder="地名を入力または地図をクリック"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
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
          <input
            type="text"
            value={destName}
            onChange={(e) => setDestName(e.target.value)}
            onBlur={handleSetDestByName}
            placeholder="地名を入力または地図をクリック"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
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
