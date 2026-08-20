"use client";

import React, { useState } from "react";
import { VoiceRecorder } from "@/components/VoiceRecorder";
import { TranscriptionView } from "@/components/TranscriptionView";
import { AnswerCard } from "@/components/AnswerCard";
import { TelemetryBar } from "@/components/TelemetryBar";
import { EngineeringMode } from "@/components/EngineeringMode";
import { sendTextQuery, QueryResponse } from "@/lib/api";
import { Search, Sparkles } from "lucide-react";

export default function Home() {
  const [queryText, setQueryText] = useState("");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [selectedLang, setSelectedLang] = useState("hi-IN");
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);

  const sampleQueries = [
    { text: "आयुष्मान भारत डिजिटल मिशन क्या है?", lang: "hi-IN", label: "Hindi (हिंदी)" },
    { text: "ગિફ્ટ સિટી ગાંધીનગર ક્યાં આવેલું છે?", lang: "gu-IN", label: "Gujarati (ગુજરાતી)" },
    { text: "সুন্দরবন ম্যানগ্রোভ বন কোথায় অবস্থিত?", lang: "bn-IN", label: "Bengali (বাংলা)" },
    { text: "தஞ்சாவூர் பிருகதீஸ்வரர் கோவில் யார் கட்டியது?", lang: "ta-IN", label: "Tamil (தமிழ்)" },
    { text: "What is India's renewable energy target by 2030?", lang: "en-IN", label: "English" },
  ];

  const handleQueryResponse = (res: QueryResponse) => {
    setResponse(res);
    setQueryText(res.original_query);
    setLiveTranscript(res.original_query);
    setIsProcessing(false);
  };

  const handleTranscriptPartial = (text: string, lang: string) => {
    setLiveTranscript(text);
    setQueryText(text);
  };

  const handleTranscriptFinal = (text: string, lang: string) => {
    setLiveTranscript(text);
    setQueryText(text);
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) return;
    setIsProcessing(true);
    try {
      const res = await sendTextQuery(queryText, selectedLang.split("-")[0]);
      setResponse(res);
      setLiveTranscript(queryText);
    } catch (err) {
      console.error("Text Query Error:", err);
      alert("Failed to process text query.");
    } finally {
      setIsProcessing(false);
    }
  };

  const triggerSampleQuery = async (text: string, lang: string) => {
    setQueryText(text);
    setSelectedLang(lang);
    setLiveTranscript(text);
    setIsProcessing(true);
    try {
      const res = await sendTextQuery(text, lang.split("-")[0]);
      setResponse(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-6 md:p-12 relative overflow-hidden bg-background text-gray-100">
      {/* Glow Effects */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 -right-40 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="flex flex-col items-center text-center mb-8 z-10 max-w-2xl">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-950/60 border border-blue-800/50 text-blue-400 text-xs font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5" /> HH Goa 2026 Task #2 Production Submission
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 via-indigo-300 to-emerald-400 bg-clip-text text-transparent">
          SHRUTI
        </h1>
        <p className="text-sm md:text-base text-gray-400 mt-2 font-medium">
          Sub-200ms Voice-First Multilingual RAG Engine for India
        </p>
      </header>

      {/* Voice Recorder & Form */}
      <div className="w-full max-w-2xl flex flex-col items-center z-10">
        <VoiceRecorder
          onQueryResponse={handleQueryResponse}
          onTranscriptPartial={handleTranscriptPartial}
          onTranscriptFinal={handleTranscriptFinal}
          selectedLanguageHint={selectedLang}
          isProcessing={isProcessing}
        />

        {/* Text Input Fallback */}
        <form onSubmit={handleTextSubmit} className="w-full relative mt-2">
          <input
            type="text"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="Or type a question in Hindi, Gujarati, Bengali, Tamil, English..."
            disabled={isProcessing}
            className="w-full py-3.5 pl-4 pr-12 rounded-xl bg-gray-900/90 border border-gray-800 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 transition shadow-inner text-sm"
          />
          <button
            type="submit"
            disabled={isProcessing || !queryText.trim()}
            className="absolute right-2 top-2 bottom-2 px-3.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-lg transition flex items-center justify-center"
          >
            <Search className="w-4 h-4" />
          </button>
        </form>

        {/* Sample Queries */}
        <div className="flex flex-wrap items-center justify-center gap-1.5 mt-4">
          <span className="text-xs text-gray-400 mr-1 font-medium">Sample Queries:</span>
          {sampleQueries.map((q, idx) => (
            <button
              key={idx}
              onClick={() => triggerSampleQuery(q.text, q.lang)}
              disabled={isProcessing}
              className="text-xs px-2.5 py-1 rounded-full bg-gray-900 hover:bg-gray-800 border border-gray-800 text-gray-300 transition"
            >
              {q.label}
            </button>
          ))}
        </div>

        {/* Live Transcript Stream */}
        {liveTranscript && !response && (
          <TranscriptionView
            queryText={liveTranscript}
            language={selectedLang.split("-")[0]}
            classification="STREAMING"
          />
        )}

        {/* Response Display */}
        {response && (
          <div className="w-full flex flex-col items-center mt-6 animate-in fade-in slide-in-from-bottom-4">
            <TranscriptionView
              queryText={response.original_query}
              language={response.language}
              classification={response.classification}
            />

            <AnswerCard
              answer={response.answer}
              tier={response.tier}
              citations={response.citations}
              grounding={response.grounding}
              audioBase64={response.audio_base64}
            />

            <TelemetryBar
              telemetry={response.telemetry}
              tier={response.tier}
              grounded={response.grounding.grounded}
            />

            <EngineeringMode data={response} />
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="mt-16 text-center text-xs text-gray-500 font-mono z-10">
        SHRUTI RAG Pipeline Core target &lt;50ms • OpenAI Realtime API (Speech-to-Speech) • Qdrant Vector &amp; BM25 Hybrid
      </footer>
    </main>
  );
}
