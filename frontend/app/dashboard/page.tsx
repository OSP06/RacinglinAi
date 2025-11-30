'use client';

import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';
import { FilterPanel } from '../components/filters/FilterPanel';
import { useFilterStore } from '@/lib/store/filters';
import { GapToLeaderChart } from '../components/charts/GapToLeaderChart';
import { TyreDegradationChart } from '../components/charts/TyreDegradationChart';
import { SectorPerformanceChart } from '../components/charts/SectorPerformanceChart';
import { StintPaceChart } from '../components/charts/StintPaceChart';
import { RaceStatisticsTable } from '../components/charts/RaceStatisticsTable';

export default function DashboardPage() {
  const { season, grandPrix, selectedDrivers } = useFilterStore();

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 bg-[#0a0a0a]">
        <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
          {/* Page header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white">Race Analytics Dashboard</h1>
            <p className="mt-2 text-gray-400">
              Analyze race data, driver performance, and lap time trends
            </p>
          </div>

          {/* Filters */}
          <FilterPanel />

          {/* Content area - Charts */}
          {!season || !grandPrix ? (
            <div className="mt-8">
              <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-8">
                <div className="text-center">
                  <svg
                    className="mx-auto h-16 w-16 text-gray-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  <h3 className="mt-4 text-lg font-medium text-white">
                    Select Season and Grand Prix
                  </h3>
                  <p className="mt-2 text-sm text-gray-400">
                    Choose a season and race from the filters above to view analytics
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-8 space-y-8">
              {/* Race Statistics Table */}
              <RaceStatisticsTable
                season={season}
                grandPrix={grandPrix}
                selectedDrivers={selectedDrivers}
              />

              {/* Gap to Leader Chart - Full width */}
              <GapToLeaderChart
                season={season}
                grandPrix={grandPrix}
                selectedDrivers={selectedDrivers}
              />

              {/* Grid for other charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <TyreDegradationChart
                  season={season}
                  grandPrix={grandPrix}
                  selectedDrivers={selectedDrivers}
                />

                <StintPaceChart
                  season={season}
                  grandPrix={grandPrix}
                  selectedDrivers={selectedDrivers}
                />
              </div>

              {/* Sector Performance - Full width */}
              <SectorPerformanceChart
                season={season}
                grandPrix={grandPrix}
                selectedDrivers={selectedDrivers}
              />
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
