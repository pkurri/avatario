import { useEffect, useState } from 'react';
import { motion, Variants } from 'framer-motion';

const containerVariants: Variants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3, ease: 'easeOut' } },
};

const buttonVariants: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.2 } },
};

function getGreetingMessage(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good Morning';
  if (hour < 17) return 'Good Afternoon';
  return 'Good Evening';
}

interface DesktopWidgetProps {
  onChat?: () => void;
  onVoice?: () => void;
  onSettings?: () => void;
}

const DesktopWidget: React.FC<DesktopWidgetProps> = ({ onChat, onVoice, onSettings }) => {
  const [greeting, setGreeting] = useState(getGreetingMessage());
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    const interval = setInterval(() => setGreeting(getGreetingMessage()), 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial="hidden"
      animate={isVisible ? 'visible' : 'hidden'}
      variants={containerVariants}
      className="fixed bottom-4 right-4 w-64 bg-white/90 backdrop-blur-md rounded-xl shadow-lg p-4 z-50 flex flex-col space-y-3"
    >
      <div className="text-center">
        <h2 className="text-xl font-bold text-gray-800">{greeting}</h2>
        <p className="text-sm text-gray-500">Your AI assistant is ready to help</p>
      </div>

      <div className="flex flex-wrap gap-2 justify-center">
        <motion.button
          variants={buttonVariants}
          className="flex-1 min-w-[80px] px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          onClick={onChat}
        >
          <span>💬</span>
          <span>Chat</span>
        </motion.button>

        <motion.button
          variants={buttonVariants}
          className="flex-1 min-w-[80px] px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
          onClick={onVoice}
        >
          <span>🎤</span>
          <span>Voice</span>
        </motion.button>

        <motion.button
          variants={buttonVariants}
          className="flex-1 min-w-[80px] px-3 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
          onClick={onSettings}
        >
          <span>⚙️</span>
          <span>Settings</span>
        </motion.button>
      </div>
    </motion.div>
  );
};

export default DesktopWidget;
