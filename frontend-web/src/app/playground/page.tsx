"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Zap, Brain, Mic, Users, Sparkles } from "lucide-react";
import DesktopWidget from "@/components/DesktopWidget";
import { DigitalTwin } from "@/components/DigitalTwin";
import { RealtimeVoice } from "@/components/RealtimeVoice";
import { PersonaCloner } from "@/components/PersonaCloner";
import { FaceClone } from "@/components/FaceClone";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.25, 0.1, 0.25, 1] as const }
  }
};

export default function PlaygroundPage() {
  return (
    <div className="min-h-screen bg-[#080b12] text-white" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 h-16 bg-[#080b12]/85 backdrop-blur-lg border-b border-white/6">
        <div className="flex items-center gap-2.5">
          <Link href="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-white text-lg tracking-tight">Avatario Playground</span>
          </Link>
        </div>
        <Link 
          href="/" 
          className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </nav>

      {/* Main Content */}
      <main className="pt-24 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Title Section */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-16"
          >
            <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-3">Interactive Demos</p>
            <h1 className="text-4xl md:text-5xl font-extrabold mb-4">AI Component Playground</h1>
            <p className="text-neutral-400 max-w-2xl mx-auto">
              Test and interact with all our AI components in real-time. 
              Experience the future of legal AI assistance.
            </p>
          </motion.div>

          {/* Components Grid */}
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
          >
            {/* Desktop Widget */}
            <motion.div variants={itemVariants} className="rounded-2xl border border-white/8 bg-[#0f1420] overflow-hidden">
              <div className="px-6 py-4 border-b border-white/8 bg-[#0c1019] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-500/15 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm">Desktop Widget</h3>
                  <p className="text-neutral-500 text-xs">Context-aware greetings & quick actions</p>
                </div>
              </div>
              <div className="p-6 flex justify-center min-h-[300px] items-center bg-gradient-to-b from-[#0f1420] to-[#0a0d14]">
                <DesktopWidget />
              </div>
            </motion.div>

            {/* Digital Twin */}
            <motion.div variants={itemVariants} className="rounded-2xl border border-white/8 bg-[#0f1420] overflow-hidden">
              <div className="px-6 py-4 border-b border-white/8 bg-[#0c1019] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-purple-500/15 flex items-center justify-center">
                  <Brain className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm">Digital Twin</h3>
                  <p className="text-neutral-500 text-xs">AI that learns from interactions</p>
                </div>
              </div>
              <div className="p-4 min-h-[300px] bg-gradient-to-b from-[#0f1420] to-[#0a0d14] overflow-y-auto">
                <DigitalTwin 
                  twinData={{
                    name: "Legal Assistant Twin",
                    interactions: 1523,
                    learnedFacts: [
                      "Prefer email summaries over detailed reports",
                      "Most active during 9-11 AM",
                      "Frequently handles contract reviews"
                    ],
                    preferences: {
                      language: "English",
                      communicationStyle: "Professional"
                    },
                    lastActive: new Date().toISOString()
                  }}
                />
              </div>
            </motion.div>

            {/* Realtime Voice */}
            <motion.div variants={itemVariants} className="rounded-2xl border border-white/8 bg-[#0f1420] overflow-hidden">
              <div className="px-6 py-4 border-b border-white/8 bg-[#0c1019] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-green-500/15 flex items-center justify-center">
                  <Mic className="w-4 h-4 text-green-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm">Realtime Voice</h3>
                  <p className="text-neutral-500 text-xs">Low-latency voice conversations</p>
                </div>
              </div>
              <div className="p-6 flex justify-center min-h-[300px] items-center bg-gradient-to-b from-[#0f1420] to-[#0a0d14]">
                <RealtimeVoice 
                  onTranscript={(text) => console.log('Voice transcript:', text)}
                  onInterrupt={() => console.log('Voice interrupted')}
                  isPlaying={false}
                />
              </div>
            </motion.div>

            {/* Persona Cloner */}
            <motion.div variants={itemVariants} className="rounded-2xl border border-white/8 bg-[#0f1420] overflow-hidden lg:col-span-2">
              <div className="px-6 py-4 border-b border-white/8 bg-[#0c1019] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-orange-500/15 flex items-center justify-center">
                  <Users className="w-4 h-4 text-orange-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm">Persona Cloner</h3>
                  <p className="text-neutral-500 text-xs">Clone and customize AI personas</p>
                </div>
              </div>
              <div className="p-6 min-h-[400px] bg-gradient-to-b from-[#0f1420] to-[#0a0d14]">
                <PersonaCloner 
                  onCloneComplete={(id) => console.log('Persona cloned:', id)} 
                />
              </div>
            </motion.div>

            {/* Face Clone */}
            <motion.div variants={itemVariants} className="rounded-2xl border border-white/8 bg-[#0f1420] overflow-hidden">
              <div className="px-6 py-4 border-b border-white/8 bg-[#0c1019] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-pink-500/15 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-pink-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm">Face Clone</h3>
                  <p className="text-neutral-500 text-xs">AI avatar face generation</p>
                </div>
              </div>
              <div className="p-6 flex justify-center min-h-[300px] items-center bg-gradient-to-b from-[#0f1420] to-[#0a0d14]">
                <FaceClone 
                  onFaceSelected={(face) => console.log('Face selected:', face)}
                />
              </div>
            </motion.div>
          </motion.div>

          {/* Footer Note */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="mt-16 text-center"
          >
            <p className="text-neutral-500 text-sm">
              All components are fully functional. Check the browser console for interaction logs.
            </p>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
