"use client";

import { motion } from 'framer-motion';
import { Mic, Square, Loader2, Video, Image as ImageIcon, RefreshCw, Sparkles, Camera } from 'lucide-react';
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
} from "@livekit/components-react";
import { llm, livekit, lipsync, personas as personasApi } from '@/lib/api';
import "@livekit/components-styles";
import { AIAvatar, AvatarConfig, AVATAR_PRESETS } from './AIAvatar';
import { TalkingAvatar } from './TalkingAvatar';
import { RealAIPerson } from './RealAIPerson';
import { RealTalkingPerson } from './RealTalkingPerson';
import { FaceClone } from './FaceClone';
import { useAudioLevel } from '../hooks/useAudioLevel';

// Extended persona definition with avatar configuration
interface PersonaDefinition {
  id: string;
  name: string;
  color: string;
  shadow: string;
  greeting: string;
  avatarConfig: AvatarConfig;
}

// Preset avatar IDs keyed by backend persona id — add entries here as personas are added to the YAML
const PERSONA_AVATAR_MAP: Record<string, string> = {
  client: 'anya',
  lawyer: 'vikram',
  'dr-priya': 'dr-priya',
  'dr-arjun': 'dr-arjun',
  'advisor-maya': 'advisor-maya',
  'analyst-raj': 'analyst-raj',
  'assistant-sarah': 'assistant-sarah',
  'assistant-alex': 'assistant-alex',
};

const DEFAULT_AVATAR_CONFIG: AvatarConfig = AVATAR_PRESETS['assistant-sarah'];

function mapBackendPersona(p: {
  id: string;
  name: string;
  color: string;
  shadow: string;
  description: string;
}): PersonaDefinition {
  const presetKey = PERSONA_AVATAR_MAP[p.id];
  const avatarConfig = presetKey && AVATAR_PRESETS[presetKey]
    ? { ...AVATAR_PRESETS[presetKey], name: p.name }
    : { ...DEFAULT_AVATAR_CONFIG, name: p.name };
  return {
    id: p.id,
    name: p.name,
    color: p.color || 'from-blue-500 to-purple-600',
    shadow: p.shadow || 'shadow-blue-500/50',
    greeting: p.description,
    avatarConfig,
  };
}

