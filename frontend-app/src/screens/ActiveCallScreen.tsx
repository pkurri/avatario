import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  Phone,
  Mic,
  MicOff,
  Pause,
  Play,
  MessageCircle,
  ChevronDown,
} from 'lucide-react-native';
import { useCall } from '../contexts/CallContext';
import { apiUrl } from '../config/api';
import { getLanguageLabel } from '../constants/translation';

const { width } = Dimensions.get('window');

export default function ActiveCallScreen({ navigation, route }: any) {
  const { callId } = route.params || {};
  const { activeCalls, endCall, muteCall, holdCall } = useCall();
  const [isMuted, setIsMuted] = useState(false);
  const [isOnHold, setIsOnHold] = useState(false);
  const [duration, setDuration] = useState(0);
  const [translationSession, setTranslationSession] = useState<any | null>(null);
  const [transcript, setTranscript] = useState<any[]>([]);

  const call = activeCalls.find((c) => c.id === callId) || activeCalls[0];

  useEffect(() => {
    if (!call) {
      navigation.goBack();
      return;
    }

    const interval = setInterval(() => {
      setDuration((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [call, navigation]);

  useEffect(() => {
    if (!callId) {
      return;
    }

    let cancelled = false;

    const loadCallState = async () => {
      try {
        const [translationResponse, transcriptResponse] = await Promise.all([
          fetch(apiUrl(`/voice/calls/${callId}/translation`)),
          fetch(apiUrl(`/voice/calls/${callId}/transcript`)),
        ]);

        if (!cancelled && translationResponse.ok) {
          const translationData = await translationResponse.json();
          setTranslationSession(translationData.translation);
        }

        if (!cancelled && transcriptResponse.ok) {
          const transcriptData = await transcriptResponse.json();
          setTranscript(transcriptData.transcript || []);
        }
      } catch (error) {
        console.error('Failed to load call state:', error);
      }
    };

    loadCallState();
    const interval = setInterval(loadCallState, 3000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [callId]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleMute = async () => {
    await muteCall(call.id, !isMuted);
    setIsMuted(!isMuted);
  };

  const handleHold = async () => {
    await holdCall(call.id, !isOnHold);
    setIsOnHold(!isOnHold);
  };

  const handleEndCall = async () => {
    await endCall(call.id);
    navigation.goBack();
  };

  if (!call) return null;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
      {/* Header */}
      <TouchableOpacity
        style={styles.minimizeButton}
        onPress={() => navigation.goBack()}
      >
        <ChevronDown size={24} color="#ffffff" />
      </TouchableOpacity>

      {/* Call Info */}
      <View style={styles.callInfo}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {call.contactName?.charAt(0) || '#'}
          </Text>
        </View>
        
        <Text style={styles.contactName}>
          {call.contactName || call.phoneNumber}
        </Text>
        
        <Text style={styles.callStatus}>
          {isOnHold ? 'On Hold' : 'Active Call'} • {formatDuration(duration)}
        </Text>
      </View>

      {translationSession?.enabled && (
        <View style={styles.translationCard}>
          <View style={styles.translationHeader}>
            <MessageCircle size={18} color="#67e8f9" />
            <Text style={styles.translationTitle}>Live Translation Active</Text>
          </View>
          <Text style={styles.translationMeta}>
            Caller: {translationSession.auto_detect ? 'Auto detect' : getLanguageLabel(translationSession.caller_language)}
          </Text>
          <Text style={styles.translationMeta}>
            You: {getLanguageLabel(translationSession.user_language)}
          </Text>
          <Text style={styles.translationMeta}>
            Voice: {translationSession.preserve_voice ? 'Cloned voice preserved' : 'Standard multilingual TTS'}
          </Text>
        </View>
      )}

      {/* Waveform Visualization */}
      <View style={styles.waveformContainer}>
        <View style={styles.waveform}>
          {[...Array(30)].map((_, i) => (
            <View
              key={i}
              style={[
                styles.waveBar,
                {
                  height: isMuted ? 10 : 20 + Math.random() * 80,
                  opacity: isMuted ? 0.3 : 1,
                },
              ]}
            />
          ))}
        </View>
      </View>

      {/* AI Status */}
      <View style={styles.aiStatus}>
        <View style={styles.aiIndicator} />
        <Text style={styles.aiText}>
          {translationSession?.enabled ? 'AI is translating and speaking' : 'AI is speaking'}
        </Text>
      </View>

      {transcript.length > 0 && (
        <View style={styles.transcriptCard}>
          <Text style={styles.transcriptTitle}>Recent transcript</Text>
          {transcript.slice(-3).reverse().map((entry, index) => (
            <View key={`${entry.timestamp || index}-${index}`} style={styles.transcriptEntry}>
              <Text style={styles.transcriptSpeaker}>{entry.role || 'speaker'}</Text>
              <Text style={styles.transcriptText}>{entry.text}</Text>
              {entry.translated_text && entry.translated_text !== entry.text && (
                <Text style={styles.transcriptTranslation}>{entry.translated_text}</Text>
              )}
            </View>
          ))}
        </View>
      )}

      {/* Call Controls */}
      <View style={styles.controls}>
        <View style={styles.controlsRow}>
          <TouchableOpacity
            style={[styles.controlButton, isMuted && styles.controlButtonActive]}
            onPress={handleMute}
          >
            {isMuted ? (
              <MicOff size={24} color="#ffffff" />
            ) : (
              <Mic size={24} color="#374151" />
            )}
            <Text style={[styles.controlLabel, isMuted && styles.controlLabelActive]}>
              {isMuted ? 'Unmute' : 'Mute'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.controlButton, isOnHold && styles.controlButtonActive]}
            onPress={handleHold}
          >
            {isOnHold ? (
              <Play size={24} color="#ffffff" />
            ) : (
              <Pause size={24} color="#374151" />
            )}
            <Text style={[styles.controlLabel, isOnHold && styles.controlLabelActive]}>
              {isOnHold ? 'Resume' : 'Hold'}
            </Text>
          </TouchableOpacity>

          <View style={styles.controlButtonStatic}>
            <MessageCircle size={24} color="#374151" />
            <Text style={styles.controlLabelStatic}>
              {translationSession?.enabled ? 'Live' : 'Ready'}
            </Text>
          </View>
        </View>

        {/* End Call */}
        <TouchableOpacity
          style={styles.endCallButton}
          onPress={handleEndCall}
        >
          <Phone size={32} color="#ffffff" />
        </TouchableOpacity>
      </View>

      {/* Bottom Padding */}
      <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  scrollContent: {
    paddingBottom: 40,
  },
  minimizeButton: {
    alignSelf: 'center',
    padding: 8,
    marginTop: 8,
  },
  callInfo: {
    alignItems: 'center',
    marginTop: 40,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#6366f1',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  contactName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  callStatus: {
    fontSize: 16,
    color: '#9ca3af',
    marginTop: 8,
  },
  waveformContainer: {
    minHeight: 180,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  waveform: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  waveBar: {
    width: 4,
    backgroundColor: '#6366f1',
    borderRadius: 2,
  },
  aiStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  aiIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#22c55e',
    marginRight: 8,
  },
  aiText: {
    fontSize: 14,
    color: '#9ca3af',
  },
  controls: {
    paddingHorizontal: 40,
  },
  controlsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 40,
  },
  controlButton: {
    alignItems: 'center',
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
  },
  controlButtonActive: {
    backgroundColor: '#6366f1',
  },
  controlLabel: {
    position: 'absolute',
    bottom: -24,
    fontSize: 12,
    color: '#9ca3af',
  },
  controlLabelActive: {
    color: '#6366f1',
  },
  controlButtonStatic: {
    alignItems: 'center',
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
  },
  controlLabelStatic: {
    position: 'absolute',
    bottom: -24,
    fontSize: 12,
    color: '#9ca3af',
  },
  endCallButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#ef4444',
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    transform: [{ rotate: '135deg' }],
  },
  translationCard: {
    marginTop: 24,
    marginHorizontal: 20,
    borderRadius: 16,
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#155e75',
    padding: 16,
    gap: 6,
  },
  translationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  translationTitle: {
    color: '#ecfeff',
    fontSize: 15,
    fontWeight: '600',
  },
  translationMeta: {
    color: '#bae6fd',
    fontSize: 13,
  },
  transcriptCard: {
    marginHorizontal: 20,
    marginBottom: 24,
    borderRadius: 16,
    backgroundColor: '#1f2937',
    padding: 16,
    gap: 12,
  },
  transcriptTitle: {
    color: '#f9fafb',
    fontSize: 15,
    fontWeight: '600',
  },
  transcriptEntry: {
    gap: 4,
  },
  transcriptSpeaker: {
    color: '#93c5fd',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  transcriptText: {
    color: '#ffffff',
    fontSize: 14,
    lineHeight: 20,
  },
  transcriptTranslation: {
    color: '#c7d2fe',
    fontSize: 13,
    lineHeight: 18,
  },
});
