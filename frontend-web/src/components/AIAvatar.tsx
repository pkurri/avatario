"use client";

import { useEffect, useRef, useCallback, useState } from 'react';
import Image from 'next/image';

// ==========================================
// AI AVATAR TYPES & CONFIGURATION
// ==========================================

export type AvatarGender = 'male' | 'female';
export type AvatarVertical = 'legal' | 'medical' | 'finance' | 'education' | 'generic';
export type AvatarMood = 'neutral' | 'happy' | 'thinking' | 'speaking' | 'listening';
export type AvatarType = 'animated' | 'realistic';

export interface AvatarConfig {
  gender: AvatarGender;
  vertical: AvatarVertical;
  skinTone: 'light' | 'medium' | 'dark';
  hairColor: string;
  eyeColor: string;
  name?: string;
  avatarType?: AvatarType;
  photoUrl?: string;  // URL to realistic photo
}

// Realistic photo URLs - Natural, authentic human faces
// Diverse, approachable, real people (not polished stock photos)
const REALISTIC_PHOTOS: Record<string, { male: string; female: string }> = {
  legal: {
    // Legal - approachable but professional, warm expressions
    male: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop&crop=face',
    female: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&h=400&fit=crop&crop=face',
  },
  medical: {
    // Medical - caring, warm, trustworthy faces
    male: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400&h=400&fit=crop&crop=face',
    female: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop&crop=face',
  },
  finance: {
    // Finance - intelligent, approachable, trustworthy
    male: 'https://images.unsplash.com/photo-1504257432389-52343af06ae3?w=400&h=400&fit=crop&crop=face',
    female: 'https://images.unsplash.com/photo-1489424731084-476a7a7dea7e?w=400&h=400&fit=crop&crop=face',
  },
  education: {
    // Education - wise, warm, intellectual
    male: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face',
    female: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&h=400&fit=crop&crop=face',
  },
  generic: {
    // Generic - friendly, diverse, natural
    male: 'https://images.unsplash.com/photo-1463453091185-61582044d556?w=400&h=400&fit=crop&crop=face',
    female: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face',
  },
};

// Color palettes for different verticals
const VERTICAL_STYLES: Record<AvatarVertical, {
  primary: string;
  secondary: string;
  accent: string;
  attire: string;
  attireSecondary: string;
  accessoryColor: string;
}> = {
  legal: {
    primary: '#1e3a5f',
    secondary: '#ffffff',
    accent: '#c9a227',
    attire: '#1e3a5f',
    attireSecondary: '#ffffff',
    accessoryColor: '#8b4513',
  },
  medical: {
    primary: '#ffffff',
    secondary: '#4a90a4',
    accent: '#e74c3c',
    attire: '#ffffff',
    attireSecondary: '#4a90a4',
    accessoryColor: '#c0392b',
  },
  finance: {
    primary: '#2c3e50',
    secondary: '#ecf0f1',
    accent: '#f39c12',
    attire: '#2c3e50',
    attireSecondary: '#ecf0f1',
    accessoryColor: '#7f8c8d',
  },
  education: {
    primary: '#8e44ad',
    secondary: '#f5f5f5',
    accent: '#f1c40f',
    attire: '#34495e',
    attireSecondary: '#ecf0f1',
    accessoryColor: '#95a5a6',
  },
  generic: {
    primary: '#3498db',
    secondary: '#ecf0f1',
    accent: '#2ecc71',
    attire: '#34495e',
    attireSecondary: '#ecf0f1',
    accessoryColor: '#95a5a6',
  },
};

// Skin tones
const SKIN_TONES = {
  light: '#f5d0c5',
  medium: '#d4a574',
  dark: '#8d5524',
};

// ==========================================
// AVATAR COMPONENT
// ==========================================

interface AIAvatarProps {
  config: AvatarConfig;
  isSpeaking?: boolean;
  isListening?: boolean;
  audioLevel?: number; // 0-1
  size?: number;
  className?: string;
}

// ==========================================
// REALISTIC HUMAN AVATAR COMPONENT
// ==========================================

interface RealisticAvatarProps {
  config: AvatarConfig;
  isSpeaking?: boolean;
  isListening?: boolean;
  audioLevel?: number;
  size?: number;
  className?: string;
}

