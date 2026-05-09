import { API_BASE } from "./config";

// ==========================================
// SHARED FETCH HELPER
// ==========================================

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ==========================================
// TYPES
// ==========================================

export interface BackendPersona {
  id: string;
  name: string;
  title: string;
  description: string;
  color: string;
  shadow: string;
  avatar: string;
  voice_speaker: string;
}

export interface AIPerson {
  id: string;
  name: string;
  image_url: string;
  vertical: string;
  gender: string;
  ready: boolean;
  traits?: { gender: string; ethnicity: string; age_group: string; profession: string };
}

export interface TalkingPerson {
  id: string;
  name: string;
  status: 'image' | 'audio' | 'video' | 'complete' | 'error';
  image_url?: string;
  video_url?: string;
  error?: string;
  config: { gender: string; age: string; ethnicity: string; profession: string };
}

export interface ClonedFace {
  id: string;
  name: string;
  mode: 'clone' | 'generate';
  source: string;
  status: 'processing' | 'ready' | 'talking' | 'error';
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

export interface TalkResult {
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

export interface LipSyncResult {
  job_id?: string;
  video_url?: string;
  status: string;
  cached: boolean;
  error?: string;
}

export interface LlmStatus {
  status: 'running' | 'stopped' | 'starting' | 'unknown';
}

export interface LiveKitToken {
  token: string;
  url: string;
}

// ==========================================
// PERSONAS
// ==========================================

export const personas = {
  list: (): Promise<{ personas: BackendPersona[] }> =>
    apiFetch('/personas'),

  get: (id: string): Promise<BackendPersona> =>
    apiFetch(`/personas/${id}`),
};

// ==========================================
// LLM STATUS
// ==========================================

export const llm = {
  status: (): Promise<LlmStatus> =>
    apiFetch('/llm_status'),

  wake: (): Promise<unknown> =>
    apiFetch('/wake_llm', { method: 'POST' }),
};

// ==========================================
// LIVEKIT
// ==========================================

export const livekit = {
  getToken: (params: {
    participant_name: string;
    room_name: string;
    role: string;
  }): Promise<LiveKitToken> => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/get_livekit_token?${qs}`);
  },
};

// ==========================================
// LIP SYNC
// ==========================================

export const lipsync = {
  generate: (body: {
    persona_id: string;
    text: string;
    model?: string;
    resolution?: string;
    image_url?: string;
  }): Promise<LipSyncResult> =>
    postJson('/lipsync/generate', {
      model: 'infinitetalk-image-to-video',
      resolution: '512x512',
      ...body,
    }),

  status: (jobId: string): Promise<LipSyncResult> =>
    apiFetch(`/lipsync/status/${jobId}`),
};

// ==========================================
// AI PERSON
// ==========================================

export const aiPerson = {
  generate: (body: {
    vertical?: string;
    gender?: string;
    name?: string;
  }): Promise<{ status: string; person: AIPerson }> =>
    postJson('/ai-person/generate', body),

  talkingHead: (body: {
    persona_id: string;
    text: string;
    image_url: string;
  }): Promise<unknown> =>
    postJson('/ai-person/talking-head', body),
};

// ==========================================
// TALKING PERSON
// ==========================================

export const talkingPerson = {
  create: (body: {
    vertical?: string;
    gender?: string;
    name?: string;
    ethnicity?: string;
  }): Promise<TalkingPerson> =>
    postJson('/talking-person/create', body),

  video: (body: {
    person_id: string;
    text: string;
    emotion?: string;
  }): Promise<unknown> =>
    postJson('/talking-person/video', { emotion: 'neutral', ...body }),
};

// ==========================================
// FACE CLONE
// ==========================================

export const faceClone = {
  list: (mode?: string): Promise<{ faces: ClonedFace[] }> =>
    apiFetch(`/face-clone/list${mode ? `?mode=${mode}` : ''}`),

  talk: (body: { face_id: string; text: string; voice_id?: string }): Promise<TalkResult> =>
    postJson('/face-clone/talk', body),

  fromUrl: (body: { image_url: string; name: string }): Promise<ClonedFace> =>
    postJson('/face-clone/from-url', body),

  generate: (body: {
    name: string;
    gender?: string;
    ethnicity?: string;
    age?: string;
    profession?: string;
  }): Promise<ClonedFace> =>
    postJson('/face-clone/generate', body),

  delete: (faceId: string): Promise<{ deleted: boolean; face_id: string }> =>
    apiFetch(`/face-clone/${faceId}`, { method: 'DELETE' }),
};
