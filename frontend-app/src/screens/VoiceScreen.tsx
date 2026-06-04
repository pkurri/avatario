import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, Dimensions, ActivityIndicator } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withRepeat, withTiming, withSequence, Easing } from 'react-native-reanimated';
import { Mic, Square } from 'lucide-react-native';
import { LiveKitRoom, useRoomContext, AudioSession } from '@livekit/react-native';
import { apiUrl } from '../config/api';

const { width } = Dimensions.get('window');

const personas = [
  {
    id: "client",
    name: "Advocate Anya",
    color: "#3b82f6", // Blue
    greetingText: "Empathetic Legal Guide for Clients",
    avatarPath: require('../../assets/avatars/anya.png')
  },
  {
    id: "lawyer",
    name: "Senior Counsel Vikram",
    color: "#334155", // Slate
    greetingText: "Strategic Advisor for Legal Professionals",
    avatarPath: require('../../assets/avatars/vikram.png')
  }
];

// Inner component that actually accesses the LiveKit Room context
function VoiceAssistantUI({ selectedPersona, onDisconnect }: { selectedPersona: any, onDisconnect: () => void }) {
  const room = useRoomContext();
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  // Reanimated Pulsing Logic
  const pulseScale = useSharedValue(1);
  const pulseOpacity = useSharedValue(0.2);

  useEffect(() => {
    if (!room) return;
    
    // In a full implementation, you would bind to room.on(RoomEvent.ActiveSpeakersChanged)
    // or use a helper hook if provided by the SDK. For now we simulate state changes
    // based on connection status.
    const handleActiveSpeakers = (speakers: any[]) => {
       const agentSpeaking = speakers.some(s => !s.isLocal);
       const userSpeaking = speakers.some(s => s.isLocal);
       
       setIsPlaying(agentSpeaking);
       setIsRecording(userSpeaking && !agentSpeaking);
    };

    room.on('activeSpeakersChanged', handleActiveSpeakers);
    return () => {
      room.off('activeSpeakersChanged', handleActiveSpeakers);
    };
  }, [room]);

  useEffect(() => {
    if (isPlaying) {
      pulseScale.value = withRepeat(
        withSequence(
          withTiming(1.2, { duration: 1000, easing: Easing.inOut(Easing.ease) }),
          withTiming(1, { duration: 1000, easing: Easing.inOut(Easing.ease) })
        ),
        -1, // infinite
        true 
      );
      pulseOpacity.value = withRepeat(
        withSequence(
          withTiming(0.6, { duration: 1000 }),
          withTiming(0.2, { duration: 1000 })
        ),
        -1,
        true
      );
    } else {
      pulseScale.value = withTiming(1, { duration: 500 });
      pulseOpacity.value = withTiming(0, { duration: 500 });
    }
  }, [isPlaying]);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ scale: pulseScale.value }],
      opacity: pulseOpacity.value,
    };
  });

  const isConnected = room?.state === 'connected';

  return (
    <View style={styles.chatContainer}>
      <TouchableOpacity style={styles.backButton} onPress={onDisconnect}>
         <Text style={styles.backButtonText}>← Change Persona</Text>
      </TouchableOpacity>

      <View style={styles.avatarContainer}>
          <Animated.View style={[
             styles.glowRing, 
             { backgroundColor: selectedPersona?.color },
             animatedStyle
          ]} />
          
          <Image source={selectedPersona?.avatarPath} style={styles.mainAvatar} />
      </View>

      <View style={styles.infoContainer}>
         <Text style={styles.chatName}>{selectedPersona?.name}</Text>
         <Text style={styles.statusText}>
           {!isConnected ? "Connecting to LiveKit Room..." : 
             isRecording ? "🔴 Listening..." : 
             isPlaying ? "Speaking..." : "Agent is Idle"
           }
         </Text>
      </View>

      <View 
         style={[
           styles.micButton, 
           isRecording ? styles.micButtonRecording : (isConnected ? styles.micButtonIdle : styles.micButtonDisabled)
         ]}
      >
        {isRecording ? <Square color="white" size={32} /> : <Mic color="black" size={32} />}
      </View>
    </View>
  );
}

