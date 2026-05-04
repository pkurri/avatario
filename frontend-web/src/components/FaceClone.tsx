"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  Link,
  Sparkles,
  Camera,
  RefreshCw,
  Play,
  Trash2,
  User,
  Loader2,
  X,
  Video,
  Mic,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

const API_BASE = "http://localhost:8000";

// ==========================================
// TYPES
// ==========================================

interface ClonedFace {
  id: string;
  name: string;
  mode: "clone" | "generate";
  source: string;
  status: "processing" | "ready" | "talking" | "error";
  image_url: string;
  thumbnail_url: string;
  created_at: string;
  gender?: string;
  ethnicity?: string;
  age?: string;
  profession?: string;
  video_count: number;
  error?: string;
  metadata?: Record<string, unknown>;
}

interface TalkResult {
  face_id: string;
  name: string;
  text: string;
  video_url?: string | null;
  audio_url?: string | null;
  image_url?: string;
  status: string;
  error?: string;
  cached?: boolean;
  has_video?: boolean;
  has_audio?: boolean;
}

interface FaceCloneProps {
  onFaceSelected?: (face: ClonedFace) => void;
  isSpeaking?: boolean;
  isListening?: boolean;
  speakingText?: string;
  size?: number;
  className?: string;
}

// ==========================================
// FACE CLONE COMPONENT
// ==========================================

