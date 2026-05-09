// Centralised design tokens — import from here instead of inlining strings in components.

export const ANIMATION = {
  blink: { durationMs: 150, intervalMs: 3000, randomMs: 2000 },
  speaking: { scale: 1.02, duration: 2 },
  pulse: { duration: 1.5 },
  spin: { duration: 2 },
} as const;

export const SHADOW = {
  avatarIdle: '0 20px 40px rgba(0,0,0,0.3)',
  avatarSpeaking: '0 0 60px rgba(59, 130, 246, 0.5), 0 20px 40px rgba(0,0,0,0.4)',
  avatarSpeakingSubtle: '0 0 60px rgba(59, 130, 246, 0.4), 0 20px 40px rgba(0,0,0,0.3)',
  speakingGlowInset: 'inset 0 0 50px rgba(59, 130, 246, 0.4)',
} as const;

export const ASPECT = {
  square: 1,
  portrait: 1.1,
  portraitTall: 1.2,
} as const;

export const COLOR = {
  blue: {
    ring: 'border-blue-500/50',
    text: 'text-blue-400',
    bg: 'bg-blue-500',
  },
  green: {
    dot: 'bg-green-500',
  },
  red: {
    dot: 'bg-red-500',
    text: 'text-red-400',
    bg: 'bg-red-500/10',
  },
  neutral: {
    badge: 'bg-black/40',
    badgeDark: 'bg-black/60',
  },
} as const;
