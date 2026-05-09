// frontend-web/src/app/page.tsx
"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  Mic,
  Scale,
  Brain,
  Zap,
  Globe,
  Shield,
  Plus,
  Minus,
  ArrowRight,
  CheckCircle,
  Users,
  FileText,
  MessageSquare,
  Phone,
  PhoneCall,
  Database,
  Code2,
  BarChart3,
  Layers,
} from "lucide-react";

const NAV_LINKS = [
  { label: "Capabilities", href: "#capabilities" },
  { label: "Use cases", href: "#use-cases" },
  { label: "Platform", href: "#platform" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
  { label: "Contact", href: "#contact" },
];

const CAPABILITIES = [
  { icon: Mic,      title: "Natural conversations",   desc: "Sub-second latency, human-like turn-taking, and graceful interruption handling — even on poor connections." },
  { icon: Brain,    title: "Tool-aware memory",        desc: "Remembers past conversations, client history and context so every session picks up where the last one left off." },
  { icon: Zap,      title: "Workflow automation",      desc: "Pre-call enrichment, in-call and post-call actions — defined visually, no developer required." },
  { icon: MessageSquare, title: "Intelligent routing", desc: "Queue management, voicemail logic and live transfers when a real human is the right answer." },
  { icon: Globe,    title: "Multi-channel deployment", desc: "One agent, every channel — phone, web widget and direct API. Same brain, same actions." },
  { icon: Code2,    title: "Full API. No code required", desc: "Visual editor for operators. REST API, webhooks and MCP for engineers. Use both, switch any time." },
];

// ── DATA ──────────────────────────────────────────────────────────────────────

const USE_CASES = [
  { icon: Scale,        title: "Law firms",              desc: "Client intake, matter updates, appointment booking — handled before the lawyer picks up." },
  { icon: FileText,     title: "Legal aid centres",      desc: "Qualify eligibility, explain rights and route clients to the right department automatically." },
  { icon: Users,        title: "Corporate legal teams",  desc: "Answer routine contract and compliance queries, escalate anything that needs counsel review." },
  { icon: MessageSquare,title: "Litigation support",     desc: "Court date reminders, document checklist follow-ups, witness scheduling — all automated." },
  { icon: Phone,        title: "Client helplines",       desc: "Triage inbound queries at scale. Handle 100 simultaneous calls without hold music." },
  { icon: Globe,        title: "Multi-jurisdiction",     desc: "Localised voice personas for different regions — same platform, different tone and language." },
];

const PRICING = [
  {
    name: "Starter", price: "₹4,999", period: "/mo",
    desc: "Solo practitioners and small firms.",
    features: ["1 AI voice persona","Up to 500 calls / month","English + 1 regional language","Basic analytics","Email support"],
    cta: "Get started", highlight: false,
  },
  {
    name: "Professional", price: "₹14,999", period: "/mo",
    desc: "Growing firms that need more personas and integrations.",
    features: ["5 AI voice personas","Up to 2,000 calls / month","All supported languages","CRM & calendar integrations","Advanced analytics","Priority support"],
    cta: "Start free trial", highlight: true,
  },
  {
    name: "Enterprise", price: "Custom", period: "",
    desc: "Full platform access with dedicated support and custom SLAs.",
    features: ["Unlimited personas","Unlimited calls","Custom integrations & API","On-premise deployment option","Dedicated success manager","SLA guarantee"],
    cta: "Contact us", highlight: false,
  },
];

const FAQS = [
  { q: "How is this different from a chatbot?",    a: "Avatario speaks and listens in real time over voice — not a chat widget. It holds multi-turn conversations, understands context, and takes actions like booking appointments or sending documents." },
  { q: "Is client data safe?",                     a: "Yes. All data is encrypted in transit and at rest. We never use client conversations to train models. You control retention and can delete data at any time." },
  { q: "Which languages are supported?",           a: "English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, and Punjabi — with more being added continuously." },
  { q: "Can it transfer to a human?",              a: "Yes. You define escalation rules — e.g. 'transfer if the caller mentions bail or urgent hearing'. The AI hands off gracefully and briefs the advocate in real time." },
  { q: "Can I build advanced workflows?",          a: "Yes. The visual workflow editor lets you define pre-call enrichment, in-call actions, and post-call follow-ups without writing code. REST API and webhooks available for engineers." },
  { q: "How long does setup take?",                a: "Most teams are live within 48 hours. You provide your practice areas, FAQs, and team availability — we handle the rest." },
];

const PLATFORM_STEPS = [
  { n: "01", icon: Brain,    title: "Configure intelligent agents",  desc: "Voice selection, knowledge bases, scripts and reasoning blocks — all from a clean visual editor." },
  { n: "02", icon: Zap,      title: "Build workflow automation",     desc: "Pre-call, in-call and post-call actions that complete real work, not just log it." },
  { n: "03", icon: Database, title: "Integrate your systems",        desc: "Webhooks, REST API, 200+ prebuilt tools and SIP trunking — meet your stack where it lives." },
  { n: "04", icon: Layers,   title: "Deploy across channels",        desc: "Phone, web widget and direct API — one agent, sub-second latency." },
  { n: "05", icon: BarChart3,title: "Optimise with data",            desc: "Real-time analytics, transcripts and recordings. Spot losing turns and fix them in minutes." },
  { n: "06", icon: Shield,   title: "Scale with confidence",         desc: "Concurrency, queue handling, smart routing and enterprise integrations — already battle-tested." },
];

const DEMO_MESSAGES = [
  { from: "client", text: "Hi, I need urgent advice on a consumer fraud case.", time: "0:02", action: "" },
  { from: "ai",     text: "I understand. Can you briefly describe what happened?", time: "0:04", action: "routing to Consumer Law" },
  { from: "client", text: "I paid for a product that was never delivered, three months ago.", time: "0:09", action: "" },
  { from: "ai",     text: "You have strong grounds under the Consumer Protection Act 2019. I'm booking you a slot with our consumer advocate now.", time: "0:13", action: "appointment booked · SMS sent" },
];

// ── HELPERS ───────────────────────────────────────────────────────────────────

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="border border-white/10 rounded-xl overflow-hidden cursor-pointer hover:border-white/20 transition-colors"
      onClick={() => setOpen(!open)}
    >
      <div className="flex items-center justify-between px-6 py-5">
        <span className="text-white font-medium pr-4">{q}</span>
        {open ? <Minus className="w-5 h-5 text-blue-400 shrink-0" /> : <Plus className="w-5 h-5 text-neutral-400 shrink-0" />}
      </div>
      {open && <div className="px-6 pb-5 text-neutral-400 text-sm leading-relaxed">{a}</div>}
    </div>
  );
}

