"use client";

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, Sparkles, Video, Loader2, User, AlertCircle } from 'lucide-react';
import { API_BASE, apiUrl } from '@/lib/config';

// ==========================================
// TYPES
// ==========================================

interface TalkingPerson {
  id: string;
  name: string;
  status: 'image' | 'audio' | 'video' | 'complete' | 'error';
  image_url?: string;
  video_url?: string;
  error?: string;
  config: {
    gender: string;
    age: string;
    ethnicity: string;
    profession: string;
  };
}

interface RealTalkingPersonProps {
  vertical?: string;
  gender?: 'male' | 'female';
  name?: string;
  ethnicity?: string;
  size?: number;
  isSpeaking?: boolean;
  isListening?: boolean;
  speakingText?: string;
  onPersonGenerated?: (person: TalkingPerson) => void;
  className?: string;
}

// ==========================================
// REAL TALKING PERSON COMPONENT (Option B)
// ==========================================

export function RealTalkingPerson({
  vertical = 'generic',
  gender = 'female',
  name,
  ethnicity = 'indian',
  size = 320,
  isSpeaking = false,
  isListening = false,
  speakingText,
  onPersonGenerated,
  className = ""
}: RealTalkingPersonProps) {
  const [person, setPerson] = useState<TalkingPerson | null>(null);
  const [currentVideo, setCurrentVideo] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Create talking person on mount
  useEffect(() => {
    createTalkingPerson();
  }, [vertical, gender, name, ethnicity]);

  const createTalkingPerson = async () => {
    setIsCreating(true);
    setError(null);

    try {
      const response = await fetch(apiUrl('/talking-person/create'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vertical,
          gender,
          name,
          ethnicity
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create talking person');
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      setPerson(data);
      onPersonGenerated?.(data);

      // Set initial video if complete
      if (data.video_url) {
        setCurrentVideo(`${API_BASE}${data.video_url}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create talking person');
    } finally {
      setIsCreating(false);
    }
  };

  // Generate new video when speaking text changes
  const generateVideoForText = useCallback(async (text: string) => {
    if (!person || !text) return;

    setIsGeneratingVideo(true);

    try {
      const response = await fetch(apiUrl('/talking-person/video'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          person_id: person.id,
          text,
          emotion: 'neutral'
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.video_url) {
          setCurrentVideo(`${API_BASE}${data.video_url}`);
        }
      }
    } catch (err) {
      console.error('Failed to generate video:', err);
    } finally {
      setIsGeneratingVideo(false);
    }
  }, [person]);

  // Handle speaking state
  useEffect(() => {
    if (isSpeaking && speakingText && person) {
      // Could trigger new video generation here
      // For now, just play the welcome video
    }
  }, [isSpeaking, speakingText, person, generateVideoForText]);

  return (
    <div className={`relative ${className}`}>
      <AnimatePresence mode="wait">
        {isCreating ? (
          <CreatingState key="creating" size={size} />
        ) : error ? (
          <ErrorState key="error" error={error} onRetry={createTalkingPerson} size={size} />
        ) : person ? (
          <PersonDisplay
            key="person"
            person={person}
            currentVideo={currentVideo}
            isSpeaking={isSpeaking}
            isListening={isListening}
            isGeneratingVideo={isGeneratingVideo}
            imageLoaded={imageLoaded}
            onImageLoad={() => setImageLoaded(true)}
            onRegenerate={createTalkingPerson}
            size={size}
          />
        ) : null}
      </AnimatePresence>
    </div>
  );
}

// ==========================================
// SUB-COMPONENTS
// ==========================================

function CreatingState({ size }: { size: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center"
      style={{ width: size, height: size * 1.1 }}
    >
      <div className="relative">
        {/* Animated rings */}
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ width: 80, height: 80 }}
          animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-full h-full rounded-full bg-gradient-to-br from-purple-500/30 to-blue-500/30 blur-xl" />
        </motion.div>
        
        <motion.div
          className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        >
          <Sparkles className="w-10 h-10 text-white" />
        </motion.div>
      </div>
      
      <div className="mt-6 text-center">
        <p className="text-white font-medium">Creating AI Person...</p>
        <div className="flex items-center justify-center gap-2 mt-2 text-neutral-400 text-xs">
          <span className="flex items-center gap-1">
            <Loader2 className="w-3 h-3 animate-spin" />
            FLUX Image
          </span>
          <span>→</span>
          <span>TTS Audio</span>
          <span>→</span>
          <span>Lip Sync</span>
        </div>
      </div>
    </motion.div>
  );
}

function ErrorState({ 
  error, 
  onRetry, 
  size 
}: { 
  error: string; 
  onRetry: () => void; 
  size: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center text-center p-4"
      style={{ width: size, height: size }}
    >
      <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-3">
        <AlertCircle className="w-8 h-8 text-red-400" />
      </div>
      <p className="text-red-400 text-sm max-w-xs">{error}</p>
      <button
        onClick={onRetry}
        className="mt-3 px-4 py-2 bg-neutral-800 hover:bg-neutral-700 rounded-full text-white text-sm flex items-center gap-2 transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Retry
      </button>
    </motion.div>
  );
}

function PersonDisplay({
  person,
  currentVideo,
  isSpeaking,
  isListening,
  isGeneratingVideo,
  imageLoaded,
  onImageLoad,
  onRegenerate,
  size
}: {
  person: TalkingPerson;
  currentVideo: string | null;
  isSpeaking: boolean;
  isListening: boolean;
  isGeneratingVideo: boolean;
  imageLoaded: boolean;
  onImageLoad: () => void;
  onRegenerate: () => void;
  size: number;
}) {
  const [showVideo, setShowVideo] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="relative"
    >
      {/* Main Avatar Display */}
      <motion.div
        className="relative rounded-2xl overflow-hidden bg-neutral-900"
        style={{
          width: size,
          height: size * 1.1,
          boxShadow: isSpeaking
            ? '0 0 60px rgba(139, 92, 246, 0.5), 0 20px 40px rgba(0,0,0,0.4)'
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
        {/* Video Mode */}
        {showVideo && currentVideo ? (
          <video
            src={currentVideo}
            autoPlay
            loop={isSpeaking}
            muted
            className="absolute inset-0 w-full h-full object-cover"
            playsInline
          />
        ) : (
          /* Image Mode */
          <>
            {person.image_url && (
              <img
                src={`${API_BASE}${person.image_url}`}
                alt={person.name}
                className={`w-full h-full object-cover transition-opacity duration-500 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
                onLoad={onImageLoad}
                style={{ display: imageLoaded ? 'block' : 'none' }}
              />
            )}
            
            {!imageLoaded && (
              <div className="absolute inset-0 bg-neutral-800 animate-pulse flex items-center justify-center">
                <User className="w-12 h-12 text-neutral-600" />
              </div>
            )}
          </>
        )}

        {/* Speaking Glow Effect */}
        {isSpeaking && (
          <motion.div
            className="absolute inset-0 rounded-2xl pointer-events-none"
            style={{
              boxShadow: 'inset 0 0 60px rgba(139, 92, 246, 0.4)',
            }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        )}

        {/* Listening Indicator */}
        {isListening && (
          <div className="absolute top-4 right-4 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
        )}

        {/* Video Generating Indicator */}
        {isGeneratingVideo && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-2" />
              <p className="text-white text-sm">Generating lip-sync...</p>
            </div>
          </div>
        )}

        {/* Name Badge */}
        <div className="absolute top-4 left-4 px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
          <span className="text-white text-sm font-medium">{person.name}</span>
        </div>

        {/* Vertical Badge */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
          <span className="text-white text-xs font-medium capitalize">
            {person.config.profession} AI
          </span>
        </div>

        {/* AI Generated Badge */}
        <div className="absolute top-4 right-4 px-2 py-1 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 text-white text-xs font-medium flex items-center gap-1">
          <Sparkles className="w-3 h-3" />
          FLUX AI
        </div>
      </motion.div>

      {/* Controls */}
      <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 flex items-center gap-2">
        <button
          onClick={onRegenerate}
          className="p-2 rounded-full bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors"
          title="Generate new AI person"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        
        <button
          onClick={() => setShowVideo(!showVideo)}
          disabled={!currentVideo}
          className={`p-2 rounded-full transition-colors ${
            showVideo
              ? 'bg-purple-500/20 text-purple-400'
              : 'bg-neutral-800 text-neutral-400 hover:text-white'
          } ${!currentVideo ? 'opacity-50 cursor-not-allowed' : ''}`}
          title={showVideo ? "Show photo" : "Show talking video"}
        >
          {showVideo ? <User className="w-4 h-4" /> : <Video className="w-4 h-4" />}
        </button>
      </div>

      {/* Status Badge */}
      {person.status !== 'complete' && (
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-yellow-500/20 text-yellow-400 text-xs">
          Status: {person.status}
        </div>
      )}
    </motion.div>
  );
}

// ==========================================
// HOOK
// ==========================================

export function useTalkingPerson(
  vertical?: string,
  gender?: 'male' | 'female',
  ethnicity?: string
) {
  const [person, setPerson] = useState<TalkingPerson | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(async (name?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(apiUrl('/talking-person/create'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vertical: vertical || 'generic',
          gender: gender || 'female',
          ethnicity: ethnicity || 'indian',
          name
        })
      });

      if (!response.ok) throw new Error('Failed to create');

      const data = await response.json();
      if (data.error) throw new Error(data.error);

      setPerson(data);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setIsLoading(false);
    }
  }, [vertical, gender, ethnicity]);

  const generateVideo = useCallback(async (text: string) => {
    if (!person) return;

    try {
      const response = await fetch(apiUrl('/talking-person/video'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          person_id: person.id,
          text,
          emotion: 'neutral'
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
    create,
    generateVideo
  };
}
