"use client";

import React, { useState } from "react";
import { CitationItem } from "@/lib/api";
import { BookOpen, ChevronRight, FileText, CheckCircle } from "lucide-react";

interface CitationsDrawerProps {
  citations: CitationItem[];
}

export const CitationsDrawer: React.FC<CitationsDrawerProps> = ({ citations }) => {
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(null);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-4 border-t border-gray-800 pt-4">
      <div className="flex items-center gap-2 mb-3">
        <BookOpen className="w-4 h-4 text-blue-400" />
        <span className="text-sm font-semibold text-gray-200">
          Grounded Sources ({citations.length})
        </span>
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {citations.map((c) => (
          <button
            key={c.citation_id}
            onClick={() => setSelectedCitation(selectedCitation?.citation_id === c.citation_id ? null : c)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-all flex items-center gap-1.5 ${
              selectedCitation?.citation_id === c.citation_id
                ? "bg-blue-600 text-white border-blue-500 shadow-md"
                : "bg-gray-900 hover:bg-gray-800 text-gray-300 border-gray-800"
            }`}
          >
            <span className="font-bold">{c.citation_id}</span>
            <span className="max-w-[140px] truncate">{c.title}</span>
            <ChevronRight className="w-3 h-3 text-gray-400" />
          </button>
        ))}
      </div>

      {selectedCitation && (
        <div className="bg-gray-950 border border-gray-800 rounded-xl p-4 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-semibold text-gray-200">{selectedCitation.title}</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-gray-400 font-mono">
              <span>Lang: {selectedCitation.language}</span>
              <span>Chunk: {selectedCitation.chunk_id}</span>
            </div>
          </div>

          <p className="text-xs text-gray-300 leading-relaxed mb-3 font-sans">
            "{selectedCitation.text}"
          </p>

          <div className="grid grid-cols-4 gap-2 text-[11px] font-mono bg-gray-900 p-2 rounded border border-gray-800 text-center">
            <div>
              <div className="text-gray-400">Dense Score</div>
              <div className="text-blue-400 font-bold">{selectedCitation.dense_score}</div>
            </div>
            <div>
              <div className="text-gray-400">BM25 Score</div>
              <div className="text-emerald-400 font-bold">{selectedCitation.bm25_score}</div>
            </div>
            <div>
              <div className="text-gray-400">Rerank Score</div>
              <div className="text-purple-400 font-bold">{selectedCitation.rerank_score}</div>
            </div>
            <div>
              <div className="text-gray-400">Final Score</div>
              <div className="text-amber-400 font-bold">{selectedCitation.final_score}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
