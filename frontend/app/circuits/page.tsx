'use client';

import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';
import { FilterPanel } from '../components/filters/FilterPanel';
import { useFilterStore } from '@/lib/store/filters';
import { CircuitVisualization } from '../components/circuits/CircuitVisualization';

export default function CircuitsPage() {
  const { season, grandPrix } = useFilterStore();

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 bg-[#0a0a0a]">
        <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white">Circuit Visualization</h1>
            <p className="mt-2 text-gray-400">
              Interactive track layouts with real-time speed data and telemetry
            </p>
          </div>

          {/* Filters */}
          <FilterPanel />

          {/* Circuit Visualization */}
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
                      d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                    />
                  </svg>
                  <h3 className="mt-4 text-lg font-medium text-white">
                    Select Season and Grand Prix
                  </h3>
                  <p className="mt-2 text-sm text-gray-400">
                    Choose a season and race from the filters above to view the circuit layout
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-8">
              <CircuitVisualization season={season} grandPrix={grandPrix} />

              {/* Additional Info Cards */}
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
                  <h3 className="font-semibold mb-2 text-sm flex items-center gap-2">
                    <span className="text-xl">🎨</span>
                    Color Coding
                  </h3>
                  <p className="text-xs text-gray-400">
                    Track sections are colored based on speed: Red (slowest/corners), Yellow (medium),
                    Green (fastest/straights). This helps identify braking zones and DRS zones.
                  </p>
                </div>

                <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
                  <h3 className="font-semibold mb-2 text-sm flex items-center gap-2">
                    <span className="text-xl">📊</span>
                    Real Data
                  </h3>
                  <p className="text-xs text-gray-400">
                    Circuit layouts are generated from actual FastF1 telemetry data, showing the exact
                    racing line and speed profiles used by drivers during the race.
                  </p>
                </div>

                <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
                  <h3 className="font-semibold mb-2 text-sm flex items-center gap-2">
                    <span className="text-xl">🖱️</span>
                    Interactive
                  </h3>
                  <p className="text-xs text-gray-400">
                    Hover over different sections of the track to see detailed speed and distance
                    information at specific points around the circuit.
                  </p>
                </div>
              </div>

              {/* Technical Details */}
              <div className="mt-6 p-4 bg-[#1a1a1a] border border-[#333] rounded-lg">
                <h3 className="font-semibold mb-3 text-sm">Visualization Technology</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-gray-400">
                  <div>
                    <p className="mb-2">
                      <span className="text-white font-semibold">D3.js Rendering:</span> Uses D3.js
                      for smooth, scalable vector graphics with interactive tooltips and animations.
                    </p>
                    <p>
                      <span className="text-white font-semibold">Speed Gradient:</span> Sequential
                      color scale (RdYlGn) maps speed values to colors for instant visual analysis.
                    </p>
                  </div>
                  <div>
                    <p className="mb-2">
                      <span className="text-white font-semibold">Smooth Curves:</span> Catmull-Rom
                      spline interpolation creates natural-looking track curves from GPS coordinates.
                    </p>
                    <p>
                      <span className="text-white font-semibold">Responsive:</span> Automatically
                      scales to fit different screen sizes while maintaining aspect ratio.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
