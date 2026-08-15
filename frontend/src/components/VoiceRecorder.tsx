"use client";

import React, { useState, useRef, useEffect } from "react";
import { Mic, Square, Loader2 } from "lucide-react";

interface VoiceRecorderProps {
  onRecordingComplete: (blob: Blob) => void;
  isProcessing: boolean;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onRecordingComplete,
  isProcessing,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        onRecordingComplete(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      drawWaveform();
    } catch (err) {
      console.error("Microphone access error:", err);
      alert("Microphone access denied or unavailable.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
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
      ctx.fillStyle = "rgba(59, 130, 246, 0.4)";
      step += 0.1;

      const bars = 30;
      const barWidth = canvas.width / bars;
      for (let i = 0; i < bars; i++) {
        const height = Math.sin(step + i * 0.3) * 15 + 20;
        ctx.fillRect(i * barWidth, (canvas.height - height) / 2, barWidth - 2, height);
      }
      animationFrameRef.current = requestAnimationFrame(render);
    };
    render();
  };

  return (
    <div className="flex flex-col items-center justify-center my-6">
      <div className="relative flex items-center justify-center">
        {isRecording && (
          <div className="absolute inset-0 rounded-full bg-blue-500/20 animate-ping" />
        )}
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          className={`relative z-10 p-6 rounded-full transition-all duration-300 shadow-xl ${
            isRecording
              ? "bg-red-600 hover:bg-red-700 text-white scale-110 shadow-red-500/50"
              : "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/40 hover:scale-105"
          } ${isProcessing ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          {isProcessing ? (
            <Loader2 className="w-10 h-10 animate-spin" />
          ) : isRecording ? (
            <Square className="w-10 h-10" />
          ) : (
            <Mic className="w-10 h-10" />
          )}
        </button>
      </div>

      <p className="mt-3 text-sm font-medium text-gray-300">
        {isProcessing
          ? "Transcribing & Retrieving..."
          : isRecording
          ? "Listening to voice input..."
          : "Tap microphone to speak"}
      </p>

      <canvas
        ref={canvasRef}
        width={240}
        height={40}
        className={`mt-2 ${isRecording ? "block" : "hidden"}`}
      />
    </div>
  );
};
