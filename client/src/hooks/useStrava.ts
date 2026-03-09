import { useState, useCallback, useEffect } from 'react';
import type { StravaTokenResponse, StravaFitnessProfile } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const STRAVA_STORAGE_KEY = 'strava_auth';

interface StravaAuth {
  access_token: string;
  refresh_token: string;
  expires_at: number;
  athlete_id: number;
  athlete_name: string;
}

interface UseStravaReturn {
  isConnected: boolean;
  athleteName: string | null;
  fitnessProfile: StravaFitnessProfile | null;
  isLoading: boolean;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  handleCallback: (code: string) => Promise<void>;
}

export function useStrava(): UseStravaReturn {
  const [auth, setAuth] = useState<StravaAuth | null>(() => {
    const stored = localStorage.getItem(STRAVA_STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  });
  const [fitnessProfile, setFitnessProfile] = useState<StravaFitnessProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const saveAuth = (data: StravaAuth) => {
    localStorage.setItem(STRAVA_STORAGE_KEY, JSON.stringify(data));
    setAuth(data);
  };

  const connect = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/strava/auth-url`);
      if (!response.ok) throw new Error('Failed to get auth URL');
      const { url } = await response.json();
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Strava接続に失敗しました');
    }
  }, []);

  const disconnect = useCallback(() => {
    localStorage.removeItem(STRAVA_STORAGE_KEY);
    setAuth(null);
    setFitnessProfile(null);
    setError(null);
  }, []);

  const handleCallback = useCallback(async (code: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/strava/token?code=${encodeURIComponent(code)}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Token exchange failed');
      const data: StravaTokenResponse = await response.json();
      saveAuth({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        expires_at: data.expires_at,
        athlete_id: data.athlete_id,
        athlete_name: data.athlete_name,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Strava認証に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch fitness profile when connected
  useEffect(() => {
    if (!auth) {
      setFitnessProfile(null);
      return;
    }

    const fetchProfile = async () => {
      setIsLoading(true);
      try {
        // Check if token is expired and refresh if needed
        let accessToken = auth.access_token;
        if (auth.expires_at * 1000 < Date.now()) {
          const refreshResponse = await fetch(
            `${API_BASE_URL}/api/strava/refresh?refresh_token=${encodeURIComponent(auth.refresh_token)}`,
            { method: 'POST' }
          );
          if (!refreshResponse.ok) {
            // Token refresh failed, disconnect
            disconnect();
            return;
          }
          const refreshData: StravaTokenResponse = await refreshResponse.json();
          accessToken = refreshData.access_token;
          saveAuth({
            ...auth,
            access_token: refreshData.access_token,
            refresh_token: refreshData.refresh_token,
            expires_at: refreshData.expires_at,
          });
        }

        const response = await fetch(
          `${API_BASE_URL}/api/strava/profile?access_token=${encodeURIComponent(accessToken)}`
        );
        if (!response.ok) throw new Error('Failed to fetch profile');
        const profile: StravaFitnessProfile = await response.json();
        setFitnessProfile(profile);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'プロフィール取得に失敗しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [auth?.access_token, disconnect]);

  return {
    isConnected: !!auth,
    athleteName: auth?.athlete_name || null,
    fitnessProfile,
    isLoading,
    error,
    connect,
    disconnect,
    handleCallback,
  };
}
