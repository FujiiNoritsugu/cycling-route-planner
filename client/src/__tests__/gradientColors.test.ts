import { describe, it, expect } from 'vitest';
import {
  getGradientColor,
  haversineDistance,
  calculateGradientSubSegments,
  GRADIENT_LEGEND_ENTRIES,
} from '../utils/gradientColors';

describe('getGradientColor', () => {
  it('returns green for flat terrain (0%)', () => {
    expect(getGradientColor(0)).toBe('#22c55e');
  });

  it('returns green for gentle uphill (2%)', () => {
    expect(getGradientColor(2)).toBe('#22c55e');
  });

  it('returns yellow for moderate uphill (5%)', () => {
    expect(getGradientColor(5)).toBe('#eab308');
  });

  it('returns orange for hard uphill (8%)', () => {
    expect(getGradientColor(8)).toBe('#f97316');
  });

  it('returns red for steep uphill (12%)', () => {
    expect(getGradientColor(12)).toBe('#dc2626');
  });

  it('returns light blue for gentle downhill (-2%)', () => {
    expect(getGradientColor(-2)).toBe('#38bdf8');
  });

  it('returns blue for moderate downhill (-5%)', () => {
    expect(getGradientColor(-5)).toBe('#3b82f6');
  });

  it('returns indigo for hard downhill (-8%)', () => {
    expect(getGradientColor(-8)).toBe('#6366f1');
  });

  it('returns purple for steep downhill (-12%)', () => {
    expect(getGradientColor(-12)).toBe('#7c3aed');
  });
});

describe('haversineDistance', () => {
  it('returns 0 for identical points', () => {
    const p: [number, number] = [34.573, 135.483];
    expect(haversineDistance(p, p)).toBe(0);
  });

  it('calculates Osaka-Nara distance (~30km)', () => {
    const osaka: [number, number] = [34.6937, 135.5023];
    const nara: [number, number] = [34.6851, 135.8048];
    const dist = haversineDistance(osaka, nara);
    expect(dist).toBeGreaterThan(25000);
    expect(dist).toBeLessThan(35000);
  });

  it('returns small distance for nearby points', () => {
    const a: [number, number] = [34.573, 135.483];
    const b: [number, number] = [34.5731, 135.4831];
    const dist = haversineDistance(a, b);
    expect(dist).toBeGreaterThan(0);
    expect(dist).toBeLessThan(200);
  });
});

describe('calculateGradientSubSegments', () => {
  it('returns empty array when elevations is undefined', () => {
    const coords: [number, number][] = [[34.0, 135.0], [34.01, 135.01]];
    expect(calculateGradientSubSegments(coords, undefined)).toEqual([]);
  });

  it('returns empty array when coordinates has fewer than 2 points', () => {
    expect(calculateGradientSubSegments([[34.0, 135.0]], [100])).toEqual([]);
  });

  it('returns empty array when elevations length mismatches coordinates', () => {
    const coords: [number, number][] = [[34.0, 135.0], [34.01, 135.01]];
    expect(calculateGradientSubSegments(coords, [100])).toEqual([]);
  });

  it('calculates uphill gradient correctly', () => {
    // Two points ~1111m apart with 50m elevation gain → ~4.5% gradient
    const coords: [number, number][] = [[34.0, 135.0], [34.01, 135.0]];
    const elevations = [100, 150];
    const result = calculateGradientSubSegments(coords, elevations);
    expect(result).toHaveLength(1);
    expect(result[0].gradient).toBeGreaterThan(3);
    expect(result[0].gradient).toBeLessThan(6);
    expect(result[0].color).toBe('#eab308'); // yellow for 3-6%
  });

  it('calculates downhill gradient correctly', () => {
    const coords: [number, number][] = [[34.0, 135.0], [34.01, 135.0]];
    const elevations = [150, 100];
    const result = calculateGradientSubSegments(coords, elevations);
    expect(result).toHaveLength(1);
    expect(result[0].gradient).toBeLessThan(-3);
    expect(result[0].gradient).toBeGreaterThan(-6);
    expect(result[0].color).toBe('#3b82f6'); // blue for moderate downhill
  });

  it('applies smoothing across 3 points', () => {
    // Middle point has a spike that should be smoothed out
    const coords: [number, number][] = [
      [34.0, 135.0],
      [34.01, 135.0],
      [34.02, 135.0],
    ];
    const elevations = [100, 100, 100]; // flat terrain
    const result = calculateGradientSubSegments(coords, elevations);
    expect(result).toHaveLength(2);
    result.forEach((seg) => {
      expect(Math.abs(seg.gradient)).toBeLessThan(0.01);
    });
  });

  it('treats very close points (< 0.5m) as gradient 0', () => {
    // Two nearly identical points
    const coords: [number, number][] = [
      [34.0, 135.0],
      [34.0000001, 135.0000001],
    ];
    const elevations = [100, 200]; // 100m diff but distance ~0
    const result = calculateGradientSubSegments(coords, elevations);
    expect(result).toHaveLength(1);
    expect(result[0].gradient).toBe(0);
  });

  it('assigns correct colors based on gradient magnitude', () => {
    // Create a steep uphill scenario
    const coords: [number, number][] = [[34.0, 135.0], [34.001, 135.0]];
    const elevations = [100, 115]; // ~15m over ~111m → ~13.5%
    const result = calculateGradientSubSegments(coords, elevations);
    expect(result).toHaveLength(1);
    expect(result[0].color).toBe('#dc2626'); // red for >10%
  });
});

describe('GRADIENT_LEGEND_ENTRIES', () => {
  it('has exactly 8 entries', () => {
    expect(GRADIENT_LEGEND_ENTRIES).toHaveLength(8);
  });

  it('each entry has label and color', () => {
    GRADIENT_LEGEND_ENTRIES.forEach((entry) => {
      expect(entry.label).toBeTruthy();
      expect(entry.color).toMatch(/^#[0-9a-f]{6}$/);
    });
  });
});
