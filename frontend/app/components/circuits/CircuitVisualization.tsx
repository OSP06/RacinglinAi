'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import * as d3 from 'd3';

interface CircuitVisualizationProps {
  season: number;
  grandPrix: string;
}

interface CircuitData {
  circuit_name: string;
  circuit_country: string;
  track_length_km: number | null;
  altitude_m: number | null;
  coordinates: Array<{
    x: number;
    y: number;
    speed: number;
    distance: number;
  }>;
  fastest_lap_time: string | null;
  fastest_lap_driver: string | null;
}

export function CircuitVisualization({ season, grandPrix }: CircuitVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Fetch races
  const { data: races } = useQuery({
    queryKey: ['races', season],
    queryFn: () => apiClient.getRacesBySeason(season),
    enabled: !!season,
  });

  const race = races?.find((r) => r.gp_slug === grandPrix);

  // Fetch circuit layout
  const { data: circuitData, isLoading, error } = useQuery({
    queryKey: ['circuit', race?.id],
    queryFn: async () => {
      if (!race?.id) return null;
      const response = await apiClient.getCircuitLayout(race.id);
      return response as CircuitData;
    },
    enabled: !!race?.id,
  });

  // Handle responsive sizing
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

  // Render D3 visualization
  useEffect(() => {
    if (!circuitData || !svgRef.current || !circuitData.coordinates.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous render

    const margin = { top: 40, right: 40, bottom: 60, left: 40 };
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Extract coordinates
    const coords = circuitData.coordinates;

    // Find bounds
    const xExtent = d3.extent(coords, (d) => d.x) as [number, number];
    const yExtent = d3.extent(coords, (d) => d.y) as [number, number];

    // Create scales
    const xScale = d3
      .scaleLinear()
      .domain(xExtent)
      .range([0, width]);

    const yScale = d3
      .scaleLinear()
      .domain(yExtent)
      .range([height, 0]); // Invert Y axis

    // Color scale for speed
    const speeds = coords.map((d) => d.speed);
    const minSpeed = Math.min(...speeds);
    const maxSpeed = Math.max(...speeds);

    const colorScale = d3
      .scaleSequential(d3.interpolateRdYlGn)
      .domain([minSpeed, maxSpeed]);

    // Create line generator
    const line = d3
      .line<typeof coords[0]>()
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y))
      .curve(d3.curveCatmullRom.alpha(0.5)); // Smooth curves

    // Draw track outline (darker base)
    g.append('path')
      .datum(coords)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', '#333')
      .attr('stroke-width', 12)
      .attr('stroke-linecap', 'round')
      .attr('stroke-linejoin', 'round');

    // Draw speed gradient segments
    for (let i = 0; i < coords.length - 1; i++) {
      const segment = [coords[i], coords[i + 1]];
      const avgSpeed = (segment[0].speed + segment[1].speed) / 2;

      g.append('path')
        .datum(segment)
        .attr('d', line)
        .attr('fill', 'none')
        .attr('stroke', colorScale(avgSpeed))
        .attr('stroke-width', 8)
        .attr('stroke-linecap', 'round')
        .attr('stroke-linejoin', 'round')
        .attr('opacity', 0.9);
    }

    // Add start/finish line marker
    const startPoint = coords[0];
    g.append('circle')
      .attr('cx', xScale(startPoint.x))
      .attr('cy', yScale(startPoint.y))
      .attr('r', 8)
      .attr('fill', '#fff')
      .attr('stroke', '#3671C6')
      .attr('stroke-width', 3);

    g.append('text')
      .attr('x', xScale(startPoint.x))
      .attr('y', yScale(startPoint.y) - 15)
      .attr('text-anchor', 'middle')
      .attr('fill', '#3671C6')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .text('START/FINISH');

    // Add interactive points with tooltips
    const tooltip = d3
      .select(containerRef.current)
      .append('div')
      .attr('class', 'absolute hidden bg-[#1a1a1a] border border-[#3671C6] rounded-md px-3 py-2 text-sm pointer-events-none z-10')
      .style('position', 'absolute');

    g.selectAll('.track-point')
      .data(coords.filter((_, i) => i % 10 === 0)) // Sample every 10th point
      .enter()
      .append('circle')
      .attr('class', 'track-point')
      .attr('cx', (d) => xScale(d.x))
      .attr('cy', (d) => yScale(d.y))
      .attr('r', 4)
      .attr('fill', (d) => colorScale(d.speed))
      .attr('opacity', 0)
      .attr('cursor', 'pointer')
      .on('mouseover', function (event, d) {
        d3.select(this).attr('opacity', 1).attr('r', 6);
        tooltip
          .html(
            `<div class="font-semibold text-[#3671C6] mb-1">Speed: ${d.speed.toFixed(0)} km/h</div>
             <div class="text-gray-400">Distance: ${d.distance.toFixed(0)}m</div>`
          )
          .classed('hidden', false)
          .style('left', `${event.pageX - containerRef.current!.offsetLeft + 10}px`)
          .style('top', `${event.pageY - containerRef.current!.offsetTop - 10}px`);
      })
      .on('mouseout', function () {
        d3.select(this).attr('opacity', 0).attr('r', 4);
        tooltip.classed('hidden', true);
      });

    // Add speed legend
    const legendWidth = 200;
    const legendHeight = 15;
    const legendMargin = 20;

    const legend = svg
      .append('g')
      .attr('transform', `translate(${margin.left}, ${dimensions.height - margin.bottom + legendMargin})`);

    // Create gradient for legend
    const defs = svg.append('defs');
    const linearGradient = defs
      .append('linearGradient')
      .attr('id', 'speed-gradient')
      .attr('x1', '0%')
      .attr('x2', '100%');

    const numStops = 10;
    for (let i = 0; i <= numStops; i++) {
      const offset = (i / numStops) * 100;
      const speed = minSpeed + (i / numStops) * (maxSpeed - minSpeed);
      linearGradient
        .append('stop')
        .attr('offset', `${offset}%`)
        .attr('stop-color', colorScale(speed));
    }

    // Draw legend rectangle
    legend
      .append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', 'url(#speed-gradient)')
      .attr('stroke', '#333')
      .attr('stroke-width', 1);

    // Legend labels
    legend
      .append('text')
      .attr('x', 0)
      .attr('y', legendHeight + 15)
      .attr('text-anchor', 'start')
      .attr('fill', '#fff')
      .attr('font-size', '11px')
      .text(`${minSpeed.toFixed(0)} km/h`);

    legend
      .append('text')
      .attr('x', legendWidth)
      .attr('y', legendHeight + 15)
      .attr('text-anchor', 'end')
      .attr('fill', '#fff')
      .attr('font-size', '11px')
      .text(`${maxSpeed.toFixed(0)} km/h`);

    legend
      .append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .text('Speed Gradient');

    // Cleanup
    return () => {
      tooltip.remove();
    };
  }, [circuitData, dimensions]);

  if (isLoading) {
    return (
      <div className="w-full h-[600px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading circuit data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-[600px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center text-red-400">
          <p className="text-xl mb-2">⚠️ Error loading circuit data</p>
          <p className="text-sm text-gray-400">Please try selecting a different race</p>
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
      <div className="mb-6">
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
            <span>
              ⚡ Fastest: {circuitData.fastest_lap_driver} ({circuitData.fastest_lap_time})
            </span>
          )}
        </div>
      </div>

      {/* SVG Container */}
      <div ref={containerRef} className="relative w-full">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="w-full h-auto"
          style={{ background: '#0a0a0a', borderRadius: '8px' }}
        />
      </div>

      {/* Info */}
      <div className="mt-4 p-4 bg-[#0a0a0a] border border-[#333] rounded-lg">
        <p className="text-xs text-gray-400">
          <span className="font-semibold text-white">Tip:</span> Hover over the track to see speed data at different points.
          Colors represent speed from slowest (red) through medium (yellow) to fastest (green).
        </p>
      </div>
    </div>
  );
}
