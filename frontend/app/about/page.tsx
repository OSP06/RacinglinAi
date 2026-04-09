import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 bg-[#0a0a0a]">
        <div className="mx-auto max-w-4xl px-4 py-16 lg:px-8">

          {/* Hero */}
          <div className="mb-16">
            <h1 className="text-4xl font-bold text-white mb-4">About RacingLineAI</h1>
            <p className="text-lg text-gray-400 leading-8">
              An open-source Formula 1 analytics platform combining eight seasons of
              FastF1 telemetry data with production-grade machine learning models.
            </p>
          </div>

          {/* What it is */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-white mb-6">What is RacingLineAI?</h2>
            <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-8 text-gray-300 leading-7 space-y-4">
              <p>
                RacingLineAI v8.4 is an advanced interactive dashboard for analysing,
                visualising, and predicting Formula 1 race data. It covers every Grand
                Prix from the 2018 through 2025 seasons — over 178 000 individual laps.
              </p>
              <p>
                The platform is built in two layers: a <strong className="text-white">FastAPI backend</strong> that
                serves pre-processed lap data from a PostgreSQL database and runs the
                ML models, and a <strong className="text-white">Next.js 15 frontend</strong> that renders
                interactive Plotly and D3 charts.
              </p>
            </div>
          </section>

          {/* ML Models */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-white mb-6">Predictive Models</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  icon: '📈',
                  name: 'LSTM Forecast',
                  desc: 'Multi-layer LSTM with multi-head attention (128→64 hidden units). Trained on 25+ engineered features including fuel load, tyre warmup state, track evolution, and DRS context. Generates 95% confidence intervals via Monte Carlo dropout.',
                  stats: ['RMSE ~0.35 s', '25+ features', '10–30 lap horizon'],
                },
                {
                  icon: '🎯',
                  name: 'LightGBM Regression',
                  desc: 'Gradient-boosted tree ensemble for single-lap prediction. Captures non-linear tyre cliff effects, wind components, fuel-mass penalties, and sector balance deltas. Feature importance is returned with every prediction.',
                  stats: ['RMSE ~0.28 s', 'R² 0.95', '40+ features'],
                },
                {
                  icon: '🏁',
                  name: 'Strategy Optimizer',
                  desc: 'Monte Carlo simulation (1 000 iterations per strategy) evaluates 1- and 2-stop options across all available compounds. Accounts for tyre degradation curves, cliff effects, safety-car probability, fuel burn, and pit-loss variance.',
                  stats: ['1 000 simulations', 'P10/P90 bounds', 'Win probability'],
                },
              ].map((m) => (
                <div key={m.name} className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
                  <div className="text-3xl mb-3">{m.icon}</div>
                  <h3 className="text-lg font-semibold text-white mb-2">{m.name}</h3>
                  <p className="text-sm text-gray-400 mb-4 leading-6">{m.desc}</p>
                  <ul className="space-y-1">
                    {m.stats.map((s) => (
                      <li key={s} className="text-xs text-[#3671C6] font-mono">• {s}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          {/* Tech Stack */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-white mb-6">Tech Stack</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  title: 'Backend',
                  items: [
                    'FastAPI + Uvicorn',
                    'PostgreSQL + SQLAlchemy',
                    'PyTorch (LSTM model)',
                    'LightGBM (regression)',
                    'FastF1 (telemetry)',
                    'Pydantic v2 schemas',
                  ],
                },
                {
                  title: 'Frontend',
                  items: [
                    'Next.js 14 (App Router)',
                    'TypeScript + Tailwind CSS',
                    'Plotly.js + D3.js',
                    'TanStack Query',
                    'Zustand (state)',
                    'Axios API client',
                  ],
                },
              ].map((col) => (
                <div key={col.title} className="bg-[#1a1a1a] border border-[#333] rounded-lg p-6">
                  <h3 className="font-semibold text-white mb-4">{col.title}</h3>
                  <ul className="space-y-2">
                    {col.items.map((item) => (
                      <li key={item} className="text-sm text-gray-400 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#3671C6] inline-block" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          {/* Data */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-white mb-6">Data</h2>
            <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-8 text-gray-300 leading-7 space-y-4">
              <p>
                Race data is sourced from the{' '}
                <a
                  href="https://docs.fastf1.dev"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#3671C6] hover:underline"
                >
                  FastF1
                </a>{' '}
                Python library, which provides official timing, telemetry, and weather
                data for every session since 2018. The CSV pipeline processes and
                normalises each season into a PostgreSQL database, with per-lap records
                containing sector times, tyre state, speed traps, and track conditions.
              </p>
              <p>
                Circuit layouts are generated on-the-fly from the fastest lap's GPS
                telemetry and cached locally so the D3 renderer stays fast.
              </p>
            </div>
          </section>

          {/* Author */}
          <section>
            <h2 className="text-2xl font-bold text-white mb-6">Author</h2>
            <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-8 flex items-center gap-6">
              <div className="h-14 w-14 rounded-full bg-[#3671C6] flex items-center justify-center text-2xl font-bold text-white flex-shrink-0">
                OP
              </div>
              <div>
                <p className="text-white font-semibold text-lg">Om Patel</p>
                <p className="text-gray-400 text-sm mt-1">
                  Full-stack & backend engineer. F1 enthusiast. AWS Certified Developer.
                </p>
                <a
                  href="https://github.com/osp06/racinglinai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-3 text-sm text-[#3671C6] hover:underline"
                >
                  github.com/osp06/racinglinai →
                </a>
              </div>
            </div>
          </section>

        </div>
      </main>

      <Footer />
    </div>
  );
}
