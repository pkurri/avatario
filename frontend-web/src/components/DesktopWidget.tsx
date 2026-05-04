import { useEffect, useState } from 'react';
import { motion, Variants } from 'framer-motion';

// Define time-based greeting messages
const getGreetingMessage = (): string => {
  const hour = new Date().getHours();
  if (hour < 12) {
    return 'Good morning!';
  } else if (hour < 17) {
    return 'Good afternoon!';
  } else if (hour < 20) {
    return 'Good evening!';
  } else {
    return 'Good night!';
  }
};

// Variants for Framer Motion animations
const containerVariants: Variants = {
  hidden: { y: 20, opacity: 0 },
  visible: { 
    y: 0, 
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 20
    }
  }
};

const buttonVariants: Variants = {
  hidden: { scale: 0 },
  visible: { 
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 260,
      damping: 20
    }
  }
};

const DesktopWidget: React.FC = () => {
  const [greeting, setGreeting] = useState(getGreetingMessage());
  const [isVisible, setIsVisible] = useState(false);

  // Update greeting based on time of day (every minute)
  useEffect(() => {
    setIsVisible(true);
    
    const updateGreeting = () => {
      setGreeting(getGreetingMessage());
    };

    const interval = setInterval(updateGreeting, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial="hidden"
      animate={isVisible ? "visible" : "hidden"}
      variants={containerVariants}
      className="fixed bottom-4 right-4 w-64 bg-white/90 backdrop-blur-md rounded-xl shadow-lg p-4 z-50 flex flex-col space-y-3"
    >
      <div className="text-center">
        <h2 className="text-xl font-bold text-gray-800">{greeting}</h2>
        <p className="text-sm text-gray-500">Your AI assistant is ready to help</p>
      </div>
      
      <div className="flex flex-wrap gap-2 justify-center">
        {/* Chat Button */}
        <motion.button
          initial="hidden"
          animate="visible"
          variants={buttonVariants}
          className="flex-1 min-w-[80px] px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          onClick={() => alert('Opening chat...')}
        >
          <span>💬</span>
          <span>Chat</span>
        </motion.button>
        
        {/* Voice Button */}
        <motion.button
          initial="hidden"
          animate="visible"
          variants={buttonVariants}
          className="flex-1 min-w-[80px] px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
          onClick={() => alert('Starting voice...')}
        >
          <span>🎤</span>
          <span>Voice</span>
        </motion.button>
        
        {/* Settings Button */}
        <motion.button
          initial="hidden"
          animate="visible"
          variants={buttonVariants}
          className="flex-1 min-w-[80px] px-3 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
          onClick={() => alert('Opening settings...')}
        >
          <span>⚙️</span>
          <span>Settings</span>
        </motion.button>
      </div>
    </motion.div>
  );
};

export default DesktopWidget;
