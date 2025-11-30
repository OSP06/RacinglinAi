'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { useFilterStore } from '@/lib/store/filters';

export function GrandPrixSelector() {
  const { season, grandPrix, setGrandPrix } = useFilterStore();

  const { data: races, isLoading } = useQuery({
    queryKey: ['races', season],
    queryFn: () => (season ? apiClient.getRacesBySeason(season) : Promise.resolve([])),
    enabled: !!season, // Only fetch when season is selected
  });

  if (!season) {
    return (
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-400 mb-2">
          Grand Prix
        </label>
        <select
          disabled
          className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-gray-500 cursor-not-allowed"
        >
          <option>Select a season first</option>
        </select>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Grand Prix
        </label>
        <div className="h-10 bg-[#1a1a1a] border border-[#333] rounded-md animate-pulse" />
      </div>
    );
  }

  return (
    <div className="w-full">
      <label
        htmlFor="gp-select"
        className="block text-sm font-medium text-gray-300 mb-2"
      >
        Grand Prix
      </label>
      <select
        id="gp-select"
        value={grandPrix || ''}
        onChange={(e) => setGrandPrix(e.target.value || null)}
        className="w-full px-4 py-2 bg-[#1a1a1a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6] focus:border-transparent transition-all"
      >
        <option value="">All Races</option>
        {races
          ?.sort((a, b) => a.round_number || 0 - (b.round_number || 0))
          .map((race) => (
            <option key={race.id} value={race.gp_slug}>
              {race.grand_prix} ({race.circuit_short || race.circuit_name})
            </option>
          ))}
      </select>
      {races && races.length > 0 && (
        <p className="mt-1 text-xs text-gray-500">
          {races.length} race{races.length !== 1 ? 's' : ''} in {season}
        </p>
      )}
    </div>
  );
}
