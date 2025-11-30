'use client';

import React, { useState, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { TEAM_COLORS, COMPOUND_COLORS } from '@/lib/constants/colors';
import { LSTMPredictionResponse } from '@/lib/types/prediction';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface LSTMPredictorProps {
  season: number;
  grandPrix: string;
}

export function LSTMPredictor({ season, grandPrix }: LSTMPredictorProps) {
  const [selectedDriver, setSelectedDriver] = useState<string>('');
  const [selectedCompound, setSelectedCompound] = useState<string>('SOFT');
  const [forecastLaps, setForecastLaps] = useState<number>(10);

  // Fetch races
  const { data: races } = useQuery({
    queryKey: ['races', season],
    queryFn: () => apiClient.getRacesBySeason(season),
    enabled: !!season,
  });

  const race = races?.find((r) => r.gp_slug === grandPrix);

  // Fetch drivers for the race
  const { data: drivers } = useQuery({
    queryKey: ['drivers', season],
    queryFn: () => apiClient.getDrivers(season),
    enabled: !!season,
  });

  // Fetch historical laps for context
  const { data: historicalLaps } = useQuery({
    queryKey: ['laps', race?.id, selectedDriver],
    queryFn: async () => {
      if (!race?.id || !selectedDriver) return [];
      const laps = await apiClient.getLaps(race.id, { driver: selectedDriver });
      return laps;
    },
    enabled: !!race?.id && !!selectedDriver,
  });

  // Prediction mutation
  const predictionMutation = useMutation({
    mutationFn: async () => {
      if (!race?.id || !selectedDriver) {
        throw new Error('Missing required parameters');
      }

      const response = await apiClient.predictLSTM({
        race_id: race.id,
        driver: selectedDriver,
        compound: selectedCompound,
        forecast_laps: forecastLaps,
      });

      return response;
    },
  });

  // Plot data combining historical and predicted
  const plotData = useMemo(() => {
    if (!historicalLaps || historicalLaps.length === 0) return [];

    const traces: any[] = [];

    // Historical lap times
    const historicalX = historicalLaps.map((l: any) => l.lap_number);
    const historicalY = historicalLaps.map((l: any) => l.lap_time_seconds);

    traces.push({
      x: historicalX,
      y: historicalY,
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Historical Laps',
      line: {
        color: '#3671C6',
        width: 2,
      },
      marker: {
        size: 6,
      },
      hovertemplate: '<b>Lap %{x}</b><br>Time: %{y:.3f}s<br><extra></extra>',
    });

    // Predicted lap times
    if (predictionMutation.data?.predictions) {
      const predictions = predictionMutation.data.predictions;
      const predX = predictions.map((p) => p.lap_number);
      const predY = predictions.map((p) => p.predicted_lap_time);
      const predUpper = predictions.map((p) => p.confidence_upper);
      const predLower = predictions.map((p) => p.confidence_lower);

      // Confidence interval band
      traces.push({
        x: [...predX, ...predX.slice().reverse()],
        y: [...predUpper, ...predLower.slice().reverse()],
        fill: 'toself',
        fillcolor: 'rgba(54, 113, 198, 0.2)',
        line: { color: 'transparent' },
        name: '95% Confidence',
        type: 'scatter',
        hoverinfo: 'skip',
        showlegend: true,
      });

      // Predicted line
      traces.push({
        x: predX,
        y: predY,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'LSTM Prediction',
        line: {
          color: '#E8002D',
          width: 3,
          dash: 'dash',
        },
        marker: {
          size: 8,
          symbol: 'diamond',
        },
        hovertemplate: '<b>Lap %{x} (Predicted)</b><br>Time: %{y:.3f}s<br><extra></extra>',
      });
    }

    return traces;
  }, [historicalLaps, predictionMutation.data]);

  const handlePredict = () => {
    if (!selectedDriver || !race?.id) return;
    predictionMutation.mutate();
  };

  return (
    <div className="w-full bg-[#1a1a1a] rounded-lg border border-[#333] p-6">
      <h2 className="text-2xl font-bold mb-6">LSTM Lap Time Prediction</h2>
      <p className="text-gray-400 mb-6">
        Advanced neural network model with attention mechanism for lap time forecasting
      </p>

      {/* Configuration Form */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {/* Driver Selection */}
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

        {/* Compound Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Tyre Compound
          </label>
          <select
            value={selectedCompound}
            onChange={(e) => setSelectedCompound(e.target.value)}
            className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#3671C6]"
          >
            <option value="SOFT">Soft</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
            <option value="INTERMEDIATE">Intermediate</option>
            <option value="WET">Wet</option>
          </select>
        </div>

        {/* Forecast Laps */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Forecast Laps
          </label>
          <input
            type="number"
            min="1"
            max="30"
            value={forecastLaps}
            onChange={(e) => setForecastLaps(Number(e.target.value))}
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
            {predictionMutation.isPending ? 'Predicting...' : 'Predict'}
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

      {/* Model Metrics */}
      {predictionMutation.data && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-[#0a0a0a] border border-[#333] rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Model RMSE</p>
            <p className="text-2xl font-bold text-[#3671C6]">
              {predictionMutation.data.model_rmse.toFixed(3)}s
            </p>
          </div>
          <div className="bg-[#0a0a0a] border border-[#333] rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Training Laps</p>
            <p className="text-2xl font-bold text-[#27F4D2]">
              {predictionMutation.data.training_laps_used}
            </p>
          </div>
        </div>
      )}

      {/* Chart */}
      {plotData.length > 0 ? (
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
              title: { text: 'Lap Number' },
              gridcolor: '#333333',
              zerolinecolor: '#333333',
            },
            yaxis: {
              title: { text: 'Lap Time (seconds)' },
              gridcolor: '#333333',
              zerolinecolor: '#333333',
            },
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
              l: 60,
              r: 40,
              t: 80,
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
      ) : (
        <div className="h-[500px] bg-[#0a0a0a] border border-[#333] rounded-lg flex items-center justify-center">
          <div className="text-center">
            {!selectedDriver ? (
              <>
                <p className="text-gray-400 mb-2">Select a driver to begin</p>
                <p className="text-sm text-gray-500">
                  Choose parameters above and click "Predict"
                </p>
              </>
            ) : predictionMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3671C6] mx-auto mb-4"></div>
                <p className="text-gray-400">Running LSTM prediction...</p>
              </>
            ) : (
              <p className="text-gray-400">No data to display</p>
            )}
          </div>
        </div>
      )}

      {/* Info Footer */}
      <div className="mt-6 p-4 bg-[#0a0a0a] border border-[#333] rounded-lg">
        <h4 className="font-semibold mb-2 text-sm">Model Features</h4>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• Multi-layer LSTM with attention mechanism (128 → 64 hidden units)</li>
          <li>• 25+ engineered features (tyre age, fuel load, track conditions)</li>
          <li>• 95% confidence intervals using Monte Carlo dropout</li>
          <li>• Trained on {historicalLaps?.length || 0} historical laps</li>
        </ul>
      </div>
    </div>
  );
}
