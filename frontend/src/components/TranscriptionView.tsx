"use client";

import React from "react";
import { Globe, Sparkles } from "lucide-react";

interface TranscriptionViewProps {
  queryText: string;
  language: string;
  classification: string;
}

const LANG_MAP: Record<string, string> = {
  hi: "Hindi (हिंदी)",
  gu: "Gujarati (ગુજરાતી)",
  bn: "Bengali (বাংলা)",
  ta: "Tamil (தமிழ்)",
  en: "English",
  te: "Telugu",
  mr: "Marathi",
  pa: "Punjabi",
};

export const TranscriptionView: React.FC<TranscriptionViewProps> = ({
  queryText,
  language,
  classification,
}) => {
  if (!queryText) return null;

  return (
    <div className="w-full max-w-2xl bg-gray-900/80 border border-gray-800 rounded-xl p-4 my-4 backdrop-blur shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs uppercase tracking-wider text-gray-400 font-semibold flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" /> Live Transcript
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-900/50 text-blue-300 border border-blue-700/50 flex items-center gap-1">
            <Globe className="w-3 h-3" /> {LANG_MAP[language] || language.toUpperCase()}
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-900/40 text-emerald-400 border border-emerald-700/40">
            {classification}
          </span>
        </div>
      </div>
      <p className="text-lg font-medium text-gray-100 italic">"{queryText}"</p>
    </div>
  );
};
