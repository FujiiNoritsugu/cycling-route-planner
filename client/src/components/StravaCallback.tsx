import { useEffect, useState } from 'react';

interface StravaCallbackProps {
  onCallback: (code: string) => Promise<void>;
}

export function StravaCallback({ onCallback }: StravaCallbackProps) {
  const [status, setStatus] = useState<'processing' | 'error'>('processing');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');

    if (code) {
      onCallback(code).then(() => {
        // Remove query params and redirect to root
        window.history.replaceState({}, '', '/');
      }).catch(() => {
        setStatus('error');
      });
    } else {
      setStatus('error');
    }
  }, [onCallback]);

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="p-6 bg-white rounded-lg shadow-md text-center">
          <p className="text-red-600 font-medium">Strava認証に失敗しました</p>
          <button
            onClick={() => window.location.href = '/'}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            トップに戻る
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="p-6 bg-white rounded-lg shadow-md text-center">
        <p className="text-gray-700 font-medium">Strava認証中...</p>
      </div>
    </div>
  );
}
