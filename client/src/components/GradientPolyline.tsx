import { useMemo } from 'react';
import { Polyline, Tooltip } from 'react-leaflet';
import { LatLngExpression } from 'leaflet';
import { calculateGradientSubSegments } from '../utils/gradientColors';
import type { RouteSegment } from '../types';

interface GradientPolylineProps {
  segment: RouteSegment;
  segmentIndex: number;
}

export function GradientPolyline({ segment, segmentIndex }: GradientPolylineProps) {
  const subSegments = useMemo(
    () => calculateGradientSubSegments(segment.coordinates, segment.elevations),
    [segment.coordinates, segment.elevations],
  );

  if (subSegments.length === 0) {
    return null;
  }

  const segmentLabel = segment.segment_type === 'return' ? '復路' : '往路';

  return (
    <>
      {subSegments.map((sub, i) => {
        const positions: LatLngExpression[] = [
          [sub.start[0], sub.start[1]],
          [sub.end[0], sub.end[1]],
        ];
        const sign = sub.gradient >= 0 ? '+' : '';
        return (
          <Polyline
            key={i}
            positions={positions}
            pathOptions={{
              color: sub.color,
              weight: 5,
              opacity: 0.85,
            }}
          >
            <Tooltip sticky>
              {segmentLabel} - 区間 {segmentIndex + 1} / 勾配: {sign}
              {sub.gradient.toFixed(1)}%
            </Tooltip>
          </Polyline>
        );
      })}
    </>
  );
}
