"use client";

import React, { useRef, useEffect, useState } from "react";
import { CitationItem, GroundingReport } from "@/lib/api";
import { CitationsDrawer } from "./CitationsDrawer";
import { Volume2, VolumeX, ShieldCheck, Zap } from "lucide-react";

interface AnswerCardProps {
  answer: string;
  tier: string;
  citations: CitationItem[];
  grounding: GroundingReport;
  audioBase64?: string;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({
  answer,
  tier,
  citations,
  grounding,
  audioBase64,
}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (audioBase64 && audioRef.current) {
      audioRef.current.src = `data:audio/wav;base64,${audioBase64}`;
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [audioBase64]);

  const toggleAudio = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  return (
    <div className="w-full max-w-2xl bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-2xl backdrop-blur">
      <audio
        ref={audioRef}
        onEnded={() => setIsPlaying(false)}
        onPause={() => setIsPlaying(false)}
      />

      <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-gray-100 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> SHRUTI Grounded Answer
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full bg-blue-950 text-blue-300 border border-blue-800/60 font-medium">
            {tier}
          </span>
          {audioBase64 && (
            <button
              onClick={toggleAudio}
              className={`p-2 rounded-full transition ${
                isPlaying
                  ? "bg-blue-600 text-white animate-pulse"
                  : "bg-gray-800 hover:bg-gray-700 text-gray-200"
              }`}
            >
              {isPlaying ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      <p className="text-base text-gray-100 leading-relaxed font-sans font-medium mb-4">
        {answer}
      </p>

      <CitationsDrawer citations={citations} />
    </div>
  );
};