function VoiceAssistantUI({ selectedPersona, onDisconnect }: { selectedPersona: PersonaDefinition | null, onDisconnect: () => void }) {
  const { state } = useVoiceAssistant();
  const audioLevel = useAudioLevel();
  
  const isPlaying = state === "speaking";
  const isRecording = state === "listening";
  const isConnected = state !== "disconnected" && state !== "connecting";
  
  // Avatar display modes
  const [displayMode, setDisplayMode] = useState<'photo' | 'video' | 'ai-person' | 'talking-person' | 'face-clone'>('photo');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [lastSpokenText, setLastSpokenText] = useState("");
  const [aiPerson, setAiPerson] = useState<{ id: string; name: string; image_url: string } | null>(null);

  // Generate video for welcome message
  useEffect(() => {
    if (displayMode === 'video' && selectedPersona && !videoUrl) {
      generateWelcomeVideo();
    }
  }, [displayMode, selectedPersona]);

  const generateWelcomeVideo = async () => {
    if (!selectedPersona) return;
    setIsGeneratingVideo(true);
    try {
      const data = await lipsync.generate({
        persona_id: selectedPersona.id,
        text: `Hello, I'm ${selectedPersona.name}. ${selectedPersona.greeting}`,
      });
      if (data.video_url) setVideoUrl(data.video_url);
    } catch (err) {
      console.error('Failed to generate welcome video:', err);
    } finally {
      setIsGeneratingVideo(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-6 relative overflow-hidden w-full">
      <RoomAudioRenderer />
      
      <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-tr ${selectedPersona?.color} rounded-full blur-[120px] opacity-10`} />

      <button 
        onClick={onDisconnect}
        className="absolute top-8 left-8 text-neutral-400 hover:text-white transition-colors z-50"
      >
        ← Switch Persona
      </button>

      {/* Display Mode Toggle */}
      <div className="absolute top-8 right-8 flex items-center gap-2 z-50">
        {/* Photo Mode */}
        <button
          onClick={() => setDisplayMode('photo')}
          className={`p-2 rounded-full transition-all ${
            displayMode === 'photo'
              ? 'bg-neutral-700 text-white border border-neutral-600'
              : 'bg-neutral-800 text-neutral-400 border border-neutral-700 hover:border-neutral-600'
          }`}
          title="Photo Mode"
        >
          <ImageIcon className="w-4 h-4" />
        </button>
        
        {/* Video Mode */}
        <button
          onClick={() => setDisplayMode('video')}
          disabled={isGeneratingVideo}
          className={`p-2 rounded-full transition-all ${
            displayMode === 'video'
              ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50'
              : 'bg-neutral-800 text-neutral-400 border border-neutral-700 hover:border-neutral-600'
          } ${isGeneratingVideo ? 'opacity-50' : ''}`}
          title="Video Mode (Lip Sync)"
        >
          {isGeneratingVideo ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Video className="w-4 h-4" />
          )}
        </button>
        
        {/* AI Person Mode */}
        <button
          onClick={() => setDisplayMode('ai-person')}
          className={`flex items-center gap-2 px-3 py-2 rounded-full transition-all ${
            displayMode === 'ai-person'
              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
              : 'bg-neutral-800 text-neutral-400 border border-neutral-700 hover:border-neutral-600'
          }`}
          title="Real AI Person - AI Generated Avatar"
        >
          <Sparkles className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">AI Person</span>
        </button>
        
        {/* Real Talking Person Mode (Option B) */}
        <button
          onClick={() => setDisplayMode('talking-person')}
          className={`flex items-center gap-2 px-3 py-2 rounded-full transition-all ${
            displayMode === 'talking-person'
              ? 'bg-gradient-to-r from-pink-500/20 to-orange-500/20 text-orange-400 border border-orange-500/50'
              : 'bg-neutral-800 text-neutral-400 border border-neutral-700 hover:border-neutral-600'
          }`}
          title="Real Talking Person - FLUX AI + Lip Sync (Option B)"
        >
          <Sparkles className="w-4 h-4" />
          <Video className="w-3 h-3" />
          <span className="text-xs font-medium hidden sm:inline">Real Talking</span>
        </button>
        
        {/* Face Clone Mode */}
        <button
          onClick={() => setDisplayMode('face-clone')}
          className={`flex items-center gap-2 px-3 py-2 rounded-full transition-all ${
            displayMode === 'face-clone'
              ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-500/50'
              : 'bg-neutral-800 text-neutral-400 border border-neutral-700 hover:border-neutral-600'
          }`}
          title="Face Clone - Clone any real person or generate new"
        >
          <Camera className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">Face Clone</span>
        </button>
      </div>

      <div className="relative z-10 flex flex-col items-center">
        {/* Avatar Display - Video or Photo Mode */}
        <motion.div
           animate={{
             scale: isPlaying ? [1, 1.02, 1] : 1,
           }}
           transition={{
             repeat: isPlaying ? Infinity : 0,
             duration: 2,
             ease: "easeInOut"
           }}
           className="mb-8"
        >
          {displayMode === 'face-clone' ? (
            <FaceClone
              isSpeaking={isPlaying}
              isListening={isRecording}
              speakingText={lastSpokenText}
              size={320}
            />
          ) : selectedPersona && displayMode === 'talking-person' ? (
            <RealTalkingPerson
              vertical={selectedPersona.avatarConfig.vertical}
              gender={selectedPersona.avatarConfig.gender}
              name={selectedPersona.name}
              ethnicity="indian"
              size={320}
              isSpeaking={isPlaying}
              isListening={isRecording}
              speakingText={lastSpokenText}
            />
          ) : selectedPersona && displayMode === 'ai-person' ? (
            <RealAIPerson
              vertical={selectedPersona.avatarConfig.vertical}
              gender={selectedPersona.avatarConfig.gender}
              name={selectedPersona.name}
              size={320}
              isSpeaking={isPlaying}
              isListening={isRecording}
              videoUrl={videoUrl}
              onPersonGenerated={(person) => setAiPerson(person)}
            />
          ) : selectedPersona && displayMode === 'video' ? (
            <TalkingAvatar
              videoUrl={videoUrl || ''}
              isSpeaking={isPlaying}
              isListening={isRecording}
              size={320}
              personaName={selectedPersona.name}
              vertical={selectedPersona.avatarConfig.vertical}
              fallbackImageUrl={selectedPersona.avatarConfig.photoUrl}
            />
          ) : selectedPersona ? (
            <AIAvatar
              config={selectedPersona.avatarConfig}
              isSpeaking={isPlaying}
              isListening={isRecording}
              audioLevel={audioLevel}
              size={280}
            />
          ) : null}
        </motion.div>

        <div className="text-center h-24">
          <h2 className="text-3xl font-medium text-white mb-2">{selectedPersona?.name}</h2>
          
          <div className="flex items-center justify-center gap-2 text-neutral-400">
            {!isConnected && <><Loader2 className="w-4 h-4 animate-spin" /> Connecting to LiveKit...</>}
            {isConnected && !isRecording && !isPlaying && <span>AI Assistant Ready</span>}
            {isRecording && <span className="text-red-500 flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Listening...</span>}
            {isPlaying && <span className="text-blue-400 flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" /> Speaking...</span>}
          </div>
          
          {displayMode === 'video' && (
            <p className="text-xs text-blue-400/70 mt-2">
              {isGeneratingVideo ? 'Generating talking video...' : 'Video mode active - AI avatar will lip-sync'}
            </p>
          )}
          {displayMode === 'ai-person' && (
            <p className="text-xs text-purple-400/70 mt-2">
              AI Person mode - Realistic AI-generated human avatar
            </p>
          )}
          {displayMode === 'talking-person' && (
            <p className="text-xs text-orange-400/70 mt-2">
              Real Talking Person - FLUX AI + Lip Sync Video
            </p>
          )}
          {displayMode === 'face-clone' && (
            <p className="text-xs text-cyan-400/70 mt-2">
              Face Clone - Clone any real person or generate a new AI face
            </p>
          )}
        </div>

        <div
          className={`mt-8 w-20 h-20 rounded-full flex items-center justify-center transition-all ${
            !isConnected ? 'bg-neutral-800 text-neutral-600' :
            isRecording ? 'bg-red-500 text-white shadow-lg shadow-red-500/20' : 
            'bg-white text-black shadow-xl shadow-white/10'
          }`}
        >
          {isRecording ? <Square className="w-8 h-8 fill-current animate-pulse" /> : <Mic className="w-8 h-8" />}
        </div>
      </div>
      
      {/* Status indicator */}
      <div className="absolute bottom-8 w-full max-w-2xl px-6 text-center">
        <p className="text-neutral-500 text-sm">
          {selectedPersona?.avatarConfig?.vertical === 'legal' && "AI Legal Assistant - Not a substitute for professional legal advice"}
          {selectedPersona?.avatarConfig?.vertical === 'medical' && "AI Medical Information - Not a substitute for professional medical advice"}
          {selectedPersona?.avatarConfig?.vertical === 'finance' && "AI Financial Information - Not personalized investment advice"}
          {selectedPersona?.avatarConfig?.vertical === 'generic' && "AI Assistant - Here to help with your questions"}
        </p>
      </div>
    </div>
  );
}

export default function VoiceInterface() {
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null);
  const [token, setToken] = useState("");
  const [url, setUrl] = useState("");
  const [llmStatus, setLlmStatus] = useState<string>("unknown");
  const [personas, setPersonas] = useState<PersonaDefinition[]>([]);
  const [personasError, setPersonasError] = useState<string | null>(null);

  useEffect(() => {
    personasApi.list()
      .then(data => setPersonas((data.personas ?? []).map(mapBackendPersona)))
      .catch(err => {
        console.error('Failed to load personas:', err);
        setPersonasError('Could not load personas. Please refresh.');
      });
  }, []);

  const selectedPersona = personas.find(p => p.id === selectedPersonaId) || null;

  // Exponential backoff state for LLM polling: 2s → 4s → 8s → … capped at 30s
  const backoffRef = useRef(2000);

  const checkLlmStatus = useCallback(async () => {
    try {
      const data = await llm.status();
      setLlmStatus(data.status);
      if (data.status === "stopped") {
        await llm.wake();
        setLlmStatus("starting");
      }
      if (data.status === "running") {
        backoffRef.current = 2000; // reset on success
      }
    } catch (err) {
      console.error("Failed to check LLM status:", err);
    }
  }, []);

  useEffect(() => {
    if (!selectedPersonaId) {
      setToken("");
      setUrl("");
      setLlmStatus("unknown");
      backoffRef.current = 2000;
      return;
    }

    let timeoutId: NodeJS.Timeout;

    const poll = async () => {
      if (llmStatus === "running") return;
      await checkLlmStatus();
      // Exponential backoff, cap at 30s
      backoffRef.current = Math.min(backoffRef.current * 2, 30000);
      timeoutId = setTimeout(poll, backoffRef.current);
    };

    // Initial check immediately, then back off
    checkLlmStatus();
    timeoutId = setTimeout(poll, backoffRef.current);

    livekit.getToken({
      participant_name: 'client',
      room_name: `avatario-${selectedPersonaId}`,
      role: selectedPersonaId,
    })
      .then(data => { setToken(data.token); setUrl(data.url); })
      .catch(err => console.error("Failed to fetch LiveKit token:", err));

    return () => clearTimeout(timeoutId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPersonaId]);

  if (!selectedPersonaId) {
    return (
      <div className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-6">
        <h1 className="text-3xl font-light text-white mb-2 tracking-tight">AI Assistant <span className="font-medium text-blue-500">Hub</span></h1>
        <p className="text-neutral-400 mb-12">Choose your AI specialist from any industry</p>

        {personasError && (
          <p className="text-red-400 text-sm mb-6">{personasError}</p>
        )}

        {personas.length === 0 && !personasError && (
          <p className="text-neutral-500 text-sm mb-6 animate-pulse">Loading personas...</p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-6xl">
          {personas.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelectedPersonaId(p.id)}
              className="group relative overflow-hidden rounded-3xl bg-neutral-900 border border-neutral-800 p-6 text-left transition-all hover:border-neutral-700 hover:scale-[1.02] flex flex-col items-center"
            >
              <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 bg-gradient-to-br ${p.color} transition-opacity duration-500`} />
              
              {/* Static avatar preview */}
              <div className="relative w-28 h-28 mb-4 rounded-full overflow-hidden border-4 border-neutral-800 shadow-xl">
                <AIAvatar
                  config={p.avatarConfig}
                  isSpeaking={false}
                  isListening={false}
                  audioLevel={0}
                  size={112}
                />
              </div>
              
              {/* Vertical badge */}
              <span className={`px-3 py-1 rounded-full text-xs font-medium mb-2 bg-gradient-to-r ${p.color} text-white capitalize`}>
                {p.avatarConfig.vertical}
              </span>
              
              <h2 className="text-xl font-medium text-white mb-1 text-center">{p.name}</h2>
              <p className="text-neutral-400 text-sm text-center">{p.greeting}</p>
            </button>
          ))}
        </div>
        
        {/* Vertical filter tabs */}
        <div className="mt-12 flex flex-wrap justify-center gap-2">
          {['all', 'legal', 'medical', 'finance', 'generic'].map((vertical) => (
            <button
              key={vertical}
              onClick={() => {
                // Filter logic would go here
                console.log(`Filter by: ${vertical}`);
              }}
              className="px-4 py-2 rounded-full bg-neutral-800 text-neutral-300 hover:bg-neutral-700 hover:text-white transition-colors text-sm capitalize"
            >
              {vertical}
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (!token || !url || (llmStatus !== "running" && llmStatus !== "unknown")) {
    return (
      <div className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-6 text-center">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-6" />
        <h2 className="text-xl text-white mb-2">
          {llmStatus === "starting" || llmStatus === "pending" 
            ? "Waking up legal engine..." 
            : "Initializing secure session..."}
        </h2>
        <p className="text-neutral-500 max-w-xs">
          {llmStatus === "starting" || llmStatus === "pending"
            ? "This usually takes 2-3 minutes as we load the specialized legal models on AWS G5."
            : "Preparing real-time voice environment..."}
        </p>
      </div>
    );
  }

  return (
    <LiveKitRoom
      token={token}
      serverUrl={url}
      connect={true}
      audio={true}
      video={false}
    >
      <VoiceAssistantUI 
        selectedPersona={selectedPersona} 
        onDisconnect={() => setSelectedPersonaId(null)} 
      />
    </LiveKitRoom>
  );
}
