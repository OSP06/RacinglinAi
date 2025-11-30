'use client';

import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { TEAM_COLORS } from '@/lib/constants/colors';
import { Lap } from '@/lib/types/race';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface GapToLeaderChartProps {
  season: number;
  grandPrix: string;
  selectedDrivers?: string[];
}

export function GapToLeaderChart({ season, grandPrix, selectedDrivers = [] }: GapToLeaderChartProps) {
  // Fetch race data
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
      return response;
    },
    enabled: !!race?.id,
  });

  // Transform data for Plotly
  const plotData = useMemo(() => {
    if (!laps || laps.length === 0) return [];

    // Calculate cumulative times for each driver
    const driverCumulativeTimes = new Map<string, Map<number, number>>();

    laps.forEach((lap) => {
      if (!lap.lap_time_seconds) return; // Skip invalid laps

      if (!driverCumulativeTimes.has(lap.driver)) {
        driverCumulativeTimes.set(lap.driver, new Map());
      }

      const driverTimes = driverCumulativeTimes.get(lap.driver)!;
      const previousTime = driverTimes.get(lap.lap_number - 1) || 0;
      driverTimes.set(lap.lap_number, previousTime + lap.lap_time_seconds);
    });

    // Find the leader's cumulative time at each lap
    const leaderTimes = new Map<number, number>();
    const maxLap = Math.max(...laps.map((l) => l.lap_number));

    for (let lapNum = 1; lapNum <= maxLap; lapNum++) {
      let minTime = Infinity;
      driverCumulativeTimes.forEach((times) => {
        const time = times.get(lapNum);
        if (time !== undefined && time < minTime) {
          minTime = time;
        }
      });
      if (minTime !== Infinity) {
        leaderTimes.set(lapNum, minTime);
      }
    }

    // Calculate gaps for each driver
    const driversToShow = selectedDrivers.length > 0
      ? selectedDrivers
      : Array.from(new Set(laps.map((l) => l.driver)));

    return driversToShow.map((driver) => {
      const driverTimes = driverCumulativeTimes.get(driver);
      if (!driverTimes) return null;

      const xValues: number[] = [];
      const yValues: number[] = [];

      leaderTimes.forEach((leaderTime, lapNum) => {
        const driverTime = driverTimes.get(lapNum);
        if (driverTime !== undefined) {
          xValues.push(lapNum);
          yValues.push(driverTime - leaderTime);
        }
      });

      // Get team color
      const driverLap = laps.find((l) => l.driver === driver);
      const color = driverLap?.team ? TEAM_COLORS[driverLap.team] || '#888888' : '#888888';

      return {
        x: xValues,
        y: yValues,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: driver,
        line: {
          color: color,
          width: 2,
        },
        hovertemplate: '<b>%{fullData.name}</b><br>' +
                      'Lap: %{x}<br>' +
                      'Gap: +%{y:.3f}s<br>' +
                      '<extra></extra>',
      };
    }).filter(Boolean);
  }, [laps, selectedDrivers]);

  if (isLoading) {
    return (
      <div className="w-full h-[500px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading race data...</p>
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

  if (!laps || laps.length === 0) {
    return (
      <div className="w-full h-[500px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <p className="text-gray-400">No data available for this race</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-4">
      <h3 className="text-xl font-semibold mb-4">Gap to Leader</h3>
      <Plot
        data={plotData as any}
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
            title: { text: 'Lap Number' },
            gridcolor: '#333333',
            zerolinecolor: '#333333',
          },
          yaxis: {
            title: { text: 'Gap to Leader (seconds)' },
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
            r: 150,
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
