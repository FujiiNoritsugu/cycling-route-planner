import { useState } from 'react';
import { PlanForm } from './components/PlanForm';
import { RouteMap } from './components/RouteMap';
import { WeatherPanel } from './components/WeatherPanel';
import { AnalysisPanel } from './components/AnalysisPanel';
import { ElevationChart } from './components/ElevationChart';
import { usePlan } from './hooks/usePlan';
import type { Location } from './types';

function App() {
  const [origin, setOrigin] = useState<Location | null>(null);
  const [destination, setDestination] = useState<Location | null>(null);
  const [clickMode, setClickMode] = useState<'origin' | 'destination' | null>(null);

  const {
    routePlan,
    weatherForecasts,
    llmAnalysis,
    isLoading,
    error,
    submitPlan,
    reset,
  } = usePlan();

  const handleMapClick = (location: Location) => {
    if (!origin) {
      setOrigin(location);
      setClickMode('destination');
    } else if (!destination) {
      setDestination(location);
      setClickMode(null);
    } else {
      // Toggle between origin and destination
      if (clickMode === 'origin') {
        setOrigin(location);
        setClickMode('destination');
      } else {
        setDestination(location);
        setClickMode('origin');
      }
    }
  };

  const handleReset = () => {
    setOrigin(null);
    setDestination(null);
    setClickMode(null);
    reset();
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-screen-2xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              Cycling Route AI Planner
            </h1>
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              リセット
            </button>
          </div>
          {clickMode && (
            <div className="mt-2 text-sm text-blue-600">
              地図をクリックして{clickMode === 'origin' ? '出発地' : '目的地'}を設定してください
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-screen-2xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Sidebar - Plan Form */}
          <div className="lg:col-span-3">
            <PlanForm
              onSubmit={submitPlan}
              isLoading={isLoading}
              origin={origin}
              destination={destination}
              onOriginChange={setOrigin}
              onDestinationChange={setDestination}
            />

            {/* Click Mode Toggle */}
            {origin && destination && (
              <div className="mt-4 p-4 bg-white rounded-lg shadow-md">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">
                  地図クリックで変更:
                </h4>
                <div className="space-y-2">
                  <button
                    onClick={() => setClickMode('origin')}
                    className={`w-full px-3 py-2 text-sm rounded-md transition-colors ${
                      clickMode === 'origin'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    出発地を変更
                  </button>
                  <button
                    onClick={() => setClickMode('destination')}
                    className={`w-full px-3 py-2 text-sm rounded-md transition-colors ${
                      clickMode === 'destination'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    目的地を変更
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Center - Map */}
          <div className="lg:col-span-5">
            <div className="bg-white rounded-lg shadow-md overflow-hidden" style={{ height: '700px' }}>
              <RouteMap
                origin={origin}
                destination={destination}
                segments={routePlan?.segments || []}
                onMapClick={handleMapClick}
              />
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 className="text-sm font-semibold text-red-800 mb-1">エラー</h4>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </div>

          {/* Right Sidebar - Weather, Analysis, Elevation */}
          <div className="lg:col-span-4 space-y-6">
            {/* Weather Panel */}
            <WeatherPanel
              forecasts={weatherForecasts}
              warnings={routePlan?.warnings || []}
            />

            {/* Analysis Panel */}
            <AnalysisPanel
              analysis={llmAnalysis}
              recommendedGear={routePlan?.recommended_gear || []}
              isStreaming={isLoading}
            />

            {/* Elevation Chart */}
            <ElevationChart segments={routePlan?.segments || []} />

            {/* Route Summary */}
            {routePlan && (
              <div className="p-6 bg-white rounded-lg shadow-md">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">ルート概要</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">総距離:</span>
                    <span className="text-sm font-semibold text-gray-800">
                      {routePlan.total_distance_km?.toFixed(2)} km
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">総獲得標高:</span>
                    <span className="text-sm font-semibold text-gray-800">
                      {routePlan.total_elevation_gain_m?.toFixed(0)} m
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">推定所要時間:</span>
                    <span className="text-sm font-semibold text-gray-800">
                      {Math.floor((routePlan.total_duration_min || 0) / 60)}時間
                      {(routePlan.total_duration_min || 0) % 60}分
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">区間数:</span>
                    <span className="text-sm font-semibold text-gray-800">
                      {routePlan.segments?.length || 0}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-screen-2xl mx-auto px-4 py-6">
          <p className="text-center text-sm text-gray-600">
            Powered by Claude AI, OpenRouteService, and OpenMeteo
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
