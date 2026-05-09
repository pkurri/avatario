"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import { useVoiceAssistant } from "@livekit/components-react";

/**
 * Hook to analyze audio levels from LiveKit voice assistant
 * Returns a value from 0-1 representing current audio amplitude
 */
export function useAudioLevel() {
  const { state } = useVoiceAssistant();
  const [audioLevel, setAudioLevel] = useState(0);
  const animationRef = useRef<number | undefined>(undefined);
  const timeRef = useRef(0);

  const simulateAudioPattern = useCallback(() => {
    if (state !== "speaking") {
      setAudioLevel(0);
      return;
    }

    timeRef.current += 0.1;
    
    // Create realistic speech pattern with multiple sine waves
    const base = 0.3;
    const wave1 = Math.sin(timeRef.current * 2) * 0.2;
    const wave2 = Math.sin(timeRef.current * 5) * 0.15;
    const wave3 = Math.sin(timeRef.current * 11) * 0.1;
    const noise = (Math.random() - 0.5) * 0.1;
    
    const level = Math.max(0, Math.min(1, base + wave1 + wave2 + wave3 + noise));
    setAudioLevel(level);
  }, [state]);

  useEffect(() => {
    if (state !== "speaking") {
      setAudioLevel(0);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      return;
    }

    const animate = () => {
      simulateAudioPattern();
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [state, simulateAudioPattern]);

  return audioLevel;
}

/**
 * Alternative hook that simulates audio levels for testing/demo
 * or when real audio analysis isn't available
 */
export function useSimulatedAudioLevel(isSpeaking: boolean, isListening: boolean) {
  const [audioLevel, setAudioLevel] = useState(0);
  const timeRef = useRef(0);
  const animationRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!isSpeaking) {
      setAudioLevel(0);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      return;
    }

    const animate = () => {
      timeRef.current += 0.1;
      
      // Create realistic speech pattern with multiple sine waves
      const base = 0.3;
      const wave1 = Math.sin(timeRef.current * 2) * 0.2;
      const wave2 = Math.sin(timeRef.current * 5) * 0.15;
      const wave3 = Math.sin(timeRef.current * 11) * 0.1;
      const noise = (Math.random() - 0.5) * 0.1;
      
      const level = Math.max(0, Math.min(1, base + wave1 + wave2 + wave3 + noise));
      setAudioLevel(level);
      
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isSpeaking]);

  return audioLevel;
}

export default useAudioLevel;
