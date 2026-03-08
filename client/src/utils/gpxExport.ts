import type { RoutePlan, Location } from '../types';

export interface GpxExportOptions {
  routePlan: Partial<RoutePlan>;
  origin: Location;
  destination: Location;
  waypoints?: Location[];
}

function parseDate(value: string | undefined): Date {
  if (value) {
    const d = new Date(value);
    if (!isNaN(d.getTime())) return d;
  }
  return new Date();
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

export function generateFileName(options: GpxExportOptions): string {
  const date = parseDate(options.routePlan.created_at);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const dateStr = `${yyyy}${mm}${dd}`;

  const originName = options.origin.name || `${options.origin.lat}_${options.origin.lng}`;
  const destName = options.destination.name || `${options.destination.lat}_${options.destination.lng}`;

  // Sanitize file name: remove characters not safe for filenames
  const sanitize = (s: string) => s.replace(/[\\/:*?"<>|]/g, '_');

  return `${dateStr}_${sanitize(originName)}_${sanitize(destName)}.gpx`;
}

export function generateGpx(options: GpxExportOptions): string {
  const { routePlan, origin, destination } = options;

  if (!routePlan.segments || routePlan.segments.length === 0) {
    throw new Error('ルートデータがありません');
  }

  const wpNames = (options.waypoints || []).map(
    (wp) => wp.name || `${wp.lat},${wp.lng}`,
  );
  const allNames = [
    origin.name || `${origin.lat},${origin.lng}`,
    ...wpNames,
    destination.name || `${destination.lat},${destination.lng}`,
  ];
  const routeName = allNames.join(' → ');
  const hours = Math.floor((routePlan.total_duration_min || 0) / 60);
  const mins = (routePlan.total_duration_min || 0) % 60;
  const description = `距離: ${routePlan.total_distance_km?.toFixed(2)} km / 獲得標高: ${routePlan.total_elevation_gain_m?.toFixed(0)} m / 所要時間: ${hours}時間${mins}分`;

  const lines: string[] = [];

  lines.push('<?xml version="1.0" encoding="UTF-8"?>');
  lines.push(
    '<gpx version="1.1" creator="Cycling Route AI Planner"' +
    ' xmlns="http://www.topografix.com/GPX/1/1"' +
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' +
    ' xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">'
  );

  // Metadata
  lines.push('  <metadata>');
  lines.push(`    <name>${escapeXml(routeName)}</name>`);
  lines.push(`    <desc>${escapeXml(description)}</desc>`);
  lines.push(`    <time>${parseDate(routePlan.created_at).toISOString()}</time>`);
  lines.push('  </metadata>');

  // Waypoints
  const addWaypoint = (loc: Location, label: string) => {
    lines.push(`  <wpt lat="${loc.lat}" lon="${loc.lng}">`);
    lines.push(`    <name>${escapeXml(loc.name || label)}</name>`);
    lines.push('  </wpt>');
  };
  addWaypoint(origin, '出発地');
  if (options.waypoints) {
    options.waypoints.forEach((wp, idx) => {
      addWaypoint(wp, `経由地 ${idx + 1}`);
    });
  }
  addWaypoint(destination, '目的地');

  // Track
  lines.push('  <trk>');
  lines.push(`    <name>${escapeXml(routeName)}</name>`);

  for (const segment of routePlan.segments) {
    lines.push('    <trkseg>');
    for (let i = 0; i < segment.coordinates.length; i++) {
      const [lat, lng] = segment.coordinates[i];
      const ele = segment.elevations?.[i];
      lines.push(`      <trkpt lat="${lat}" lon="${lng}">`);
      if (ele !== undefined) {
        lines.push(`        <ele>${ele}</ele>`);
      }
      lines.push('      </trkpt>');
    }
    lines.push('    </trkseg>');
  }

  lines.push('  </trk>');
  lines.push('</gpx>');

  return lines.join('\n');
}

export function downloadGpx(options: GpxExportOptions): void {
  const xml = generateGpx(options);
  const blob = new Blob([xml], { type: 'application/gpx+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = generateFileName(options);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
