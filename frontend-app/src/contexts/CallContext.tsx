import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Alert, AppState, Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Audio } from 'expo-av';
import { apiUrl } from '../config/api';
import {
  DEFAULT_CALLER_LANGUAGE,
  DEFAULT_USER_LANGUAGE,
} from '../constants/translation';

interface CallSettings {
  enabled: boolean;
  autoAnswer: boolean;
  autoAnswerDelay: number; // seconds
  businessHoursOnly: boolean;
  businessHoursStart: string; // "09:00"
  businessHoursEnd: string; // "17:00"
  timezone: string;
  allowedCallTypes: ('inbound' | 'outbound')[];
  maxConcurrentCalls: number;
  voicemailEnabled: boolean;
  voicemailGreeting?: string;
  doNotDisturb: boolean;
  dndSchedule?: {
    enabled: boolean;
    startTime: string;
    endTime: string;
  };
  // Voice cloning settings
  selectedVoiceId: string | null;
  useClonedVoice: boolean;
  greetingScript: string;
  translationEnabled: boolean;
  callerLanguage: string;
  userLanguage: string;
  autoDetectCallerLanguage: boolean;
  voicePreservationEnabled: boolean;
}

interface ActiveCall {
  id: string;
  type: 'inbound' | 'outbound';
  phoneNumber: string;
  contactName?: string;
  status: 'ringing' | 'connected' | 'hold' | 'ended';
  startTime: Date;
  duration: number;
  channel: 'phone' | 'whatsapp' | 'widget';
}

interface CallContextType {
  settings: CallSettings;
  updateSettings: (settings: Partial<CallSettings>) => Promise<void>;
  isCallHandlingEnabled: () => boolean;
  activeCalls: ActiveCall[];
  incomingCall: ActiveCall | null;
  acceptCall: (callId: string) => Promise<void>;
  rejectCall: (callId: string) => Promise<void>;
  endCall: (callId: string) => Promise<void>;
  muteCall: (callId: string, muted: boolean) => Promise<void>;
  holdCall: (callId: string, held: boolean) => Promise<void>;
  makeOutboundCall: (phoneNumber: string, voiceId?: string) => Promise<void>;
  isAvailable: boolean;
  setAvailability: (available: boolean) => void;
}

const defaultSettings: CallSettings = {
  enabled: false, // Disabled by default
  autoAnswer: false,
  autoAnswerDelay: 5,
  businessHoursOnly: false,
  businessHoursStart: "09:00",
  businessHoursEnd: "17:00",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  allowedCallTypes: ['inbound', 'outbound'],
  maxConcurrentCalls: 1,
  voicemailEnabled: true,
  doNotDisturb: false,
  // Voice cloning defaults
  selectedVoiceId: null,
  useClonedVoice: false,
  greetingScript: "Hello! You've reached me. I'm using my AI assistant to take this call. How can I help you today?",
  translationEnabled: true,
  callerLanguage: DEFAULT_CALLER_LANGUAGE,
  userLanguage: DEFAULT_USER_LANGUAGE,
  autoDetectCallerLanguage: true,
  voicePreservationEnabled: true,
};

const CallContext = createContext<CallContextType | undefined>(undefined);

const SETTINGS_KEY = '@call_settings';

