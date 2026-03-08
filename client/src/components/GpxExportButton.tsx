import type { RoutePlan, Location } from '../types';
import { downloadGpx } from '../utils/gpxExport';

interface GpxExportButtonProps {
  routePlan: Partial<RoutePlan>;
  origin: Location;
  destination: Location;
  waypoints?: Location[];
}

export function GpxExportButton({ routePlan, origin, destination, waypoints }: GpxExportButtonProps) {
  const disabled = !routePlan.segments || routePlan.segments.length === 0;

  const handleClick = () => {
    downloadGpx({ routePlan, origin, destination, waypoints });
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
      GPXエクスポート
    </button>
  );
}
