"use client";

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

// ==========================================
// TALKING AVATAR - Video-based with lip sync
// ==========================================

interface TalkingAvatarProps {
  videoUrl: string;
  isSpeaking?: boolean;
  isListening?: boolean;
  size?: number;
  className?: string;
  fallbackImageUrl?: string;
  personaName?: string;
  vertical?: string;
}

export function TalkingAvatar({
  videoUrl,
  isSpeaking = false,
  isListening = false,
  size = 300,
  className = "",
  fallbackImageUrl,
  personaName = "AI Assistant",
  vertical = "generic"
}: TalkingAvatarProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isVideoMode, setIsVideoMode] = useState(true);

  // Handle video playback based on speaking state
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !videoUrl) return;

    if (isSpeaking) {
      video.play().catch(() => {
        // Auto-play might be blocked, show controls
      });
    } else {
      video.pause();
    }
  }, [isSpeaking, videoUrl]);

  // Handle video load
  const handleVideoLoad = () => {
    setIsLoaded(true);
    setHasError(false);
  };

  const handleVideoError = () => {
    setHasError(true);
    setIsVideoMode(false);
  };

  // If video failed or no URL, show fallback
  if (hasError || !videoUrl) {
    return (
      <FallbackAvatar
        imageUrl={fallbackImageUrl}
        personaName={personaName}
        vertical={vertical}
        isSpeaking={isSpeaking}
        isListening={isListening}
        size={size}
        className={className}
      />
    );
  }

  return (
    <motion.div
      className={`relative rounded-2xl overflow-hidden ${className}`}
      style={{
        width: size,
        height: size * 1.2, // Slightly taller for video aspect ratio
        boxShadow: isSpeaking 
          ? '0 0 60px rgba(59, 130, 246, 0.5), 0 20px 40px rgba(0,0,0,0.4)' 
          : '0 20px 40px rgba(0,0,0,0.3)',
      }}
      animate={{
        scale: isSpeaking ? [1, 1.02, 1] : 1,
      }}
      transition={{
        duration: 0.5,
        repeat: isSpeaking ? Infinity : 0,
        repeatType: "reverse"
      }}
    >
      {/* Video Element */}
      <video
        ref={videoRef}
        src={videoUrl}
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
        onLoadedData={handleVideoLoad}
        onError={handleVideoError}
        playsInline
        muted // Audio is handled separately via TTS
        loop={isSpeaking}
        preload="auto"
      />

      {/* Loading State */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-neutral-800 animate-pulse flex items-center justify-center">
          <div className="text-neutral-400 text-sm">Loading avatar...</div>
        </div>
      )}

      {/* Speaking Indicator Ring */}
      {isSpeaking && (
        <motion.div
          className="absolute -inset-2 rounded-2xl border-2 border-blue-500/50"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}

      {/* Listening Indicator */}
      {isListening && (
        <div className="absolute top-4 right-4 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
      )}

      {/* Vertical Badge */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
        <span className="text-white text-xs font-medium capitalize">{vertical}</span>
      </div>

      {/* Name Badge */}
      <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/40 backdrop-blur-sm">
        <span className="text-white text-sm font-medium">{personaName}</span>
      </div>

      {/* Toggle Mode Button */}
      <button
        onClick={() => setIsVideoMode(!isVideoMode)}
        className="absolute top-4 right-4 p-2 rounded-full bg-black/40 backdrop-blur-sm text-white/70 hover:text-white transition-colors"
        title={isVideoMode ? "Switch to photo mode" : "Switch to video mode"}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {isVideoMode ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          )}
        </svg>
      </button>
    </motion.div>
  );
}

// ==========================================
// FALLBACK AVATAR - When video unavailable
// ==========================================

interface FallbackAvatarProps {
  imageUrl?: string;
  personaName?: string;
  vertical?: string;
  isSpeaking?: boolean;
  isListening?: boolean;
  size?: number;
  className?: string;
}

