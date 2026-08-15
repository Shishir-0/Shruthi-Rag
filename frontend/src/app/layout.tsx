import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SHRUTI — Voice-First Multilingual RAG",
  description: "Sub-50ms Voice Enabled Multilingual Retrieval-Augmented Generation System for India (HH Goa 2026 Task #2)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
