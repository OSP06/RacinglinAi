'use client';

import { SeasonSelector } from './SeasonSelector';
import { GrandPrixSelector } from './GrandPrixSelector';
import { DriverMultiSelect } from './DriverMultiSelect';
import { useFilterStore } from '@/lib/store/filters';

export function FilterPanel() {
  const { clearFilters, season, grandPrix, selectedDrivers } = useFilterStore();

  const hasActiveFilters = season || grandPrix || selectedDrivers.length > 0;

  return (
    <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white">Filters</h2>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Clear All
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SeasonSelector />
        <GrandPrixSelector />
        <DriverMultiSelect />
      </div>

      {/* Active filters summary */}
      {hasActiveFilters && (
        <div className="mt-4 pt-4 border-t border-[#333]">
          <p className="text-sm text-gray-400">
            Active filters:{' '}
            <span className="text-white">
              {season && `${season}`}
              {grandPrix && ` • ${grandPrix}`}
              {selectedDrivers.length > 0 &&
                ` • ${selectedDrivers.length} driver${selectedDrivers.length !== 1 ? 's' : ''}`}
            </span>
          </p>
        </div>
      )}
    </div>
  );
}
