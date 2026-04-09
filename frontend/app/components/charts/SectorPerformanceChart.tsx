'use client';

import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { TEAM_COLORS } from '@/lib/constants/colors';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface SectorPerformanceChartProps {
  season: number;
  grandPrix: string;
  selectedDrivers?: string[];
}

interface LapData {
  driver: string;
  sector1_time_seconds: number | null;
  sector2_time_seconds: number | null;
  sector3_time_seconds: number | null;
  team: string;
}

export function SectorPerformanceChart({ season, grandPrix, selectedDrivers = [] }: SectorPerformanceChartProps) {
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

    // Calculate average sector times per driver
    const driverStats = new Map<string, {
      sector1: number[];
      sector2: number[];
      sector3: number[];
      team: string;
    }>();

    laps.forEach((lap) => {
      if (!driverStats.has(lap.driver)) {
        driverStats.set(lap.driver, {
          sector1: [],
          sector2: [],
          sector3: [],
          team: lap.team,
        });
      }

      const stats = driverStats.get(lap.driver)!;
      if (lap.sector1_time_seconds !== null && lap.sector1_time_seconds > 0) {
        stats.sector1.push(lap.sector1_time_seconds);
      }
      if (lap.sector2_time_seconds !== null && lap.sector2_time_seconds > 0) {
        stats.sector2.push(lap.sector2_time_seconds);
      }
      if (lap.sector3_time_seconds !== null && lap.sector3_time_seconds > 0) {
        stats.sector3.push(lap.sector3_time_seconds);
      }
    });

    // Calculate averages and find fastest times
    const driverAverages: Array<{
      driver: string;
      sector1_avg: number;
      sector2_avg: number;
      sector3_avg: number;
      team: string;
    }> = [];

    driverStats.forEach((stats, driver) => {
      const avg = (arr: number[]) => arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

      driverAverages.push({
        driver,
        sector1_avg: avg(stats.sector1),
        sector2_avg: avg(stats.sector2),
        sector3_avg: avg(stats.sector3),
        team: stats.team,
      });
    });

    // Filter drivers if specified
    let driversToShow = driverAverages;
    if (selectedDrivers.length > 0) {
      driversToShow = driverAverages.filter((d) => selectedDrivers.includes(d.driver));
    }

    // Sort by total time
    driversToShow.sort((a, b) => {
      const totalA = a.sector1_avg + a.sector2_avg + a.sector3_avg;
      const totalB = b.sector1_avg + b.sector2_avg + b.sector3_avg;
      return totalA - totalB;
    });

    // Take top 10 if no specific drivers selected
    if (selectedDrivers.length === 0) {
      driversToShow = driversToShow.slice(0, 10);
    }

    // Find fastest times for delta calculation — guard against empty arrays
    const validS1 = driversToShow.map((d) => d.sector1_avg).filter((t) => t > 0);
    const validS2 = driversToShow.map((d) => d.sector2_avg).filter((t) => t > 0);
    const validS3 = driversToShow.map((d) => d.sector3_avg).filter((t) => t > 0);
    const fastestS1 = validS1.length > 0 ? Math.min(...validS1) : 0;
    const fastestS2 = validS2.length > 0 ? Math.min(...validS2) : 0;
    const fastestS3 = validS3.length > 0 ? Math.min(...validS3) : 0;

    // Create traces for each sector
    const sector1Trace = {
      y: driversToShow.map((d) => d.driver),
      x: driversToShow.map((d) => d.sector1_avg - fastestS1),
      name: 'Sector 1',
      type: 'bar' as const,
      orientation: 'h' as const,
      marker: {
        color: '#3671C6',
      },
      hovertemplate: '<b>%{y}</b><br>' +
                    'Sector 1 Delta: +%{x:.3f}s<br>' +
                    '<extra></extra>',
    };

    const sector2Trace = {
      y: driversToShow.map((d) => d.driver),
      x: driversToShow.map((d) => d.sector2_avg - fastestS2),
      name: 'Sector 2',
      type: 'bar' as const,
      orientation: 'h' as const,
      marker: {
        color: '#27F4D2',
      },
      hovertemplate: '<b>%{y}</b><br>' +
                    'Sector 2 Delta: +%{x:.3f}s<br>' +
                    '<extra></extra>',
    };

    const sector3Trace = {
      y: driversToShow.map((d) => d.driver),
      x: driversToShow.map((d) => d.sector3_avg - fastestS3),
      name: 'Sector 3',
      type: 'bar' as const,
      orientation: 'h' as const,
      marker: {
        color: '#E8002D',
      },
      hovertemplate: '<b>%{y}</b><br>' +
                    'Sector 3 Delta: +%{x:.3f}s<br>' +
                    '<extra></extra>',
    };

    return [sector1Trace, sector2Trace, sector3Trace];
  }, [laps, selectedDrivers]);

  if (isLoading) {
    return (
      <div className="w-full h-[500px] bg-[#1a1a1a] rounded-lg border border-[#333] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading sector data...</p>
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
        <p className="text-gray-400">No sector data available for this race</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-4">
      <h3 className="text-xl font-semibold mb-4">Sector Performance Comparison</h3>
      <p className="text-sm text-gray-400 mb-4">Average delta to fastest sector time</p>
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
            title: { text: 'Delta to Fastest (seconds)' },
            gridcolor: '#333333',
            zerolinecolor: '#666666',
            zerolinewidth: 2,
          },
          yaxis: {
            title: { text: '' },
            gridcolor: '#333333',
            automargin: true,
          },
          barmode: 'group',
          hovermode: 'closest',
          legend: {
            orientation: 'h',
            yanchor: 'bottom',
            y: 1.02,
            xanchor: 'center',
            x: 0.5,
            bgcolor: 'rgba(26, 26, 26, 0.8)',
            bordercolor: '#333333',
            borderwidth: 1,
          },
          margin: {
            l: 120,
            r: 40,
            t: 60,
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