export function CallProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<CallSettings>(defaultSettings);
  const [activeCalls, setActiveCalls] = useState<ActiveCall[]>([]);
  const [incomingCall, setIncomingCall] = useState<ActiveCall | null>(null);
  const [isAvailable, setIsAvailable] = useState(true);
  const [pushToken, setPushToken] = useState<string | null>(null);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
    setupNotifications();
    registerForPushNotifications();
  }, []);

  // Load saved settings
  const loadSettings = async () => {
    try {
      const saved = await AsyncStorage.getItem(SETTINGS_KEY);
      if (saved) {
        setSettings({ ...defaultSettings, ...JSON.parse(saved) });
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  // Save settings
  const saveSettings = async (newSettings: CallSettings) => {
    try {
      await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(newSettings));
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  // Update settings
  const updateSettings = async (updates: Partial<CallSettings>) => {
    const newSettings = { ...settings, ...updates };
    setSettings(newSettings);
    await saveSettings(newSettings);

    // Sync with backend
    try {
      await fetch(apiUrl('/mobile/settings'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'mobile_user', // TODO: Get from auth
          settings: newSettings,
          push_token: pushToken,
        }),
      });
    } catch (error) {
      console.error('Failed to sync settings:', error);
    }
  };

  // Check if call handling is currently enabled
  const isCallHandlingEnabled = useCallback(() => {
    if (!settings.enabled) return false;
    if (settings.doNotDisturb) return false;
    if (!isAvailable) return false;

    // Check business hours
    if (settings.businessHoursOnly) {
      const now = new Date();
      const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      
      if (currentTime < settings.businessHoursStart || currentTime > settings.businessHoursEnd) {
        return false;
      }
    }

    // Check DND schedule
    if (settings.dndSchedule?.enabled) {
      const now = new Date();
      const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      
      if (currentTime >= settings.dndSchedule.startTime && currentTime <= settings.dndSchedule.endTime) {
        return false;
      }
    }

    return true;
  }, [settings, isAvailable]);

  // Setup push notifications
  const setupNotifications = async () => {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });

    // Listen for incoming call notifications
    const subscription = Notifications.addNotificationReceivedListener(notification => {
      const data = notification.request.content.data;
      
      if (data.type === 'incoming_call') {
        handleIncomingCall(data.call);
      }
    });

    return () => subscription.remove();
  };

  // Register for push notifications
  const registerForPushNotifications = async () => {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Push notification permission denied');
      return;
    }

    const token = (await Notifications.getExpoPushTokenAsync()).data;
    setPushToken(token);

    // Register with backend
    try {
      await fetch(apiUrl('/mobile/register-push'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'mobile_user',
          push_token: token,
          platform: Platform.OS,
        }),
      });
    } catch (error) {
      console.error('Failed to register push token:', error);
    }
  };

  // Handle incoming call
  const handleIncomingCall = (callData: any) => {
    if (!isCallHandlingEnabled()) {
      // Auto-reject if not available
      rejectCall(callData.id);
      return;
    }

    const call: ActiveCall = {
      id: callData.id,
      type: 'inbound',
      phoneNumber: callData.phone_number,
      contactName: callData.contact_name,
      status: 'ringing',
      startTime: new Date(),
      duration: 0,
      channel: callData.channel,
    };

    setIncomingCall(call);

    // Auto-answer if enabled
    if (settings.autoAnswer) {
      setTimeout(() => {
        acceptCall(call.id);
      }, settings.autoAnswerDelay * 1000);
    }

    // Play ringtone
    playRingtone();
  };

  // Play ringtone
  const playRingtone = async () => {
    console.log('Incoming demo call ringtone');
  };

  // Accept incoming call
  const acceptCall = async (callId: string) => {
    try {
      await fetch(apiUrl(`/voice/calls/${callId}/accept`), {
        method: 'POST',
      });

      await fetch(apiUrl(`/voice/calls/${callId}/translation/start`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'mobile_user',
          translation_enabled: settings.translationEnabled,
          caller_language: settings.autoDetectCallerLanguage ? 'auto' : settings.callerLanguage,
          user_language: settings.userLanguage,
          preserve_voice: settings.voicePreservationEnabled && settings.useClonedVoice,
        }),
      });

      const call = incomingCall;
      if (call && call.id === callId) {
        setActiveCalls(prev => [...prev, { ...call, status: 'connected' }]);
        setIncomingCall(null);
      }
    } catch (error) {
      console.error('Failed to accept call:', error);
      Alert.alert('Error', 'Could not accept call');
    }
  };

  // Reject incoming call
  const rejectCall = async (callId: string) => {
    try {
      await fetch(apiUrl(`/voice/calls/${callId}/reject`), {
        method: 'POST',
      });

      if (incomingCall?.id === callId) {
        setIncomingCall(null);
      }
    } catch (error) {
      console.error('Failed to reject call:', error);
    }
  };

  // End active call
  const endCall = async (callId: string) => {
    try {
      await fetch(apiUrl(`/voice/calls/${callId}/hangup`), {
        method: 'POST',
      });

      setActiveCalls(prev => prev.filter(c => c.id !== callId));
    } catch (error) {
      console.error('Failed to end call:', error);
    }
  };

  // Mute/unmute call
  const muteCall = async (callId: string, muted: boolean) => {
    try {
      await fetch(apiUrl(`/voice/calls/${callId}/mute`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ muted }),
      });
    } catch (error) {
      console.error('Failed to mute call:', error);
    }
  };

  // Hold/unhold call
  const holdCall = async (callId: string, held: boolean) => {
    try {
      await fetch(apiUrl(`/voice/calls/${callId}/hold`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ held }),
      });

      setActiveCalls(prev =>
        prev.map(c =>
          c.id === callId ? { ...c, status: held ? 'hold' : 'connected' } : c
        )
      );
    } catch (error) {
      console.error('Failed to hold call:', error);
    }
  };

  // Make outbound call
  const makeOutboundCall = async (phoneNumber: string, voiceId?: string) => {
    if (!settings.enabled) {
      Alert.alert('Calls Disabled', 'Enable call handling in settings first');
      return;
    }

    try {
      const response = await fetch(apiUrl('/voice/calls'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: phoneNumber,
          from_number: '+15550101010',
          persona_id: 'client',
          context: {
            user_id: 'mobile_user',
            voice_id: voiceId,
            channel: 'phone',
            translation: {
              enabled: settings.translationEnabled,
              caller_language: settings.autoDetectCallerLanguage ? 'auto' : settings.callerLanguage,
              user_language: settings.userLanguage,
              preserve_voice: settings.voicePreservationEnabled && settings.useClonedVoice,
            },
          },
        }),
      });

      if (!response.ok) throw new Error('Failed to initiate call');

      const data = await response.json();

      const call: ActiveCall = {
        id: data.call_sid,
        type: 'outbound',
        phoneNumber,
        status: 'connected',
        startTime: new Date(),
        duration: 0,
        channel: 'phone',
      };

      setActiveCalls(prev => [...prev, call]);

    } catch (error) {
      console.error('Failed to make call:', error);
      Alert.alert('Error', 'Could not initiate call');
    }
  };

  // Track call duration
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveCalls(prev =>
        prev.map(call =>
          call.status === 'connected'
            ? { ...call, duration: call.duration + 1 }
            : call
        )
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <CallContext.Provider
      value={{
        settings,
        updateSettings,
        isCallHandlingEnabled,
        activeCalls,
        incomingCall,
        acceptCall,
        rejectCall,
        endCall,
        muteCall,
        holdCall,
        makeOutboundCall,
        isAvailable,
        setAvailability: setIsAvailable,
      }}
    >
      {children}
    </CallContext.Provider>
  );
}

export function useCall() {
  const context = useContext(CallContext);
  if (!context) {
    throw new Error('useCall must be used within a CallProvider');
  }
  return context;
}
