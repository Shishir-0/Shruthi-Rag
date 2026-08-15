"use client";

import React, { useState, useRef, useEffect } from "react";
import { Mic, Square, Loader2, Volume2, ShieldAlert } from "lucide-react";
import { VoiceWebSocketClient, VoiceClientState } from "@/lib/voice/VoiceWebSocketClient";
import { AudioEngine } from "@/lib/voice/AudioEngine";
import { QueryResponse } from "@/lib/api";

interface VoiceRecorderProps {
  onQueryResponse?: (response: QueryResponse) => void;
  onTranscriptPartial?: (text: string, lang: string) => void;
  onTranscriptFinal?: (text: string, lang: string) => void;
  selectedLanguageHint?: string;
  isProcessing?: boolean;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onQueryResponse,
  onTranscriptPartial,
  onTranscriptFinal,
  selectedLanguageHint = "hi-IN",
  isProcessing = false,
}) => {
  const [clientState, setClientState] = useState<VoiceClientState>("DISCONNECTED");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const wsClientRef = useRef<VoiceWebSocketClient | null>(null);
  const audioEngineRef = useRef<AudioEngine | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    // Initialize AudioEngine and VoiceWebSocketClient
    audioEngineRef.current = new AudioEngine({
      onAudioChunk: (chunk) => {
        wsClientRef.current?.sendAudioChunk(chunk);
      },
      onError: (err) => {
        setErrorMessage(err);
      },
    });

    wsClientRef.current = new VoiceWebSocketClient({
      onStateChange: (state) => {
        setClientState(state);
        if (state === "LISTENING") {
          drawWaveform();
        } else if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
      },
      onTranscriptPartial: (text, lang) => {
        onTranscriptPartial?.(text, lang);
      },
      onTranscriptFinal: (text, lang) => {
        onTranscriptFinal?.(text, lang);
      },
      onQueryResponse: (resp) => {
        onQueryResponse?.(resp);
      },
      onAudioChunkReceived: (chunk) => {
        audioEngineRef.current?.enqueuePlaybackAudio(chunk);
      },
      onError: (err) => {
        setErrorMessage(err);
      },
    });

    return () => {
      audioEngineRef.current?.cleanup();
      wsClientRef.current?.disconnect();
    };
  }, []);

  const handleMicClick = async () => {
    setErrorMessage(null);

    // Instant Barge-In: If assistant is speaking or processing, tap button to interrupt immediately
    if (clientState === "SPEAKING" || clientState === "TRANSCRIBING" || clientState === "THINKING") {
      audioEngineRef.current?.stopPlaybackBargeIn();
      wsClientRef.current?.sendBargeIn();
      audioEngineRef.current?.stopMicrophone();
      return;
    }

    if (clientState === "LISTENING") {
      // Stop recording and trigger end-of-speech stream completion
      audioEngineRef.current?.stopMicrophone();
      wsClientRef.current?.stopStream(selectedLanguageHint);
      return;
    }

    // Connect & start streaming microphone
    try {
      if (wsClientRef.current?.getState() !== "CONNECTED") {
        await wsClientRef.current?.connect();
      }
      wsClientRef.current?.startStream(selectedLanguageHint);
      await audioEngineRef.current?.startMicrophone();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to start streaming recording");
    }
  };

  const drawWaveform = () => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let step = 0;
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "rgba(59, 130, 246, 0.6)";
      step += 0.15;

      const bars = 32;
      const barWidth = canvas.width / bars;
      for (let i = 0; i < bars; i++) {
        const height = Math.sin(step + i * 0.3) * 16 + 22;
        ctx.fillRect(i * barWidth, (canvas.height - height) / 2, barWidth - 2, height);
      }
      animationFrameRef.current = requestAnimationFrame(render);
    };
    render();
  };

  const isListening = clientState === "LISTENING";
  const isSpeaking = clientState === "SPEAKING";
  const isBusy = clientState === "THINKING" || clientState === "TRANSCRIBING" || isProcessing;

  return (
    <div className="flex flex-col items-center justify-center my-6">
      {errorMessage && (
        <div className="flex items-center gap-2 text-xs text-red-400 bg-red-950/60 border border-red-800/60 px-3 py-1.5 rounded-lg mb-3">
          <ShieldAlert className="w-3.5 h-3.5" />
          {errorMessage}
        </div>
      )}

      <div className="relative flex items-center justify-center">
        {isListening && (
          <div className="absolute inset-0 rounded-full bg-blue-500/20 animate-ping" />
        )}
        {isSpeaking && (
          <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-pulse" />
        )}
        <button
          onClick={handleMicClick}
          className={`relative z-10 p-6 rounded-full transition-all duration-300 shadow-xl ${
            isListening
              ? "bg-red-600 hover:bg-red-700 text-white scale-110 shadow-red-500/50"
              : isSpeaking
              ? "bg-emerald-600 hover:bg-emerald-700 text-white scale-105 shadow-emerald-500/40"
              : "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/40 hover:scale-105"
          }`}
        >
          {isBusy ? (
            <Loader2 className="w-10 h-10 animate-spin" />
          ) : isListening ? (
            <Square className="w-10 h-10" />
          ) : isSpeaking ? (
            <Volume2 className="w-10 h-10 animate-bounce" />
          ) : (
            <Mic className="w-10 h-10" />
          )}
        </button>
      </div>

      <p className="mt-3 text-sm font-medium text-gray-300">
        {isListening
          ? "Listening & streaming voice input..."
          : clientState === "TRANSCRIBING"
          ? "Transcribing live speech..."
          : clientState === "THINKING"
          ? "Retrieving & verifying facts..."
          : isSpeaking
          ? "Assistant is speaking (Tap to Barge-In)..."
          : "Tap microphone to stream speech"}
      </p>

      <canvas
        ref={canvasRef}
        width={240}
        height={40}
        className={`mt-2 ${isListening ? "block" : "hidden"}`}
      />
    </div>
  );
};
