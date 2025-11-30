'use client';

import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { COMPOUND_COLORS } from '@/lib/constants/colors';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface StintPaceChartProps {
  season: number;
  grandPrix: string;
  selectedDrivers?: string[];
}

interface LapData {
  driver: string;
  lap_number: number;
  lap_time_seconds: number;
  compound: string;
  tyre_life: number;
  stint: number;
  is_pit_out_lap: boolean;
  is_pit_in_lap: boolean;
}

interface Stint {
  driver: string;
  stintNumber: number;
  compound: string;
  lapTimes: number[];
}

export function StintPaceChart({ season, grandPrix, selectedDrivers = [] }: StintPaceChartProps) {
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

    // Group laps into stints
    const driverStints = new Map<string, Stint[]>();

    laps.forEach((lap) => {
      if (lap.is_pit_out_lap || lap.is_pit_in_lap || !lap.compound) return;
      if (lap.lap_time_seconds <= 0) return;

      if (!driverStints.has(lap.driver)) {
        driverStints.set(lap.driver, []);
      }

      const stints = driverStints.get(lap.driver)!;

      // Find or create stint
      let stint = stints.find((s) => s.stintNumber === lap.stint);
      if (!stint) {
        stint = {
          driver: lap.driver,
          stintNumber: lap.stint,
          compound: lap.compound,
          lapTimes: [],
        };
        stints.push(stint);
      }

      stint.lapTimes.push(lap.lap_time_seconds);
    });

    // Filter by selected drivers
    let stintsToShow: Stint[] = [];
    driverStints.forEach((stints, driver) => {
      if (selectedDrivers.length === 0 || selectedDrivers.includes(driver)) {
        stintsToShow.push(...stints);
      }
    });

    // If no drivers selected, show top 6 drivers by total laps
    if (selectedDrivers.length === 0) {
      const driverLapCounts = new Map<string, number>();
      laps.forEach((lap) => {
        driverLapCounts.set(lap.driver, (driverLapCounts.get(lap.driver) || 0) + 1);
      });

      const topDrivers = Array.from(driverLapCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
        .map((e) => e[0]);

      stintsToShow = stintsToShow.filter((s) => topDrivers.includes(s.driver));
    }

    // Sort by driver and stint
    stintsToShow.sort((a, b) => {
      if (a.driver !== b.driver) {
        return a.driver.localeCompare(b.driver);
      }
      return a.stintNumber - b.stintNumber;
    });

    // Create box plot traces
    const traces = stintsToShow.map((stint) => {
      const label = `${stint.driver} - Stint ${stint.stintNumber} (${stint.compound})`;

      return {
        y: stint.lapTimes,
        type: 'box' as const,
        name: label,
        marker: {
          color: COMPOUND_COLORS[stint.compound.toUpperCase()] || '#888888',
        },
        boxmean: 'sd' as const,
        hovertemplate: '<b>%{fullData.name}</b><br>' +
                      'Lap Time: %{y:.3f}s<br>' +
                      '<extra></extra>',
      };
    });

    return traces;
  }, [laps, selectedDrivers]);

  if (isLoading) {
    return (
      <div className="w-full h-[500px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading stint data...</p>
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
        <p className="text-gray-400">No stint data available for this race</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-4">
      <h3 className="text-xl font-semibold mb-4">Stint Pace Distribution</h3>
      <p className="text-sm text-gray-400 mb-4">Box plots showing lap time distribution per stint (colors indicate compound)</p>
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
            title: { text: '' },
            tickangle: -45,
            gridcolor: '#333333',
          },
          yaxis: {
            title: { text: 'Lap Time (seconds)' },
            gridcolor: '#333333',
            zerolinecolor: '#333333',
          },
          hovermode: 'closest',
          showlegend: false,
          margin: {
            l: 60,
            r: 40,
            t: 20,
            b: 120,
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
