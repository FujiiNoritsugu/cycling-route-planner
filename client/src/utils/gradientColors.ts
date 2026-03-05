/**
 * Shared gradient calculation and color mapping utilities for route visualization.
 */

export interface GradientSubSegment {
  start: [number, number]; // [lat, lng]
  end: [number, number];
  gradient: number; // percentage
  color: string;
}

export interface GradientLegendEntry {
  label: string;
  color: string;
}

/**
 * Map a gradient percentage to a color.
 * Uphill: green → yellow → orange → red
 * Downhill: light blue → blue → indigo → purple
 */
export function getGradientColor(gradient: number): string {
  if (gradient > 10) return '#dc2626'; // steep uphill - red
  if (gradient > 6) return '#f97316'; // hard uphill - orange
  if (gradient > 3) return '#eab308'; // moderate uphill - yellow
  if (gradient >= 0) return '#22c55e'; // gentle/flat - green
  if (gradient > -3) return '#38bdf8'; // gentle downhill - light blue
  if (gradient > -6) return '#3b82f6'; // moderate downhill - blue
  if (gradient > -10) return '#6366f1'; // hard downhill - indigo
  return '#7c3aed'; // steep downhill - purple
}

/**
 * Haversine distance between two [lat, lng] points in meters.
 */
export function haversineDistance(
  a: [number, number],
  b: [number, number],
): number {
  const R = 6371000; // Earth radius in meters
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(b[0] - a[0]);
  const dLng = toRad(b[1] - a[1]);
  const sinLat = Math.sin(dLat / 2);
  const sinLng = Math.sin(dLng / 2);
  const h =
    sinLat * sinLat +
    Math.cos(toRad(a[0])) * Math.cos(toRad(b[0])) * sinLng * sinLng;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/**
 * Calculate gradient sub-segments from coordinate/elevation arrays.
 * Applies 3-point moving average smoothing to reduce GPS noise.
 */
export function calculateGradientSubSegments(
  coordinates: [number, number][],
  elevations: number[] | undefined,
): GradientSubSegment[] {
  if (
    !elevations ||
    coordinates.length < 2 ||
    elevations.length !== coordinates.length
  ) {
    return [];
  }

  // Calculate raw gradients for each pair of adjacent points
  const rawGradients: number[] = [];
  for (let i = 0; i < coordinates.length - 1; i++) {
    const dist = haversineDistance(coordinates[i], coordinates[i + 1]);
    if (dist < 0.5) {
      rawGradients.push(0);
    } else {
      const elevDiff = elevations[i + 1] - elevations[i];
      rawGradients.push((elevDiff / dist) * 100);
    }
  }

  // 3-point moving average smoothing
  const smoothed: number[] = rawGradients.map((_, i) => {
    const start = Math.max(0, i - 1);
    const end = Math.min(rawGradients.length - 1, i + 1);
    let sum = 0;
    let count = 0;
    for (let j = start; j <= end; j++) {
      sum += rawGradients[j];
      count++;
    }
    return sum / count;
  });

  // Build sub-segments
  return smoothed.map((gradient, i) => ({
    start: coordinates[i],
    end: coordinates[i + 1],
    gradient,
    color: getGradientColor(gradient),
  }));
}

/** Legend entries for 8 gradient categories. */
export const GRADIENT_LEGEND_ENTRIES: GradientLegendEntry[] = [
  { label: '急登 (>10%)', color: '#dc2626' },
  { label: '強い上り (6-10%)', color: '#f97316' },
  { label: '中程度の上り (3-6%)', color: '#eab308' },
  { label: '緩い上り/平坦 (0-3%)', color: '#22c55e' },
  { label: '緩い下り (0-3%)', color: '#38bdf8' },
  { label: '中程度の下り (3-6%)', color: '#3b82f6' },
  { label: '強い下り (6-10%)', color: '#6366f1' },
  { label: '急降下 (>10%)', color: '#7c3aed' },
];
