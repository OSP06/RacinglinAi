import Image from 'next/image';
import Link from 'next/link';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-gradient-to-b from-[#0a0a0a] to-[#1a1a1a] py-20 sm:py-32">
          <div className="mx-auto max-w-7xl px-4 lg:px-8">
            <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:gap-8 items-center">
              {/* Text Content */}
              <div className="max-w-2xl">
                <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
                  AI-Powered{' '}
                  <span className="text-[#3671C6]">Formula 1</span>{' '}
                  Analytics
                </h1>
                <p className="mt-6 text-lg leading-8 text-gray-300">
                  Explore 8 seasons of F1 data with advanced machine learning models.
                  LSTM forecasting, regression analysis, and Monte Carlo strategy
                  optimization — all in one platform.
                </p>
                <div className="mt-10 flex items-center gap-x-6">
                  <Link
                    href="/dashboard"
                    className="rounded-md bg-[#3671C6] px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-[#2a5ba8] transition-colors"
                  >
                    Explore Dashboard
                  </Link>
                  <Link
                    href="/about"
                    className="text-base font-semibold leading-7 text-white hover:text-gray-300 transition-colors"
                  >
                    Learn more <span aria-hidden="true">→</span>
                  </Link>
                </div>

                {/* Stats */}
                <div className="mt-12 grid grid-cols-3 gap-8 border-t border-[#333] pt-8">
                  <div>
                    <p className="text-3xl font-bold text-[#3671C6]">178K+</p>
                    <p className="text-sm text-gray-400">Laps Analyzed</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-[#3671C6]">8</p>
                    <p className="text-sm text-gray-400">F1 Seasons</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-[#3671C6]">95%</p>
                    <p className="text-sm text-gray-400">ML Accuracy</p>
                  </div>
                </div>
              </div>

              {/* Hero Image */}
              <div className="relative lg:mt-0 flex justify-center items-center">
                <div className="relative w-full max-w-[1024px] aspect-square">
                  <Image
                    src="/images/hero.png"
                    alt="RacingLineAI Dashboard Preview"
                    width={1024}
                    height={1024}
                    className="w-full h-full"
                    priority
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="bg-[#0a0a0a] py-24 sm:py-32">
          <div className="mx-auto max-w-7xl px-4 lg:px-8">
            <div className="mx-auto max-w-2xl lg:text-center">
              <h2 className="text-base font-semibold leading-7 text-[#3671C6]">
                Advanced Analytics
              </h2>
              <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Everything you need to analyze F1 races
              </p>
              <p className="mt-6 text-lg leading-8 text-gray-300">
                Powered by state-of-the-art machine learning models and comprehensive
                telemetry data from FastF1.
              </p>
            </div>
            <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
              <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
                {/* Feature 1 */}
                <div className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-[#3671C6]">
                      <svg
                        className="h-6 w-6 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6"
                        />
                      </svg>
                    </div>
                    LSTM Forecasting
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      Multi-layer LSTM with attention mechanism predicts lap times up
                      to 15 laps ahead with 95% accuracy. Includes confidence intervals.
                    </p>
                  </dd>
                </div>

                {/* Feature 2 */}
                <div className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-[#3671C6]">
                      <svg
                        className="h-6 w-6 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
                        />
                      </svg>
                    </div>
                    Strategy Optimization
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      Monte Carlo simulation with 1000 iterations predicts optimal pit
                      strategies. See win probabilities and risk scores for each option.
                    </p>
                  </dd>
                </div>

                {/* Feature 3 */}
                <div className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-[#3671C6]">
                      <svg
                        className="h-6 w-6 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941"
                        />
                      </svg>
                    </div>
                    Regression Analysis
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      LightGBM model with 40+ features analyzes lap times. See feature
                      importance and understand which factors matter most.
                    </p>
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="bg-gradient-to-b from-[#1a1a1a] to-[#0a0a0a] py-24">
          <div className="mx-auto max-w-7xl px-4 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Ready to dive into F1 analytics?
              </h2>
              <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-gray-300">
                Start exploring race data, analyzing driver performance, and making
                predictions with our advanced ML models.
              </p>
              <div className="mt-10 flex items-center justify-center gap-x-6">
                <Link
                  href="/dashboard"
                  className="rounded-md bg-[#3671C6] px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-[#2a5ba8] transition-colors"
                >
                  Get Started
                </Link>
                <a
                  href="https://github.com/osp06/racinglinai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-base font-semibold leading-7 text-white hover:text-gray-300 transition-colors"
                >
                  View on GitHub <span aria-hidden="true">→</span>
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
