import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';

interface RealtimeVoiceProps {
  onTranscript: (text: string) => void;
  onInterrupt: () => void;
  isPlaying: boolean;
}

export const RealtimeVoice: React.FC<RealtimeVoiceProps> = ({
  onTranscript,
  onInterrupt,
  isPlaying
}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const sendAudioForTranscription = useCallback(async (blob: Blob) => {
    const formData = new FormData();
    formData.append('audio', blob);
    
    try {
      const response = await fetch('/api/voice/transcribe', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.text) {
        setTranscript(data.text);
        onTranscript(data.text);
      }
    } catch (error) {
      console.error('Transcription error:', error);
    }
  }, [onTranscript]);

  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      const chunks: Blob[] = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        sendAudioForTranscription(blob);
      };
      
      mediaRecorder.start(100);
      setIsListening(true);
      
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const checkAudioLevel = () => {
        if (!isListening) return;
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average);
        
        if (isPlaying && average > 50) {
          onInterrupt();
        }
        
        requestAnimationFrame(checkAudioLevel);
      };
      checkAudioLevel();
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  }, [isPlaying, onInterrupt, isListening, sendAudioForTranscription]);

  const stopListening = useCallback(() => {
    mediaRecorderRef.current?.stop();
    streamRef.current?.getTracks().forEach(track => track.stop());
    audioContextRef.current?.close();
    setIsListening(false);
    setAudioLevel(0);
  }, []);

  useEffect(() => {
    return () => {
      stopListening();
    };
  }, [stopListening]);

  return (
    <div className="flex flex-col items-center gap-4">
      <motion.button
        onClick={isListening ? stopListening : startListening}
        className={`relative w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all ${
          isListening 
            ? 'bg-red-500 hover:bg-red-600' 
            : 'bg-blue-500 hover:bg-blue-600'
        }`}
        whileTap={{ scale: 0.95 }}
        animate={{
          boxShadow: isListening 
            ? `0 0 ${20 + audioLevel / 5}px rgba(239, 68, 68, 0.5)`
            : '0 0 0px rgba(59, 130, 246, 0)'
        }}
      >
        {isListening ? '⏹️' : '🎤'}
        {isListening && (
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-red-400"
            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
      </motion.button>
      
      {isListening && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-gray-600"
        >
          Listening... {transcript && `("${transcript}")`}
        </motion.div>
      )}
      
      {isPlaying && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded-full"
        >
          Speaking (click mic to interrupt)
        </motion.div>
      )}
    </div>
  );
};

export default RealtimeVoice;
