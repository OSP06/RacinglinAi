export function Footer() {
  return (
    <footer className="border-t border-[#333] bg-[#0a0a0a]">
      <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-4">
          {/* About */}
          <div className="lg:col-span-2">
            <h3 className="text-lg font-semibold text-white mb-4">
              <span className="text-white">Racing</span>
              <span className="text-[#3671C6]">Line</span>
              <span className="text-white">AI</span>
            </h3>
            <p className="text-sm text-gray-400 max-w-md">
              Advanced F1 analytics powered by machine learning. Analyze 8 seasons of
              Formula 1 data with LSTM forecasting, regression analysis, and Monte Carlo
              strategy optimization.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <a href="/dashboard" className="text-sm text-gray-400 hover:text-white transition-colors">
                  Dashboard
                </a>
              </li>
              <li>
                <a href="/predictions" className="text-sm text-gray-400 hover:text-white transition-colors">
                  Predictions
                </a>
              </li>
              <li>
                <a href="/circuits" className="text-sm text-gray-400 hover:text-white transition-colors">
                  Circuits
                </a>
              </li>
              <li>
                <a href="/about" className="text-sm text-gray-400 hover:text-white transition-colors">
                  About
                </a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Resources</h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="https://github.com/osp06/racinglinai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  GitHub
                </a>
              </li>
              <li>
                <a
                  href="/api/docs"
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  API Documentation
                </a>
              </li>
              <li>
                <a
                  href="https://docs.fastf1.dev"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  FastF1 Docs
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-8 border-t border-[#333] pt-8 flex flex-col sm:flex-row justify-between items-center">
          <p className="text-sm text-gray-400">
            © {new Date().getFullYear()} RacingLineAI. Built by{' '}
            <a
              href="https://github.com/osp06"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#3671C6] hover:underline"
            >
              Om Patel
            </a>
          </p>
          <div className="flex space-x-6 mt-4 sm:mt-0">
            <a
              href="https://github.com/osp06/racinglinai"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-white transition-colors"
            >
              <span className="sr-only">GitHub</span>
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  fillRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  clipRule="evenodd"
                />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
