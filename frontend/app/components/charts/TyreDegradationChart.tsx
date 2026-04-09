'use client';

import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { COMPOUND_COLORS } from '@/lib/constants/colors';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface TyreDegradationChartProps {
  season: number;
  grandPrix: string;
  selectedDrivers?: string[];
}

interface LapData {
  lap_number: number;
  driver: string;
  lap_time_seconds: number;
  compound: string;
  tyre_life: number;
  is_pit_out_lap: boolean;
  is_pit_in_lap: boolean;
}

export function TyreDegradationChart({ season, grandPrix, selectedDrivers = [] }: TyreDegradationChartProps) {
  const { data: races } = useQuery({
    queryKey: ['races', season],
    queryFn: () => apiClient.getRacesBySeason(season),
    enabled: !!season,
  });

  const race = races?.find((r) => r.gp_slug === grandPrix);

  const { data: laps, isLoading, error } = useQuery({
    queryKey: ['laps', race?.id],
    queryFn: async () => {
      if (!race?.id) return [];
      const response = await apiClient.getLaps(race.id);
      return response as LapData[];
    },
    enabled: !!race?.id,
  });

  const plotData = useMemo(() => {
    if (!laps || laps.length === 0) return [];

    const driversToShow = selectedDrivers.length > 0
      ? selectedDrivers
      : Array.from(new Set(laps.map((l) => l.driver))).slice(0, 10); // Limit to 10 drivers for readability

    const compoundGroups = new Map<string, any[]>();

    laps.forEach((lap) => {
      if (!driversToShow.includes(lap.driver)) return;
      if (lap.is_pit_out_lap || lap.is_pit_in_lap) return; // Exclude pit laps
      if (!lap.compound || lap.tyre_life === null || lap.tyre_life === undefined) return;

      const key = `${lap.driver}_${lap.compound}`;
      if (!compoundGroups.has(key)) {
        compoundGroups.set(key, []);
      }

      compoundGroups.get(key)!.push({
        tyre_life: lap.tyre_life,
        lap_time: lap.lap_time_seconds,
      });
    });

    const traces: any[] = [];

    compoundGroups.forEach((data, key) => {
      const [driver, compound] = key.split('_');

      // Sort by tyre life
      data.sort((a, b) => a.tyre_life - b.tyre_life);

      const xValues = data.map((d) => d.tyre_life);
      const yValues = data.map((d) => d.lap_time);

      // Add scatter trace
      traces.push({
        x: xValues,
        y: yValues,
        type: 'scatter',
        mode: 'markers',
        name: `${driver} - ${compound}`,
        marker: {
          color: COMPOUND_COLORS[compound.toUpperCase()] || '#888888',
          size: 8,
          opacity: 0.6,
        },
        hovertemplate: '<b>%{fullData.name}</b><br>' +
                      'Tyre Life: %{x} laps<br>' +
                      'Lap Time: %{y:.3f}s<br>' +
                      '<extra></extra>',
      });

      // Add trendline if enough data points
      if (data.length >= 3) {
        // Simple linear regression
        const n = data.length;
        const sumX = xValues.reduce((a, b) => a + b, 0);
        const sumY = yValues.reduce((a, b) => a + b, 0);
        const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
        const sumX2 = xValues.reduce((sum, x) => sum + x * x, 0);

        const denom = n * sumX2 - sumX * sumX;
        const slope = denom !== 0 ? (n * sumXY - sumX * sumY) / denom : 0;
        const intercept = (sumY - slope * sumX) / n;

        const trendX = [Math.min(...xValues), Math.max(...xValues)];
        const trendY = trendX.map((x) => slope * x + intercept);

        traces.push({
          x: trendX,
          y: trendY,
          type: 'scatter',
          mode: 'lines',
          name: `${driver} - ${compound} (trend)`,
          line: {
            color: COMPOUND_COLORS[compound.toUpperCase()] || '#888888',
            width: 2,
            dash: 'dash',
          },
          showlegend: false,
          hoverinfo: 'skip',
        });
      }
    });

    return traces;
  }, [laps, selectedDrivers]);

  if (isLoading) {
    return (
      <div className="w-full h-[500px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading tyre data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-[500px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center text-red-400">
          <p className="text-xl mb-2">⚠️ Error loading data</p>
          <p className="text-sm text-gray-400">Please try selecting a different race</p>
        </div>
      </div>
    );
  }

  if (!laps || laps.length === 0 || plotData.length === 0) {
    return (
      <div className="w-full h-[500px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <p className="text-gray-400">No tyre data available for this race</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-4">
      <h3 className="text-xl font-semibold mb-4">Tyre Degradation Analysis</h3>
      <Plot
        data={plotData}
        layout={{
          autosize: true,
          height: 500,
          paper_bgcolor: '#1a1a1a',
          plot_bgcolor: '#0a0a0a',
          font: {
            color: '#ffffff',
            family: 'Inter, system-ui, sans-serif',
          },
          xaxis: {
            title: { text: 'Tyre Life (laps)' },
            gridcolor: '#333333',
            zerolinecolor: '#333333',
          },
          yaxis: {
            title: { text: 'Lap Time (seconds)' },
            gridcolor: '#333333',
            zerolinecolor: '#333333',
          },
          hovermode: 'closest',
          legend: {
            orientation: 'v',
            yanchor: 'top',
            y: 1,
            xanchor: 'left',
            x: 1.02,
            bgcolor: 'rgba(26, 26, 26, 0.8)',
            bordercolor: '#333333',
            borderwidth: 1,
          },
          margin: {
            l: 60,
            r: 200,
            t: 20,
            b: 60,
          },
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}
