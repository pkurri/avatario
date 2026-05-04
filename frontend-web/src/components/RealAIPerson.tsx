"use client";

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, User, Sparkles, Video, Image as ImageIcon, Loader2 } from 'lucide-react';
import Image from 'next/image';

// ==========================================
// TYPES
// ==========================================

interface AIPerson {
  id: string;
  name: string;
  image_url: string;
  vertical: string;
  gender: string;
  ready: boolean;
  traits?: {
    gender: string;
    ethnicity: string;
    age_group: string;
    profession: string;
  };
}

interface RealAIPersonProps {
  vertical?: string;
  gender?: 'male' | 'female';
  name?: string;
  size?: number;
  isSpeaking?: boolean;
  isListening?: boolean;
  videoUrl?: string | null;
  onPersonGenerated?: (person: AIPerson) => void;
  className?: string;
}

// ==========================================
// REAL AI PERSON COMPONENT
// ==========================================

export function RealAIPerson({
  vertical = 'generic',
  gender = 'female',
  name,
  size = 320,
  isSpeaking = false,
  isListening = false,
  videoUrl,
  onPersonGenerated,
  className = ""
}: RealAIPersonProps) {
  const [person, setPerson] = useState<AIPerson | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [displayMode, setDisplayMode] = useState<'image' | 'video'>('image');
  const [imageLoaded, setImageLoaded] = useState(false);

  // Generate AI person on mount
  useEffect(() => {
    generatePerson();
  }, [vertical, gender, name]);

  const generatePerson = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/ai-person/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vertical,
          gender,
          name
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate AI person');
      }

      const data = await response.json();
      
      if (data.person) {
        setPerson(data.person);
        onPersonGenerated?.(data.person);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate AI person');
    } finally {
      setIsGenerating(false);
    }
  };

  // Check if we have a real image URL or need to generate one
  const hasRealImage = person?.image_url?.startsWith('http');
  const isPlaceholder = person?.image_url?.startsWith('ai://');

  // Generate talking video when speaking
  const generateTalkingVideo = useCallback(async (text: string) => {
    if (!person || !hasRealImage) return;

    try {
      const response = await fetch('http://localhost:8000/ai-person/talking-head', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona_id: person.id,
          text,
          image_url: person.image_url
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.video_url) {
          setDisplayMode('video');
        }
      }
    } catch (err) {
      console.error('Failed to generate talking video:', err);
    }
  }, [person, hasRealImage]);

  return (
    <div className={`relative ${className}`}>
      <AnimatePresence mode="wait">
        {isGenerating ? (
          <motion.div
            key="generating"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center"
            style={{ width: size, height: size * 1.1 }}
          >
            <div className="relative">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="w-12 h-12 text-blue-500" />
              </motion.div>
              <motion.div
                className="absolute inset-0"
                animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <div className="w-12 h-12 rounded-full bg-blue-500/30 blur-xl" />
              </motion.div>
            </div>
            <p className="mt-4 text-neutral-400 text-sm">Generating AI Person...</p>
            <p className="text-neutral-500 text-xs mt-1">Using FLUX AI</p>
          </motion.div>
        ) : error ? (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center text-center p-4"
            style={{ width: size, height: size }}
          >
            <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-3">
              <User className="w-8 h-8 text-red-400" />
            </div>
            <p className="text-red-400 text-sm">{error}</p>
            <button
              onClick={generatePerson}
              className="mt-3 px-4 py-2 bg-neutral-800 hover:bg-neutral-700 rounded-full text-white text-sm flex items-center gap-2 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </motion.div>
        ) : person ? (
          <motion.div
            key="person"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="relative"
          >
            {/* Main Avatar Display */}
            <motion.div
              className="relative rounded-2xl overflow-hidden"
              style={{
                width: size,
                height: size * 1.1,
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
              {/* AI Generated Image */}
              {hasRealImage ? (
                <Image
                  src={person.image_url}
                  alt={person.name}
                  fill
                  className={`object-cover transition-opacity duration-500 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
                  onLoad={() => setImageLoaded(true)}
                  sizes={`${size}px`}
                  priority
                />
              ) : isPlaceholder ? (
                // Placeholder while AI generates
                <div className="absolute inset-0 bg-gradient-to-br from-neutral-800 to-neutral-900 flex items-center justify-center">
                  <div className="text-center">
                    <motion.div
                      animate={{ scale: [1, 1.1, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mx-auto mb-3"
                    >
                      <User className="w-10 h-10 text-blue-400" />
                    </motion.div>
                    <p className="text-neutral-400 text-sm">AI Person</p>
                    <p className="text-neutral-500 text-xs mt-1">#{person.id.slice(0, 8)}</p>
                  </div>
                </div>
              ) : (
                // Fallback to generated placeholder
                <AIGeneratedPlaceholder name={person.name} vertical={vertical} />
              )}

              {/* Loading overlay */}
              {!imageLoaded && hasRealImage && (
                <div className="absolute inset-0 bg-neutral-800 animate-pulse" />
              )}

              {/* Speaking glow effect */}
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

              {/* Name badge */}
              <div className="absolute top-4 left-4 px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
                <span className="text-white text-sm font-medium">{person.name}</span>
              </div>

              {/* Vertical badge */}
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
                <span className="text-white text-xs font-medium capitalize">{vertical}</span>
              </div>

              {/* AI Generated badge */}
              <div className="absolute top-4 right-4 px-2 py-1 rounded-full bg-blue-500/80 text-white text-xs font-medium flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                AI
              </div>
            </motion.div>

            {/* Controls */}
            <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 flex items-center gap-2">
              <button
                onClick={generatePerson}
                disabled={isGenerating}
                className="p-2 rounded-full bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors"
                title="Generate new AI person"
              >
                <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
              </button>
              
              {hasRealImage && (
                <>
                  <button
                    onClick={() => setDisplayMode('image')}
                    className={`p-2 rounded-full transition-colors ${
                      displayMode === 'image' 
                        ? 'bg-blue-500/20 text-blue-400' 
                        : 'bg-neutral-800 text-neutral-400 hover:text-white'
                    }`}
                    title="Photo mode"
                  >
                    <ImageIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setDisplayMode('video')}
                    className={`p-2 rounded-full transition-colors ${
                      displayMode === 'video' 
                        ? 'bg-blue-500/20 text-blue-400' 
                        : 'bg-neutral-800 text-neutral-400 hover:text-white'
                    }`}
                    title="Video mode (talking)"
                  >
                    <Video className="w-4 h-4" />
                  </button>
                </>
              )}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

// ==========================================
// AI GENERATED PLACEHOLDER
// ==========================================

function AIGeneratedPlaceholder({ name, vertical }: { name: string; vertical: string }) {
  const [seed] = useState(() => Math.random());
  
  return (
    <div className="absolute inset-0 bg-gradient-to-br from-neutral-800 to-neutral-900">
      {/* Abstract face visualization */}
      <svg 
        className="absolute inset-0 w-full h-full opacity-30"
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        {/* Face outline */}
        <ellipse 
          cx="50" 
          cy="45" 
          rx="25" 
          ry="30" 
          fill="none" 
          stroke="url(#faceGradient)" 
          strokeWidth="0.5"
          filter="url(#glow)"
        />
        
        {/* Eyes */}
        <circle cx="40" cy="40" r="3" fill="url(#eyeGradient)" opacity="0.6" />
        <circle cx="60" cy="40" r="3" fill="url(#eyeGradient)" opacity="0.6" />
        
        {/* Gradient definitions */}
        <defs>
          <linearGradient id="faceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
          <radialGradient id="eyeGradient">
            <stop offset="0%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#3b82f6" />
          </radialGradient>
        </defs>
      </svg>
      
      {/* Center text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Sparkles className="w-8 h-8 text-blue-400 mx-auto mb-2" />
          </motion.div>
          <p className="text-neutral-400 text-sm font-medium">{name}</p>
          <p className="text-neutral-500 text-xs mt-1 capitalize">{vertical} AI</p>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// HOOK FOR AI PERSON MANAGEMENT
// ==========================================

export function useAIPerson(vertical?: string, gender?: 'male' | 'female') {
  const [person, setPerson] = useState<AIPerson | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async (customName?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/ai-person/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vertical: vertical || 'generic',
          gender: gender || 'female',
          name: customName
        })
      });

      if (!response.ok) throw new Error('Failed to generate');

      const data = await response.json();
      if (data.person) {
        setPerson(data.person);
        return data.person;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setIsLoading(false);
    }
  }, [vertical, gender]);

  const generateTalkingVideo = useCallback(async (text: string) => {
    if (!person) return;

    try {
      const response = await fetch('http://localhost:8000/ai-person/talking-head', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona_id: person.id,
          text,
          image_url: person.image_url
        })
      });

      return await response.json();
    } catch (err) {
      console.error('Failed to generate video:', err);
    }
  }, [person]);

  return {
    person,
    isLoading,
    error,
    generate,
    generateTalkingVideo,
    regenerate: () => generate()
  };
}
