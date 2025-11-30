'use client';

import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { TEAM_COLORS } from '@/lib/constants/colors';

interface RaceStatisticsTableProps {
  season: number;
  grandPrix: string;
  selectedDrivers?: string[];
}

interface LapData {
  driver: string;
  lap_number: number;
  lap_time_seconds: number;
  sector1_time_seconds: number | null;
  sector2_time_seconds: number | null;
  sector3_time_seconds: number | null;
  speed_fl: number | null;
  speed_st: number | null;
  compound: string;
  team: string;
  is_pit_out_lap: boolean;
  is_pit_in_lap: boolean;
}

interface DriverStats {
  driver: string;
  team: string;
  totalLaps: number;
  bestLap: number;
  avgLap: number;
  bestS1: number;
  bestS2: number;
  bestS3: number;
  maxSpeed: number;
  pitStops: number;
}

type SortKey = keyof DriverStats;
type SortDirection = 'asc' | 'desc';

export function RaceStatisticsTable({ season, grandPrix, selectedDrivers = [] }: RaceStatisticsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('bestLap');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

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

  const statistics = useMemo(() => {
    if (!laps || laps.length === 0) return [];

    const driverMap = new Map<string, {
      team: string;
      laps: LapData[];
    }>();

    laps.forEach((lap) => {
      if (!driverMap.has(lap.driver)) {
        driverMap.set(lap.driver, {
          team: lap.team,
          laps: [],
        });
      }
      driverMap.get(lap.driver)!.laps.push(lap);
    });

    const stats: DriverStats[] = [];

    driverMap.forEach(({ team, laps: driverLaps }, driver) => {
      // Filter out pit laps for best lap calculation
      const raceLaps = driverLaps.filter((l) => !l.is_pit_in_lap && !l.is_pit_out_lap && l.lap_time_seconds > 0);

      const validLapTimes = raceLaps.map((l) => l.lap_time_seconds).filter((t) => t > 0);
      const bestLap = validLapTimes.length > 0 ? Math.min(...validLapTimes) : 0;
      const avgLap = validLapTimes.length > 0
        ? validLapTimes.reduce((a, b) => a + b, 0) / validLapTimes.length
        : 0;

      const validS1 = raceLaps.map((l) => l.sector1_time_seconds).filter((t) => t !== null && t > 0) as number[];
      const validS2 = raceLaps.map((l) => l.sector2_time_seconds).filter((t) => t !== null && t > 0) as number[];
      const validS3 = raceLaps.map((l) => l.sector3_time_seconds).filter((t) => t !== null && t > 0) as number[];

      const bestS1 = validS1.length > 0 ? Math.min(...validS1) : 0;
      const bestS2 = validS2.length > 0 ? Math.min(...validS2) : 0;
      const bestS3 = validS3.length > 0 ? Math.min(...validS3) : 0;

      const speeds = driverLaps.map((l) => l.speed_fl).filter((s) => s !== null && s > 0) as number[];
      const maxSpeed = speeds.length > 0 ? Math.max(...speeds) : 0;

      const pitStops = driverLaps.filter((l) => l.is_pit_in_lap).length;

      stats.push({
        driver,
        team,
        totalLaps: driverLaps.length,
        bestLap,
        avgLap,
        bestS1,
        bestS2,
        bestS3,
        maxSpeed,
        pitStops,
      });
    });

    // Filter by selected drivers
    let filteredStats = stats;
    if (selectedDrivers.length > 0) {
      filteredStats = stats.filter((s) => selectedDrivers.includes(s.driver));
    }

    // Sort
    filteredStats.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return 0;
    });

    return filteredStats;
  }, [laps, selectedDrivers, sortKey, sortDirection]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  const formatTime = (seconds: number) => {
    if (seconds === 0) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}:${secs.toFixed(3).padStart(6, '0')}` : `${secs.toFixed(3)}s`;
  };

  if (isLoading) {
    return (
      <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-6">
        <h3 className="text-xl font-semibold mb-4">Race Statistics</h3>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
            <p className="text-gray-400">Loading statistics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-6">
        <h3 className="text-xl font-semibold mb-4">Race Statistics</h3>
        <div className="text-center text-red-400 py-12">
          <p className="text-xl mb-2">⚠️ Error loading data</p>
          <p className="text-sm text-gray-400">Please try selecting a different race</p>
        </div>
      </div>
    );
  }

  if (!laps || laps.length === 0 || statistics.length === 0) {
    return (
      <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-6">
        <h3 className="text-xl font-semibold mb-4">Race Statistics</h3>
        <div className="text-center py-12">
          <p className="text-gray-400">No statistics available for this race</p>
        </div>
      </div>
    );
  }

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return <span className="text-gray-600">⇅</span>;
    return sortDirection === 'asc' ? <span className="text-[#3671C6]">↑</span> : <span className="text-[#3671C6]">↓</span>;
  };

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-6">
      <h3 className="text-xl font-semibold mb-4">Race Statistics</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#333]">
              <th className="text-left py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('driver')}>
                Driver <SortIcon column="driver" />
              </th>
              <th className="text-left py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('team')}>
                Team <SortIcon column="team" />
              </th>
              <th className="text-center py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('totalLaps')}>
                Laps <SortIcon column="totalLaps" />
              </th>
              <th className="text-center py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('bestLap')}>
                Best Lap <SortIcon column="bestLap" />
              </th>
              <th className="text-center py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('avgLap')}>
                Avg Lap <SortIcon column="avgLap" />
              </th>
              <th className="text-center py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('bestS1')}>
                Best S1 <SortIcon column="bestS1" />
              </th>
              <th className="text-center py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('bestS2')}>
                Best S2 <SortIcon column="bestS2" />
              </th>
              <th className="text-center py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('bestS3')}>
                Best S3 <SortIcon column="bestS3" />
              </th>
              <th className="text-center py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('maxSpeed')}>
                Max Speed <SortIcon column="maxSpeed" />
              </th>
              <th className="text-center py-3 px-4 font-semibold cursor-pointer hover:text-[#3671C6]" onClick={() => handleSort('pitStops')}>
                Pit Stops <SortIcon column="pitStops" />
              </th>
            </tr>
          </thead>
          <tbody>
            {statistics.map((stat, idx) => (
              <tr
                key={stat.driver}
                className="border-b border-[#222] hover:bg-[#222] transition-colors"
              >
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: TEAM_COLORS[stat.team] || '#888888' }}
                    />
                    <span className="font-medium">{stat.driver}</span>
                  </div>
                </td>
                <td className="py-3 px-4 text-gray-400">{stat.team}</td>
                <td className="py-3 px-4 text-center">{stat.totalLaps}</td>
                <td className="py-3 px-4 text-center font-mono">
                  {idx === 0 && sortKey === 'bestLap' ? (
                    <span className="text-[#3671C6] font-bold">{formatTime(stat.bestLap)}</span>
                  ) : (
                    formatTime(stat.bestLap)
                  )}
                </td>
                <td className="py-3 px-4 text-center font-mono">{formatTime(stat.avgLap)}</td>
                <td className="py-3 px-4 text-center font-mono">{formatTime(stat.bestS1)}</td>
                <td className="py-3 px-4 text-center font-mono">{formatTime(stat.bestS2)}</td>
                <td className="py-3 px-4 text-center font-mono">{formatTime(stat.bestS3)}</td>
                <td className="py-3 px-4 text-center">{stat.maxSpeed > 0 ? `${stat.maxSpeed.toFixed(1)} km/h` : '-'}</td>
                <td className="py-3 px-4 text-center">{stat.pitStops}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
