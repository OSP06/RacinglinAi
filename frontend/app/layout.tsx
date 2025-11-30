import type { Metadata } from "next";
// import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

// Temporarily disabled Google Fonts due to network restrictions
// const inter = Inter({
//   subsets: ["latin"],
//   display: "swap",
//   variable: "--font-inter",
// });

export const metadata: Metadata = {
  title: "RacingLineAI - Advanced F1 Analytics & Predictions",
  description: "AI-powered Formula 1 race analytics with LSTM forecasting, regression analysis, and strategy optimization. Explore 8 seasons of F1 data with interactive visualizations.",
  keywords: ["F1", "Formula 1", "Analytics", "AI", "Machine Learning", "LSTM", "Racing", "Predictions"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased bg-[#0a0a0a] text-white min-h-screen">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
