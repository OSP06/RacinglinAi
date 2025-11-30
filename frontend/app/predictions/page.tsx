'use client';

import { useState } from 'react';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';
import { FilterPanel } from '../components/filters/FilterPanel';
import { useFilterStore } from '@/lib/store/filters';
import { LSTMPredictor } from '../components/predictions/LSTMPredictor';
import { RegressionAnalyzer } from '../components/predictions/RegressionAnalyzer';
import { StrategyOptimizer } from '../components/predictions/StrategyOptimizer';

type PredictionTab = 'lstm' | 'regression' | 'strategy';

export default function PredictionsPage() {
  const { season, grandPrix } = useFilterStore();
  const [activeTab, setActiveTab] = useState<PredictionTab>('lstm');

  const tabs = [
    { id: 'lstm' as PredictionTab, label: 'LSTM Forecast', icon: '📈' },
    { id: 'regression' as PredictionTab, label: 'Regression Analysis', icon: '🎯' },
    { id: 'strategy' as PredictionTab, label: 'Strategy Optimizer', icon: '🏁' },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 bg-[#0a0a0a]">
        <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white">ML Predictions</h1>
            <p className="mt-2 text-gray-400">
              Advanced machine learning models for lap time prediction and race strategy optimization
            </p>
          </div>

          {/* Filters */}
          <FilterPanel />

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
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                  <h3 className="mt-4 text-lg font-medium text-white">
                    Select Season and Grand Prix
                  </h3>
                  <p className="mt-2 text-sm text-gray-400">
                    Choose a season and race from the filters above to access ML predictions
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-8">
              {/* Tabs */}
              <div className="border-b border-[#333] mb-6">
                <div className="flex flex-wrap gap-2">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-6 py-3 font-semibold text-sm transition-all rounded-t-lg ${
                        activeTab === tab.id
                          ? 'bg-[#1a1a1a] text-white border-t-2 border-l-2 border-r-2 border-[#3671C6]'
                          : 'bg-transparent text-gray-400 hover:text-white hover:bg-[#1a1a1a]/50'
                      }`}
                    >
                      <span className="mr-2">{tab.icon}</span>
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tab Content */}
              <div className="min-h-[600px]">
                {activeTab === 'lstm' && (
                  <LSTMPredictor season={season} grandPrix={grandPrix} />
                )}
                {activeTab === 'regression' && (
                  <RegressionAnalyzer season={season} grandPrix={grandPrix} />
                )}
                {activeTab === 'strategy' && (
                  <StrategyOptimizer season={season} grandPrix={grandPrix} />
                )}
              </div>

              {/* Model Comparison Info */}
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
                  <div className="text-2xl mb-2">📈</div>
                  <h3 className="font-semibold mb-2">LSTM Forecast</h3>
                  <p className="text-sm text-gray-400">
                    Multi-lap sequence prediction using deep learning with attention mechanism.
                    Best for forecasting race pace trends.
                  </p>
                  <div className="mt-4 text-xs text-gray-500">
                    <p>• 25+ features</p>
                    <p>• 95% confidence intervals</p>
                    <p>• 10-30 lap forecasts</p>
                  </div>
                </div>

                <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
                  <div className="text-2xl mb-2">🎯</div>
                  <h3 className="font-semibold mb-2">Regression Analysis</h3>
                  <p className="text-sm text-gray-400">
                    Single-lap prediction with feature importance analysis using LightGBM.
                    Best for what-if scenarios.
                  </p>
                  <div className="mt-4 text-xs text-gray-500">
                    <p>• 40+ engineered features</p>
                    <p>• Feature importance ranking</p>
                    <p>• Interpretable results</p>
                  </div>
                </div>

                <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
                  <div className="text-2xl mb-2">🏁</div>
                  <h3 className="font-semibold mb-2">Strategy Optimizer</h3>
                  <p className="text-sm text-gray-400">
                    Monte Carlo simulation testing 1000+ strategy variations to find optimal pit stops.
                  </p>
                  <div className="mt-4 text-xs text-gray-500">
                    <p>• 1000 iterations/strategy</p>
                    <p>• Win probability analysis</p>
                    <p>• Pit window recommendations</p>
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
