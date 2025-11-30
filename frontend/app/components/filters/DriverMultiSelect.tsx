'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { apiClient } from '@/lib/api/client';
import { useFilterStore } from '@/lib/store/filters';

export function DriverMultiSelect() {
  const { season, selectedDrivers, toggleDriver, setSelectedDrivers } = useFilterStore();
  const [isOpen, setIsOpen] = useState(false);

  const { data: drivers, isLoading } = useQuery({
    queryKey: ['drivers', season],
    queryFn: () => apiClient.getDrivers(season || undefined),
  });

  const handleSelectAll = () => {
    if (drivers) {
      setSelectedDrivers(drivers);
    }
  };

  const handleClearAll = () => {
    setSelectedDrivers([]);
  };

  if (isLoading) {
    return (
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Drivers
        </label>
        <div className="h-10 bg-[#1a1a1a] border border-[#333] rounded-md animate-pulse" />
      </div>
    );
  }

  return (
    <div className="w-full relative">
      <label className="block text-sm font-medium text-gray-300 mb-2">
        Drivers
      </label>

      {/* Dropdown button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 bg-[#1a1a1a] border border-[#333] rounded-md text-left text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6] focus:border-transparent transition-all flex justify-between items-center"
      >
        <span className="truncate">
          {selectedDrivers.length === 0
            ? 'All Drivers'
            : `${selectedDrivers.length} driver${selectedDrivers.length !== 1 ? 's' : ''} selected`}
        </span>
        <svg
          className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute z-10 mt-2 w-full bg-[#1a1a1a] border border-[#333] rounded-md shadow-lg max-h-64 overflow-y-auto">
          {/* Select/Clear all buttons */}
          <div className="sticky top-0 bg-[#1a1a1a] border-b border-[#333] p-2 flex gap-2">
            <button
              type="button"
              onClick={handleSelectAll}
              className="flex-1 px-3 py-1.5 text-sm bg-[#3671C6] text-white rounded hover:bg-[#2a5ba8] transition-colors"
            >
              Select All
            </button>
            <button
              type="button"
              onClick={handleClearAll}
              className="flex-1 px-3 py-1.5 text-sm bg-[#333] text-white rounded hover:bg-[#444] transition-colors"
            >
              Clear All
            </button>
          </div>

          {/* Driver list */}
          <div className="p-2">
            {drivers && drivers.length === 0 ? (
              <p className="text-sm text-gray-500 p-2">No drivers found</p>
            ) : (
              drivers?.map((driver) => (
                <label
                  key={driver}
                  className="flex items-center px-3 py-2 hover:bg-[#2a2a2a] rounded cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedDrivers.includes(driver)}
                    onChange={() => toggleDriver(driver)}
                    className="w-4 h-4 text-[#3671C6] bg-[#0a0a0a] border-[#333] rounded focus:ring-[#3671C6] focus:ring-2"
                  />
                  <span className="ml-3 text-sm text-white font-medium">
                    {driver}
                  </span>
                </label>
              ))
            )}
          </div>
        </div>
      )}

      {/* Close dropdown when clicking outside */}
      {isOpen && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Selected count helper text */}
      {selectedDrivers.length > 0 && (
        <p className="mt-1 text-xs text-gray-500">
          {selectedDrivers.join(', ')}
        </p>
      )}
    </div>
  );
}
