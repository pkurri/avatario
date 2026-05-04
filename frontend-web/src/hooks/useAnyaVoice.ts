import { useState, useRef, useCallback, useEffect } from 'react';

type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';
type Role = 'client' | 'lawyer';

export function useAnyaVoice(role: Role = 'client') {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [messages, setMessages] = useState<{sender: string, text: string}[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  // Initialize AudioContext
  useEffect(() => {
    // Only initialize in browser
    if (typeof window !== 'undefined') {
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      audioContextRef.current = new AudioContext();
    }
    return () => {
      audioContextRef.current?.close();
    };
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionState('connecting');
    const ws = new WebSocket(`ws://localhost:8000/chat/${role}`);

    ws.onopen = () => {
      setConnectionState('connected');
    };

    ws.onmessage = async (event) => {
      if (typeof event.data === 'string') {
        const data = JSON.parse(event.data);
        if (data.type === 'text' || data.type === 'info') {
           setMessages(prev => [...prev, { sender: 'Anya', text: data.content }]);
        }
      } else if (event.data instanceof Blob) {
         // Received binary audio string from Sarvam TTS!
         playAudio(event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setConnectionState('error');
    };

    ws.onclose = () => {
      setConnectionState('disconnected');
    };

    wsRef.current = ws;
  }, [role]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const playAudio = async (audioBlob: Blob) => {
    if (!audioContextRef.current) return;
    
    setIsPlaying(true);
    try {
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
      
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      
      source.onended = () => {
        setIsPlaying(false);
      };
      
      source.start();
    } catch (e) {
      console.error("Failed to play audio:", e);
      setIsPlaying(false);
    }
  };

  const startRecording = async () => {
    if (connectionState !== 'connected') {
       console.warn('Cannot record when disconnected');
       return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Use webm for best browser compatibility with Sarvam endpoints
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        // Send the blob to the backend over WebSocket
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(blob);
          setMessages(prev => [...prev, { sender: 'You', text: '(Voice Input Sent)' }]);
        }
        
        // Cleanup stream tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Failed to get microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return {
    connectionState,
    isRecording,
    isPlaying,
    messages,
    connect,
    disconnect,
    startRecording,
    stopRecording
  };
}
