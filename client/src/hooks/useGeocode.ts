/**
 * Custom hook for geocoding addresses and place names.
 */

import { useState } from 'react';
import type { Location, GeocodeResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

interface UseGeocodeReturn {
  geocode: (query: string, country?: string) => Promise<Location[]>;
  isLoading: boolean;
  error: string | null;
}

export function useGeocode(): UseGeocodeReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const geocode = async (query: string, country: string = 'JP'): Promise<Location[]> => {
    if (!query.trim()) {
      setError('検索語を入力してください');
      return [];
    }

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        query: query.trim(),
        country,
      });

      const response = await fetch(`${API_BASE_URL}/api/geocode?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 404) {
          throw new Error('場所が見つかりませんでした。「JR」などを除いたシンプルな地名を試してください');
        }
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data: GeocodeResponse = await response.json();
      return data.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : '住所の検索に失敗しました';
      setError(message);
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  return { geocode, isLoading, error };
}
