import React, { createContext, useContext, useState, useCallback } from 'react';
import { Alert } from 'react-native';
import * as FileSystem from 'expo-file-system';
import { Audio } from 'expo-av';
import { apiUrl } from '../config/api';

interface VoiceClone {
  id: string;
  name: string;
  status: 'recording' | 'processing' | 'ready' | 'error';
  recordingUri?: string;
  voiceId?: string;
  previewUrl?: string;
  createdAt: Date;
}

interface VoiceContextType {
  voices: VoiceClone[];
  currentRecording: Audio.Recording | null;
  isRecording: boolean;
  recordingDuration: number;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string | null>;
  uploadVoiceSample: (name: string) => Promise<void>;
  deleteVoice: (voiceId: string) => Promise<void>;
  previewVoice: (voiceId: string, text?: string) => Promise<void>;
  selectedVoice: VoiceClone | null;
  setSelectedVoice: (voice: VoiceClone | null) => void;
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

export function VoiceProvider({ children }: { children: React.ReactNode }) {
  const [voices, setVoices] = useState<VoiceClone[]>([]);
  const [currentRecording, setCurrentRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [selectedVoice, setSelectedVoice] = useState<VoiceClone | null>(null);
  const [recordingInterval, setRecordingInterval] = useState<NodeJS.Timeout | null>(null);

  // Request microphone permissions
  const requestPermissions = async () => {
    const { status } = await Audio.requestPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission required', 'Microphone access is needed for voice cloning');
      return false;
    }
    return true;
  };

  // Start recording voice sample
  const startRecording = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      setCurrentRecording(recording);
      setIsRecording(true);
      setRecordingDuration(0);

      // Track recording duration
      const interval = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
      setRecordingInterval(interval);

    } catch (error) {
      console.error('Failed to start recording', error);
      Alert.alert('Error', 'Could not start recording');
    }
  };

  // Stop recording
  const stopRecording = async (): Promise<string | null> => {
    if (!currentRecording) return null;

    try {
      await currentRecording.stopAndUnloadAsync();
      
      if (recordingInterval) {
        clearInterval(recordingInterval);
        setRecordingInterval(null);
      }

      const uri = currentRecording.getURI();
      setIsRecording(false);
      setCurrentRecording(null);
      
      return uri;
    } catch (error) {
      console.error('Failed to stop recording', error);
      return null;
    }
  };

  // Upload voice sample to ElevenLabs for cloning
  const uploadVoiceSample = async (name: string) => {
    if (!currentRecording) return;

    const uri = currentRecording.getURI();
    if (!uri) return;

    // Create a temporary voice entry
    const tempVoice: VoiceClone = {
      id: Date.now().toString(),
      name,
      status: 'processing',
      recordingUri: uri,
      createdAt: new Date(),
    };

    setVoices(prev => [...prev, tempVoice]);

    try {
      // Read the recording file
      const fileInfo = await FileSystem.getInfoAsync(uri);
      if (!fileInfo.exists) throw new Error('Recording file not found');

      // Upload to backend which will handle ElevenLabs API
      const formData = new FormData();
      formData.append('name', name);
      formData.append('description', `Cloned voice for ${name}`);
      formData.append('files', {
        uri: uri,
        name: 'voice_sample.m4a',
        type: 'audio/m4a',
      } as any);

      const response = await fetch(apiUrl('/voice/clone'), {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) throw new Error('Voice cloning failed');

      const data = await response.json();

      // Update voice with ElevenLabs voice_id
      setVoices(prev => 
        prev.map(v => 
          v.id === tempVoice.id 
            ? { ...v, voiceId: data.voice_id, status: 'ready' as const }
            : v
        )
      );

      Alert.alert('Success', 'Voice cloned successfully!');

    } catch (error) {
      console.error('Voice cloning error:', error);
      setVoices(prev => 
        prev.map(v => 
          v.id === tempVoice.id 
            ? { ...v, status: 'error' as const }
            : v
        )
      );
      Alert.alert('Error', 'Failed to clone voice. Please try again.');
    }
  };

  // Delete a cloned voice
  const deleteVoice = async (voiceId: string) => {
    try {
      const voice = voices.find(v => v.voiceId === voiceId);
      if (voice?.voiceId) {
        await fetch(apiUrl(`/voice/clones/${voice.voiceId}`), {
          method: 'DELETE',
        });
      }

      setVoices(prev => prev.filter(v => v.voiceId !== voiceId));
      
      if (selectedVoice?.voiceId === voiceId) {
        setSelectedVoice(null);
      }

    } catch (error) {
      console.error('Failed to delete voice:', error);
    }
  };

  // Preview cloned voice
  const previewVoice = async (voiceId: string, text: string = 'Hello! This is my cloned voice.') => {
    try {
      const response = await fetch(apiUrl('/voice/synthesize'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          voice_id: voiceId,
          text,
        }),
      });

      if (!response.ok) throw new Error('Synthesis failed');

      const data = await response.json();
      
      // Play the audio
      const { sound } = await Audio.Sound.createAsync(
        { uri: data.audio_url },
        { shouldPlay: true }
      );

    } catch (error) {
      console.error('Voice preview error:', error);
      Alert.alert('Error', 'Could not preview voice');
    }
  };

  return (
    <VoiceContext.Provider
      value={{
        voices,
        currentRecording,
        isRecording,
        recordingDuration,
        startRecording,
        stopRecording,
        uploadVoiceSample,
        deleteVoice,
        previewVoice,
        selectedVoice,
        setSelectedVoice,
      }}
    >
      {children}
    </VoiceContext.Provider>
  );
}

export function useVoice() {
  const context = useContext(VoiceContext);
  if (!context) {
    throw new Error('useVoice must be used within a VoiceProvider');
  }
  return context;
}
