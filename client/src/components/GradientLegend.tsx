import { GRADIENT_LEGEND_ENTRIES } from '../utils/gradientColors';

export function GradientLegend() {
  return (
    <div
      className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-md p-3 text-xs"
      style={{ zIndex: 1000 }}
    >
      <div className="font-semibold text-gray-700 mb-2">勾配</div>
      <div className="space-y-1">
        {GRADIENT_LEGEND_ENTRIES.map((entry) => (
          <div key={entry.label} className="flex items-center gap-2">
            <div
              className="w-4 h-2 rounded-sm flex-shrink-0"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-600">{entry.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