export function FaceClone({
  onFaceSelected,
  isSpeaking = false,
  isListening = false,
  speakingText,
  size = 320,
  className = "",
}: FaceCloneProps) {
  const [faces, setFaces] = useState<ClonedFace[]>([]);
  const [activeFace, setActiveFace] = useState<ClonedFace | null>(null);
  const [activeVideo, setActiveVideo] = useState<string | null>(null);
  const [activeAudio, setActiveAudio] = useState<string | null>(null);
  const [isFaceTalking, setIsFaceTalking] = useState(false);
  const [view, setView] = useState<"gallery" | "upload" | "url" | "generate">("gallery");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load existing faces on mount
  useEffect(() => {
    loadFaces();
  }, []);

  const loadFaces = async () => {
    try {
      const res = await fetch(`${API_BASE}/face-clone/list`);
      if (res.ok) {
        const data = await res.json();
        setFaces(data.faces || []);
      }
    } catch {
      // silent
    }
  };

  const selectFace = (face: ClonedFace) => {
    setActiveFace(face);
    setActiveVideo(null);
    setActiveAudio(null);
    onFaceSelected?.(face);
  };

  const deleteFace = async (faceId: string) => {
    try {
      await fetch(`${API_BASE}/face-clone/${faceId}`, { method: "DELETE" });
      setFaces((prev) => prev.filter((f) => f.id !== faceId));
      if (activeFace?.id === faceId) {
        setActiveFace(null);
        setActiveVideo(null);
        setActiveAudio(null);
      }
    } catch {
      // silent
    }
  };

  // Handle speaking text changes
  useEffect(() => {
    if (isSpeaking && speakingText && activeFace) {
      makeTalk(activeFace.id, speakingText);
    }
  }, [isSpeaking, speakingText]);

  const makeTalk = async (faceId: string, text: string): Promise<TalkResult | null> => {
    setIsFaceTalking(true);
    try {
      const res = await fetch(`${API_BASE}/face-clone/talk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ face_id: faceId, text }),
      });
      if (res.ok) {
        const data: TalkResult = await res.json();
        if (data.video_url) {
          setActiveVideo(`${API_BASE}${data.video_url}`);
        }
        if (data.audio_url) {
          setActiveAudio(`${API_BASE}${data.audio_url}`);
        }
        return data;
      }
    } catch {
      // silent
    } finally {
      setIsFaceTalking(false);
    }
    return null;
  };

  // If we have an active face, show it
  if (activeFace) {
    return (
      <ActiveFaceDisplay
        face={activeFace}
        videoUrl={activeVideo}
        audioUrl={activeAudio}
        isSpeaking={isSpeaking}
        isListening={isListening}
        isFaceTalking={isFaceTalking}
        size={size}
        onBack={() => { setActiveFace(null); setActiveVideo(null); setActiveAudio(null); }}
        onRegenerate={() => loadFaces()}
        onMakeTalk={(text) => makeTalk(activeFace.id, text)}
        className={className}
      />
    );
  }

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <AnimatePresence mode="wait">
        {view === "gallery" ? (
          <GalleryView
            key="gallery"
            faces={faces}
            onSelect={selectFace}
            onDelete={deleteFace}
            onSwitchView={setView}
            size={size}
          />
        ) : view === "upload" ? (
          <UploadView
            key="upload"
            onDone={(face) => { setFaces((p) => [face, ...p]); selectFace(face); setView("gallery"); }}
            onBack={() => setView("gallery")}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
            error={error}
            setError={setError}
          />
        ) : view === "url" ? (
          <UrlCloneView
            key="url"
            onDone={(face) => { setFaces((p) => [face, ...p]); selectFace(face); setView("gallery"); }}
            onBack={() => setView("gallery")}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
            error={error}
            setError={setError}
          />
        ) : (
          <GenerateView
            key="generate"
            onDone={(face) => { setFaces((p) => [face, ...p]); selectFace(face); setView("gallery"); }}
            onBack={() => setView("gallery")}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
            error={error}
            setError={setError}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// ==========================================
// GALLERY VIEW
// ==========================================

function GalleryView({
  faces,
  onSelect,
  onDelete,
  onSwitchView,
  size,
}: {
  faces: ClonedFace[];
  onSelect: (f: ClonedFace) => void;
  onDelete: (id: string) => void;
  onSwitchView: (v: "gallery" | "upload" | "url" | "generate") => void;
  size: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center gap-4"
      style={{ maxWidth: size + 80 }}
    >
      <h3 className="text-white text-lg font-medium">Face Clone Studio</h3>
      <p className="text-neutral-400 text-xs text-center">
        Clone any real person or generate a new AI face for conversational AI
      </p>

      {/* Action buttons */}
      <div className="flex gap-2 flex-wrap justify-center">
        <button
          onClick={() => onSwitchView("upload")}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white rounded-xl text-sm font-medium transition-all shadow-lg shadow-blue-500/20"
        >
          <Upload className="w-4 h-4" />
          Upload Photo
        </button>
        <button
          onClick={() => onSwitchView("url")}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white rounded-xl text-sm font-medium transition-all shadow-lg shadow-purple-500/20"
        >
          <Link className="w-4 h-4" />
          From URL
        </button>
        <button
          onClick={() => onSwitchView("generate")}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-orange-600 to-pink-500 hover:from-orange-500 hover:to-pink-400 text-white rounded-xl text-sm font-medium transition-all shadow-lg shadow-orange-500/20"
        >
          <Sparkles className="w-4 h-4" />
          Generate New
        </button>
      </div>

      {/* Existing faces grid */}
      {faces.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mt-2 w-full">
          {faces.map((face) => (
            <motion.div
              key={face.id}
              whileHover={{ scale: 1.05 }}
              className="relative group cursor-pointer"
              onClick={() => onSelect(face)}
            >
              <div className="w-full aspect-square rounded-xl overflow-hidden bg-neutral-800 border border-neutral-700 group-hover:border-blue-500/50 transition-colors">
                <img
                  src={`${API_BASE}${face.image_url}`}
                  alt={face.name}
                  className="w-full h-full object-cover"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                  <span className="text-white text-xs font-medium truncate">{face.name}</span>
                </div>
                {/* Mode badge */}
                <div className={`absolute top-1 right-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
                  face.mode === "clone"
                    ? "bg-blue-500/80 text-white"
                    : "bg-orange-500/80 text-white"
                }`}>
                  {face.mode === "clone" ? "Clone" : "AI"}
                </div>
                {/* Status */}
                {face.status === "error" && (
                  <div className="absolute top-1 left-1">
                    <AlertCircle className="w-4 h-4 text-red-400" />
                  </div>
                )}
              </div>
              {/* Delete button */}
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(face.id); }}
                className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="w-3 h-3 text-white" />
              </button>
            </motion.div>
          ))}
        </div>
      )}

      {faces.length === 0 && (
        <div className="text-center py-8 text-neutral-500 text-sm">
          <User className="w-12 h-12 mx-auto mb-2 opacity-30" />
          No faces yet. Upload, paste a URL, or generate one.
        </div>
      )}
    </motion.div>
  );
}

// ==========================================
// UPLOAD VIEW
// ==========================================

function UploadView({
  onDone,
  onBack,
  isLoading,
  setIsLoading,
  error,
  setError,
}: {
  onDone: (face: ClonedFace) => void;
  onBack: () => void;
  isLoading: boolean;
  setIsLoading: (b: boolean) => void;
  error: string | null;
  setError: (e: string | null) => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("name", name || "Cloned Person");

      const res = await fetch(`${API_BASE}/face-clone/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      const data = await res.json();
      if (data.error) throw new Error(data.error);
      onDone(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="flex flex-col items-center gap-4 w-full max-w-sm"
    >
      <button onClick={onBack} className="self-start text-neutral-400 hover:text-white text-sm flex items-center gap-1">
        ← Back
      </button>

      <h3 className="text-white text-lg font-medium flex items-center gap-2">
        <Camera className="w-5 h-5 text-blue-400" />
        Clone from Photo
      </h3>

      {/* Drop zone */}
      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); }}
        className="w-full aspect-square max-w-[240px] rounded-2xl border-2 border-dashed border-neutral-600 hover:border-blue-500/50 bg-neutral-900 flex flex-col items-center justify-center cursor-pointer transition-colors overflow-hidden"
      >
        {preview ? (
          <img src={preview} alt="Preview" className="w-full h-full object-cover" />
        ) : (
          <>
            <Upload className="w-10 h-10 text-neutral-500 mb-2" />
            <p className="text-neutral-400 text-sm">Drop photo or click to upload</p>
            <p className="text-neutral-600 text-xs mt-1">Clear frontal face works best</p>
          </>
        )}
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />

      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Name this person..."
        className="w-full max-w-[240px] px-4 py-2.5 bg-neutral-800 border border-neutral-700 rounded-xl text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-blue-500/50"
      />

      {error && <p className="text-red-400 text-xs">{error}</p>}

      <button
        onClick={handleUpload}
        disabled={!selectedFile || isLoading}
        className="w-full max-w-[240px] py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-700 disabled:text-neutral-500 text-white rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
        {isLoading ? "Cloning..." : "Clone Face"}
      </button>
    </motion.div>
  );
}

