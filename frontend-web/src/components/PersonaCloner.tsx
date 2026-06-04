import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';

interface PersonaClonerProps {
  onCloneComplete: (personaId: string) => void;
}

export const PersonaCloner: React.FC<PersonaClonerProps> = ({ onCloneComplete }) => {
  const [step, setStep] = useState(1);
  const [personaName, setPersonaName] = useState('');
  const [samples, setSamples] = useState<string[]>([]);
  const [isCloning, setIsCloning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [cloneResult, setCloneResult] = useState<{ id: string; name: string } | null>(null);

  const handleAddSample = useCallback((text: string) => {
    if (text.trim() && samples.length < 10) {
      setSamples([...samples, text.trim()]);
    }
  }, [samples]);

  const handleRemoveSample = useCallback((index: number) => {
    setSamples(samples.filter((_, i) => i !== index));
  }, [samples]);

  const startCloning = useCallback(async () => {
    setIsCloning(true);
    setProgress(0);

    // Simulate cloning process
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 500);

    // Simulate API call
    setTimeout(() => {
      clearInterval(interval);
      setProgress(100);
      const result = { id: `persona-${Date.now()}`, name: personaName };
      setCloneResult(result);
      setIsCloning(false);
      onCloneComplete(result.id);
    }, 5000);
  }, [personaName, samples, onCloneComplete]);

  const reset = useCallback(() => {
    setStep(1);
    setPersonaName('');
    setSamples([]);
    setIsCloning(false);
    setProgress(0);
    setCloneResult(null);
  }, []);

  return (
    <div className="w-full max-w-lg bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Clone Persona</h2>

      {step === 1 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Persona Name
            </label>
            <input
              type="text"
              value={personaName}
              onChange={(e) => setPersonaName(e.target.value)}
              placeholder="e.g., Professional Assistant, Friendly Companion"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <motion.button
            onClick={() => setStep(2)}
            disabled={!personaName.trim()}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
            whileTap={{ scale: 0.98 }}
          >
            Next: Add Training Samples
          </motion.button>
        </motion.div>
      )}

      {step === 2 && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Training Samples ({samples.length}/10)
            </label>
            <p className="text-xs text-gray-500 mb-3">
              Add text samples that represent how this persona should speak. These can be transcripts, writing samples, or example responses.
            </p>
            
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                id="sample-input"
                placeholder="Enter a sample phrase or response..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const input = e.target as HTMLInputElement;
                    handleAddSample(input.value);
                    input.value = '';
                  }
                }}
              />
              <button
                onClick={() => {
                  const input = document.getElementById('sample-input') as HTMLInputElement;
                  handleAddSample(input.value);
                  input.value = '';
                }}
                disabled={samples.length >= 10}
                className="px-4 py-2 bg-green-600 text-white rounded-lg disabled:bg-gray-300 hover:bg-green-700 transition-colors"
              >
                Add
              </button>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto">
              {samples.map((sample, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center justify-between bg-gray-50 p-3 rounded-lg"
                >
                  <span className="text-sm text-gray-700 truncate flex-1">{sample}</span>
                  <button
                    onClick={() => handleRemoveSample(index)}
                    className="ml-2 text-red-500 hover:text-red-700"
                  >
                    ✕
                  </button>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setStep(1)}
              className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Back
            </button>
            <motion.button
              onClick={() => setStep(3)}
              disabled={samples.length < 3}
              className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
              whileTap={{ scale: 0.98 }}
            >
              Next: Review & Clone
            </motion.button>
          </div>
        </motion.div>
      )}

      {step === 3 && !isCloning && !cloneResult && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-4"
        >
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-800 mb-2">Review</h3>
            <p className="text-sm text-gray-600">Name: {personaName}</p>
            <p className="text-sm text-gray-600">Samples: {samples.length}</p>
          </div>

          <p className="text-sm text-gray-500">
            Cloning will train a custom persona model based on your samples. This process takes about 5 minutes.
          </p>

          <div className="flex gap-3">
            <button
              onClick={() => setStep(2)}
              className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Back
            </button>
            <motion.button
              onClick={startCloning}
              className="flex-1 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
              whileTap={{ scale: 0.98 }}
            >
              Start Cloning
            </motion.button>
          </div>
        </motion.div>
      )}

      {isCloning && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4 text-center"
        >
          <div className="text-lg font-medium text-gray-800">Cloning in progress...</div>
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <motion.div
              className="h-full bg-blue-600"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          <p className="text-sm text-gray-500">{progress}% complete</p>
          <p className="text-xs text-gray-400">Training custom LoRA adapter...</p>
        </motion.div>
      )}

      {cloneResult && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-4 text-center"
        >
          <div className="text-4xl mb-2">🎉</div>
          <h3 className="text-xl font-bold text-gray-800">Persona Cloned Successfully!</h3>
          <p className="text-gray-600">{cloneResult.name} is ready to use.</p>
          <motion.button
            onClick={reset}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            whileTap={{ scale: 0.98 }}
          >
            Clone Another Persona
          </motion.button>
        </motion.div>
      )}
    </div>
  );
};

export default PersonaCloner;