export default function VoiceScreen() {
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null);
  const [token, setToken] = useState("");
  const [url, setUrl] = useState("");
  
  const selectedPersona = personas.find(p => p.id === selectedPersonaId) || null;

  useEffect(() => {
    if (selectedPersonaId) {
      // Allow audio playback in iOS silent mode via AudioSession
      AudioSession.startAudioSession();
      
      // Fetch LiveKit connection details from FastAPI Backend
      fetch(apiUrl('/get_livekit_token', {
        participant_name: 'mobile_client',
        room_name: `avatario-${selectedPersonaId}`,
        role: selectedPersonaId,
      }))
        .then(res => res.json())
        .then(data => {
          setToken(data.token);
          setUrl(data.url);
        })
        .catch(err => console.error("Failed to fetch LiveKit token:", err));
    } else {
      setToken("");
      setUrl("");
      AudioSession.stopAudioSession();
    }
  }, [selectedPersonaId]);

  // Screen 1: Selection
  if (!selectedPersonaId) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Avatario</Text>
        <Text style={styles.subtitle}>Start a LiveKit voice or video call with an AI persona.</Text>
        
        {personas.map(p => (
           <TouchableOpacity 
             key={p.id} 
             style={styles.card}
             onPress={() => setSelectedPersonaId(p.id)}
           >
             <Image source={p.avatarPath} style={styles.cardImage} />
             <Text style={styles.cardName}>{p.name}</Text>
             <Text style={styles.cardDesc}>{p.greetingText}</Text>
           </TouchableOpacity>
        ))}
      </View>
    );
  }

  // Loading Token
  if (!token || !url) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={{color: 'white', marginTop: 16}}>Securing WebRTC channel...</Text>
      </View>
    );
  }

  // Screen 2: Voice Chat with LiveKit
  return (
    <LiveKitRoom
      serverUrl={url}
      token={token}
      connect={true}
      audio={true}
      video={true}
    >
      <VoiceAssistantUI 
        selectedPersona={selectedPersona} 
        onDisconnect={() => setSelectedPersonaId(null)} 
      />
    </LiveKitRoom>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#09090b', // neutral-950
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: '300',
    color: 'white',
    marginBottom: 8,
  },
  titleHighlight: {
    fontWeight: '500',
    color: '#3b82f6',
  },
  subtitle: {
    color: '#a1a1aa', // neutral-400
    marginBottom: 48,
    fontSize: 16,
  },
  card: {
    width: '100%',
    backgroundColor: '#171717', // neutral-900
    borderRadius: 24,
    padding: 24,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#262626',
    alignItems: 'center',
  },
  cardImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 16,
  },
  cardName: {
    fontSize: 20,
    fontWeight: '600',
    color: 'white',
    marginBottom: 8,
  },
  cardDesc: {
    color: '#a1a1aa',
    textAlign: 'center',
  },
  chatContainer: {
    flex: 1,
    backgroundColor: '#09090b',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  backButton: {
    position: 'absolute',
    top: 60,
    left: 24,
    zIndex: 50,
  },
  backButtonText: {
    color: '#a1a1aa',
    fontSize: 16,
  },
  avatarContainer: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 48,
  },
  mainAvatar: {
    width: 200,
    height: 200,
    borderRadius: 100,
    borderWidth: 4,
    borderColor: '#262626',
    zIndex: 10,
  },
  glowRing: {
    position: 'absolute',
    width: 200,
    height: 200,
    borderRadius: 100,
    zIndex: 1,
  },
  infoContainer: {
    alignItems: 'center',
    height: 80,
  },
  chatName: {
    fontSize: 24,
    fontWeight: '500',
    color: 'white',
    marginBottom: 8,
  },
  statusText: {
    color: '#a1a1aa',
    fontSize: 16,
  },
  micButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 24,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    elevation: 8,
  },
  micButtonIdle: {
    backgroundColor: 'white',
  },
  micButtonRecording: {
    backgroundColor: '#ef4444', 
  },
  micButtonDisabled: {
    backgroundColor: '#262626',
  }
});
