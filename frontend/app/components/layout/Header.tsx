'use client';

import Link from 'next/link';
import { useState } from 'react';

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#333] bg-[#0a0a0a]/95 backdrop-blur supports-[backdrop-filter]:bg-[#0a0a0a]/60">
      <nav className="mx-auto flex max-w-7xl items-center justify-between p-4 lg:px-8">
        {/* Logo */}
        <div className="flex lg:flex-1">
          <Link href="/" className="-m-1.5 p-1.5">
            <span className="text-2xl font-bold">
              <span className="text-white">Racing</span>
              <span className="text-[#3671C6]">Line</span>
              <span className="text-white">AI</span>
            </span>
          </Link>
        </div>

        {/* Mobile menu button */}
        <div className="flex lg:hidden">
          <button
            type="button"
            className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-gray-400"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span className="sr-only">Open main menu</span>
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d={
                  mobileMenuOpen
                    ? 'M6 18L18 6M6 6l12 12'
                    : 'M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5'
                }
              />
            </svg>
          </button>
        </div>

        {/* Desktop navigation */}
        <div className="hidden lg:flex lg:gap-x-8">
          <Link
            href="/dashboard"
            className="text-sm font-semibold leading-6 text-gray-300 hover:text-white transition-colors"
          >
            Dashboard
          </Link>
          <Link
            href="/predictions"
            className="text-sm font-semibold leading-6 text-gray-300 hover:text-white transition-colors"
          >
            Predictions
          </Link>
          <Link
            href="/circuits"
            className="text-sm font-semibold leading-6 text-gray-300 hover:text-white transition-colors"
          >
            Circuits
          </Link>
          <Link
            href="/about"
            className="text-sm font-semibold leading-6 text-gray-300 hover:text-white transition-colors"
          >
            About
          </Link>
        </div>

        {/* CTA button */}
        <div className="hidden lg:flex lg:flex-1 lg:justify-end">
          <a
            href="https://github.com/osp06/racinglinai"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md bg-[#3671C6] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#2a5ba8] transition-colors"
          >
            View on GitHub
          </a>
        </div>
      </nav>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden">
          <div className="space-y-2 px-4 pb-3 pt-2">
            <Link
              href="/dashboard"
              className="block rounded-md px-3 py-2 text-base font-medium text-gray-300 hover:bg-[#1a1a1a] hover:text-white"
              onClick={() => setMobileMenuOpen(false)}
            >
              Dashboard
            </Link>
            <Link
              href="/predictions"
              className="block rounded-md px-3 py-2 text-base font-medium text-gray-300 hover:bg-[#1a1a1a] hover:text-white"
              onClick={() => setMobileMenuOpen(false)}
            >
              Predictions
            </Link>
            <Link
              href="/circuits"
              className="block rounded-md px-3 py-2 text-base font-medium text-gray-300 hover:bg-[#1a1a1a] hover:text-white"
              onClick={() => setMobileMenuOpen(false)}
            >
              Circuits
            </Link>
            <Link
              href="/about"
              className="block rounded-md px-3 py-2 text-base font-medium text-gray-300 hover:bg-[#1a1a1a] hover:text-white"
              onClick={() => setMobileMenuOpen(false)}
            >
              About
            </Link>
            <a
              href="https://github.com/osp06/racinglinai"
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-md bg-[#3671C6] px-3 py-2 text-base font-medium text-white hover:bg-[#2a5ba8]"
            >
              View on GitHub
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
