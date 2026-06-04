"use client";

import { useEffect, useState } from 'react';
import { motion, Variants, AnimatePresence } from 'framer-motion';
import { MessageCircle, Mic, Settings, ChevronDown, Briefcase, Calendar, Cloud, Focus, MoreHorizontal, User, CheckCircle2, TrendingUp } from 'lucide-react';
import { Modal } from './Modal';
import { useDemoUser } from '@/hooks/useDemoUser';

// ==========================================
// TYPES
// ==========================================

type ContextType = 'time' | 'weather' | 'tasks' | 'calendar' | 'focus';

interface ContextData {
  type: ContextType;
  message: string;
  icon?: React.ReactNode;
  priority: number;
}

interface SmartAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  onClick: () => void;
  timeRange?: { start: number; end: number }; // 0-24 hours
}

// ==========================================
// MINI AVATAR COMPONENT
// ==========================================

interface MiniAvatarProps {
  state: 'idle' | 'greeting' | 'listening' | 'thinking';
  size?: number;
}

const MiniAvatar: React.FC<MiniAvatarProps> = ({ state, size = 48 }) => {
  const [isBlinking, setIsBlinking] = useState(false);

  // Auto-blink every 3-6 seconds
  useEffect(() => {
    const blinkLoop = () => {
      const nextBlink = 3000 + Math.random() * 3000;
      setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => setIsBlinking(false), 150);
        blinkLoop();
      }, nextBlink);
    };
    blinkLoop();
  }, []);

  return (
    <motion.div
      className="relative rounded-full overflow-hidden bg-gradient-to-br from-blue-500 to-purple-600"
      style={{ width: size, height: size }}
      animate={{
        scale: state === 'greeting' ? [1, 1.1, 1] : state === 'listening' ? [1, 1.05, 1] : 1,
        boxShadow: state === 'listening' 
          ? '0 0 20px rgba(59, 130, 246, 0.5)' 
          : state === 'greeting' 
            ? '0 0 15px rgba(168, 85, 247, 0.4)' 
            : '0 2px 8px rgba(0,0,0,0.1)'
      }}
      transition={{ duration: 0.5, repeat: state === 'listening' ? Infinity : 0 }}
    >
      {/* Avatar face SVG */}
      <svg viewBox="0 0 48 48" className="w-full h-full">
        {/* Background */}
        <defs>
          <linearGradient id="faceGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
        <circle cx="24" cy="24" r="24" fill="url(#faceGrad)" />
        
        {/* Face base */}
        <circle cx="24" cy="26" r="14" fill="#fce7f3" />
        
        {/* Eyes */}
        <AnimatePresence>
          {!isBlinking ? (
            <>
              <motion.circle cx="19" cy="24" r="2.5" fill="#1f2937" 
                animate={{ scaleY: state === 'listening' ? [1, 0.8, 1] : 1 }}
                transition={{ duration: 0.3, repeat: state === 'listening' ? Infinity : 0 }}
              />
              <motion.circle cx="29" cy="24" r="2.5" fill="#1f2937"
                animate={{ scaleY: state === 'listening' ? [1, 0.8, 1] : 1 }}
                transition={{ duration: 0.3, repeat: state === 'listening' ? Infinity : 0, delay: 0.1 }}
              />
            </>
          ) : (
            <>
              <line x1="16.5" y1="24" x2="21.5" y2="24" stroke="#1f2937" strokeWidth="1.5" />
              <line x1="26.5" y1="24" x2="31.5" y2="24" stroke="#1f2937" strokeWidth="1.5" />
            </>
          )}
        </AnimatePresence>
        
        {/* Smile - changes based on state */}
        <path
          d={state === 'greeting' ? "M 17 32 Q 24 38 31 32" : "M 18 31 Q 24 34 30 31"}
          stroke="#1f2937"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
        
        {/* Listening indicator ring */}
        {state === 'listening' && (
          <motion.circle
            cx="24" cy="24" r="22"
            stroke="rgba(59, 130, 246, 0.6)"
            strokeWidth="2"
            fill="none"
            animate={{ r: [20, 24, 20], opacity: [0.8, 0.3, 0.8] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
      </svg>
    </motion.div>
  );
};

// ==========================================
// CONTEXT ENGINE
// ==========================================

const getContextualGreeting = (): ContextData[] => {
  const hour = new Date().getHours();
  const contexts: ContextData[] = [];
  
  // Time-based (always present)
  let timeMessage = '';
  if (hour < 12) timeMessage = 'Good morning!';
  else if (hour < 17) timeMessage = 'Good afternoon!';
  else if (hour < 20) timeMessage = 'Good evening!';
  else timeMessage = 'Good night!';
  
  contexts.push({
    type: 'time',
    message: timeMessage,
    priority: 1
  });
  
  // Mock weather (would come from API)
  const weatherOptions = [
    { message: "It's sunny - perfect day for focused work!", icon: <Cloud className="w-4 h-4" /> },
    { message: "Rainy outside - cozy coding weather!", icon: <Cloud className="w-4 h-4" /> },
    { message: "Clear skies - great day ahead!", icon: <Cloud className="w-4 h-4" /> }
  ];
  const weather = weatherOptions[Math.floor(Math.random() * weatherOptions.length)];
  contexts.push({
    type: 'weather',
    message: weather.message,
    icon: weather.icon,
    priority: 2
  });
  
  // Mock tasks
  const pendingTasks = 3; // Would come from task API
  if (pendingTasks > 0) {
    contexts.push({
      type: 'tasks',
      message: `You have ${pendingTasks} code reviews pending`,
      icon: <Briefcase className="w-4 h-4" />,
      priority: 3
    });
  }
  
  // Focus mode suggestion (work hours)
  if (hour >= 9 && hour < 17) {
    contexts.push({
      type: 'focus',
      message: 'Ready for deep work?',
      icon: <Focus className="w-4 h-4" />,
      priority: 4
    });
  }
  
  return contexts.sort((a, b) => a.priority - b.priority);
};

// ==========================================
// ANIMATION VARIANTS
// ==========================================

const containerVariants: Variants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { type: 'spring', stiffness: 300, damping: 20 }
  }
};

const actionVariants: Variants = {
  hidden: { scale: 0, opacity: 0 },
  visible: (i: number) => ({
    scale: 1,
    opacity: 1,
    transition: { 
      type: 'spring', 
      stiffness: 260, 
      damping: 20,
      delay: i * 0.1
    }
  })
};

/**
 * Enhanced Desktop Widget - DeskGreet-style floating AI assistant
 * Features:
 * - Animated mini avatar with blinking and expressions
 * - Context-aware greetings (time, weather, tasks, focus)
 * - Smart quick actions that change based on context
 * - Expandable "more actions" menu
 */
const DesktopWidget: React.FC = () => {
  const [contexts, setContexts] = useState<ContextData[]>([]);
  const [isVisible, setIsVisible] = useState(false);
  const [avatarState, setAvatarState] = useState<'idle' | 'greeting' | 'listening'>('idle');
  const [showMoreActions, setShowMoreActions] = useState(false);
  const [currentContextIndex, setCurrentContextIndex] = useState(0);
  
  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState('');
  const [modalContent, setModalContent] = useState<React.ReactNode>(null);
  
  // Demo user
  const { user, updateStats } = useDemoUser();

  // Initialize visibility
  useEffect(() => {
    requestAnimationFrame(() => setIsVisible(true));
  }, []);

  // Update contexts periodically
  useEffect(() => {
    const updateContexts = () => {
      const newContexts = getContextualGreeting();
      setContexts(newContexts);
      
      // Trigger greeting animation when contexts update
      setAvatarState('greeting');
      setTimeout(() => setAvatarState('idle'), 2000);
    };

    updateContexts();
    const interval = setInterval(updateContexts, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // Detect Electron environment (synchronously)
  const isElectron = typeof window !== 'undefined' && !!(window as typeof window & { electronAPI?: unknown }).electronAPI;

  // Rotate through context messages
  useEffect(() => {
    if (contexts.length <= 1) return;
    
    const rotateInterval = setInterval(() => {
      setCurrentContextIndex((prev) => (prev + 1) % contexts.length);
    }, 5000); // Show each context for 5 seconds
    
    return () => clearInterval(rotateInterval);
  }, [contexts.length]);

  // Get current context message
  const currentContext = contexts[currentContextIndex] || contexts[0];
  const mainGreeting = contexts.find(c => c.type === 'time')?.message || 'Hello!';

  // Helper to show modal with demo user content
  const showModal = (title: string, content: React.ReactNode) => {
    setModalTitle(title);
    setModalContent(content);
    setModalOpen(true);
  };

  // Demo action handlers with modals
  const handleStandup = () => {
    updateStats('meetingsScheduled');
    showModal('Daily Standup', (
      <div className="space-y-4">
        <div className="flex items-center gap-3 p-3 bg-blue-500/10 rounded-lg">
          <User className="w-5 h-5 text-blue-400" />
          <div>
            <p className="text-white font-medium">{user.name}</p>
            <p className="text-neutral-400 text-sm">{user.role}</p>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-neutral-300">
            <CheckCircle2 className="w-4 h-4 text-green-400" />
            <span>Reviewed yesterday&apos;s tasks</span>
          </div>
          <div className="flex items-center gap-2 text-neutral-300">
            <CheckCircle2 className="w-4 h-4 text-green-400" />
            <span>Updated Jira tickets</span>
          </div>
          <div className="flex items-center gap-2 text-neutral-300">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <span>Today: Focus on API integration</span>
          </div>
        </div>
        <p className="text-neutral-500 text-sm">Standup prep complete! Ready for team sync.</p>
      </div>
    ));
  };

  const handleFocusMode = () => {
    showModal('Focus Mode Activated', (
      <div className="space-y-4">
        <div className="p-4 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-lg text-center">
          <Focus className="w-8 h-8 text-purple-400 mx-auto mb-2" />
          <p className="text-white font-semibold">Deep Work Session</p>
          <p className="text-neutral-400 text-sm">Notifications silenced for 25 minutes</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-white/5 rounded-lg text-center">
            <p className="text-2xl font-bold text-white">25</p>
            <p className="text-neutral-500 text-xs">minutes</p>
          </div>
          <div className="p-3 bg-white/5 rounded-lg text-center">
            <p className="text-2xl font-bold text-green-400">{user.stats.tasksCompleted}</p>
            <p className="text-neutral-500 text-xs">tasks today</p>
          </div>
        </div>
      </div>
    ));
  };

  const handleDailyReport = () => {
    updateStats('tasksCompleted');
    showModal('Daily Report', (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 bg-blue-500/10 rounded-lg text-center">
            <p className="text-xl font-bold text-blue-400">{user.stats.callsHandled}</p>
            <p className="text-neutral-500 text-xs">Calls</p>
          </div>
          <div className="p-3 bg-purple-500/10 rounded-lg text-center">
            <p className="text-xl font-bold text-purple-400">{user.stats.meetingsScheduled}</p>
            <p className="text-neutral-500 text-xs">Meetings</p>
          </div>
          <div className="p-3 bg-green-500/10 rounded-lg text-center">
            <p className="text-xl font-bold text-green-400">{user.stats.tasksCompleted}</p>
            <p className="text-neutral-500 text-xs">Tasks</p>
          </div>
        </div>
        <div className="p-3 bg-white/5 rounded-lg">
          <p className="text-neutral-300 text-sm">Great productivity today! 🎉</p>
          <p className="text-neutral-500 text-xs mt-1">Report saved and shared with team.</p>
        </div>
      </div>
    ));
  };

  // Smart actions based on time and context - NOT memoized since handlers change
  const getSmartActions = (): SmartAction[] => {
    const hour = new Date().getHours();
    const actions: SmartAction[] = [];
    
    // Morning actions (6-12)
    if (hour >= 6 && hour < 12) {
      actions.push(
        { id: 'standup', label: 'Daily Standup', icon: <MessageCircle className="w-4 h-4" />, shortcut: '⌘1', onClick: handleStandup },
        { id: 'reviews', label: 'Review PRs', icon: <Briefcase className="w-4 h-4" />, shortcut: '⌘2', onClick: () => showModal('PR Reviews', <p className="text-neutral-300">3 pull requests awaiting review. Opening GitHub...</p>) }
      );
    }
    
    // Work hours (9-17)
    if (hour >= 9 && hour < 17) {
      actions.push(
        { id: 'focus', label: 'Focus Mode', icon: <Focus className="w-4 h-4" />, shortcut: '⌘3', onClick: handleFocusMode },
        { id: 'schedule', label: 'Schedule Break', icon: <Calendar className="w-4 h-4" />, shortcut: '⌘4', onClick: () => showModal('Break Scheduled', <p className="text-neutral-300">15-minute break added to your calendar at 3:00 PM</p>) }
      );
    }
    
    // Evening actions (17-22)
    if (hour >= 17 && hour < 22) {
      actions.push(
        { id: 'report', label: 'Daily Report', icon: <Briefcase className="w-4 h-4" />, shortcut: '⌘5', onClick: handleDailyReport },
        { id: 'plan', label: 'Plan Tomorrow', icon: <Calendar className="w-4 h-4" />, shortcut: '⌘6', onClick: () => showModal('Tomorrow\'s Plan', <p className="text-neutral-300">Top priorities for tomorrow: API integration review, team standup, client presentation prep.</p>) }
      );
    }
    
    // Always available
    actions.push(
      { id: 'chat', label: 'Chat', icon: <MessageCircle className="w-4 h-4" />, shortcut: '⌘C', onClick: () => showModal('Chat', <p className="text-neutral-300">Opening chat interface...</p>) },
      { id: 'voice', label: 'Voice', icon: <Mic className="w-4 h-4" />, shortcut: '⌘V', onClick: () => { setAvatarState('listening'); showModal('Voice Mode', <p className="text-neutral-300">Listening... Speak now.</p>); } }
    );
    
    return actions;
  };

  const smartActions = getSmartActions();
  const primaryActions = smartActions.slice(0, 3); // Show top 3
  const moreActions = smartActions.slice(3); // Rest in "more" menu

  // ==========================================
  // ELECTRON INTEGRATION (Tasks 4-6)
  // ==========================================
  
  useEffect(() => {
    const electronAPI = (window as typeof window & { 
      electronAPI?: {
        onWidgetShown: (cb: () => void) => void;
        onWidgetHidden: (cb: () => void) => void;
        onWakeWordDetected: (cb: () => void) => void;
        onStartVoiceMode: (cb: () => void) => void;
        onOpenSettings: (cb: () => void) => void;
        removeAllListeners: (channel: string) => void;
      }
    }).electronAPI;
    
    if (!electronAPI) return;
    
    // Listen for widget visibility changes from tray
    electronAPI.onWidgetShown(() => {
      setIsVisible(true);
      setAvatarState('greeting');
      setTimeout(() => setAvatarState('idle'), 2000);
    });
    
    electronAPI.onWidgetHidden(() => {
      setIsVisible(false);
    });
    
    // Listen for wake word detection
    electronAPI.onWakeWordDetected(() => {
      setAvatarState('listening');
      // Pulse animation effect
      const pulseInterval = setInterval(() => {
        setAvatarState(prev => prev === 'listening' ? 'idle' : 'listening');
      }, 500);
      
      setTimeout(() => {
        clearInterval(pulseInterval);
        setAvatarState('listening');
      }, 1500);
    });
    
    // Start voice mode on wake word
    electronAPI.onStartVoiceMode(() => {
      setAvatarState('listening');
      // Trigger voice button action
      const voiceAction = smartActions.find(a => a.id === 'voice');
      if (voiceAction) voiceAction.onClick();
    });
    
    // Open settings request
    electronAPI.onOpenSettings(() => {
      showModal('Settings', <p className="text-neutral-300">Settings panel would open here.</p>);
    });
    
    // Cleanup listeners on unmount
    return () => {
      electronAPI.removeAllListeners('widget-shown');
      electronAPI.removeAllListeners('widget-hidden');
      electronAPI.removeAllListeners('wake-word-detected');
      electronAPI.removeAllListeners('start-voice-mode');
      electronAPI.removeAllListeners('open-settings');
    };
  }, [smartActions]);
  
  // Hide widget function (for Electron tray)
  const handleHideWidget = () => {
    const electronAPI = (window as typeof window & { electronAPI?: { hideWidget: () => void } }).electronAPI;
    if (electronAPI?.hideWidget) {
      electronAPI.hideWidget();
    } else {
      setIsVisible(false);
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate={isVisible ? "visible" : "hidden"}
      variants={containerVariants}
      className="fixed bottom-4 right-4 w-72 bg-[#0f1420]/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/10 p-4 z-50 flex flex-col gap-3"
    >
      {/* Header with Avatar and Greeting */}
      <div className="flex items-center gap-3">
        <div data-testid="widget-avatar" className="widget-avatar">
          <MiniAvatar state={avatarState} size={48} />
        </div>
        
        <div className="flex-1 min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentContextIndex}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <h2 className="text-lg font-bold text-white truncate">{mainGreeting}</h2>
              {currentContext && currentContext.type !== 'time' && (
                <div className="flex items-center gap-1.5 text-xs text-blue-400">
                  {currentContext.icon}
                  <span className="truncate">{currentContext.message}</span>
                </div>
              )}
              {!currentContext && (
                <p className="text-xs text-neutral-400">Your AI assistant is ready</p>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Context indicators (dots) */}
      {contexts.length > 1 && (
        <div className="flex gap-1 justify-center">
          {contexts.map((_, idx) => (
            <div
              key={idx}
              className={`w-1.5 h-1.5 rounded-full transition-colors ${
                idx === currentContextIndex ? 'bg-blue-500' : 'bg-white/20'
              }`}
            />
          ))}
        </div>
      )}
      
      {/* Smart Quick Actions */}
      <div className="flex flex-wrap gap-2">
        {primaryActions.map((action, i) => (
          <motion.button
            key={action.id}
            custom={i}
            initial="hidden"
            animate="visible"
            variants={actionVariants}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex-1 min-w-[80px] px-3 py-2 bg-blue-600/80 hover:bg-blue-500 text-white rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
            data-testid="quick-action"
            onClick={action.onClick}
            title={action.shortcut}
          >
            {action.icon}
            <span>{action.label}</span>
          </motion.button>
        ))}
        
        {/* More actions button */}
        {moreActions.length > 0 && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-3 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm font-medium transition-colors flex items-center justify-center"
            onClick={() => setShowMoreActions(!showMoreActions)}
          >
            <MoreHorizontal className="w-4 h-4" />
            <ChevronDown className={`w-3 h-3 ml-1 transition-transform ${showMoreActions ? 'rotate-180' : ''}`} />
          </motion.button>
        )}
      </div>

      {/* Expanded more actions */}
      <AnimatePresence>
        {showMoreActions && moreActions.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="flex flex-wrap gap-2 pt-2 border-t border-white/10">
              {moreActions.map((action) => (
                <motion.button
                  key={action.id}
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  whileHover={{ scale: 1.02, backgroundColor: 'rgba(255,255,255,0.15)' }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 min-w-[100px] px-3 py-2 bg-white/5 text-white/90 rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1.5"
                  data-testid="quick-action"
                  onClick={action.onClick}
                  title={action.shortcut}
                >
                  {action.icon}
                  <span>{action.label}</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer / Settings */}
      <div className="flex items-center justify-between pt-2 border-t border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-neutral-500">Avatario AI</span>
          {isElectron && (
            <span className="text-[8px] px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded-full">
              Desktop
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {isElectron && (
            <button 
              className="p-1.5 rounded-lg hover:bg-white/10 text-neutral-400 hover:text-white transition-colors"
              onClick={handleHideWidget}
              title="Hide to tray"
            >
              <span className="text-xs">−</span>
            </button>
          )}
          <button 
            className="p-1.5 rounded-lg hover:bg-white/10 text-neutral-400 hover:text-white transition-colors"
            onClick={() => showModal('Settings', (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <span className="text-neutral-300">Theme</span>
                  <span className="text-white">{user.preferences.theme}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <span className="text-neutral-300">Language</span>
                  <span className="text-white">{user.preferences.language}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <span className="text-neutral-300">Notifications</span>
                  <span className="text-green-400">{user.preferences.notifications ? 'On' : 'Off'}</span>
                </div>
              </div>
            ))}
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Modern Centered Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={modalTitle}
      >
        {modalContent}
      </Modal>
    </motion.div>
  );
};

export default DesktopWidget;
