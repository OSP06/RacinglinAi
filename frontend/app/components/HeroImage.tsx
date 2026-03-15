'use client';

export function HeroImage() {
  return (
    <div
      className="relative aspect-video overflow-hidden rounded-2xl bg-[#1a1a1a] border border-[#333]"
      style={{ minHeight: 260 }}
    >
      {/* Placeholder — always rendered underneath; hidden by CSS once image loads */}
      <div className="absolute inset-0 flex flex-col items-center justify-center z-0">
        <svg
          className="h-20 w-20 text-gray-700"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828
               0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2
               2v12a2 2 0 002 2z"
          />
        </svg>
        <p className="mt-3 text-gray-600 text-xs">
          Add hero image → /public/images/hero.png
        </p>
      </div>

      {/* Actual image — hides itself if the file is missing */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/images/hero.png"
        alt="RacingLineAI F1 Dashboard Preview"
        className="absolute inset-0 w-full h-full object-cover rounded-2xl z-10"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
    </div>
  );
}
