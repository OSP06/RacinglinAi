'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { COMPOUND_COLORS } from '@/lib/constants/colors';
import { RegressionPredictionResponse } from '@/lib/types/prediction';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface RegressionAnalyzerProps {
  season: number;
  grandPrix: string;
}

export function RegressionAnalyzer({ season, grandPrix }: RegressionAnalyzerProps) {
  const [selectedDriver, setSelectedDriver] = useState<string>('');
  const [lapNumber, setLapNumber] = useState<number>(10);
  const [compound, setCompound] = useState<string>('SOFT');
  const [tyreLife, setTyreLife] = useState<number>(5);
  const [trackTemp, setTrackTemp] = useState<number>(35);
  const [airTemp, setAirTemp] = useState<number>(25);
  const [fuelLoad, setFuelLoad] = useState<number>(50);

  // Fetch races
  const { data: races } = useQuery({
    queryKey: ['races', season],
    queryFn: () => apiClient.getRacesBySeason(season),
    enabled: !!season,
  });

  const race = races?.find((r) => r.gp_slug === grandPrix);

  // Fetch race-specific drivers from statistics
  const { data: raceStats } = useQuery({
    queryKey: ['race-statistics', race?.id],
    queryFn: () => apiClient.getRaceStatistics(race!.id),
    enabled: !!race?.id,
  });
  const drivers = raceStats?.map((s) => s.driver) ?? [];

  // Prediction mutation
  const predictionMutation = useMutation({
    mutationFn: async () => {
      if (!race?.id || !selectedDriver) {
        throw new Error('Missing required parameters');
      }

      const response = await apiClient.predictRegression({
        race_id: race.id,
        driver: selectedDriver,
        lap_number: lapNumber,
        compound: compound,
        tyre_life: tyreLife,
        track_temp: trackTemp,
        air_temp: airTemp,
        fuel_load: fuelLoad,
      });

      return response;
    },
  });

  const handlePredict = () => {
    if (!selectedDriver || !race?.id) return;
    predictionMutation.mutate();
  };

  // Feature importance chart data
  const featureImportancePlot = predictionMutation.data?.feature_importances
    ? [{
        y: predictionMutation.data.feature_importances.map((f) => f.feature),
        x: predictionMutation.data.feature_importances.map((f) => f.importance * 100),
        type: 'bar' as const,
        orientation: 'h' as const,
        marker: {
          color: predictionMutation.data.feature_importances.map((f) => {
            const importance = f.importance;
            if (importance > 0.15) return '#E8002D';
            if (importance > 0.10) return '#FF8000';
            if (importance > 0.05) return '#3671C6';
            return '#27F4D2';
          }),
        },
        hovertemplate: '<b>%{y}</b><br>Importance: %{x:.2f}%<br><extra></extra>',
      }]
    : [];

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-6">
      <h2 className="text-2xl font-bold mb-6">Regression Analysis</h2>
      <p className="text-gray-400 mb-6">
        LightGBM gradient boosting with 40+ engineered features for single-lap prediction
      </p>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Driver */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Driver
          </label>
          <select
            value={selectedDriver}
            onChange={(e) => setSelectedDriver(e.target.value)}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          >
            <option value="">Select driver</option>
            {drivers?.map((driver) => (
              <option key={driver} value={driver}>
                {driver}
              </option>
            ))}
          </select>
        </div>

        {/* Lap Number */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Lap Number
          </label>
          <input
            type="number"
            min="1"
            max="70"
            value={lapNumber}
            onChange={(e) => setLapNumber(Number(e.target.value))}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          />
        </div>

        {/* Compound */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Tyre Compound
          </label>
          <select
            value={compound}
            onChange={(e) => setCompound(e.target.value)}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          >
            <option value="SOFT">Soft</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
          </select>
        </div>

        {/* Tyre Life */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Tyre Life (laps)
          </label>
          <input
            type="number"
            min="1"
            max="40"
            value={tyreLife}
            onChange={(e) => setTyreLife(Number(e.target.value))}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          />
        </div>

        {/* Track Temp */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Track Temp (°C)
          </label>
          <input
            type="number"
            min="10"
            max="60"
            value={trackTemp}
            onChange={(e) => setTrackTemp(Number(e.target.value))}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          />
        </div>

        {/* Air Temp */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Air Temp (°C)
          </label>
          <input
            type="number"
            min="0"
            max="45"
            value={airTemp}
            onChange={(e) => setAirTemp(Number(e.target.value))}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          />
        </div>

        {/* Fuel Load */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Fuel Load (kg)
          </label>
          <input
            type="number"
            min="0"
            max="110"
            value={fuelLoad}
            onChange={(e) => setFuelLoad(Number(e.target.value))}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          />
        </div>

        {/* Predict Button */}
        <div className="flex items-end">
          <button
            onClick={handlePredict}
            disabled={!selectedDriver || predictionMutation.isPending}
            className="w-full px-6 py-2 bg-[#3671C6] text-white font-semibold rounded-md hover:bg-[#2a5ba8] disabled:bg-[#333] disabled:cursor-not-allowed transition-colors"
          >
            {predictionMutation.isPending ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {predictionMutation.isError && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-500/50 rounded-md">
          <p className="text-red-400">
            ⚠️ Error making prediction. Please try different parameters.
          </p>
        </div>
      )}

      {/* Results Grid */}
      {predictionMutation.data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Prediction Result Card */}
          <div className="bg-[#0a0a0a] border border-[#333] rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Predicted Lap Time</h3>
            <div className="text-center mb-6">
              <p className="text-5xl font-bold text-[#3671C6] mb-2">
                {predictionMutation.data.predicted_lap_time.toFixed(3)}s
              </p>
              {predictionMutation.data.actual_lap_time && (
                <p className="text-sm text-gray-400">
                  Actual: {predictionMutation.data.actual_lap_time.toFixed(3)}s
                  {predictionMutation.data.prediction_error && (
                    <span className="ml-2">
                      (Error: {Math.abs(predictionMutation.data.prediction_error).toFixed(3)}s)
                    </span>
                  )}
                </p>
              )}
            </div>

            {/* Model Metrics */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Model RMSE</span>
                <span className="font-semibold">
                  {predictionMutation.data.model_rmse.toFixed(3)}s
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">R² Score</span>
                <span className="font-semibold">
                  {predictionMutation.data.model_r2.toFixed(3)}
                </span>
              </div>
            </div>

            {/* Input Summary */}
            <div className="mt-6 pt-6 border-t border-[#333]">
              <h4 className="text-sm font-semibold mb-3">Input Parameters</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-400">Lap:</span>{' '}
                  <span className="text-white">{lapNumber}</span>
                </div>
                <div>
                  <span className="text-gray-400">Compound:</span>{' '}
                  <span className="text-white">{compound}</span>
                </div>
                <div>
                  <span className="text-gray-400">Tyre Life:</span>{' '}
                  <span className="text-white">{tyreLife} laps</span>
                </div>
                <div>
                  <span className="text-gray-400">Track Temp:</span>{' '}
                  <span className="text-white">{trackTemp}°C</span>
                </div>
                <div>
                  <span className="text-gray-400">Air Temp:</span>{' '}
                  <span className="text-white">{airTemp}°C</span>
                </div>
                <div>
                  <span className="text-gray-400">Fuel Load:</span>{' '}
                  <span className="text-white">{fuelLoad}kg</span>
                </div>
              </div>
            </div>
          </div>

          {/* Feature Importance Chart */}
          <div className="bg-[#0a0a0a] border border-[#333] rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Feature Importance</h3>
            {featureImportancePlot.length > 0 ? (
              <Plot
                data={featureImportancePlot}
                layout={{
                  autosize: true,
                  height: 400,
                  paper_bgcolor: '#0a0a0a',
                  plot_bgcolor: '#0a0a0a',
                  font: {
                    color: '#ffffff',
                    family: 'Inter, system-ui, sans-serif',
                    size: 11,
                  },
                  xaxis: {
                    title: { text: 'Importance (%)' },
                    gridcolor: '#333333',
                  },
                  yaxis: {
                    title: { text: '' },
                    gridcolor: '#333333',
                    automargin: true,
                  },
                  margin: {
                    l: 120,
                    r: 20,
                    t: 20,
                    b: 60,
                  },
                  showlegend: false,
                }}
                config={{
                  responsive: true,
                  displayModeBar: false,
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
              />
            ) : (
              <div className="h-[400px] flex items-center justify-center">
                <p className="text-gray-500">No data available</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!predictionMutation.data && !predictionMutation.isPending && (
        <div className="h-[400px] bg-[#0a0a0a] border border-[#333] rounded-lg flex items-center justify-center">
          <div className="text-center">
            <p className="text-gray-400 mb-2">Configure parameters and analyze</p>
            <p className="text-sm text-gray-500">
              {!selectedDriver
                ? 'Select a driver to begin'
                : 'Click "Analyze" to see prediction'}
            </p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {predictionMutation.isPending && (
        <div className="h-[400px] bg-[#0a0a0a] border border-[#333] rounded-lg flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
            <p className="text-gray-400">Running regression analysis...</p>
          </div>
        </div>
      )}

      {/* Info Footer */}
      <div className="mt-6 p-4 bg-[#0a0a0a] border border-[#333] rounded-lg">
        <h4 className="font-semibold mb-2 text-sm">Model Features (40+)</h4>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• Physical factors: Fuel load, air density, wind effects (headwind/crosswind)</li>
          <li>• Tyre modeling: Non-linear degradation, warmup phase, cliff detection</li>
          <li>• Track evolution: Rubber buildup, grip improvement over race</li>
          <li>• Driver context: Historical pace, team performance, circuit familiarity</li>
        </ul>
      </div>
    </div>
  );
}