// ==========================================
// URL CLONE VIEW
// ==========================================

function UrlCloneView({
  onDone,
  onBack,
  isLoading,
  setIsLoading,
  error,
  setError,
}: {
  onDone: (face: ClonedFace) => void;
  onBack: () => void;
  isLoading: boolean;
  setIsLoading: (b: boolean) => void;
  error: string | null;
  setError: (e: string | null) => void;
}) {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");

  const handleClone = async () => {
    if (!url) return;
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/face-clone/from-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: url, name: name || "Cloned Person" }),
      });

      if (!res.ok) throw new Error("Clone failed");

      const data = await res.json();
      if (data.error) throw new Error(data.error);
      onDone(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clone failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="flex flex-col items-center gap-4 w-full max-w-sm"
    >
      <button onClick={onBack} className="self-start text-neutral-400 hover:text-white text-sm flex items-center gap-1">
        ← Back
      </button>

      <h3 className="text-white text-lg font-medium flex items-center gap-2">
        <Link className="w-5 h-5 text-purple-400" />
        Clone from URL
      </h3>

      <div className="w-full max-w-[300px] aspect-video rounded-2xl bg-neutral-900 border border-neutral-700 flex items-center justify-center overflow-hidden">
        {url ? (
          <img
            src={url}
            alt="Preview"
            className="w-full h-full object-cover"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
          />
        ) : (
          <Link className="w-10 h-10 text-neutral-600" />
        )}
      </div>

      <input
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="Paste image URL..."
        className="w-full max-w-[300px] px-4 py-2.5 bg-neutral-800 border border-neutral-700 rounded-xl text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-purple-500/50"
      />

      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Name this person..."
        className="w-full max-w-[300px] px-4 py-2.5 bg-neutral-800 border border-neutral-700 rounded-xl text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-purple-500/50"
      />

      {error && <p className="text-red-400 text-xs">{error}</p>}

      <button
        onClick={handleClone}
        disabled={!url || isLoading}
        className="w-full max-w-[300px] py-2.5 bg-purple-600 hover:bg-purple-500 disabled:bg-neutral-700 disabled:text-neutral-500 text-white rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Link className="w-4 h-4" />}
        {isLoading ? "Cloning..." : "Clone Face"}
      </button>
    </motion.div>
  );
}

