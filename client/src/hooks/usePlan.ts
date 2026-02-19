import { useState, useCallback } from 'react';
import type { PlanRequest, RoutePlan, WeatherForecast } from '../types';

interface UsePlanState {
  routePlan: Partial<RoutePlan> | null;
  weatherForecasts: WeatherForecast[];
  llmAnalysis: string;
  isLoading: boolean;
  error: string | null;
}

interface UsePlanReturn extends UsePlanState {
  submitPlan: (request: PlanRequest) => Promise<void>;
  reset: () => void;
}

/**
 * Custom hook for handling route planning with SSE streaming
 */
export function usePlan(): UsePlanReturn {
  const [routePlan, setRoutePlan] = useState<Partial<RoutePlan> | null>(null);
  const [weatherForecasts, setWeatherForecasts] = useState<WeatherForecast[]>([]);
  const [llmAnalysis, setLlmAnalysis] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setRoutePlan(null);
    setWeatherForecasts([]);
    setLlmAnalysis('');
    setIsLoading(false);
    setError(null);
  }, []);

  const submitPlan = useCallback(async (request: PlanRequest) => {
    setIsLoading(true);
    setError(null);
    setRoutePlan(null);
    setWeatherForecasts([]);
    setLlmAnalysis('');

    try {
      const response = await fetch('/api/plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim() || line.startsWith(':')) continue;

          if (line.startsWith('data: ')) {
            const data = line.slice(6);

            try {
              const event = JSON.parse(data);

              switch (event.type) {
                case 'route_data':
                  setRoutePlan(event.data);
                  break;

                case 'weather':
                  setWeatherForecasts(event.data);
                  break;

                case 'token':
                  setLlmAnalysis((prev) => prev + event.data);
                  break;

                case 'done':
                  setIsLoading(false);
                  break;

                case 'error':
                  setError(event.data);
                  setIsLoading(false);
                  break;

                default:
                  console.warn('Unknown event type:', event.type);
              }
            } catch (parseError) {
              console.error('Failed to parse SSE data:', parseError);
            }
          }
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      setIsLoading(false);
    }
  }, []);

  return {
    routePlan,
    weatherForecasts,
    llmAnalysis,
    isLoading,
    error,
    submitPlan,
    reset,
  };
}
