"use client";

import { useEffect, useState, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { SHADOW, ASPECT, ANIMATION, COLOR } from '@/lib/design-tokens';

export interface AvatarBaseProps {
  size: number;
  aspectRatio?: number;
  isSpeaking?: boolean;
  isListening?: boolean;
  personaName?: string;
  vertical?: string;
  showBlink?: boolean;
  className?: string;
  children: ReactNode;
}

export function AvatarBase({
  size,
  aspectRatio = ASPECT.square,
  isSpeaking = false,
  isListening = false,
  personaName,
  vertical,
  showBlink = false,
  className = '',
  children,
}: AvatarBaseProps) {
  const [blink, setBlink] = useState(false);

  useEffect(() => {
    if (!showBlink) return;
    const interval = setInterval(() => {
      setBlink(true);
      setTimeout(() => setBlink(false), ANIMATION.blink.durationMs);
    }, ANIMATION.blink.intervalMs + Math.random() * ANIMATION.blink.randomMs);
    return () => clearInterval(interval);
  }, [showBlink]);

  return (
    <motion.div
      className={`relative rounded-2xl overflow-hidden ${className}`}
      style={{
        width: size,
        height: size * aspectRatio,
        boxShadow: isSpeaking ? SHADOW.avatarSpeaking : SHADOW.avatarIdle,
      }}
      animate={{ scale: isSpeaking ? [1, ANIMATION.speaking.scale, 1] : 1 }}
      transition={{
        duration: ANIMATION.speaking.duration,
        repeat: isSpeaking ? Infinity : 0,
        repeatType: 'reverse',
      }}
    >
      {children}

      {/* Speaking indicator ring */}
      {isSpeaking && (
        <motion.div
          className={`absolute -inset-2 rounded-2xl border-2 ${COLOR.blue.ring}`}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: ANIMATION.pulse.duration, repeat: Infinity }}
        />
      )}

      {/* Speaking inner glow */}
      {isSpeaking && (
        <motion.div
          className="absolute inset-0 rounded-2xl"
          style={{ boxShadow: SHADOW.speakingGlowInset }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}

      {/* Listening dot */}
      {isListening && (
        <div className={`absolute top-4 right-4 w-3 h-3 ${COLOR.green.dot} rounded-full animate-pulse`} />
      )}

      {/* Blink overlay */}
      {showBlink && blink && (
        <div className="absolute inset-0 bg-black/10 transition-opacity duration-75 pointer-events-none" />
      )}

      {/* Name badge */}
      {personaName && (
        <div className={`absolute top-4 left-4 px-3 py-1 rounded-full ${COLOR.neutral.badge} backdrop-blur-sm`}>
          <span className="text-white text-sm font-medium">{personaName}</span>
        </div>
      )}

      {/* Vertical badge */}
      {vertical && (
        <div className={`absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full ${COLOR.neutral.badgeDark} backdrop-blur-sm`}>
          <span className="text-white text-xs font-medium capitalize">{vertical}</span>
        </div>
      )}
    </motion.div>
  );
}
