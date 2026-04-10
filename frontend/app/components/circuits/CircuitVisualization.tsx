'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import * as d3 from 'd3';

interface CircuitVisualizationProps {
  season: number;
  grandPrix: string;
}

interface Coordinate {
  x: number;
  y: number;
  speed: number;
  distance: number;
}

interface CircuitData {
  circuit_name: string;
  circuit_country: string;
  track_length_km: number | null;
  altitude_m: number | null;
  coordinates: Coordinate[];
  fastest_lap_time: string | null;
  fastest_lap_driver: string | null;
}

interface ComparisonCoord {
  x: number;
  y: number;
  speed: number;
  distance: number;
  throttle: number;
  brake: boolean;
}

interface DriverComparison {
  driver1: {
    driver: string;
    lap_time: string | null;
    max_speed: number;
    avg_speed: number;
    coordinates: ComparisonCoord[];
  };
  driver2: {
    driver: string;
    lap_time: string | null;
    max_speed: number;
    avg_speed: number;
    coordinates: ComparisonCoord[];
  };
  delta: {
    lap_time_diff: number;
    max_speed_diff: number;
  };
}

export function CircuitVisualization({ season, grandPrix }: CircuitVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Comparison state
  const [compareMode, setCompareMode] = useState(false);
  const [driver1, setDriver1] = useState('');
  const [driver2, setDriver2] = useState('');
  const [comparing, setComparing] = useState(false);

  // Fetch races → resolve race id
  const { data: races } = useQuery({
    queryKey: ['races', season],
    queryFn: () => apiClient.getRacesBySeason(season),
    enabled: !!season,
  });

  const race = races?.find((r) => r.gp_slug === grandPrix);

  // Fetch circuit layout (speed-gradient view) — retries on 503 (data loading)
  const { data: circuitData, isLoading, error } = useQuery({
    queryKey: ['circuit', race?.id],
    queryFn: async () => {
      if (!race?.id) return null;
      return apiClient.getCircuitLayout(race.id) as Promise<CircuitData>;
    },
    enabled: !!race?.id,
    retry: (failureCount: number, err: unknown) => {
      // Retry up to 5 times on 503 (FastF1 still loading on server)
      const status = (err as any)?.response?.status ?? (err as any)?.status;
      return status === 503 && failureCount < 5;
    },
    retryDelay: 15000, // wait 15s between retries
  });

  // Fetch race-specific driver list for comparison selectors
  const { data: raceStats } = useQuery({
    queryKey: ['race-statistics', race?.id],
    queryFn: () => apiClient.getRaceStatistics(race?.id ?? 0),
    enabled: !!race?.id,
  });
  const availableDrivers = raceStats?.map((s) => s.driver) ?? [];

  // Comparison data
  const {
    data: comparisonData,
    isLoading: comparisonLoading,
    error: comparisonError,
    refetch: runComparison,
  } = useQuery<DriverComparison>({
    queryKey: ['comparison', race?.id, driver1, driver2],
    queryFn: async () => {
      if (!race?.id || !driver1 || !driver2) throw new Error('Missing params');
      return apiClient.compareTelemetry(race.id, driver1, driver2) as Promise<DriverComparison>;
    },
    enabled: false, // triggered manually
  });

  // Responsive sizing
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const width = containerRef.current.clientWidth;
        const height = Math.min(width * 0.75, 600);
        setDimensions({ width, height });
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // ── D3: speed-gradient circuit view ─────────────────────────────────────────
  useEffect(() => {
    if (compareMode) return; // handled by comparison effect
    if (!circuitData || !svgRef.current) return;

    const coords = circuitData.coordinates;
    if (!coords.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 40, right: 40, bottom: 60, left: 40 };
    const width  = dimensions.width  - margin.left - margin.right;
    const height = dimensions.height - margin.top  - margin.bottom;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const xExtent = d3.extent(coords, (d) => d.x) as [number, number];
    const yExtent = d3.extent(coords, (d) => d.y) as [number, number];
    if (xExtent[0] === undefined || yExtent[0] === undefined) return;

    const xScale = d3.scaleLinear().domain(xExtent).range([0, width]);
    const yScale = d3.scaleLinear().domain(yExtent).range([height, 0]);

    const speeds = coords.map((d) => d.speed);
    const colorScale = d3.scaleSequential(d3.interpolateRdYlGn)
      .domain([Math.min(...speeds), Math.max(...speeds)]);

    const line = d3.line<Coordinate>()
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y))
      .curve(d3.curveCatmullRom.alpha(0.5));

    // Base track outline
    g.append('path').datum(coords)
      .attr('d', line).attr('fill', 'none')
      .attr('stroke', '#333').attr('stroke-width', 12)
      .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round');

    // Speed-coloured segments
    for (let i = 0; i < coords.length - 1; i++) {
      const segment = [coords[i], coords[i + 1]];
      const avgSpeed = (segment[0].speed + segment[1].speed) / 2;
      g.append('path').datum(segment)
        .attr('d', line).attr('fill', 'none')
        .attr('stroke', colorScale(avgSpeed)).attr('stroke-width', 8)
        .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round')
        .attr('opacity', 0.9);
    }

    // Start/finish marker
    const start = coords[0];
    g.append('circle')
      .attr('cx', xScale(start.x)).attr('cy', yScale(start.y))
      .attr('r', 8).attr('fill', '#fff').attr('stroke', '#3671C6').attr('stroke-width', 3);
    g.append('text')
      .attr('x', xScale(start.x)).attr('y', yScale(start.y) - 15)
      .attr('text-anchor', 'middle').attr('fill', '#3671C6')
      .attr('font-size', '12px').attr('font-weight', 'bold')
      .text('START/FINISH');

    // Tooltip
    const tooltip = d3.select(containerRef.current)
      .append('div')
      .attr('class', 'absolute hidden bg-[#1a1a1a] border border-[#3671C6] rounded-md px-3 py-2 text-sm pointer-events-none z-10')
      .style('position', 'absolute');

    g.selectAll('.track-point')
      .data(coords.filter((_, i) => i % 10 === 0))
      .enter().append('circle')
      .attr('class', 'track-point')
      .attr('cx', (d) => xScale(d.x)).attr('cy', (d) => yScale(d.y))
      .attr('r', 4).attr('fill', (d) => colorScale(d.speed)).attr('opacity', 0).attr('cursor', 'pointer')
      .on('mouseover', function (event, d) {
        d3.select(this).attr('opacity', 1).attr('r', 6);
        tooltip
          .html(`<div class="font-semibold text-[#3671C6] mb-1">Speed: ${d.speed.toFixed(0)} km/h</div><div class="text-gray-400">Distance: ${d.distance.toFixed(0)}m</div>`)
          .classed('hidden', false)
          .style('left', `${event.pageX - (containerRef.current?.offsetLeft ?? 0) + 10}px`)
          .style('top',  `${event.pageY - (containerRef.current?.offsetTop  ?? 0) - 10}px`);
      })
      .on('mouseout', function () {
        d3.select(this).attr('opacity', 0).attr('r', 4);
        tooltip.classed('hidden', true);
      });

    // Speed legend
    const minSpeed = Math.min(...speeds);
    const maxSpeed = Math.max(...speeds);
    const legendWidth = 200;
    const legendHeight = 15;
    const legendMargin = 20;

    const legend = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${dimensions.height - margin.bottom + legendMargin})`);

    const defs = svg.append('defs');
    const gradient = defs.append('linearGradient').attr('id', 'speed-gradient').attr('x1', '0%').attr('x2', '100%');
    for (let i = 0; i <= 10; i++) {
      gradient.append('stop')
        .attr('offset', `${i * 10}%`)
        .attr('stop-color', colorScale(minSpeed + (i / 10) * (maxSpeed - minSpeed)));
    }
    legend.append('rect').attr('width', legendWidth).attr('height', legendHeight)
      .style('fill', 'url(#speed-gradient)').attr('stroke', '#333').attr('stroke-width', 1);
    legend.append('text').attr('x', 0).attr('y', legendHeight + 15)
      .attr('text-anchor', 'start').attr('fill', '#fff').attr('font-size', '11px')
      .text(`${minSpeed.toFixed(0)} km/h`);
    legend.append('text').attr('x', legendWidth).attr('y', legendHeight + 15)
      .attr('text-anchor', 'end').attr('fill', '#fff').attr('font-size', '11px')
      .text(`${maxSpeed.toFixed(0)} km/h`);
    legend.append('text').attr('x', legendWidth / 2).attr('y', -5)
      .attr('text-anchor', 'middle').attr('fill', '#fff').attr('font-size', '12px').attr('font-weight', 'bold')
      .text('Speed Gradient');

    return () => { tooltip.remove(); };
  }, [circuitData, dimensions, compareMode]);

  // ── D3: comparison overlay view ──────────────────────────────────────────────
  useEffect(() => {
    if (!compareMode || !comparisonData || !svgRef.current || !circuitData) return;

    const coords = circuitData.coordinates;
    const c1 = comparisonData.driver1.coordinates;
    const c2 = comparisonData.driver2.coordinates;
    if (!coords.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 40, right: 40, bottom: 40, left: 40 };
    const width  = dimensions.width  - margin.left - margin.right;
    const height = dimensions.height - margin.top  - margin.bottom;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const allCoords = [...coords, ...c1, ...c2];
    const xExtent = d3.extent(allCoords, (d) => d.x) as [number, number];
    const yExtent = d3.extent(allCoords, (d) => d.y) as [number, number];
    if (xExtent[0] === undefined || yExtent[0] === undefined) return;

    const xScale = d3.scaleLinear().domain(xExtent).range([0, width]);
    const yScale = d3.scaleLinear().domain(yExtent).range([height, 0]);

    const baseLine = d3.line<Coordinate>()
      .x((d) => xScale(d.x)).y((d) => yScale(d.y))
      .curve(d3.curveCatmullRom.alpha(0.5));

    const cmpLine = d3.line<ComparisonCoord>()
      .x((d) => xScale(d.x)).y((d) => yScale(d.y))
      .curve(d3.curveCatmullRom.alpha(0.5));

    // Grey base track
    g.append('path').datum(coords).attr('d', baseLine).attr('fill', 'none')
      .attr('stroke', '#444').attr('stroke-width', 10)
      .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round');

    // Driver 2 (blue)
    if (c2.length) {
      g.append('path').datum(c2).attr('d', cmpLine).attr('fill', 'none')
        .attr('stroke', '#3671C6').attr('stroke-width', 5).attr('opacity', 0.85)
        .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round');
    }

    // Driver 1 (red) on top
    if (c1.length) {
      g.append('path').datum(c1).attr('d', cmpLine).attr('fill', 'none')
        .attr('stroke', '#E8002D').attr('stroke-width', 5).attr('opacity', 0.85)
        .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round');
    }

    // Start marker
    if (coords.length) {
      const start = coords[0];
      g.append('circle').attr('cx', xScale(start.x)).attr('cy', yScale(start.y))
        .attr('r', 7).attr('fill', '#fff').attr('stroke', '#888').attr('stroke-width', 2);
    }

    // Legend
    const legend = svg.append('g').attr('transform', `translate(${margin.left + 10}, ${margin.top + 10})`);
    [
      { color: '#E8002D', label: comparisonData.driver1.driver },
      { color: '#3671C6', label: comparisonData.driver2.driver },
    ].forEach(({ color, label }, i) => {
      legend.append('rect').attr('x', 0).attr('y', i * 24).attr('width', 20).attr('height', 6)
        .attr('fill', color).attr('rx', 3);
      legend.append('text').attr('x', 28).attr('y', i * 24 + 6)
        .attr('fill', '#fff').attr('font-size', '13px').attr('font-weight', 'bold').text(label);
    });
  }, [compareMode, comparisonData, circuitData, dimensions]);

  const handleCompare = async () => {
    if (!driver1 || !driver2 || driver1 === driver2) return;
    setComparing(true);
    await runComparison();
    setComparing(false);
  };

  // ── Loading / error states ───────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="w-full h-[600px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4" />
          <p className="text-gray-400">Loading circuit data…</p>
          <p className="text-sm text-gray-500 mt-1">Fetching FastF1 telemetry — first load may take ~30s</p>
        </div>
      </div>
    );
  }

  if (error) {
    const is503 = (error as any)?.response?.status === 503 || (error as any)?.status === 503;
    return (
      <div className="w-full h-[600px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center text-red-400">
          {is503 ? (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4" />
              <p className="text-gray-300 text-lg mb-2">Loading circuit telemetry…</p>
              <p className="text-sm text-gray-400">FastF1 is fetching data for this race. Retrying automatically…</p>
            </>
          ) : (
            <>
              <p className="text-xl mb-2">⚠️ Error loading circuit data</p>
              <p className="text-sm text-gray-400">Please try selecting a different race</p>
            </>
          )}
        </div>
      </div>
    );
  }

  if (!circuitData || !circuitData.coordinates.length) {
    return (
      <div className="w-full h-[600px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <p className="text-gray-400">No circuit data available for this race</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-6">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-2xl font-bold mb-2">{circuitData.circuit_name}</h2>
            <div className="flex flex-wrap gap-4 text-sm text-gray-400">
              <span>📍 {circuitData.circuit_country}</span>
              {circuitData.track_length_km && (
                <span>🏁 {circuitData.track_length_km.toFixed(3)} km</span>
              )}
              {circuitData.altitude_m && (
                <span>⛰️ {circuitData.altitude_m}m altitude</span>
              )}
              {circuitData.fastest_lap_time && circuitData.fastest_lap_driver && (
                <span>⚡ Fastest: {circuitData.fastest_lap_driver} ({circuitData.fastest_lap_time})</span>
              )}
            </div>
          </div>

          {/* View toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setCompareMode(false)}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors ${
                !compareMode ? 'bg-[#3671C6] text-white' : 'bg-[#0a0a0a] text-gray-400 border border-[#333]'
              }`}
            >
              Circuit View
            </button>
            <button
              onClick={() => setCompareMode(true)}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors ${
                compareMode ? 'bg-[#3671C6] text-white' : 'bg-[#0a0a0a] text-gray-400 border border-[#333]'
              }`}
            >
              Compare Drivers
            </button>
          </div>
        </div>
      </div>

      {/* Comparison controls */}
      {compareMode && (
        <div className="mb-4 p-4 bg-[#0a0a0a] border border-[#333] rounded-lg">
          <div className="flex flex-wrap gap-4 items-end">
            {/* Driver 1 */}
            <div className="flex-1 min-w-[140px]">
              <label className="block text-xs font-medium text-[#E8002D] mb-1">Driver 1 (Red)</label>
              <select
                value={driver1}
                onChange={(e) => setDriver1(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1a1a] border border-[#E8002D]/50 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-[#E8002D]"
              >
                <option value="">Select driver</option>
                {availableDrivers.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            {/* Driver 2 */}
            <div className="flex-1 min-w-[140px]">
              <label className="block text-xs font-medium text-[#3671C6] mb-1">Driver 2 (Blue)</label>
              <select
                value={driver2}
                onChange={(e) => setDriver2(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1a1a] border border-[#3671C6]/50 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
              >
                <option value="">Select driver</option>
                {availableDrivers.filter((d) => d !== driver1).map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            {/* Compare button */}
            <button
              onClick={handleCompare}
              disabled={!driver1 || !driver2 || driver1 === driver2 || comparing || comparisonLoading}
              className="px-6 py-2 bg-[#3671C6] text-white font-semibold rounded-md hover:bg-[#2a5ba8] disabled:bg-[#333] disabled:cursor-not-allowed transition-colors text-sm"
            >
              {comparing || comparisonLoading ? 'Loading…' : 'Compare'}
            </button>
          </div>

          {comparisonError && (
            <p className="mt-3 text-sm text-red-400">
              ⚠️ Could not load telemetry. Try a different race or check Render logs.
            </p>
          )}

          {/* Stats cards */}
          {comparisonData && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                {
                  label: 'Lap Time',
                  v1: comparisonData.driver1.lap_time ?? '—',
                  v2: comparisonData.driver2.lap_time ?? '—',
                },
                {
                  label: 'Max Speed',
                  v1: `${comparisonData.driver1.max_speed.toFixed(1)} km/h`,
                  v2: `${comparisonData.driver2.max_speed.toFixed(1)} km/h`,
                },
                {
                  label: 'Avg Speed',
                  v1: `${comparisonData.driver1.avg_speed.toFixed(1)} km/h`,
                  v2: `${comparisonData.driver2.avg_speed.toFixed(1)} km/h`,
                },
                {
                  label: 'Gap',
                  v1: comparisonData.delta.lap_time_diff > 0
                    ? `+${comparisonData.delta.lap_time_diff.toFixed(3)}s`
                    : `${comparisonData.delta.lap_time_diff.toFixed(3)}s`,
                  v2: 'vs driver 2',
                },
              ].map(({ label, v1, v2 }) => (
                <div key={label} className="bg-[#1a1a1a] border border-[#333] rounded-lg p-3">
                  <p className="text-xs text-gray-400 mb-2">{label}</p>
                  <p className="text-sm font-bold text-[#E8002D]">{v1}</p>
                  <p className="text-sm font-bold text-[#3671C6]">{v2}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SVG */}
      <div ref={containerRef} className="relative w-full">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="w-full h-auto"
          style={{ background: '#0a0a0a', borderRadius: '8px' }}
        />
      </div>

      {/* Footer tip */}
      {!compareMode && (
        <div className="mt-4 p-4 bg-[#0a0a0a] border border-[#333] rounded-lg">
          <p className="text-xs text-gray-400">
            <span className="font-semibold text-white">Tip:</span> Hover over the track to see speed data.
            Colors: red (slowest/corners) → yellow → green (fastest/straights).
            Switch to <span className="text-white">Compare Drivers</span> to overlay two fastest laps.
          </p>
        </div>
      )}
    </div>
  );
}
