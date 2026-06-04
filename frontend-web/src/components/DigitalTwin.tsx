import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface TwinData {
  name: string;
  interactions: number;
  learnedFacts: string[];
  preferences: Record<string, string>;
  lastActive: string;
}

interface DigitalTwinProps {
  twinData?: TwinData;
  onSuggest?: (suggestion: string) => void;
}

export const DigitalTwin: React.FC<DigitalTwinProps> = ({ 
  twinData,
  onSuggest 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [learningStatus, setLearningStatus] = useState<'idle' | 'learning' | 'ready'>('idle');

  useEffect(() => {
    // Generate proactive suggestions based on time and twin data
    const generateSuggestions = () => {
      const hour = new Date().getHours();
      const newSuggestions: string[] = [];

      if (hour >= 9 && hour < 10) {
        newSuggestions.push('You usually check emails at this time. Shall I summarize your inbox?');
      }
      if (hour >= 14 && hour < 15) {
        newSuggestions.push('Time for your afternoon standup. I can prepare your update notes.');
      }
      if (twinData?.interactions && twinData.interactions > 100) {
        newSuggestions.push('I\'ve learned a lot about your preferences. Would you like me to optimize my responses?');
      }

      setSuggestions(newSuggestions);
    };

    generateSuggestions();
    const interval = setInterval(generateSuggestions, 60000);
    return () => clearInterval(interval);
  }, [twinData]);

  const handleLearnFromInteraction = async () => {
    setLearningStatus('learning');
    
    // Simulate learning process
    setTimeout(() => {
      setLearningStatus('ready');
      setTimeout(() => setLearningStatus('idle'), 3000);
    }, 2000);
  };

  const defaultTwinData: TwinData = {
    name: 'My Digital Twin',
    interactions: 0,
    learnedFacts: [],
    preferences: {},
    lastActive: new Date().toISOString()
  };

  const data = twinData || defaultTwinData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-md bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl shadow-lg p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <motion.div
            className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-2xl"
            animate={{ 
              scale: learningStatus === 'learning' ? [1, 1.1, 1] : 1,
              rotate: learningStatus === 'learning' ? [0, 360] : 0
            }}
            transition={{ duration: 2, repeat: learningStatus === 'learning' ? Infinity : 0 }}
          >
            🤖
          </motion.div>
          <div>
            <h3 className="font-bold text-gray-800">{data.name}</h3>
            <p className="text-xs text-gray-500">
              Last active: {new Date(data.lastActive).toLocaleDateString()}
            </p>
          </div>
        </div>
        
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-white/60 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-600">{data.interactions}</div>
          <div className="text-xs text-gray-500">Interactions</div>
        </div>
        <div className="bg-white/60 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">{data.learnedFacts.length}</div>
          <div className="text-xs text-gray-500">Facts Learned</div>
        </div>
        <div className="bg-white/60 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-600">{Object.keys(data.preferences).length}</div>
          <div className="text-xs text-gray-500">Preferences</div>
        </div>
      </div>

      {/* Learning Status */}
      {learningStatus !== 'idle' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mb-4 p-3 bg-blue-100 rounded-lg"
        >
          <p className="text-sm text-blue-700">
            {learningStatus === 'learning' ? '🧠 Learning from your interactions...' : '✅ Learning complete!'}
          </p>
        </motion.div>
      )}

      {/* Proactive Suggestions */}
      {suggestions.length > 0 && (
        <div className="space-y-2 mb-4">
          <h4 className="text-sm font-medium text-gray-700">Proactive Suggestions</h4>
          {suggestions.map((suggestion, index) => (
            <motion.button
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => onSuggest?.(suggestion)}
              className="w-full text-left p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow text-sm text-gray-700"
            >
              💡 {suggestion}
            </motion.button>
          ))}
        </div>
      )}

      {/* Expanded Details */}
      {isExpanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="space-y-3"
        >
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Learned Facts</h4>
            {data.learnedFacts.length > 0 ? (
              <ul className="space-y-1">
                {data.learnedFacts.map((fact, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-purple-400 rounded-full"></span>
                    {fact}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400 italic">No facts learned yet. Start interacting to build your twin!</p>
            )}
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Preferences</h4>
            {Object.keys(data.preferences).length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {Object.entries(data.preferences).map(([key, value]) => (
                  <span key={key} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                    {key}: {value}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">No preferences set yet.</p>
            )}
          </div>

          <motion.button
            onClick={handleLearnFromInteraction}
            disabled={learningStatus !== 'idle'}
            className="w-full py-2 bg-purple-600 text-white rounded-lg text-sm font-medium disabled:bg-gray-300 hover:bg-purple-700 transition-colors"
            whileTap={{ scale: 0.98 }}
          >
            {learningStatus === 'idle' ? '🔄 Learn from Recent Interactions' : 'Learning...'}
          </motion.button>
        </motion.div>
      )}
    </motion.div>
  );
};

export default DigitalTwin;
