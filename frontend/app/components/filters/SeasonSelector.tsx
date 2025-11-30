'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { useFilterStore } from '@/lib/store/filters';

export function SeasonSelector() {
  const { season, setSeason } = useFilterStore();

  const { data: seasons, isLoading } = useQuery({
    queryKey: ['seasons'],
    queryFn: () => apiClient.getSeasons(),
  });

  if (isLoading) {
    return (
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Season
        </label>
        <div className="h-10 bg-[#1a1a1a] border border-[#333] rounded-md animate-pulse" />
      </div>
    );
  }

  return (
    <div className="w-full">
      <label
        htmlFor="season-select"
        className="block text-sm font-medium text-gray-300 mb-2"
      >
        Season
      </label>
      <select
        id="season-select"
        value={season || ''}
        onChange={(e) => setSeason(e.target.value ? Number(e.target.value) : null)}
        className="w-full px-4 py-2 bg-[#1a1a1a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6] focus:border-transparent transition-all"
      >
        <option value="">All Seasons</option>
        {seasons
          ?.sort((a, b) => b.year - a.year)
          .map((s) => (
            <option key={s.id} value={s.year}>
              {s.year}
            </option>
          ))}
      </select>
    </div>
  );
}