// ==========================================
// GENERATE VIEW
// ==========================================

function GenerateView({
  onDone,
  onBack,
  isLoading,
  setIsLoading,
  error,
  setError,
}: {
  onDone: (face: ClonedFace) => void;
  onBack: () => void;
  isLoading: boolean;
  setIsLoading: (b: boolean) => void;
  error: string | null;
  setError: (e: string | null) => void;
}) {
  const [name, setName] = useState("");
  const [gender, setGender] = useState("female");
  const [ethnicity, setEthnicity] = useState("indian");
  const [age, setAge] = useState("middle");
  const [profession, setProfession] = useState("generic");

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/face-clone/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name || "AI Person",
          gender,
          ethnicity,
          age,
          profession,
        }),
      });

      if (!res.ok) throw new Error("Generation failed");

      const data = await res.json();
      if (data.error) throw new Error(data.error);
      onDone(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setIsLoading(false);
    }
  };

  const SelectButton = ({
    label,
    value,
    current,
    onClick,
  }: {
    label: string;
    value: string;
    current: string;
    onClick: (v: string) => void;
  }) => (
    <button
      onClick={() => onClick(value)}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
        current === value
          ? "bg-orange-500/20 text-orange-400 border border-orange-500/50"
          : "bg-neutral-800 text-neutral-400 border border-neutral-700 hover:border-neutral-600"
      }`}
    >
      {label}
    </button>
  );

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="flex flex-col items-center gap-3 w-full max-w-sm"
    >
      <button onClick={onBack} className="self-start text-neutral-400 hover:text-white text-sm flex items-center gap-1">
        ← Back
      </button>

      <h3 className="text-white text-lg font-medium flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-orange-400" />
        Generate New AI Face
      </h3>

      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Name (e.g. Dr. Priya)..."
        className="w-full max-w-[300px] px-4 py-2.5 bg-neutral-800 border border-neutral-700 rounded-xl text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-orange-500/50"
      />

      {/* Gender */}
      <div className="w-full max-w-[300px]">
        <p className="text-neutral-500 text-xs mb-1.5">Gender</p>
        <div className="flex gap-2">
          <SelectButton label="Female" value="female" current={gender} onClick={setGender} />
          <SelectButton label="Male" value="male" current={gender} onClick={setGender} />
        </div>
      </div>

      {/* Ethnicity */}
      <div className="w-full max-w-[300px]">
        <p className="text-neutral-500 text-xs mb-1.5">Ethnicity</p>
        <div className="flex gap-2 flex-wrap">
          {["indian", "asian", "caucasian", "african", "hispanic", "middle_eastern"].map((e) => (
            <SelectButton key={e} label={e.replace("_", " ")} value={e} current={ethnicity} onClick={setEthnicity} />
          ))}
        </div>
      </div>

      {/* Age */}
      <div className="w-full max-w-[300px]">
        <p className="text-neutral-500 text-xs mb-1.5">Age</p>
        <div className="flex gap-2">
          <SelectButton label="Young" value="young" current={age} onClick={setAge} />
          <SelectButton label="Middle" value="middle" current={age} onClick={setAge} />
          <SelectButton label="Mature" value="mature" current={age} onClick={setAge} />
        </div>
      </div>

      {/* Profession */}
      <div className="w-full max-w-[300px]">
        <p className="text-neutral-500 text-xs mb-1.5">Profession</p>
        <div className="flex gap-2 flex-wrap">
          {["legal", "medical", "finance", "tech", "education", "generic"].map((p) => (
            <SelectButton key={p} label={p} value={p} current={profession} onClick={setProfession} />
          ))}
        </div>
      </div>

      {error && <p className="text-red-400 text-xs">{error}</p>}

      <button
        onClick={handleGenerate}
        disabled={isLoading}
        className="w-full max-w-[300px] py-2.5 bg-gradient-to-r from-orange-600 to-pink-500 hover:from-orange-500 hover:to-pink-400 disabled:from-neutral-700 disabled:to-neutral-700 disabled:text-neutral-500 text-white rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-orange-500/20"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
        {isLoading ? "Generating with FLUX..." : "Generate AI Face"}
      </button>
    </motion.div>
  );
}

// ==========================================
// ACTIVE FACE DISPLAY
// ==========================================

function ActiveFaceDisplay({
  face,
  videoUrl,
  audioUrl,
  isSpeaking,
  isListening,
  isFaceTalking,
  size,
  onBack,
  onRegenerate,
  onMakeTalk,
  className,
}: {
  face: ClonedFace;
  videoUrl: string | null;
  audioUrl: string | null;
  isSpeaking: boolean;
  isListening: boolean;
  isFaceTalking: boolean;
  size: number;
  onBack: () => void;
  onRegenerate: () => void;
  onMakeTalk: (text: string) => Promise<TalkResult | null>;
  className: string;
}) {
  const [showVideo, setShowVideo] = useState(false);
  const [testText, setTestText] = useState("");
  const [isTalking, setIsTalking] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Play audio when audioUrl changes (audio-only mode)
  useEffect(() => {
    if (audioUrl && !videoUrl) {
      playAudio(audioUrl);
    }
  }, [audioUrl]);

  const playAudio = (url: string) => {
    // Stop any existing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    
    const audio = new Audio(url);
    audioRef.current = audio;
    
    audio.onplay = () => setIsPlayingAudio(true);
    audio.onended = () => setIsPlayingAudio(false);
    audio.onerror = () => setIsPlayingAudio(false);
    audio.onpause = () => setIsPlayingAudio(false);
    
    audio.play().catch(() => setIsPlayingAudio(false));
  };

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const handleTestTalk = async () => {
    if (!testText.trim()) return;
    setIsTalking(true);
    const result = await onMakeTalk(testText);
    if (result?.has_video && result.video_url) {
      setShowVideo(true);
    }
    setIsTalking(false);
  };

  const isAnimatedTalking = isPlayingAudio || isFaceTalking || isSpeaking;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`relative flex flex-col items-center ${className}`}
    >
      {/* Face Display */}
      <motion.div
        className="relative rounded-2xl overflow-hidden bg-neutral-900"
        style={{
          width: size,
          height: size * 1.1,
          boxShadow: isAnimatedTalking
            ? "0 0 60px rgba(59, 130, 246, 0.5)"
            : "0 20px 40px rgba(0,0,0,0.3)",
        }}
        animate={{ scale: isAnimatedTalking ? [1, 1.02, 1] : 1 }}
        transition={{ duration: 0.5, repeat: isAnimatedTalking ? Infinity : 0, repeatType: "reverse" }}
      >
        {showVideo && videoUrl ? (
          <video
            src={videoUrl}
            autoPlay
            loop={isSpeaking}
            playsInline
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <div className="relative w-full h-full">
            <img
              src={`${API_BASE}${face.image_url}`}
              alt={face.name}
              className="w-full h-full object-cover"
            />
            {/* Audio-speaking animation overlay */}
            {isPlayingAudio && (
              <>
                {/* Pulsing ring */}
                <motion.div
                  className="absolute inset-0 rounded-2xl pointer-events-none"
                  style={{ border: "3px solid rgba(59, 130, 246, 0.6)" }}
                  animate={{ opacity: [0.4, 1, 0.4], scale: [1, 1.01, 1] }}
                  transition={{ duration: 0.6, repeat: Infinity }}
                />
                {/* Sound wave bars at bottom */}
                <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex items-end gap-1">
                  {[...Array(5)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="w-1 bg-blue-400 rounded-full"
                      animate={{ height: [4, 12 + Math.random() * 12, 4] }}
                      transition={{ duration: 0.3 + i * 0.1, repeat: Infinity, delay: i * 0.08 }}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Speaking glow */}
        {isAnimatedTalking && (
          <motion.div
            className="absolute inset-0 pointer-events-none"
            style={{ boxShadow: "inset 0 0 60px rgba(59, 130, 246, 0.3)" }}
            animate={{ opacity: [0.3, 0.8, 0.3] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        )}

        {/* Listening indicator */}
        {isListening && !isAnimatedTalking && (
          <div className="absolute top-4 right-4 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
        )}

        {/* Name badge */}
        <div className="absolute top-4 left-4 px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
          <span className="text-white text-sm font-medium">{face.name}</span>
        </div>

        {/* Mode badge */}
        <div className={`absolute top-4 right-4 px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${
          face.mode === "clone"
            ? "bg-blue-500/80 text-white"
            : "bg-gradient-to-r from-orange-500 to-pink-500 text-white"
        }`}>
          {face.mode === "clone" ? (
            <><Camera className="w-3 h-3" /> Cloned</>
          ) : (
            <><Sparkles className="w-3 h-3" /> AI Generated</>
          )}
        </div>

        {/* Status */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-black/60 backdrop-blur-sm flex items-center gap-2">
          {isPlayingAudio && <><Mic className="w-3 h-3 text-blue-400 animate-pulse" /><span className="text-blue-400 text-xs">Speaking...</span></>}
          {!isPlayingAudio && face.status === "ready" && <><CheckCircle className="w-3 h-3 text-green-400" /><span className="text-white text-xs">Ready</span></>}
          {!isPlayingAudio && face.status === "talking" && <><Loader2 className="w-3 h-3 text-blue-400 animate-spin" /><span className="text-white text-xs">Generating...</span></>}
          {face.status === "error" && <><AlertCircle className="w-3 h-3 text-red-400" /><span className="text-white text-xs">Error</span></>}
        </div>
      </motion.div>

      {/* Controls */}
      <div className="flex items-center gap-2 mt-4">
        <button
          onClick={onBack}
          className="p-2 rounded-full bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors"
          title="Back to gallery"
        >
          <User className="w-4 h-4" />
        </button>
        <button
          onClick={() => setShowVideo(!showVideo)}
          disabled={!videoUrl}
          className={`p-2 rounded-full transition-colors ${
            showVideo
              ? "bg-blue-500/20 text-blue-400"
              : "bg-neutral-800 text-neutral-400 hover:text-white"
          } ${!videoUrl ? "opacity-50 cursor-not-allowed" : ""}`}
          title={showVideo ? "Show photo" : "Show video"}
        >
          <Video className="w-4 h-4" />
        </button>
        <button
          onClick={onRegenerate}
          className="p-2 rounded-full bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors"
          title="Regenerate"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Quick talk test */}
      <div className="flex gap-2 mt-3 w-full max-w-xs">
        <input
          type="text"
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleTestTalk()}
          placeholder="Type to make it talk..."
          className="flex-1 px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white text-xs placeholder-neutral-500 focus:outline-none focus:border-blue-500/50"
        />
        <button
          onClick={handleTestTalk}
          disabled={!testText.trim() || isTalking}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-700 text-white rounded-lg text-xs flex items-center gap-1"
        >
          {isTalking ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
        </button>
      </div>
    </motion.div>
  );
}

export default FaceClone;