// ── PAGE ──────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  const [industry, setIndustry] = useState("Law firm");
  const [language, setLanguage] = useState("English");

  return (
    <div className="min-h-screen bg-[#080b12] text-white" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>

      {/* ── NAV ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 h-16 bg-[#080b12]/85 backdrop-blur-lg border-b border-white/6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <Scale className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-white text-lg tracking-tight">Avatario</span>
        </div>
        <div className="hidden md:flex items-center gap-7">
          {NAV_LINKS.map(l => (
            <a key={l.label} href={l.href} className="text-sm text-neutral-400 hover:text-white transition-colors">{l.label}</a>
          ))}
        </div>
        <Link href="/assistant" className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-colors shadow-md shadow-blue-500/20">
          Book a demo
        </Link>
      </nav>

      {/* ── HERO ── */}
      <section className="relative pt-36 pb-16 flex flex-col items-center text-center px-6 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[700px] bg-blue-700/8 rounded-full blur-[140px] pointer-events-none" />

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-blue-500/25 bg-blue-500/8 text-blue-400 text-sm mb-7 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          AI assistant that answers your client calls
        </motion.div>

        <motion.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.08 }}
          className="text-5xl md:text-7xl font-extrabold tracking-tight max-w-4xl leading-[1.06] text-white">
          The AI lawyer that{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
            answers your<br />client calls
          </span>
        </motion.h1>

        <motion.p initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.16 }}
          className="mt-6 text-[1.1rem] text-neutral-400 max-w-2xl leading-relaxed">
          Avatario receives and answers client calls and messages 24/7 — booking consultations,
          qualifying matters, taking instructions, routing urgent cases and following up.
          A complete AI advocate, in English and 9 Indian languages.
        </motion.p>

        {/* ── LIVE DEMO WIDGET ── */}
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.24 }}
          className="mt-10 w-full max-w-lg rounded-2xl border border-white/12 bg-[#0f1420] overflow-hidden shadow-2xl text-left">
          <div className="flex items-center justify-between px-5 py-3 border-b border-white/8">
            <div className="flex items-center gap-2 text-sm text-white font-medium">
              <PhoneCall className="w-4 h-4 text-blue-400" />
              Talk to your AI lawyer live
            </div>
            <span className="text-neutral-500 text-xs">Free, no signup, ends in ~3 min</span>
          </div>
          <div className="p-5 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-neutral-500 text-xs uppercase tracking-wider mb-1.5 block">I run a</label>
                <select value={industry} onChange={e => setIndustry(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg bg-[#1a2030] border border-white/10 text-white text-sm focus:outline-none focus:border-blue-500/50 cursor-pointer">
                  {["Law firm","Legal aid centre","Corporate legal team","Litigation firm","Law school","Solo practice"].map(o => <option key={o}>{o}</option>)}
                </select>
              </div>
              <div>
                <label className="text-neutral-500 text-xs uppercase tracking-wider mb-1.5 block">Language</label>
                <select value={language} onChange={e => setLanguage(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg bg-[#1a2030] border border-white/10 text-white text-sm focus:outline-none focus:border-blue-500/50 cursor-pointer">
                  {["English","Hindi only","Tamil only","Telugu only","English + Hindi","All languages"].map(o => <option key={o}>{o}</option>)}
                </select>
              </div>
            </div>
            <Link href="/assistant"
              className="flex items-center justify-center gap-2 w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 text-white font-semibold text-base transition-all shadow-lg shadow-blue-500/25">
              <Mic className="w-4 h-4" />
              Talk to it now in your browser
            </Link>
            <p className="text-center text-neutral-500 text-xs">Free, no signup. Mic permission required for browser call.</p>
          </div>
        </motion.div>

        {/* ── NEW SECTION ── */}
        <section className="py-20 px-6 flex justify-center">
          <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-[#0f1420] overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between px-5 py-3 border-t border-white/8 bg-[#0c1019]">
              <div className="flex items-end gap-0.5 h-5">
                {[...Array(22)].map((_, i) => (
                  <motion.div key={i} className="w-[3px] bg-blue-400/50 rounded-full"
                    animate={{ height: [3, 6 + (i % 4) * 4, 3] }}
                    transition={{ duration: 0.35 + (i % 3) * 0.15, repeat: Infinity, delay: i * 0.04 }} />
                ))}
              </div>
              <span className="text-neutral-500 text-xs">0:14 · 480ms latency · 1 booking · 1 SMS sent</span>
            </div>
            <div className="p-6 space-y-5">
              <h2 className="text-4xl font-extrabold leading-tight mb-5">Desktop Widget, Digital Twin, Realtime Voice, and Persona Cloner</h2>
              <p className="text-neutral-400 text-sm leading-relaxed mb-8">Avatario's cutting-edge features enable seamless integration with your existing systems, providing a more comprehensive and efficient experience for your clients.</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-6 rounded-2xl border border-white/8 bg-[#0f1420] hover:border-blue-500/25 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center mb-4">
                    <DesktopWidget className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="text-white font-semibold mb-2">Desktop Widget</h3>
                  <p className="text-neutral-400 text-sm leading-relaxed">A customizable widget that allows you to integrate Avatario's AI capabilities directly into your desktop environment.</p>
                </div>
                <div className="p-6 rounded-2xl border border-white/8 bg-[#0f1420] hover:border-blue-500/25 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center mb-4">
                    <DigitalTwin className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="text-white font-semibold mb-2">Digital Twin</h3>
                  <p className="text-neutral-400 text-sm leading-relaxed">A virtual replica of your physical systems, allowing for real-time monitoring and optimization of your operations.</p>
                </div>
                <div className="p-6 rounded-2xl border border-white/8 bg-[#0f1420] hover:border-blue-500/25 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center mb-4">
                    <RealtimeVoice className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="text-white font-semibold mb-2">Realtime Voice</h3>
                  <p className="text-neutral-400 text-sm leading-relaxed">A feature that enables real-time voice interactions with your clients, providing a more human-like experience.</p>
                </div>
                <div className="p-6 rounded-2xl border border-white/8 bg-[#0f1420] hover:border-blue-500/25 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center mb-4">
                    <PersonaCloner className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="text-white font-semibold mb-2">Persona Cloner</h3>
                  <p className="text-neutral-400 text-sm leading-relaxed">A feature that allows you to clone and customize existing personas, enabling you to create unique and tailored experiences for your clients.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── TRUSTED BY ── */}
        <div className="py-10 px-6 border-y border-white/5">
          <p className="text-center text-xs text-neutral-500 uppercase tracking-widest mb-6">Trusted by legal teams across clinics, firms, and corporates</p>
          <div className="flex flex-wrap items-center justify-center gap-12 text-neutral-600 font-bold text-sm tracking-widest">
            {["LEXCORP","JUSTICE HUB","VAKIL DESK","LAWBRIDGE","LEXICA","COURTSIDE"].map(b => <span key={b}>{b}</span>)}
          </div>
        </div>

        {/* ── CHAT DEMO ── */}
        <section className="py-20 px-6 flex justify-center">
          <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-[#0f1420] overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between px-5 py-3 border-t border-white/8 bg-[#0c1019]">
              <div className="flex items-end gap-0.5 h-5">
                {[...Array(22)].map((_, i) => (
                  <motion.div key={i} className="w-[3px] bg-blue-400/50 rounded-full"
                    animate={{ height: [3, 6 + (i % 4) * 4, 3] }}
                    transition={{ duration: 0.35 + (i % 3) * 0.15, repeat: Infinity, delay: i * 0.04 }} />
                ))}
              </div>
              <span className="text-neutral-500 text-xs">0:14 · 480ms latency · 1 booking · 1 SMS sent</span>
            </div>
            <div className="p-6 space-y-5">
              {DEMO_MESSAGES.map((msg, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 + i * 0.4, duration: 0.4 }}
                  className={`flex ${msg.from === "ai" ? "justify-end" : "justify-start"}`}>
                  <div className="flex flex-col gap-1.5 max-w-sm">
                    <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.from === "ai" ? "bg-blue-600 text-white rounded-br-sm" : "bg-white/10 text-white rounded-bl-sm"}`}>
                      {msg.text}
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-neutral-500 text-xs">{msg.from === "ai" ? "Avatario" : "Caller"} · {msg.time}</span>
                      {msg.action && <span className="px-2 py-0.5 rounded-full bg-green-500/12 border border-green-500/20 text-green-400 text-xs">+ {msg.action}</span>}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
            <div className="flex items-center justify-between px-5 py-3 border-t border-white/8 bg-[#0c1019]">
              <div className="flex items-end gap-0.5 h-5">
                {[...Array(22)].map((_, i) => (
                  <motion.div key={i} className="w-[3px] bg-blue-400/50 rounded-full"
                    animate={{ height: [3, 6 + (i % 4) * 4, 3] }}
                    transition={{ duration: 0.35 + (i % 3) * 0.15, repeat: Infinity, delay: i * 0.04 }} />
                ))}
              </div>
              <span className="text-neutral-500 text-xs">0:14 · 480ms latency · 1 booking · 1 SMS sent</span>
            </div>
          </div>
        </section>

        {/* ── CAPABILITIES ── */}
        <section id="capabilities" className="py-24 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-14">
              <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-3">Core Capabilities</p>
              <h2 className="text-4xl md:text-5xl font-extrabold leading-tight">Everything an agent needs to<br />actually finish the job</h2>
              <p className="mt-4 text-neutral-400 max-w-xl mx-auto">Voice AI that doesn&apos;t just talk — it books, updates, escalates and follows up across your stack.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {CAPABILITIES.map(cap => (
                <div key={cap.title} className="p-6 rounded-2xl border border-white/8 bg-[#0f1420] hover:border-blue-500/30 hover:bg-blue-500/4 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center mb-4">
                    <cap.icon className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="text-white font-semibold mb-2">{cap.title}</h3>
                  <p className="text-neutral-400 text-sm leading-relaxed">{cap.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── USE CASES ── */}
        <section id="use-cases" className="py-24 px-6 bg-white/[0.02]">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-14">
              <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-3">Use Cases</p>
              <h2 className="text-4xl md:text-5xl font-extrabold leading-tight">
                One AI receptionist for law firms,<br />legal aid, and corporate teams
              </h2>
              <p className="mt-4 text-neutral-400 max-w-xl mx-auto">Avatario adapts to your practice — answers calls, qualifies matters, books consultations and updates your CRM. Same AI, your tone, your hours, your workflows.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {USE_CASES.map(uc => (
                <div key={uc.title} className="p-6 rounded-2xl border border-white/8 bg-[#0f1420] hover:border-blue-500/30 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center mb-4">
                    <uc.icon className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="text-white font-semibold mb-2">{uc.title}</h3>
                  <p className="text-neutral-400 text-sm leading-relaxed">{uc.desc}</p>
                </div>
              ))}
            </div>
            <p className="text-center text-neutral-500 text-sm mt-8 italic">...and any practice with a phone — arbitration, IP, family law, tax, notary and more.</p>
          </div>
        </section>

        {/* ── EVERY CALL ── */}
        <section className="py-24 px-6">
          <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-16 items-center">
            <div>
              <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-4">Every Call</p>
              <h2 className="text-4xl font-extrabold leading-tight mb-5">Calls that finish,<br />not just answer</h2>
              <p className="text-neutral-400 leading-relaxed mb-8">Avatario completes the workflow while still on the line — checks your records, searches the knowledge base, books the slot and updates the ticket. No &quot;let me put you on hold.&quot;</p>
              <div className="space-y-2">
                {[
                  ["Incoming call", "Pre-call context"],
                  ["Intent recognition", "Knowledge base"],
                  ["Tools & APIs", "Smart actions"],
                  ["Escalation rules", "Live transfer / SMS"],
                ].map(([l, r], i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className="flex-1 px-4 py-2.5 rounded-xl border border-white/10 bg-white/3 text-sm text-neutral-300 text-center">{l}</div>
                    <ArrowRight className="w-4 h-4 text-blue-400 shrink-0" />
                    <div className="flex-1 px-4 py-2.5 rounded-xl border border-blue-500/30 bg-blue-500/10 text-sm text-blue-300 text-center">{r}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {[
                { val: "<500ms", label: "Voice response latency" },
                { val: "10+",    label: "Indian languages" },
                { val: "24 / 7", label: "Always available" },
                { val: "100%",   label: "Call coverage, no misses" },
              ].map(s => (
                <div key={s.label} className="p-7 rounded-2xl border border-white/8 bg-white/2 text-center">
                  <div className="text-3xl font-extrabold text-blue-400 mb-1">{s.val}</div>
                  <div className="text-neutral-400 text-sm">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CHANNELS ── */}
        <section className="py-24 px-6 bg-white/[0.02]">
          <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-16 items-center">
            {/* Visual flow */}
            <div className="p-6 rounded-2xl border border-white/8 bg-[#0f1420] space-y-3">
              {["Phone / WhatsApp", "Web widget", "Mobile app", "REST / API"].map(ch => (
                <div key={ch} className="flex items-center gap-3">
                  <div className="flex-1 px-4 py-3 rounded-xl border border-white/10 bg-white/4 text-sm text-neutral-300 text-center">{ch}</div>
                  <ArrowRight className="w-4 h-4 text-blue-400 shrink-0" />
                  <div className="flex-1 px-4 py-3 rounded-xl border border-blue-500/30 bg-blue-600 text-sm text-white text-center font-medium">Avatario agent</div>
                </div>
              ))}
            </div>
            <div>
              <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-4">Channels</p>
              <h2 className="text-4xl font-extrabold leading-tight mb-5">One agent. Every channel<br />your clients use.</h2>
              <p className="text-neutral-400 leading-relaxed mb-6">Plug into the channels you already pay for. Bring your phone number, your WhatsApp account, or just embed our web widget — and the same agent handles them all.</p>
              <ul className="space-y-2.5">
                {[
                  "Phone — bring your own number, SIP trunking included",
                  "WhatsApp Business API — text, voice notes and live calls",
                  "Web chat & voice widget for your site",
                  "REST API and webhooks for custom channels",
                  "Unified dashboard across every channel",
                ].map(f => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-neutral-300">
                    <CheckCircle className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* ── PLATFORM ── */}
        <section id="platform" className="py-24 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-14">
              <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-3">Platform</p>
              <h2 className="text-4xl md:text-5xl font-extrabold">Production-ready voice AI</h2>
              <p className="mt-4 text-neutral-400 max-w-xl mx-auto">Build intelligent agents that handle complex workflows, integrate with your stack and scale from prototype to thousands of calls a day.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {PLATFORM_STEPS.map(s => (
                <div key={s.n} className="p-6 rounded-2xl border border-white/8 bg-[#0f1420] hover:border-blue-500/25 transition-all">
                  <div className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 text-xs font-bold mb-4">{s.n}</div>
                  <h3 className="text-white font-semibold mb-2">{s.title}</h3>
                  <p className="text-neutral-400 text-sm leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── PRICING ── */}
        <section id="pricing" className="py-24 px-6">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-14">
              <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-3">Pricing</p>
              <h2 className="text-4xl font-extrabold">Simple, transparent pricing</h2>
              <p className="mt-4 text-neutral-400">Start free. Scale as your practice grows.</p>
            </div>
            <div className="grid md:grid-cols-3 gap-5">
              {PRICING.map(plan => (
                <div key={plan.name} className={`relative p-8 rounded-2xl border transition-all ${plan.highlight ? "border-blue-500/50 bg-gradient-to-b from-blue-600/10 to-transparent shadow-xl shadow-blue-500/10" : "border-white/10 bg-white/2 hover:border-white/20"}`}>
                  {plan.highlight && <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-blue-600 text-white text-xs font-bold">Most popular</div>}
                  <h3 className="text-base font-semibold text-white mb-1">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-4xl font-extrabold text-white">{plan.price}</span>
                    <span className="text-neutral-400 text-sm">{plan.period}</span>
                  </div>
                  <p className="text-neutral-400 text-sm mb-6">{plan.desc}</p>
                  <ul className="space-y-2.5 mb-7">
                    {plan.features.map(f => (
                      <li key={f} className="flex items-center gap-2 text-sm text-neutral-300">
                        <CheckCircle className="w-4 h-4 text-blue-400 shrink-0" />{f}
                      </li>
                    ))}
                  </ul>
                  <Link href="/assistant" className={`block text-center py-3 rounded-xl font-semibold text-sm transition-all ${plan.highlight ? "bg-blue-600 hover:bg-blue-500 text-white" : "border border-white/15 hover:border-white/35 text-white"}`}>
                    {plan.cta}
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── FAQ ── */}
        <section id="faq" className="py-24 px-6 bg-white/[0.02]">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-12">
              <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-3">FAQ</p>
              <h2 className="text-4xl font-extrabold">Common questions</h2>
            </div>
            <div className="space-y-2">
              {FAQS.map(faq => <FAQItem key={faq.q} q={faq.q} a={faq.a} />)}
            </div>
          </div>
        </section>

        {/* ── CONTACT ── */}
        <section id="contact" className="py-24 px-6">
          <div className="max-w-xl mx-auto">
            <div className="text-center mb-10">
              <p className="text-blue-400 text-xs font-bold uppercase tracking-widest mb-3">Contact</p>
              <h2 className="text-4xl font-extrabold">Talk to the team</h2>
              <p className="mt-3 text-neutral-400">Tell us about your practice and what you’d like the agent to do. We usually reply within one business day.</p>
            </div>
            <div className="p-8 rounded-2xl border border-white/10 bg-[#0f1420] space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-neutral-400 text-xs mb-1.5 block">Name</label>
                  <input type="text" placeholder="Your name" className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-neutral-600 focus:outline-none focus:border-blue-500/50" />
                </div>
                <div>
                  <label className="text-neutral-400 text-xs mb-1.5 block">Email</label>
                  <input type="email" placeholder="you@firm.com" className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-neutral-600 focus:outline-none focus:border-blue-500/50" />
                </div>
              </div>
              <div>
                <label className="text-neutral-400 text-xs mb-1.5 block">Practice type</label>
                <input type="text" placeholder="e.g. Criminal law firm, 10 lawyers" className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-neutral-600 focus:outline-none focus:border-blue-500/50" />
              </div>
              <div>
                <label className="text-neutral-400 text-xs mb-1.5 block">What should the agent do?</label>
                <textarea rows={3} placeholder="e.g. Answer inbound calls, qualify bail matters, book consultations..." className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-neutral-600 focus:outline-none focus:border-blue-500/50 resize-none" />
              </div>
              <button className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-colors">
                Send message
              </button>
            </div>
          </div>
        </section>

        {/* ── FOOTER ── */}
        <footer className="border-t border-white/6 py-10 px-6">
          <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
                <Scale className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-bold text-white">Avatario</span>
            </div>
            <p className="text-neutral-500 text-sm">AI Legal Assistant — Not a substitute for professional legal advice.</p>
            <div className="flex items-center gap-6 text-neutral-500 text-sm">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="mailto:hello@avatario.ai" className="hover:text-white transition-colors">Contact</a>
            </div>
          </div>
        </footer>
      </section>
    </div>
  );
}
