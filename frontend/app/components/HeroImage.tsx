'use client';

import Image from 'next/image';

export function HeroImage() {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-[#333] shadow-2xl">
      <Image
        src="/images/Hero.png"
        alt="RacingLineAI F1 Dashboard Preview"
        width={1376}
        height={768}
        className="w-full h-auto rounded-2xl"
        priority
      />
    </div>
  );
}