function RealisticHumanAvatar({
  config,
  isSpeaking = false,
  isListening = false,
  audioLevel = 0,
  size = 300,
  className = "",
}: RealisticAvatarProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [blink, setBlink] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Get the appropriate photo based on gender and vertical
  const photoUrl = config.photoUrl || REALISTIC_PHOTOS[config.vertical]?.[config.gender] || 
    (config.gender === 'male' 
      ? 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop&crop=face'
      : 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&crop=face');

  // Blink animation
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlink(true);
      setTimeout(() => setBlink(false), 150);
    }, 3000 + Math.random() * 2000);
    
    return () => clearInterval(blinkInterval);
  }, []);

  // Speaking animation - subtle scale pulse
  const scale = isSpeaking ? 1 + audioLevel * 0.02 : 1;

  return (
    <div 
      ref={containerRef}
      className={`relative rounded-full overflow-hidden ${className}`}
      style={{ 
        width: size, 
        height: size,
        boxShadow: '0 20px 60px rgba(0,0,0,0.4), 0 0 0 4px rgba(255,255,255,0.1)',
      }}
    >
      {/* Base image */}
      <div 
        className="absolute inset-0 transition-transform duration-300"
        style={{ transform: `scale(${scale})` }}
      >
        <Image
          src={photoUrl}
          alt={config.name || 'AI Assistant'}
          fill
          className={`object-cover transition-opacity duration-500 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setIsLoaded(true)}
          sizes={`${size}px`}
          priority
        />
      </div>

      {/* Loading placeholder */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-neutral-800 animate-pulse" />
      )}

      {/* Blink overlay - subtle darkening */}
      {blink && (
        <div className="absolute inset-0 bg-black/10 transition-opacity duration-75" />
      )}

      {/* Speaking glow effect */}
      {isSpeaking && (
        <div 
          className="absolute inset-0 rounded-full"
          style={{
            boxShadow: `inset 0 0 ${30 + audioLevel * 20}px rgba(59, 130, 246, ${0.3 + audioLevel * 0.4})`,
            animation: 'pulse 1.5s ease-in-out infinite',
          }}
        />
      )}

      {/* Listening indicator */}
      {isListening && (
        <div 
          className="absolute inset-0 rounded-full"
          style={{
            boxShadow: 'inset 0 0 20px rgba(34, 197, 94, 0.3)',
          }}
        />
      )}

      {/* Outer ring pulse when speaking */}
      {isSpeaking && (
        <div className="absolute -inset-2 rounded-full border-2 border-blue-500/30 animate-ping" style={{ animationDuration: '2s' }} />
      )}

      {/* Professional attire overlay badge */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs font-medium capitalize">
        {config.vertical}
      </div>
    </div>
  );
}

// ==========================================
// ANIMATED AVATAR COMPONENT (Original Canvas-based)
// ==========================================

export function AIAvatar({
  config,
  isSpeaking = false,
  isListening = false,
  audioLevel = 0,
  size = 300,
  className = "",
}: AIAvatarProps) {
  // Use realistic human avatar by default, fallback to animated
  const avatarType = config.avatarType || 'realistic';

  if (avatarType === 'realistic') {
    return (
      <RealisticHumanAvatar
        config={config}
        isSpeaking={isSpeaking}
        isListening={isListening}
        audioLevel={audioLevel}
        size={size}
        className={className}
      />
    );
  }

  // Original animated avatar implementation
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | undefined>(undefined);
  const stateRef = useRef({
    blinkTimer: 0,
    isBlinking: false,
    mouthOpenness: 0,
    headTilt: 0,
    headTiltTarget: 0,
    breathing: 0,
    time: 0,
    lastAudioLevel: 0,
  });

  const verticalStyle = VERTICAL_STYLES[config.vertical];
  const skinColor = SKIN_TONES[config.skinTone];

  const getSmoothedAudioLevel = useCallback(() => {
    const target = isSpeaking ? audioLevel : 0;
    stateRef.current.lastAudioLevel += (target - stateRef.current.lastAudioLevel) * 0.3;
    return stateRef.current.lastAudioLevel;
  }, [audioLevel, isSpeaking]);

  const drawAvatar = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const state = stateRef.current;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const scale = size / 300;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    state.time += 0.016;
    state.breathing = Math.sin(state.time * 0.5) * 0.03;
    
    if (isListening) {
      state.headTiltTarget = Math.sin(state.time * 0.8) * 0.05;
    } else {
      state.headTiltTarget = Math.sin(state.time * 0.3) * 0.02;
    }
    state.headTilt += (state.headTiltTarget - state.headTilt) * 0.1;

    state.blinkTimer -= 0.016;
    if (state.blinkTimer <= 0) {
      state.isBlinking = true;
      state.blinkTimer = 2 + Math.random() * 4;
    }
    if (state.isBlinking) {
      state.blinkTimer += 0.1;
      if (state.blinkTimer > 0.15) {
        state.isBlinking = false;
        state.blinkTimer = 2 + Math.random() * 4;
      }
    }

    const smoothedAudio = getSmoothedAudioLevel();
    const targetMouthOpenness = isSpeaking ? smoothedAudio * 0.8 : 
                                isListening ? 0.1 + Math.sin(state.time * 2) * 0.05 : 
                                0.05;
    state.mouthOpenness += (targetMouthOpenness - state.mouthOpenness) * 0.2;

    ctx.save();
    ctx.translate(centerX, centerY + state.breathing * 10 * scale);
    ctx.rotate(state.headTilt);

    ctx.fillStyle = skinColor;
    ctx.beginPath();
    ctx.roundRect(-35 * scale, 80 * scale, 70 * scale, 60 * scale, 10 * scale);
    ctx.fill();

    drawAttire(ctx, config, verticalStyle, scale, skinColor);

    ctx.fillStyle = skinColor;
    ctx.beginPath();
    ctx.ellipse(0, 0, 75 * scale, 95 * scale, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = skinColor;
    ctx.beginPath();
    ctx.ellipse(-78 * scale, 0, 12 * scale, 20 * scale, 0, 0, Math.PI * 2);
    ctx.ellipse(78 * scale, 0, 12 * scale, 20 * scale, 0, 0, Math.PI * 2);
    ctx.fill();

    drawHair(ctx, config, scale, skinColor);
    drawEyes(ctx, config, scale, state.isBlinking);
    drawNose(ctx, scale, skinColor);
    drawMouth(ctx, scale, state.mouthOpenness, skinColor);
    drawEyebrows(ctx, config, scale, isSpeaking, isListening);
    drawAccessories(ctx, config, verticalStyle, scale);

    ctx.restore();

    if (isSpeaking) {
      drawSpeakingIndicator(ctx, centerX, centerY, scale, state.time, smoothedAudio);
    }

    animationRef.current = requestAnimationFrame(drawAvatar);
  }, [config, isSpeaking, isListening, size, verticalStyle, skinColor, getSmoothedAudioLevel]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = size;
    canvas.height = size + 100;

    animationRef.current = requestAnimationFrame(drawAvatar);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [drawAvatar, size]);

  return (
    <canvas
      ref={canvasRef}
      className={`rounded-full ${className}`}
      style={{ 
        width: size, 
        height: size + 100,
        filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.3))',
      }}
    />
  );
}

// ==========================================
// DRAWING HELPER FUNCTIONS
// ==========================================

function drawAttire(
  ctx: CanvasRenderingContext2D,
  config: AvatarConfig,
  style: typeof VERTICAL_STYLES['legal'],
  scale: number,
  skinColor: string
) {
  const { vertical, gender } = config;

  // Base shirt/blouse
  ctx.fillStyle = style.attireSecondary;
  ctx.beginPath();
  ctx.moveTo(-80 * scale, 100 * scale);
  ctx.lineTo(80 * scale, 100 * scale);
  ctx.lineTo(100 * scale, 200 * scale);
  ctx.lineTo(-100 * scale, 200 * scale);
  ctx.closePath();
  ctx.fill();

  // Collar
  ctx.fillStyle = style.attireSecondary;
  ctx.beginPath();
  if (gender === 'male') {
    // Shirt collar
    ctx.moveTo(-30 * scale, 85 * scale);
    ctx.lineTo(0, 110 * scale);
    ctx.lineTo(30 * scale, 85 * scale);
    ctx.lineTo(20 * scale, 70 * scale);
    ctx.lineTo(-20 * scale, 70 * scale);
    ctx.closePath();
    
    // Tie (for formal verticals)
    if (vertical === 'legal' || vertical === 'finance') {
      ctx.fill();
      ctx.fillStyle = style.accent;
      ctx.beginPath();
      ctx.moveTo(-8 * scale, 100 * scale);
      ctx.lineTo(8 * scale, 100 * scale);
      ctx.lineTo(12 * scale, 160 * scale);
      ctx.lineTo(0, 180 * scale);
      ctx.lineTo(-12 * scale, 160 * scale);
      ctx.closePath();
      ctx.fill();
      
      // Tie knot
      ctx.beginPath();
      ctx.moveTo(-12 * scale, 85 * scale);
      ctx.lineTo(12 * scale, 85 * scale);
      ctx.lineTo(15 * scale, 105 * scale);
      ctx.lineTo(-15 * scale, 105 * scale);
      ctx.closePath();
      ctx.fill();
    } else {
      ctx.fill();
    }
  } else {
    // Female blouse collar
    ctx.moveTo(-35 * scale, 80 * scale);
    ctx.lineTo(0, 115 * scale);
    ctx.lineTo(35 * scale, 80 * scale);
    ctx.lineTo(25 * scale, 65 * scale);
    ctx.lineTo(-25 * scale, 65 * scale);
    ctx.closePath();
    ctx.fill();
  }

  // Outer attire (jacket/coat)
  ctx.fillStyle = style.attire;
  ctx.beginPath();
  
  if (vertical === 'medical') {
    // Lab coat - white coat with open front
    ctx.moveTo(-90 * scale, 95 * scale);
    ctx.lineTo(-70 * scale, 200 * scale);
    ctx.lineTo(-40 * scale, 200 * scale);
    ctx.lineTo(-30 * scale, 120 * scale);
    ctx.lineTo(0, 130 * scale);
    ctx.lineTo(30 * scale, 120 * scale);
    ctx.lineTo(40 * scale, 200 * scale);
    ctx.lineTo(70 * scale, 200 * scale);
    ctx.lineTo(90 * scale, 95 * scale);
    ctx.lineTo(60 * scale, 85 * scale);
    ctx.lineTo(-60 * scale, 85 * scale);
    ctx.closePath();
    ctx.fill();
    
    // Stethoscope
    ctx.strokeStyle = '#c0392b';
    ctx.lineWidth = 4 * scale;
    ctx.beginPath();
    ctx.arc(0, 100 * scale, 45 * scale, 0.2 * Math.PI, 0.8 * Math.PI);
    ctx.stroke();
    
    // Stethoscope chest piece
    ctx.fillStyle = '#95a5a6';
    ctx.beginPath();
    ctx.arc(0, 140 * scale, 15 * scale, 0, Math.PI * 2);
    ctx.fill();
    
  } else if (vertical === 'legal') {
    // Legal gown/band
    ctx.moveTo(-95 * scale, 90 * scale);
    ctx.lineTo(-80 * scale, 200 * scale);
    ctx.lineTo(80 * scale, 200 * scale);
    ctx.lineTo(95 * scale, 90 * scale);
    ctx.lineTo(70 * scale, 80 * scale);
    ctx.lineTo(-70 * scale, 80 * scale);
    ctx.closePath();
    ctx.fill();
    
    // Lawyer band (white neckband)
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.rect(-15 * scale, 70 * scale, 8 * scale, 40 * scale);
    ctx.rect(7 * scale, 70 * scale, 8 * scale, 40 * scale);
    ctx.fill();
    
  } else {
    // Standard suit/blazer
    ctx.moveTo(-100 * scale, 95 * scale);
    ctx.lineTo(-85 * scale, 200 * scale);
    ctx.lineTo(85 * scale, 200 * scale);
    ctx.lineTo(100 * scale, 95 * scale);
    ctx.lineTo(65 * scale, 85 * scale);
    ctx.lineTo(-65 * scale, 85 * scale);
    ctx.closePath();
    ctx.fill();
    
    // Lapels
    ctx.fillStyle = darkenColor(style.attire, 20);
    ctx.beginPath();
    ctx.moveTo(-65 * scale, 85 * scale);
    ctx.lineTo(-30 * scale, 200 * scale);
    ctx.lineTo(-10 * scale, 200 * scale);
    ctx.lineTo(-20 * scale, 100 * scale);
    ctx.closePath();
    ctx.fill();
    
    ctx.beginPath();
    ctx.moveTo(65 * scale, 85 * scale);
    ctx.lineTo(30 * scale, 200 * scale);
    ctx.lineTo(10 * scale, 200 * scale);
    ctx.lineTo(20 * scale, 100 * scale);
    ctx.closePath();
    ctx.fill();
  }

  // Buttons
  ctx.fillStyle = style.accent;
  for (let i = 0; i < 3; i++) {
    ctx.beginPath();
    ctx.arc(0, (120 + i * 25) * scale, 4 * scale, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawHair(
  ctx: CanvasRenderingContext2D,
  config: AvatarConfig,
  scale: number,
  skinColor: string
) {
  const { gender, hairColor } = config;
  ctx.fillStyle = hairColor;

  if (gender === 'male') {
    // Male hair - professional cut
    ctx.beginPath();
    ctx.arc(0, -20 * scale, 82 * scale, Math.PI, 0);
    ctx.lineTo(78 * scale, 10 * scale);
    ctx.quadraticCurveTo(75 * scale, -30 * scale, 50 * scale, -45 * scale);
    ctx.quadraticCurveTo(0, -65 * scale, -50 * scale, -45 * scale);
    ctx.quadraticCurveTo(-75 * scale, -30 * scale, -78 * scale, 10 * scale);
    ctx.closePath();
    ctx.fill();

    // Side hair
    ctx.beginPath();
    ctx.roundRect(-82 * scale, -10 * scale, 20 * scale, 50 * scale, 5 * scale);
    ctx.roundRect(62 * scale, -10 * scale, 20 * scale, 50 * scale, 5 * scale);
    ctx.fill();
  } else {
    // Female hair - longer style
    ctx.beginPath();
    ctx.arc(0, -25 * scale, 85 * scale, Math.PI, 0);
    ctx.lineTo(82 * scale, 80 * scale);
    ctx.quadraticCurveTo(90 * scale, 100 * scale, 85 * scale, 120 * scale);
    ctx.lineTo(-85 * scale, 120 * scale);
    ctx.quadraticCurveTo(-90 * scale, 100 * scale, -82 * scale, 80 * scale);
    ctx.closePath();
    ctx.fill();

    // Front hair volume
    ctx.beginPath();
    ctx.arc(0, -40 * scale, 80 * scale, Math.PI * 0.8, Math.PI * 0.2, true);
    ctx.quadraticCurveTo(0, -20 * scale, -80 * scale, -30 * scale);
    ctx.closePath();
    ctx.fill();
  }
}

function drawEyes(
  ctx: CanvasRenderingContext2D,
  config: AvatarConfig,
  scale: number,
  isBlinking: boolean
) {
  const { eyeColor } = config;
  const eyeY = -15 * scale;
  const eyeSpacing = 35 * scale;

  if (isBlinking) {
    // Closed eyes - simple lines
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2 * scale;
    ctx.beginPath();
    ctx.moveTo(-eyeSpacing - 15 * scale, eyeY);
    ctx.lineTo(-eyeSpacing + 15 * scale, eyeY);
    ctx.moveTo(eyeSpacing - 15 * scale, eyeY);
    ctx.lineTo(eyeSpacing + 15 * scale, eyeY);
    ctx.stroke();
    return;
  }

  // Eye whites
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.ellipse(-eyeSpacing, eyeY, 18 * scale, 12 * scale, 0, 0, Math.PI * 2);
  ctx.ellipse(eyeSpacing, eyeY, 18 * scale, 12 * scale, 0, 0, Math.PI * 2);
  ctx.fill();

  // Irises
  ctx.fillStyle = eyeColor;
  ctx.beginPath();
  ctx.arc(-eyeSpacing, eyeY, 8 * scale, 0, Math.PI * 2);
  ctx.arc(eyeSpacing, eyeY, 8 * scale, 0, Math.PI * 2);
  ctx.fill();

  // Pupils
  ctx.fillStyle = '#000000';
  ctx.beginPath();
  ctx.arc(-eyeSpacing, eyeY, 4 * scale, 0, Math.PI * 2);
  ctx.arc(eyeSpacing, eyeY, 4 * scale, 0, Math.PI * 2);
  ctx.fill();

  // Eye shine
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.arc(-eyeSpacing - 2 * scale, eyeY - 2 * scale, 2 * scale, 0, Math.PI * 2);
  ctx.arc(eyeSpacing - 2 * scale, eyeY - 2 * scale, 2 * scale, 0, Math.PI * 2);
  ctx.fill();

  // Upper eyelid/shadow
  ctx.fillStyle = 'rgba(0,0,0,0.1)';
  ctx.beginPath();
  ctx.ellipse(-eyeSpacing, eyeY - 8 * scale, 18 * scale, 6 * scale, 0, 0, Math.PI * 2);
  ctx.ellipse(eyeSpacing, eyeY - 8 * scale, 18 * scale, 6 * scale, 0, 0, Math.PI * 2);
  ctx.fill();
}

function drawNose(ctx: CanvasRenderingContext2D, scale: number, skinColor: string) {
  ctx.strokeStyle = darkenColor(skinColor, 30);
  ctx.lineWidth = 2 * scale;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(0, -5 * scale);
  ctx.quadraticCurveTo(-5 * scale, 15 * scale, -8 * scale, 25 * scale);
  ctx.moveTo(0, -5 * scale);
  ctx.quadraticCurveTo(5 * scale, 15 * scale, 8 * scale, 25 * scale);
  ctx.stroke();

  // Nose tip shadow
  ctx.fillStyle = 'rgba(0,0,0,0.1)';
  ctx.beginPath();
  ctx.ellipse(0, 28 * scale, 6 * scale, 3 * scale, 0, 0, Math.PI * 2);
  ctx.fill();
}

function drawMouth(
  ctx: CanvasRenderingContext2D,
  scale: number,
  openness: number,
  skinColor: string
) {
  const mouthY = 45 * scale;
  const mouthWidth = 30 * scale;
  const openHeight = 15 * scale * openness;

  if (openness > 0.1) {
    // Open mouth - speaking
    ctx.fillStyle = '#8b0000'; // Dark red inside
    ctx.beginPath();
    ctx.ellipse(0, mouthY, mouthWidth * (0.7 + openness * 0.3), openHeight, 0, 0, Math.PI * 2);
    ctx.fill();

    // Tongue
    ctx.fillStyle = '#ff6b6b';
    ctx.beginPath();
    ctx.ellipse(0, mouthY + openHeight * 0.3, mouthWidth * 0.4, openHeight * 0.5, 0, 0, Math.PI * 2);
    ctx.fill();

    // Teeth (top)
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.roundRect(-mouthWidth * 0.6, mouthY - openHeight * 0.8, mouthWidth * 1.2, 6 * scale, 2 * scale);
    ctx.fill();

    // Lips
    ctx.strokeStyle = darkenColor(skinColor, 40);
    ctx.lineWidth = 3 * scale;
    ctx.beginPath();
    ctx.ellipse(0, mouthY - openHeight, mouthWidth, 8 * scale, 0, 0, Math.PI, false);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.ellipse(0, mouthY + openHeight * 0.5, mouthWidth * 0.8, 5 * scale, 0, 0, Math.PI, false);
    ctx.stroke();
  } else {
    // Closed mouth - smile
    ctx.strokeStyle = darkenColor(skinColor, 40);
    ctx.lineWidth = 3 * scale;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(0, mouthY + 5 * scale, mouthWidth * 0.8, 0.1 * Math.PI, 0.9 * Math.PI);
    ctx.stroke();
  }
}

function drawEyebrows(
  ctx: CanvasRenderingContext2D,
  config: AvatarConfig,
  scale: number,
  isSpeaking: boolean,
  isListening: boolean
) {
  const { hairColor } = config;
  const browY = -40 * scale;
  const eyeSpacing = 35 * scale;

  ctx.strokeStyle = hairColor;
  ctx.lineWidth = 4 * scale;
  ctx.lineCap = 'round';

  let browAngle = 0;
  if (isListening) {
    browAngle = 0.15; // Raised - interested
  } else if (isSpeaking) {
    browAngle = -0.05; // Slightly engaged
  }

  // Left eyebrow
  ctx.beginPath();
  ctx.moveTo(-eyeSpacing - 20 * scale, browY + Math.sin(browAngle) * 10 * scale);
  ctx.quadraticCurveTo(
    -eyeSpacing, browY - 5 * scale + Math.sin(browAngle) * 10 * scale,
    -eyeSpacing + 20 * scale, browY + Math.sin(browAngle) * 10 * scale
  );
  ctx.stroke();

  // Right eyebrow
  ctx.beginPath();
  ctx.moveTo(eyeSpacing - 20 * scale, browY + Math.sin(browAngle) * 10 * scale);
  ctx.quadraticCurveTo(
    eyeSpacing, browY - 5 * scale + Math.sin(browAngle) * 10 * scale,
    eyeSpacing + 20 * scale, browY + Math.sin(browAngle) * 10 * scale
  );
  ctx.stroke();
}

function drawAccessories(
  ctx: CanvasRenderingContext2D,
  config: AvatarConfig,
  style: typeof VERTICAL_STYLES['legal'],
  scale: number
) {
  const { vertical, gender } = config;

  // Glasses (for some personas)
  if (vertical === 'legal' || vertical === 'finance') {
    ctx.strokeStyle = '#2c3e50';
    ctx.lineWidth = 2 * scale;
    const eyeSpacing = 35 * scale;
    const eyeY = -15 * scale;

    // Frames
    ctx.beginPath();
    ctx.arc(-eyeSpacing, eyeY, 22 * scale, 0, Math.PI * 2);
    ctx.arc(eyeSpacing, eyeY, 22 * scale, 0, Math.PI * 2);
    ctx.stroke();

    // Bridge
    ctx.beginPath();
    ctx.moveTo(-eyeSpacing + 22 * scale, eyeY);
    ctx.lineTo(eyeSpacing - 22 * scale, eyeY);
    ctx.stroke();

    // Arms
    ctx.beginPath();
    ctx.moveTo(-eyeSpacing - 22 * scale, eyeY);
    ctx.lineTo(-eyeSpacing - 40 * scale, eyeY - 5 * scale);
    ctx.moveTo(eyeSpacing + 22 * scale, eyeY);
    ctx.lineTo(eyeSpacing + 40 * scale, eyeY - 5 * scale);
    ctx.stroke();
  }
}

function drawSpeakingIndicator(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  centerY: number,
  scale: number,
  time: number,
  audioLevel: number
) {
  const radius = 160 * scale;
  const intensity = 0.3 + audioLevel * 0.7;

  // Pulsing ring
  ctx.strokeStyle = `rgba(59, 130, 246, ${intensity})`;
  ctx.lineWidth = 3 * scale;
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius + Math.sin(time * 8) * 5 * scale, 0, Math.PI * 2);
  ctx.stroke();

  // Outer glow
  const gradient = ctx.createRadialGradient(centerX, centerY, radius * 0.8, centerX, centerY, radius * 1.2);
  gradient.addColorStop(0, `rgba(59, 130, 246, ${intensity * 0.5})`);
  gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius * 1.2, 0, Math.PI * 2);
  ctx.fill();

  // Sound waves
  for (let i = 0; i < 3; i++) {
    ctx.strokeStyle = `rgba(59, 130, 246, ${intensity * (0.5 - i * 0.15)})`;
    ctx.lineWidth = 2 * scale;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius + 20 * scale + i * 15 * scale + Math.sin(time * 6 + i) * 3 * scale, 0, Math.PI * 2);
    ctx.stroke();
  }
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

function darkenColor(color: string, percent: number): string {
  const num = parseInt(color.replace('#', ''), 16);
  const amt = Math.round(2.55 * percent);
  const R = Math.max((num >> 16) - amt, 0);
  const G = Math.max((num >> 8 & 0x00FF) - amt, 0);
  const B = Math.max((num & 0x0000FF) - amt, 0);
  return `#${(0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)}`;
}

// Preset avatar configurations for easy use
export const AVATAR_PRESETS: Record<string, AvatarConfig> = {
  // Legal
  'anya': { gender: 'female', vertical: 'legal', skinTone: 'medium', hairColor: '#2d1b0e', eyeColor: '#4a3728' },
  'vikram': { gender: 'male', vertical: 'legal', skinTone: 'medium', hairColor: '#1a1a1a', eyeColor: '#3d3d3d' },
  
  // Medical
  'dr-priya': { gender: 'female', vertical: 'medical', skinTone: 'light', hairColor: '#2d1b0e', eyeColor: '#4a6741' },
  'dr-arjun': { gender: 'male', vertical: 'medical', skinTone: 'medium', hairColor: '#1a1a1a', eyeColor: '#2c3e50' },
  
  // Finance
  'advisor-maya': { gender: 'female', vertical: 'finance', skinTone: 'dark', hairColor: '#0d0d0d', eyeColor: '#5d4e37' },
  'analyst-raj': { gender: 'male', vertical: 'finance', skinTone: 'medium', hairColor: '#2c2c2c', eyeColor: '#3d3d3d' },
  
  // Generic
  'assistant-alex': { gender: 'male', vertical: 'generic', skinTone: 'light', hairColor: '#4a3728', eyeColor: '#2c5aa0' },
  'assistant-sarah': { gender: 'female', vertical: 'generic', skinTone: 'light', hairColor: '#d4a574', eyeColor: '#4a6741' },
};

export default AIAvatar;