function FallbackAvatar({
  imageUrl,
  personaName = "AI Assistant",
  vertical = "generic",
  isSpeaking = false,
  isListening = false,
  size = 300,
  className = ""
}: FallbackAvatarProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [blink, setBlink] = useState(false);

  // Blink animation for realistic effect
  useEffect(() => {
    const interval = setInterval(() => {
      setBlink(true);
      setTimeout(() => setBlink(false), 150);
    }, 3000 + Math.random() * 2000);
    return () => clearInterval(interval);
  }, []);

  const scale = isSpeaking ? 1 + 0.02 : 1;

  // Default placeholder
  const defaultImage = vertical === 'medical' 
    ? 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400&h=400&fit=crop&crop=face'
    : vertical === 'legal'
    ? 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop&crop=face'
    : vertical === 'finance'
    ? 'https://images.unsplash.com/photo-1504257432389-52343af06ae3?w=400&h=400&fit=crop&crop=face'
    : 'https://images.unsplash.com/photo-1463453091185-61582044d556?w=400&h=400&fit=crop&crop=face';

  const finalImageUrl = imageUrl || defaultImage;

  return (
    <motion.div
      className={`relative rounded-2xl overflow-hidden ${className}`}
      style={{
        width: size,
        height: size,
        boxShadow: isSpeaking 
          ? '0 0 60px rgba(59, 130, 246, 0.4), 0 20px 40px rgba(0,0,0,0.3)' 
          : '0 20px 40px rgba(0,0,0,0.3)',
      }}
      animate={{ scale }}
      transition={{ duration: 0.3 }}
    >
      {/* Image */}
      <div className="absolute inset-0">
        <img
          src={finalImageUrl}
          alt={personaName}
          className={`w-full h-full object-cover transition-opacity duration-500 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setIsLoaded(true)}
        />
      </div>

      {/* Loading */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-neutral-800 animate-pulse" />
      )}

      {/* Blink overlay */}
      {blink && (
        <div className="absolute inset-0 bg-black/10 transition-opacity duration-75" />
      )}

      {/* Speaking glow */}
      {isSpeaking && (
        <motion.div
          className="absolute inset-0 rounded-2xl"
          style={{
            boxShadow: 'inset 0 0 50px rgba(59, 130, 246, 0.4)',
          }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}

      {/* Listening indicator */}
      {isListening && (
        <div className="absolute top-4 right-4 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
      )}

      {/* Badges */}
      <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/40 backdrop-blur-sm">
        <span className="text-white text-sm font-medium">{personaName}</span>
      </div>
      
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
        <span className="text-white text-xs font-medium capitalize">{vertical}</span>
      </div>

      {/* Offline indicator */}
      <div className="absolute top-4 right-4 px-2 py-1 rounded-full bg-yellow-500/80 text-black text-xs font-medium">
        Photo Mode
      </div>
    </motion.div>
  );
}

// ==========================================
// HOOK FOR VIDEO GENERATION
// ==========================================

interface UseTalkingAvatarOptions {
  personaId: string;
  text: string;
  autoGenerate?: boolean;
}

interface UseTalkingAvatarReturn {
  videoUrl: string | null;
  isGenerating: boolean;
  error: string | null;
  generateVideo: () => Promise<void>;
  status: 'idle' | 'generating' | 'completed' | 'error';
}

export function useTalkingAvatar({
  personaId,
  text,
  autoGenerate = false
}: UseTalkingAvatarOptions): UseTalkingAvatarReturn {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'generating' | 'completed' | 'error'>('idle');

  const generateVideo = async () => {
    if (!text || !personaId) return;

    setIsGenerating(true);
    setError(null);
    setStatus('generating');

    try {
      const response = await fetch('/api/lipsync/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona_id: personaId,
          text,
          model: 'infinitetalk-image-to-video',
          resolution: '512x512'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate video');
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      if (data.video_url) {
        setVideoUrl(data.video_url);
        setStatus('completed');
      } else if (data.job_id) {
        // Poll for completion
        pollForVideo(data.job_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus('error');
    } finally {
      setIsGenerating(false);
    }
  };

  const pollForVideo = async (jobId: string) => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`/api/lipsync/status/${jobId}`);
        const data = await response.json();

        if (data.status === 'completed' && data.video_url) {
          setVideoUrl(data.video_url);
          setStatus('completed');
          setIsGenerating(false);
        } else if (data.status === 'failed' || data.error) {
          setError(data.error || 'Video generation failed');
          setStatus('error');
          setIsGenerating(false);
        } else {
          // Still processing, poll again
          setTimeout(() => checkStatus(), 2000);
        }
      } catch (err) {
        setError('Failed to check video status');
        setStatus('error');
        setIsGenerating(false);
      }
    };

    checkStatus();
  };

  // Auto-generate if enabled
  useEffect(() => {
    if (autoGenerate && text && personaId) {
      generateVideo();
    }
  }, [text, personaId, autoGenerate]);

  return {
    videoUrl,
    isGenerating,
    error,
    generateVideo,
    status
  };
}
