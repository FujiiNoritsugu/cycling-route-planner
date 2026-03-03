import { describe, it, expect } from 'vitest';
import { generateGpx, generateFileName } from '../utils/gpxExport';
import type { RoutePlan, Location } from '../types';

function makeRoutePlan(overrides: Partial<RoutePlan> = {}): RoutePlan {
  return {
    id: 'test-1',
    segments: [
      {
        coordinates: [[34.573, 135.483], [34.55, 135.5], [34.396, 135.757]],
        elevations: [10, 50, 200],
        distance_km: 35.5,
        elevation_gain_m: 400,
        elevation_loss_m: 210,
        estimated_duration_min: 120,
        surface_type: 'paved',
      },
    ],
    total_distance_km: 35.5,
    total_elevation_gain_m: 400,
    total_duration_min: 120,
    weather_forecasts: [],
    llm_analysis: '',
    warnings: [],
    recommended_gear: [],
    created_at: '2026-03-04T07:00:00Z',
    ...overrides,
  };
}

const origin: Location = { lat: 34.573, lng: 135.483, name: '堺市上野芝' };
const destination: Location = { lat: 34.396, lng: 135.757, name: '吉野山' };

describe('generateGpx', () => {
  it('produces valid GPX 1.1 with correct namespace and version', () => {
    const gpx = generateGpx({ routePlan: makeRoutePlan(), origin, destination });
    expect(gpx).toContain('<?xml version="1.0" encoding="UTF-8"?>');
    expect(gpx).toContain('version="1.1"');
    expect(gpx).toContain('xmlns="http://www.topografix.com/GPX/1/1"');
  });

  it('includes origin and destination as waypoints', () => {
    const gpx = generateGpx({ routePlan: makeRoutePlan(), origin, destination });
    expect(gpx).toContain(`<wpt lat="${origin.lat}" lon="${origin.lng}">`);
    expect(gpx).toContain(`<wpt lat="${destination.lat}" lon="${destination.lng}">`);
    expect(gpx).toContain('<name>堺市上野芝</name>');
    expect(gpx).toContain('<name>吉野山</name>');
  });

  it('maps coordinates to trkpt lat/lon attributes', () => {
    const gpx = generateGpx({ routePlan: makeRoutePlan(), origin, destination });
    expect(gpx).toContain('<trkpt lat="34.573" lon="135.483">');
    expect(gpx).toContain('<trkpt lat="34.55" lon="135.5">');
    expect(gpx).toContain('<trkpt lat="34.396" lon="135.757">');
  });

  it('includes <ele> when elevation data is present', () => {
    const gpx = generateGpx({ routePlan: makeRoutePlan(), origin, destination });
    expect(gpx).toContain('<ele>10</ele>');
    expect(gpx).toContain('<ele>50</ele>');
    expect(gpx).toContain('<ele>200</ele>');
  });

  it('omits <ele> when elevation data is absent', () => {
    const plan = makeRoutePlan({
      segments: [
        {
          coordinates: [[34.573, 135.483], [34.396, 135.757]],
          distance_km: 35.5,
          elevation_gain_m: 0,
          elevation_loss_m: 0,
          estimated_duration_min: 120,
          surface_type: 'paved',
        },
      ],
    });
    const gpx = generateGpx({ routePlan: plan, origin, destination });
    expect(gpx).not.toContain('<ele>');
  });

  it('creates multiple <trkseg> for multiple segments', () => {
    const plan = makeRoutePlan({
      segments: [
        {
          coordinates: [[34.573, 135.483], [34.55, 135.5]],
          elevations: [10, 50],
          distance_km: 15,
          elevation_gain_m: 200,
          elevation_loss_m: 100,
          estimated_duration_min: 60,
          surface_type: 'paved',
        },
        {
          coordinates: [[34.55, 135.5], [34.396, 135.757]],
          elevations: [50, 200],
          distance_km: 20.5,
          elevation_gain_m: 200,
          elevation_loss_m: 110,
          estimated_duration_min: 60,
          surface_type: 'gravel',
        },
      ],
    });
    const gpx = generateGpx({ routePlan: plan, origin, destination });
    const trksegCount = (gpx.match(/<trkseg>/g) || []).length;
    expect(trksegCount).toBe(2);
  });

  it('escapes XML special characters in names', () => {
    const specialOrigin: Location = { lat: 34.0, lng: 135.0, name: 'A & B <C>' };
    const specialDest: Location = { lat: 35.0, lng: 136.0, name: '"D" \'E\'' };
    const gpx = generateGpx({ routePlan: makeRoutePlan(), origin: specialOrigin, destination: specialDest });
    expect(gpx).toContain('A &amp; B &lt;C&gt;');
    expect(gpx).toContain('&quot;D&quot; &apos;E&apos;');
  });

  it('handles Japanese characters in metadata', () => {
    const gpx = generateGpx({ routePlan: makeRoutePlan(), origin, destination });
    expect(gpx).toContain('堺市上野芝 → 吉野山');
    expect(gpx).toContain('距離:');
  });

  it('throws error for empty segments', () => {
    const plan = makeRoutePlan({ segments: [] });
    expect(() => generateGpx({ routePlan: plan, origin, destination }))
      .toThrow('ルートデータがありません');
  });

  it('falls back to current date when created_at is missing', () => {
    const { created_at: _, ...planWithoutDate } = makeRoutePlan();
    const gpx = generateGpx({ routePlan: planWithoutDate, origin, destination });
    expect(gpx).toContain('<time>');
    expect(gpx).not.toContain('Invalid');
  });

  it('uses fallback label when waypoint has no name', () => {
    const noNameOrigin: Location = { lat: 34.573, lng: 135.483 };
    const noNameDest: Location = { lat: 34.396, lng: 135.757 };
    const gpx = generateGpx({ routePlan: makeRoutePlan(), origin: noNameOrigin, destination: noNameDest });
    expect(gpx).toContain('<name>出発地</name>');
    expect(gpx).toContain('<name>目的地</name>');
  });
});

describe('generateFileName', () => {
  it('generates filename with date and location names', () => {
    const name = generateFileName({ routePlan: makeRoutePlan(), origin, destination });
    expect(name).toBe('20260304_堺市上野芝_吉野山.gpx');
  });

  it('uses lat/lng when names are missing', () => {
    const noNameOrigin: Location = { lat: 34.573, lng: 135.483 };
    const noNameDest: Location = { lat: 34.396, lng: 135.757 };
    const name = generateFileName({ routePlan: makeRoutePlan(), origin: noNameOrigin, destination: noNameDest });
    expect(name).toBe('20260304_34.573_135.483_34.396_135.757.gpx');
  });

  it('sanitizes special characters in names', () => {
    const specialOrigin: Location = { lat: 34.0, lng: 135.0, name: 'A/B:C' };
    const specialDest: Location = { lat: 35.0, lng: 136.0, name: 'D*E?' };
    const name = generateFileName({ routePlan: makeRoutePlan(), origin: specialOrigin, destination: specialDest });
    expect(name).toBe('20260304_A_B_C_D_E_.gpx');
  });
});
