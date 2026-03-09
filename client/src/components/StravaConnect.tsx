import type { StravaFitnessProfile } from '../types';

interface StravaConnectProps {
  isConnected: boolean;
  athleteName: string | null;
  fitnessProfile: StravaFitnessProfile | null;
  isLoading: boolean;
  error: string | null;
  onConnect: () => void;
  onDisconnect: () => void;
}

const FITNESS_LEVEL_LABELS: Record<string, string> = {
  beginner: '初級',
  intermediate: '中級',
  advanced: '上級',
};

export function StravaConnect({
  isConnected,
  athleteName,
  fitnessProfile,
  isLoading,
  error,
  onConnect,
  onDisconnect,
}: StravaConnectProps) {
  if (!isConnected) {
    return (
      <div className="p-4 bg-white rounded-lg shadow-md">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Strava連携</h3>
        <p className="text-xs text-gray-500 mb-3">
          Stravaと連携すると、あなたの走行履歴に基づいたパーソナライズされたルート提案を受けられます。
        </p>
        <button
          onClick={onConnect}
          disabled={isLoading}
          className="w-full px-4 py-2 bg-[#FC4C02] text-white text-sm font-medium rounded-md hover:bg-[#E34402] disabled:bg-gray-400 transition-colors"
        >
          {isLoading ? '接続中...' : 'Stravaと連携する'}
        </button>
        {error && (
          <p className="mt-2 text-xs text-red-600">{error}</p>
        )}
      </div>
    );
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">Strava連携</h3>
        <button
          onClick={onDisconnect}
          className="text-xs text-gray-500 hover:text-red-600 transition-colors"
        >
          解除
        </button>
      </div>

      <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-100">
        <div className="w-2 h-2 bg-green-500 rounded-full" />
        <span className="text-sm text-gray-700">{athleteName || 'アスリート'}</span>
      </div>

      {isLoading && (
        <p className="text-xs text-gray-500">プロフィール読み込み中...</p>
      )}

      {error && (
        <p className="text-xs text-red-600">{error}</p>
      )}

      {fitnessProfile?.has_data && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">フィットネスレベル</span>
            <span className="font-medium text-[#FC4C02]">
              {FITNESS_LEVEL_LABELS[fitnessProfile.fitness_level || ''] || fitnessProfile.fitness_level}
            </span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">平均距離</span>
            <span className="font-medium text-gray-700">{fitnessProfile.avg_distance_km} km</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">平均速度</span>
            <span className="font-medium text-gray-700">{fitnessProfile.avg_speed_kmh} km/h</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">平均獲得標高</span>
            <span className="font-medium text-gray-700">{fitnessProfile.avg_elevation_gain_m} m</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">走行頻度</span>
            <span className="font-medium text-gray-700">{fitnessProfile.rides_per_week} 回/週</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">アクティビティ数</span>
            <span className="font-medium text-gray-700">{fitnessProfile.total_activities} 件</span>
          </div>
          <p className="text-xs text-green-700 bg-green-50 rounded p-2 mt-2">
            Stravaデータを使って、あなたに最適なルートを提案します
          </p>
        </div>
      )}

      {fitnessProfile && !fitnessProfile.has_data && (
        <p className="text-xs text-gray-500">{fitnessProfile.message}</p>
      )}
    </div>
  );
}
