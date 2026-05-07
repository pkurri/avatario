/**
 * Avatario API Client
 * Stubs for backend integration
 */

// Types
export interface TwinData {
  id: string;
  name: string;
  interactions: number;
  learnedFacts: string[];
  preferences: Record<string, string>;
  lastActive: string;
}

export interface PersonaConfig {
  id: string;
  name: string;
  description: string;
  voiceId?: string;
  trainingSamples: string[];
  status: 'training' | 'ready' | 'error';
  createdAt: string;
}

export interface VoiceSession {
  sessionId: string;
  status: 'connecting' | 'active' | 'closed';
  transcript: string[];
  latency: number;
}

export interface WidgetConfig {
  position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  greeting: string;
  quickActions: { label: string; action: string }[];
  theme: 'dark' | 'light';
}

import { API_BASE } from "./config";

class AvatarioAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  // Digital Twin API
  async fetchTwinData(twinId: string): Promise<TwinData> {
    // Stub - replace with actual API call
    console.log(`Fetching twin data for: ${twinId}`);
    return {
      id: twinId,
      name: 'My Digital Twin',
      interactions: 1523,
      learnedFacts: [
        'Prefer email summaries over detailed reports',
        'Most active during 9-11 AM',
        'Frequently handles contract reviews'
      ],
      preferences: {
        language: 'English',
        communicationStyle: 'Professional'
      },
      lastActive: new Date().toISOString()
    };
  }

  async updateTwinPreferences(twinId: string, preferences: Record<string, string>): Promise<TwinData> {
    console.log(`Updating twin preferences for: ${twinId}`, preferences);
    return this.fetchTwinData(twinId);
  }

  // Persona Cloner API
  async clonePersona(name: string, samples: string[]): Promise<PersonaConfig> {
    console.log(`Cloning persona: ${name} with ${samples.length} samples`);
    return {
      id: `persona-${Date.now()}`,
      name,
      description: `Cloned persona based on ${samples.length} training samples`,
      trainingSamples: samples,
      status: 'training',
      createdAt: new Date().toISOString()
    };
  }

  async getPersonaStatus(personaId: string): Promise<PersonaConfig> {
    console.log(`Fetching persona status: ${personaId}`);
    return {
      id: personaId,
      name: 'Legal Assistant',
      description: 'Trained legal AI persona',
      trainingSamples: [],
      status: 'ready',
      createdAt: new Date().toISOString()
    };
  }

  // Realtime Voice API
  async startVoiceSession(): Promise<VoiceSession> {
    console.log('Starting voice session');
    return {
      sessionId: `voice-${Date.now()}`,
      status: 'connecting',
      transcript: [],
      latency: 0
    };
  }

  async sendVoiceChunk(sessionId: string, audioChunk: Blob): Promise<{ transcript: string }> {
    console.log(`Sending voice chunk to session: ${sessionId}`);
    return { transcript: 'Voice transcription stub' };
  }

  async endVoiceSession(sessionId: string): Promise<void> {
    console.log(`Ending voice session: ${sessionId}`);
  }

  // Widget Config API
  async getWidgetConfig(): Promise<WidgetConfig> {
    console.log('Fetching widget config');
    return {
      position: 'bottom-right',
      greeting: 'Hello! How can I help you today?',
      quickActions: [
        { label: 'Chat', action: 'openChat' },
        { label: 'Voice', action: 'startVoice' },
        { label: 'Book', action: 'bookAppointment' }
      ],
      theme: 'dark'
    };
  }

  async updateWidgetConfig(config: Partial<WidgetConfig>): Promise<WidgetConfig> {
    console.log('Updating widget config:', config);
    return this.getWidgetConfig();
  }
}

// Export singleton instance
export const api = new AvatarioAPI();

// Export individual functions for convenience
export const fetchTwinData = (twinId: string) => api.fetchTwinData(twinId);
export const clonePersona = (name: string, samples: string[]) => api.clonePersona(name, samples);
export const startVoiceSession = () => api.startVoiceSession();
export const getWidgetConfig = () => api.getWidgetConfig();
