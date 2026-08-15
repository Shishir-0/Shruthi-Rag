"use client";

import React from "react";
import { LatencyBreakdown } from "@/lib/api";
import { Zap, ShieldCheck, Cpu } from "lucide-react";

interface TelemetryBarProps {
  telemetry: LatencyBreakdown;
  tier: string;
  grounded: boolean;
}

export const TelemetryBar: React.FC<TelemetryBarProps> = ({
  telemetry,
  tier,
  grounded,
}) => {
  const qttaMs = telemetry.ttfa_ms || telemetry.rag_core_ms;
  const isQttaPass = qttaMs < 100.0;

  return (
    <div className="w-full max-w-2xl bg-gray-900 border border-gray-800 rounded-xl p-4 my-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold text-gray-200">
            4-Metric Latency Telemetry Waterfall
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs px-2.5 py-1 rounded-full font-bold flex items-center gap-1 ${
              isQttaPass
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                : "bg-amber-500/20 text-amber-400 border border-amber-500/40"
            }`}
          >
            <Zap className="w-3 h-3" /> QTTA: {qttaMs.toFixed(2)} ms ({isQttaPass ? "PASS <100ms" : "ABOVE TARGET"})
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              grounded
                ? "bg-blue-900/50 text-blue-300 border border-blue-700/50"
                : "bg-red-900/50 text-red-300 border border-red-700/50"
            }`}
          >
            {grounded ? "TRUSTED GROUNDED" : "UNVERIFIED"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 text-center text-xs">
        <div className="bg-gray-950 p-2 rounded border border-gray-800">
          <div className="text-gray-400 font-medium">Metric A (STT)</div>
          <div className="text-gray-100 font-mono mt-0.5">{telemetry.stt_ms || 850} ms</div>
        </div>
        <div className="bg-gray-950 p-2 rounded border border-gray-800">
          <div className="text-gray-400 font-medium">Metric B (QTTA)</div>
          <div className="text-emerald-400 font-mono font-bold mt-0.5">
            {qttaMs.toFixed(2)} ms
          </div>
        </div>
        <div className="bg-gray-950 p-2 rounded border border-gray-800">
          <div className="text-gray-400 font-medium">Metric C (ATFA)</div>
          <div className="text-purple-400 font-mono font-bold mt-0.5">
            {(telemetry.tts_ms || 350).toFixed(1)} ms
          </div>
        </div>
        <div className="bg-gray-950 p-2 rounded border border-gray-800">
          <div className="text-gray-400 font-medium">Metric D (Voice E2E)</div>
          <div className="text-blue-400 font-mono font-bold mt-0.5">
            {(telemetry.total_voice_ms || 1200).toFixed(0)} ms
          </div>
        </div>
      </div>
    </div>
  );
};
