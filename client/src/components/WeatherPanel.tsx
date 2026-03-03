import type { WeatherForecast } from '../types';

interface WeatherPanelProps {
  forecasts: WeatherForecast[];
  warnings: string[];
}

/**
 * Get weather icon based on WMO weather code
 * https://open-meteo.com/en/docs
 */
function getWeatherIcon(code: number): string {
  if (code === 0) return '☀️'; // Clear sky
  if (code <= 3) return '⛅'; // Partly cloudy
  if (code <= 49) return '🌫️'; // Fog
  if (code <= 59) return '🌧️'; // Drizzle
  if (code <= 69) return '🌧️'; // Rain
  if (code <= 79) return '❄️'; // Snow
  if (code <= 84) return '🌦️'; // Showers
  if (code <= 99) return '⛈️'; // Thunderstorm
  return '🌤️';
}

/**
 * Format time from ISO string
 */
function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
}

/**
 * Format date from ISO string
 */
function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
}

export function WeatherPanel({ forecasts, warnings }: WeatherPanelProps) {
  // Remove duplicate forecasts based on time
  const uniqueForecasts = forecasts.reduce((acc, forecast) => {
    // Check if we already have a forecast for this time
    const exists = acc.some(f => f.time === forecast.time);
    if (!exists) {
      acc.push(forecast);
    }
    return acc;
  }, [] as WeatherForecast[]);

  // Debug: Log if duplicates were removed
  if (forecasts.length !== uniqueForecasts.length) {
    console.log(`Removed ${forecasts.length - uniqueForecasts.length} duplicate forecasts`);
  }

  if (uniqueForecasts.length === 0) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">天気予報</h3>
        <p className="text-gray-500 text-sm">ルートを生成すると天気予報が表示されます</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">天気予報</h3>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <h4 className="text-sm font-semibold text-red-800 mb-2">⚠️ 注意事項</h4>
          <ul className="list-disc list-inside space-y-1">
            {warnings.map((warning, idx) => (
              <li key={idx} className="text-sm text-red-700">
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Weather Timeline */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {uniqueForecasts.map((forecast, idx) => {
          // Ensure all required fields exist
          if (!forecast || !forecast.time) {
            console.warn('Invalid forecast data at index', idx, forecast);
            return null;
          }

          return (
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="text-3xl">{getWeatherIcon(forecast.weather_code ?? 0)}</div>
                <div>
                  <div className="text-sm font-medium text-gray-800">
                    {formatDate(forecast.time)} {formatTime(forecast.time)}
                  </div>
                  <div className="text-xs text-gray-600">{forecast.description || 'N/A'}</div>
                </div>
              </div>

              <div className="text-right space-y-1">
                <div className="text-lg font-semibold text-gray-800">
                  {(forecast.temperature ?? 0).toFixed(1)}°C
                </div>
                <div className="text-xs text-gray-600">
                  風速: {(forecast.wind_speed ?? 0).toFixed(1)} m/s
                </div>
                <div className="text-xs text-gray-600">
                  降水確率: {(forecast.precipitation_probability ?? 0).toFixed(0)}%
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {uniqueForecasts.length > 5 && (
        <div className="mt-3 text-xs text-gray-500 text-center">
          {uniqueForecasts.length} 件の予報データ
        </div>
      )}
    </div>
  );
}
