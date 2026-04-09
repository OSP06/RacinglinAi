'use client';

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { COMPOUND_COLORS } from '@/lib/constants/colors';
import type { StrategyOption } from '@/lib/types/prediction';

interface StrategyOptimizerProps {
  season: number;
  grandPrix: string;
}

export function StrategyOptimizer({ season, grandPrix }: StrategyOptimizerProps) {
  const [selectedDriver, setSelectedDriver] = useState<string>('');
  const [currentLap, setCurrentLap] = useState<number>(1);
  const [availableCompounds, setAvailableCompounds] = useState<string[]>(['SOFT', 'MEDIUM', 'HARD']);

  // Fetch races to resolve race id from gp_slug
  const { data: races } = useQuery({
    queryKey: ['races', season],
    queryFn: () => apiClient.getRacesBySeason(season),
    enabled: !!season,
  });

  const race = races?.find((r) => r.gp_slug === grandPrix);

  // Fetch race-specific drivers from statistics (not season-wide)
  const { data: statistics } = useQuery({
    queryKey: ['race-statistics', race?.id],
    queryFn: () => apiClient.getRaceStatistics(race!.id),
    enabled: !!race?.id,
  });

  const drivers = statistics?.map((s) => s.driver) ?? [];

  // Prediction mutation
  const predictionMutation = useMutation({
    mutationFn: async () => {
      if (!race?.id || !selectedDriver) {
        throw new Error('Missing required parameters');
      }

      return apiClient.predictStrategy({
        race_id: race.id,
        driver: selectedDriver,
        current_lap: currentLap,
        available_compounds: availableCompounds,
      });
    },
  });

  const handleOptimize = () => {
    if (!selectedDriver || !race?.id) return;
    predictionMutation.mutate();
  };

  const toggleCompound = (compound: string) => {
    setAvailableCompounds((prev) =>
      prev.includes(compound)
        ? prev.filter((c) => c !== compound)
        : [...prev, compound]
    );
  };

  const getCompoundBadgeColor = (compound: string) => {
    return COMPOUND_COLORS[compound.toUpperCase()] || '#888888';
  };

  // Derived display values — computed once, not inside JSX
  const result = predictionMutation.data;
  const recommendedStrat: StrategyOption | null = result
    ? (result.strategies.find((s) => s.strategy_name === result.recommended_strategy) ??
       result.strategies[0])
    : null;
  const alternatives: StrategyOption[] = result
    ? result.strategies.filter((s) => s.strategy_name !== result.recommended_strategy)
    : [];

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-6">
      <h2 className="text-2xl font-bold mb-6">Strategy Optimizer</h2>
      <p className="text-gray-400 mb-6">
        Monte Carlo simulation (1000 iterations) for optimal pit stop strategy
      </p>

      {/* Race not found warning */}
      {races && !race && (
        <div className="mb-6 p-4 bg-yellow-900/20 border border-yellow-500/50 rounded-md">
          <p className="text-yellow-400 text-sm">
            No race data found for &quot;{grandPrix}&quot; in the {season} season.
          </p>
        </div>
      )}

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Driver */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Driver
          </label>
          <select
            value={selectedDriver}
            onChange={(e) => setSelectedDriver(e.target.value)}
            disabled={!race}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value="">Select driver</option>
            {drivers.map((driver) => (
              <option key={driver} value={driver}>
                {driver}
              </option>
            ))}
          </select>
        </div>

        {/* Current Lap */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Current Lap
          </label>
          <input
            type="number"
            min="1"
            max="70"
            value={currentLap}
            onChange={(e) => setCurrentLap(Number(e.target.value))}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          />
        </div>

        {/* Optimize Button */}
        <div className="flex items-end">
          <button
            onClick={handleOptimize}
            disabled={!race || !selectedDriver || availableCompounds.length === 0 || predictionMutation.isPending}
            className="w-full px-6 py-2 bg-[#3671C6] text-white font-semibold rounded-md hover:bg-[#2a5ba8] disabled:bg-[#333] disabled:cursor-not-allowed transition-colors"
          >
            {predictionMutation.isPending ? 'Optimizing...' : 'Optimize'}
          </button>
        </div>
      </div>

      {/* Available Compounds */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-300 mb-3">
          Available Tyre Compounds
        </label>
        <div className="flex flex-wrap gap-3">
          {['SOFT', 'MEDIUM', 'HARD'].map((compound) => (
            <button
              key={compound}
              onClick={() => toggleCompound(compound)}
              className={`px-4 py-2 rounded-md font-semibold text-sm transition-all ${
                availableCompounds.includes(compound)
                  ? 'opacity-100 ring-2 ring-white'
                  : 'opacity-40'
              }`}
              style={{
                backgroundColor: getCompoundBadgeColor(compound),
                color: compound === 'HARD' ? '#000000' : '#FFFFFF',
              }}
            >
              {compound}
            </button>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {predictionMutation.isError && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-500/50 rounded-md">
          <p className="text-red-400">
            ⚠️ Error optimizing strategy. Please try different parameters.
          </p>
        </div>
      )}

      {/* Results */}
      {result && recommendedStrat && (
        <div className="space-y-6">
          {/* Recommended Strategy */}
          <div className="bg-gradient-to-br from-[#3671C6]/20 to-[#0a0a0a] border-2 border-[#3671C6] rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">Recommended Strategy</h3>
              <div className="text-sm">
                <span className="text-gray-400">Safety Car Risk:</span>{' '}
                <span className="text-[#3671C6] font-bold">
                  {(result.safety_car_probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Strategy Visualization */}
            <div className="flex flex-wrap gap-2 mb-4">
              {recommendedStrat.compounds.map((compound, idx) => (
                <div
                  key={idx}
                  className="px-6 py-3 rounded-lg font-bold text-lg"
                  style={{
                    backgroundColor: getCompoundBadgeColor(compound),
                    color: compound === 'HARD' ? '#000000' : '#FFFFFF',
                  }}
                >
                  Stint {idx + 1}: {compound}
                </div>
              ))}
            </div>

            <p className="text-sm text-gray-400">
              {recommendedStrat.pit_stops.length} pit stop
              {recommendedStrat.pit_stops.length !== 1 ? 's' : ''}
            </p>
          </div>

          {/* Pit Stop Windows */}
          {recommendedStrat.pit_stops.length > 0 && (
            <div className="bg-[#0a0a0a] border border-[#333] rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Recommended Pit Windows</h3>
              <div className="space-y-3">
                {recommendedStrat.pit_stops.map((pitStop, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-[#1a1a1a] border border-[#333] rounded-md"
                  >
                    <div>
                      <p className="font-semibold">Lap {pitStop.lap_number}</p>
                      <p className="text-sm text-gray-400">
                        {pitStop.compound_from} → {pitStop.compound_to}
                        <span className="ml-2">({pitStop.expected_loss_seconds.toFixed(1)}s loss)</span>
                      </p>
                    </div>
                    <div className="w-2 h-2 bg-[#3671C6] rounded-full"></div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Alternative Strategies */}
          {alternatives.length > 0 && (
            <div className="bg-[#0a0a0a] border border-[#333] rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Alternative Strategies</h3>
              <div className="space-y-4">
                {alternatives.map((alt, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-[#1a1a1a] border border-[#333] rounded-lg hover:border-[#3671C6]/50 transition-colors"
                  >
                    {/* Strategy Name */}
                    <div className="flex items-center gap-3 mb-3">
                      <p className="font-semibold">{alt.strategy_name}</p>
                      <div className="flex flex-wrap gap-2">
                        {alt.compounds.map((compound, cIdx) => (
                          <span
                            key={cIdx}
                            className="px-3 py-1 rounded text-xs font-bold"
                            style={{
                              backgroundColor: getCompoundBadgeColor(compound),
                              color: compound === 'HARD' ? '#000000' : '#FFFFFF',
                            }}
                          >
                            {compound}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Statistics Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-400 text-xs mb-1">Expected Time</p>
                        <p className="font-semibold">{alt.expected_race_time.toFixed(2)}s</p>
                      </div>
                      <div>
                        <p className="text-gray-400 text-xs mb-1">Best Case</p>
                        <p className="font-semibold text-green-400">
                          {alt.percentile_10.toFixed(2)}s
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-400 text-xs mb-1">Worst Case</p>
                        <p className="font-semibold text-red-400">
                          {alt.percentile_90.toFixed(2)}s
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-400 text-xs mb-1">Win Probability</p>
                        <p className="font-semibold text-[#3671C6]">
                          {(alt.win_probability * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !predictionMutation.isPending && (
        <div className="h-[400px] bg-[#0a0a0a] border border-[#333] rounded-lg flex items-center justify-center">
          <div className="text-center">
            <svg
              className="mx-auto h-16 w-16 text-gray-600 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
            <p className="text-gray-400 mb-2">Configure and optimize strategy</p>
            <p className="text-sm text-gray-500">
              {!race
                ? 'No race data available for this selection'
                : !selectedDriver
                ? 'Select a driver to begin'
                : availableCompounds.length === 0
                ? 'Select at least one compound'
                : 'Click "Optimize" to see recommendations'}
            </p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {predictionMutation.isPending && (
        <div className="h-[400px] bg-[#0a0a0a] border border-[#333] rounded-lg flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
            <p className="text-gray-400">Running Monte Carlo simulation...</p>
            <p className="text-sm text-gray-500 mt-2">Testing 1000+ strategy variations</p>
          </div>
        </div>
      )}

      {/* Info Footer */}
      <div className="mt-6 p-4 bg-[#0a0a0a] border border-[#333] rounded-lg">
        <h4 className="font-semibold mb-2 text-sm">Simulation Details</h4>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• 1000 Monte Carlo iterations per strategy variant</li>
          <li>• Models tyre degradation curves (linear + cliff effect)</li>
          <li>• Accounts for fuel load reduction (~2kg/lap, ~0.03s/kg impact)</li>
          <li>• Pit stop time loss: 20-25s (randomized per simulation)</li>
          <li>• Win probability based on distribution overlap with fastest strategies</li>
        </ul>
      </div>
    </div>
  );
}
