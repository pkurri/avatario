// frontend-web/src/app/page.tsx
// "Chambers" redesign — warm ink + ivory, editorial serif, brass accent.
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  AudioLines,
  Mic,
  Brain,
  Zap,
  MessageSquare,
  Globe,
  Code2,
  Scale,
  Stethoscope,
  Landmark,
  GraduationCap,
  Building2,
  Headphones,
  Phone,
  MessageCircle,
  ArrowRight,
  Check,
  Plus,
} from "lucide-react";

// ── DATA ──────────────────────────────────────────────────────────────────────

const NAV_LINKS = [
  { label: "Capabilities", href: "#capabilities" },
  { label: "Use cases",    href: "#use-cases" },
  { label: "Platform",     href: "#platform" },
  { label: "ROI",          href: "#roi" },
  { label: "Pricing",      href: "#pricing" },
  { label: "FAQ",          href: "#faq" },
];

const DEMO_THREAD = [
  { from: "client", text: "Hi, I'd like to book an appointment for this week.", time: "0:02", act: null },
  { from: "ai",     text: "Of course. May I take your name and what it's regarding?", time: "0:04", act: "checking availability" },
  { from: "client", text: "It's Priya — a first consultation, sometime Thursday if possible.", time: "0:09", act: null },
  { from: "ai",     text: "Thanks, Priya. Thursday 4 PM is open — I've booked it and sent you a confirmation.", time: "0:13", act: "appointment booked · SMS sent" },
];

const CAPABILITIES = [
  { icon: Mic,           title: "Natural conversations",      desc: "Sub-second latency, human-like turn-taking, and graceful interruption handling — even on poor connections." },
  { icon: Brain,         title: "Tool-aware memory",          desc: "Remembers past conversations, client history and context so every session picks up where the last one left off." },
  { icon: Zap,           title: "Workflow automation",        desc: "Pre-call enrichment, in-call and post-call actions — defined visually, no developer required." },
  { icon: MessageSquare, title: "Intelligent routing",        desc: "Queue management, voicemail logic and live transfers when a real human is the right answer." },
  { icon: Globe,         title: "Multi-channel deployment",   desc: "One agent, every channel — phone, web widget and direct API. Same brain, same actions." },
  { icon: Code2,         title: "Full API, no code required", desc: "Visual editor for operators. REST API, webhooks and MCP for engineers. Use both, switch any time." },
];

const USE_CASES = [
  { icon: Scale,         title: "Legal",         desc: "Client intake, matter updates and appointment booking — handled before anyone picks up." },
  { icon: Stethoscope,   title: "Healthcare",    desc: "Appointment scheduling, triage and reminders for clinics, hospitals and diagnostics." },
  { icon: Landmark,      title: "Finance",       desc: "KYC, loan and account queries — answered and logged, with a clean handoff for anything sensitive." },
  { icon: GraduationCap, title: "Education",     desc: "Admissions, fee questions and parent updates — answered in the family's own language." },
  { icon: Building2,     title: "Real estate",   desc: "Qualify buyers, book site visits and follow up on every enquiry, day or night." },
  { icon: Headphones,    title: "Support desks", desc: "Triage inbound queries at scale. Handle 100 simultaneous calls without hold music." },
];

const PRICING = [
  {
    name: "Starter",      price: "₹4,999",  per: "/mo",
    desc: "Solo operators and small teams.",
    features: ["1 AI voice persona", "Up to 500 calls / month", "English + 1 regional language", "Basic analytics", "Email support"],
    cta: "Get started",    hi: false,
  },
  {
    name: "Professional", price: "₹14,999", per: "/mo",
    desc: "Growing teams that need more personas and integrations.",
    features: ["5 AI voice personas", "Up to 2,000 calls / month", "All supported languages", "CRM & calendar integrations", "Advanced analytics", "Priority support"],
    cta: "Start free trial", hi: true,
  },
  {
    name: "Enterprise",   price: "Custom",  per: "",
    desc: "Complete access with dedicated support and custom SLAs.",
    features: ["Unlimited personas", "Unlimited calls", "Custom integrations & API", "On-premise deployment option", "Dedicated success manager", "SLA guarantee"],
    cta: "Contact us",    hi: false,
  },
];

const FAQS = [
  { id: "chatbot",   q: "How is this different from a chatbot?",  a: "Avatario speaks and listens in real time over voice — not a chat widget. It holds multi-turn conversations, understands context, and takes actions like booking appointments or sending documents." },
  { id: "safe",      q: "Is client data safe?",                   a: "Yes. All data is encrypted in transit and at rest. We never use your conversations to train models. You control retention and can delete data at any time." },
  { id: "languages", q: "Which languages are supported?",         a: "English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, and Punjabi — with more being added continuously." },
  { id: "transfer",  q: "Can it transfer to a human?",            a: "Yes. You define escalation rules — e.g. 'transfer if the caller mentions an emergency or asks for a manager'. The AI hands off gracefully and briefs your team in real time." },
  { id: "workflows", q: "Can I build advanced workflows?",        a: "Yes. The visual workflow editor lets you define pre-call enrichment, in-call actions, and post-call follow-ups without writing code. REST API and webhooks available for engineers." },
  { id: "setup",     q: "How long does setup take?",              a: "Most teams are live within 48 hours. You provide your services, FAQs, and team availability — we handle the rest." },
];

// ── CSS VARS SHORTHAND ────────────────────────────────────────────────────────
const V = {
  ink:          "var(--ink)",
  inkSoft:      "var(--ink-soft)",
  panel:        "var(--panel)",
  panel2:       "var(--panel-2)",
  ivory:        "var(--ivory)",
  ivoryDim:     "var(--ivory-dim)",
  muted:        "var(--muted)",
  muted2:       "var(--muted-2)",
  line:         "var(--line)",
  lineFaint:    "var(--line-faint)",
  lineStrong:   "var(--line-strong)",
  accent:       "var(--accent)",
  accentBright: "var(--accent-bright)",
  accentTint:   "var(--accent-tint)",
  accentLine:   "var(--accent-line)",
  blue:         "var(--blue)",
  blueBright:   "var(--blue-bright)",
  emerald:      "var(--emerald)",
  displayFont:  "var(--font-display)",
  monoFont:     "var(--font-mono)",
  sansFont:     "var(--font-sans)",
};

// ── HELPERS ───────────────────────────────────────────────────────────────────

/** Fade-up reveal on scroll */
function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.7, delay, ease: [0.2, 0.7, 0.2, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/** Max-width content wrapper */
function Wrap({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div
      style={{
        width: "100%",
        maxWidth: 1180,
        marginInline: "auto",
        paddingInline: "clamp(20px, 5vw, 56px)",
        position: "relative",
        zIndex: 1,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

/** Section eyebrow with leading hairline */
function Eyebrow({ secNo, label }: { secNo?: string; label: string }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 10,
        fontFamily: V.monoFont,
        fontSize: 11,
        letterSpacing: "0.26em",
        textTransform: "uppercase",
        color: V.muted,
      }}
    >
      <span style={{ width: 22, height: 1, background: V.accentLine, display: "inline-block", flexShrink: 0 }} />
      {secNo && <span style={{ color: V.accent, fontWeight: 500 }}>{secNo}</span>}
      {label}
    </span>
  );
}

/** Display heading with shared typographic style */
function Display({ children, size = "section" }: { children: React.ReactNode; size?: "hero" | "section" | "cta" }) {
  const fontSize =
    size === "hero"    ? "clamp(40px, 6.4vw, 76px)" :
    size === "cta"     ? "clamp(30px, 4.5vw, 52px)" :
    /* section */        "clamp(30px, 4vw, 47px)";
  return (
    <h2
      style={{
        margin: "18px 0 0",
        fontFamily: V.displayFont,
        fontWeight: 500,
        letterSpacing: "-0.015em",
        lineHeight: 1.04,
        color: V.ivory,
        fontSize,
        fontOpticalSizing: "auto" as React.CSSProperties["fontOpticalSizing"],
      }}
    >
      {children}
    </h2>
  );
}

/** Italic accent span */
function It({ children }: { children: React.ReactNode }) {
  return <em style={{ fontStyle: "italic", fontWeight: 500, color: V.accentBright }}>{children}</em>;
}

/** Subhead / lede */
function Lede({ children, center }: { children: React.ReactNode; center?: boolean }) {
  return (
    <p
      style={{
        marginTop: 18,
        color: V.ivoryDim,
        fontSize: "clamp(16px, 1.4vw, 19px)",
        lineHeight: 1.65,
        maxWidth: center ? undefined : "56ch",
        textAlign: center ? "center" : undefined,
        marginInline: center ? "auto" : undefined,
      }}
    >
      {children}
    </p>
  );
}

/** Waveform bars */
function Waveform() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 3, height: 26, flex: 1 }}>
      {Array.from({ length: 28 }, (_, i) => {
        const h = 5 + (i % 5) * 4 + Math.round(Math.abs(Math.sin(i)) * 3 + 3);
        return (
          <span
            key={i}
            className="av-wave-bar"
            style={{
              ["--wv-h" as string]: `${h}px`,
              animationDelay: `${i * 45}ms`,
              animationDuration: `${700 + (i % 4) * 120}ms`,
            }}
          />
        );
      })}
    </div>
  );
}

/** Pulsing status dot */
function Dot({ size = 7 }: { size?: number }) {
  return <span className="av-dot" style={{ width: size, height: size }} />;
}

/** FAQ accordion item */
function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      style={{ borderBottom: `1px solid ${V.line}`, cursor: "pointer" }}
      onClick={() => setOpen(!open)}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 20,
          padding: "24px 4px",
          fontSize: 17,
          fontWeight: 500,
          color: V.ivory,
        }}
      >
        <span>{q}</span>
        <span
          style={{
            color: V.accent,
            flexShrink: 0,
            transition: "transform 0.25s",
            display: "inline-flex",
            transform: open ? "rotate(45deg)" : "none",
          }}
        >
          <Plus className="w-5 h-5" />
        </span>
      </div>
      <div className={`av-faq-answer${open ? " open" : ""}`}>
        <div style={{ padding: "0 48px 26px 4px", color: V.muted, fontSize: 15, lineHeight: 1.7 }}>
          {a}
        </div>
      </div>
    </div>
  );
}

/** Primary action button */
function BtnAccent({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 9,
        fontSize: 14,
        fontWeight: 600,
        padding: "13px 22px",
        borderRadius: 11,
        background: V.accent,
        color: "#15130f",
        border: "1px solid transparent",
        boxShadow: `0 10px 30px -12px color-mix(in srgb, ${V.accent} 70%, transparent)`,
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </a>
  );
}

/** Ghost / outline button */
function BtnGhost({ href, children, as: Tag = "a" }: { href: string; children: React.ReactNode; as?: "a" | typeof Link }) {
  const style: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: 9,
    fontSize: 14,
    fontWeight: 500,
    padding: "13px 22px",
    borderRadius: 11,
    border: `1px solid ${V.lineStrong}`,
    color: V.ivory,
    background: "transparent",
    whiteSpace: "nowrap",
  };
  if (Tag === Link) return <Link href={href} style={style}>{children}</Link>;
  return <a href={href} style={style}>{children}</a>;
}

// ── PAGE ──────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  // Nav scroll shadow
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 12);
    fn();
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);

  // ROI state
  const [calls,  setCalls]  = useState(800);
  const [missed, setMissed] = useState(22);
  const [mval,   setMval]   = useState(3500);
  const [conv,   setConv]   = useState(18);
  const recovered = Math.round(calls * (missed / 100) * 0.75);
  const matters   = Math.max(1, Math.round(recovered * (conv / 100)));
  const revenue   = matters * mval;
  const plan      = calls > 2000 ? "Enterprise" : calls > 500 ? "Professional" : "Starter";
  const fmt       = (n: number) => "₹ " + n.toLocaleString("en-IN");

  return (
    <main
      style={{
        minHeight: "100vh",
        background: V.ink,
        color: V.ivory,
        fontFamily: V.sansFont,
        overflowX: "hidden",
        position: "relative",
      }}
    >
      {/* page radial glow */}
      <div className="av-page-glow" />

      {/* ══════════════════════════════════════════════════ NAV */}
      <nav
        style={{
          position: "fixed",
          inset: "0 0 auto 0",
          zIndex: 50,
          height: 66,
          display: "flex",
          alignItems: "center",
          transition: "background 0.3s, border-color 0.3s, backdrop-filter 0.3s",
          borderBottom: `1px solid ${scrolled ? V.line : "transparent"}`,
          background: scrolled ? `color-mix(in srgb, ${V.ink} 78%, transparent)` : "transparent",
          backdropFilter: scrolled ? "blur(16px) saturate(150%)" : "none",
          WebkitBackdropFilter: scrolled ? "blur(16px) saturate(150%)" : "none",
        }}
      >
        <Wrap style={{ display: "flex", alignItems: "center", gap: 28 }}>
          {/* brand */}
          <a href="#top" style={{ display: "inline-flex", alignItems: "center", gap: 11 }}>
            <span
              style={{
                width: 30,
                height: 30,
                borderRadius: 9,
                display: "grid",
                placeItems: "center",
                color: V.accentBright,
                border: `1px solid ${V.accentLine}`,
                background: `linear-gradient(160deg, color-mix(in srgb, ${V.accent} 20%, transparent), transparent 70%)`,
              }}
            >
              <AudioLines className="w-[17px] h-[17px]" />
            </span>
            <span style={{ fontFamily: V.displayFont, fontSize: 21, fontWeight: 600, letterSpacing: "-0.01em", color: V.ivory }}>
              Avatario
            </span>
          </a>

          {/* links (hidden on mobile) */}
          <div className="hidden md:flex" style={{ alignItems: "center", gap: 26, marginLeft: "auto" }}>
            {NAV_LINKS.map((l) => (
              <a key={l.label} href={l.href} style={{ fontSize: 13.5, color: V.muted, transition: "color 0.16s" }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = V.ivory; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = V.muted; }}>
                {l.label}
              </a>
            ))}
          </div>

          {/* nav CTA */}
          <a
            href="#contact"
            style={{
              marginLeft: 4,
              display: "inline-flex",
              alignItems: "center",
              fontSize: 14,
              fontWeight: 500,
              padding: "11px 20px",
              borderRadius: 11,
              border: `1px solid ${V.lineStrong}`,
              color: V.ivory,
              background: "transparent",
              transition: "border-color 0.18s",
              whiteSpace: "nowrap",
            }}
          >
            Book a call
          </a>
        </Wrap>
      </nav>

      {/* ══════════════════════════════════════════════════ HERO */}
      <header id="top" style={{ paddingTop: 132, paddingBottom: 88 }}>
        <Wrap
          style={{
            display: "grid",
            gridTemplateColumns: "1.05fr 0.95fr",
            gap: "clamp(32px, 5vw, 72px)",
            alignItems: "center",
          }}
        >
          {/* copy */}
          <motion.div
            initial={{ opacity: 0, y: 22 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.2, 0.7, 0.2, 1] }}
          >
            {/* chip */}
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 9,
                fontFamily: V.monoFont,
                fontSize: 11.5,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                color: V.ivoryDim,
                padding: "7px 14px 7px 11px",
                border: `1px solid ${V.line}`,
                borderRadius: 999,
                background: V.panel,
                whiteSpace: "nowrap",
              }}
            >
              <Dot /> Live now — answering in 10 Indian languages
            </span>

            {/* h1 */}
            <h1
              style={{
                margin: "26px 0 0",
                fontFamily: V.displayFont,
                fontWeight: 500,
                letterSpacing: "-0.015em",
                lineHeight: 1.04,
                color: V.ivory,
                fontSize: "clamp(40px, 6.4vw, 76px)",
                fontOpticalSizing: "auto" as React.CSSProperties["fontOpticalSizing"],
              }}
            >
              The AI receptionist that
              <br />
              <It>answers your client calls.</It>
            </h1>

            <Lede>
              Avatario receives and answers client calls and messages 24/7 —
              booking appointments, qualifying enquiries, taking messages,
              routing urgent cases and following up. A complete AI assistant for
              any team, in English and 9 Indian languages.
            </Lede>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 34, alignItems: "center" }}>
              <BtnAccent href="#contact">Get started <ArrowRight className="w-4 h-4" /></BtnAccent>
              <BtnGhost href="#platform">Watch a 90-second tour</BtnGhost>
            </div>
            <p style={{ marginTop: 18, fontFamily: V.monoFont, fontSize: 11.5, letterSpacing: "0.04em", color: V.muted2 }}>
              Free, no signup. Mic permission required for browser call.
            </p>
          </motion.div>

          {/* console widget */}
          <motion.div
            initial={{ opacity: 0, y: 22 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15, ease: [0.2, 0.7, 0.2, 1] }}
            style={{
              background: `linear-gradient(180deg, ${V.panel} 0%, ${V.inkSoft} 100%)`,
              border: `1px solid ${V.line}`,
              borderRadius: 18,
              boxShadow: "0 1px 0 rgba(255,255,255,0.03) inset, 0 40px 80px -40px rgba(0,0,0,0.8)",
              overflow: "hidden",
            }}
          >
            {/* top bar */}
            <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "13px 16px", borderBottom: `1px solid ${V.line}`, background: "rgba(0,0,0,0.18)" }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 9, fontSize: 12.5, color: V.ivoryDim }}>
                <Dot /> Talking to Anya — AI Receptionist
              </span>
              <span style={{ marginLeft: "auto", fontFamily: V.monoFont, fontSize: 11, color: V.blueBright, display: "inline-flex", alignItems: "center", gap: 6 }}>
                <Zap className="w-3 h-3" /> &lt;500ms
              </span>
            </div>

            {/* avatar stage */}
            <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "20px 18px", borderBottom: `1px solid ${V.lineFaint}` }}>
              <div style={{ position: "relative", width: 56, height: 56, borderRadius: "50%", display: "grid", placeItems: "center", fontFamily: V.displayFont, fontSize: 24, fontWeight: 600, color: "#15130f", background: `linear-gradient(150deg, ${V.accentBright}, ${V.accent})`, flexShrink: 0, boxShadow: "0 0 0 4px rgba(243,239,230,0.06)" }}>
                A
                <span className="av-avatar-ring" />
              </div>
              <div>
                <div style={{ fontSize: 14, color: V.ivory, fontWeight: 500 }}>Anya</div>
                <div style={{ fontSize: 12.5, color: V.muted, marginTop: 2 }}>Front-desk intake · Connected</div>
              </div>
            </div>

            {/* thread */}
            <div
              className="av-thread-mask"
              style={{ padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12, maxHeight: 268, overflow: "hidden" }}
            >
              {DEMO_THREAD.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 + i * 0.35, duration: 0.4 }}
                  style={{ maxWidth: "84%", alignSelf: msg.from === "ai" ? "flex-start" : "flex-end" }}
                >
                  <div
                    style={{
                      fontSize: 13.5,
                      lineHeight: 1.5,
                      padding: "11px 14px",
                      borderRadius: msg.from === "ai" ? "13px 13px 13px 5px" : "13px 13px 5px 13px",
                      background: msg.from === "ai"
                        ? V.panel2
                        : `color-mix(in srgb, ${V.blue} 16%, ${V.panel2})`,
                      border: `1px solid ${msg.from === "ai" ? V.line : `color-mix(in srgb, ${V.blue} 30%, transparent)`}`,
                      color: msg.from === "ai" ? V.ivoryDim : V.ivory,
                    }}
                  >
                    {msg.text}
                  </div>
                  <div style={{ display: "flex", gap: 9, alignItems: "center", marginTop: 7, fontFamily: V.monoFont, fontSize: 10, color: V.muted2 }}>
                    <span>{msg.time}</span>
                    {msg.act && <span style={{ color: V.accent }}>· {msg.act}</span>}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* footer */}
            <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 18px", borderTop: `1px solid ${V.line}`, background: "rgba(0,0,0,0.18)" }}>
              <button
                aria-label="Microphone"
                style={{ width: 40, height: 40, borderRadius: "50%", display: "grid", placeItems: "center", background: V.accent, color: "#15130f", border: "none", flexShrink: 0, cursor: "pointer" }}
              >
                <Mic className="w-[17px] h-[17px]" />
              </button>
              <Waveform />
              <span style={{ fontFamily: V.monoFont, fontSize: 11, display: "inline-flex", alignItems: "center", gap: 6, color: V.muted2 }}>
                <Dot size={5} /> Recording
              </span>
            </div>
          </motion.div>

          {/* mobile: stack columns */}
          <style>{`@media(max-width:860px){header .wrap-hero{grid-template-columns:1fr!important}}`}</style>
        </Wrap>
      </header>

      {/* ══════════════════════════════════════════════════ TRUST */}
      <section style={{ borderTop: `1px solid ${V.lineFaint}`, borderBottom: `1px solid ${V.lineFaint}`, padding: "26px 0", position: "relative", zIndex: 1 }}>
        <Wrap style={{ display: "flex", alignItems: "center", gap: "clamp(20px, 4vw, 52px)", flexWrap: "wrap", justifyContent: "center" }}>
          <span style={{ fontFamily: V.monoFont, fontSize: 11, letterSpacing: "0.18em", textTransform: "uppercase", color: V.muted2, marginRight: "auto" }}>
            Trusted by practices across India
          </span>
          {["Lexcorp", "Justice Hub", "Vakil Desk", "Lawbridge", "Lexica", "Courtside"].map((b) => (
            <span key={b} style={{ fontFamily: V.displayFont, fontWeight: 600, fontSize: 16, letterSpacing: "0.02em", color: V.muted }}>
              {b}
            </span>
          ))}
        </Wrap>
      </section>

      {/* ══════════════════════════════════════════════════ §01 CAPABILITIES */}
      <section id="capabilities" style={{ padding: "clamp(72px, 9vw, 116px) 0", position: "relative", zIndex: 1 }}>
        <Wrap>
          <Reveal className="mb-[52px] max-w-[720px]">
            <Eyebrow secNo="§ 01" label="Core capabilities" />
            <Display>
              Everything your team needs to <It>handle calls at scale.</It>
            </Display>
            <Lede>A complete AI assistant that picks up, qualifies, schedules and follows up — so your people focus on the work that needs them.</Lede>
          </Reveal>

          <div style={{ borderTop: `1px solid ${V.line}` }}>
            {CAPABILITIES.map((cap, i) => (
              <Reveal key={cap.title} delay={i * 0.05}>
                <div
                  className="av-feat-row"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "64px 1fr 1.3fr",
                    gap: 24,
                    alignItems: "start",
                    padding: "30px 8px",
                    borderBottom: `1px solid ${V.line}`,
                    transition: "background 0.2s",
                  }}
                >
                  <div style={{ fontFamily: V.monoFont, fontSize: 12, color: V.accent, paddingTop: 4 }}>
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 13, fontSize: 19, fontWeight: 500, color: V.ivory }}>
                    <span
                      style={{
                        width: 34,
                        height: 34,
                        borderRadius: 9,
                        display: "grid",
                        placeItems: "center",
                        border: `1px solid ${V.line}`,
                        color: V.accentBright,
                        background: V.accentTint,
                        flexShrink: 0,
                      }}
                    >
                      <cap.icon className="w-[17px] h-[17px]" />
                    </span>
                    {cap.title}
                  </div>
                  <p style={{ margin: 0, color: V.muted, fontSize: 15, lineHeight: 1.6 }}>{cap.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </Wrap>
        <style>{`
          .av-feat-row:hover{background:rgba(243,239,230,0.02)}
          @media(max-width:720px){.av-feat-row{grid-template-columns:1fr!important;gap:10px!important}}
        `}</style>
      </section>

      {/* ══════════════════════════════════════════════════ §02 USE CASES */}
      <section
        id="use-cases"
        style={{
          padding: "clamp(72px, 9vw, 116px) 0",
          background: "rgba(243,239,230,0.015)",
          borderBlock: `1px solid ${V.lineFaint}`,
          position: "relative",
          zIndex: 1,
        }}
      >
        <Wrap>
          <Reveal className="mb-[52px] max-w-[720px]">
            <Eyebrow secNo="§ 02" label="Industries served" />
            <Display>
              Built for the way Indian businesses <It>actually work.</It>
            </Display>
            <Lede>One platform, every industry — legal, healthcare, finance, education and more. Same engine, a persona tuned to your sector.</Lede>
          </Reveal>

          <Reveal>
            <div
              className="av-case-grid"
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: 1,
                background: V.line,
                border: `1px solid ${V.line}`,
                borderRadius: 16,
                overflow: "hidden",
              }}
            >
              {USE_CASES.map((uc) => (
                <div
                  key={uc.title}
                  className="av-case-card"
                  style={{ background: V.ink, padding: "28px 26px", transition: "background 0.2s" }}
                >
                  <div style={{ width: 38, height: 38, borderRadius: 10, display: "grid", placeItems: "center", color: V.accentBright, border: `1px solid ${V.line}`, marginBottom: 18 }}>
                    <uc.icon className="w-[18px] h-[18px]" />
                  </div>
                  <h3 style={{ margin: "0 0 8px", fontSize: 17, fontWeight: 600, color: V.ivory }}>{uc.title}</h3>
                  <p style={{ margin: 0, fontSize: 14, color: V.muted, lineHeight: 1.6 }}>{uc.desc}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </Wrap>
        <style>{`
          .av-case-card:hover{background:var(--panel)!important}
          @media(max-width:720px){.av-case-grid{grid-template-columns:1fr!important}}
          @media(max-width:960px) and (min-width:721px){.av-case-grid{grid-template-columns:repeat(2,1fr)!important}}
        `}</style>
      </section>

      {/* ══════════════════════════════════════════════════ §03 PLATFORM */}
      <section id="platform" style={{ padding: "clamp(72px, 9vw, 116px) 0", position: "relative", zIndex: 1 }}>
        <Wrap>
          <Reveal className="mb-[52px] max-w-[720px]">
            <Eyebrow secNo="§ 03" label="Platform" />
            <Display>
              Plug into the channels you <It>already pay for.</It>
            </Display>
            <Lede>Bring your phone, your WhatsApp, or just embed our web widget. One agent, every channel — same brain, same actions.</Lede>
          </Reveal>

          <Reveal>
            <div
              className="av-channels"
              style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 22 }}
            >
              {[
                { icon: Phone,         title: "Phone",             desc: "Point your number over SIP, Exotel or Twilio. Avatario answers on the first ring, 24/7." },
                { icon: MessageCircle, title: "WhatsApp Business", desc: "Voice notes and text, handled in the same conversation memory as the phone line." },
                { icon: Code2,         title: "Web widget & API",  desc: "Embed a live voice widget in one line, or drive everything over REST, webhooks and MCP." },
              ].map((ch) => (
                <div
                  key={ch.title}
                  style={{ border: `1px solid ${V.line}`, borderRadius: 14, padding: 24, background: V.panel }}
                >
                  <div style={{ color: V.accentBright, marginBottom: 16 }}><ch.icon className="w-[22px] h-[22px]" /></div>
                  <h4 style={{ margin: "0 0 6px", fontSize: 16, fontWeight: 600, color: V.ivory }}>{ch.title}</h4>
                  <p style={{ margin: 0, fontSize: 13.5, color: V.muted }}>{ch.desc}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </Wrap>
        <style>{`@media(max-width:720px){.av-channels{grid-template-columns:1fr!important}}`}</style>
      </section>

      {/* ══════════════════════════════════════════════════ §04 ROI */}
      <section
        id="roi"
        style={{
          padding: "clamp(72px, 9vw, 116px) 0",
          background: "rgba(243,239,230,0.015)",
          borderBlock: `1px solid ${V.lineFaint}`,
          position: "relative",
          zIndex: 1,
        }}
      >
        <Wrap>
          <Reveal className="mb-[52px] max-w-[720px]">
            <Eyebrow secNo="§ 04" label="Calculate your ROI" />
            <Display>
              See the matters <It>you&rsquo;re missing.</It>
            </Display>
            <Lede>Most firms recover 60–80% of missed calls with Avatario. Drop in your numbers below.</Lede>
          </Reveal>

          <Reveal>
            <div className="av-roi" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, alignItems: "stretch" }}>
              {/* inputs */}
              <div style={{ border: `1px solid ${V.line}`, borderRadius: 18, padding: 30, background: V.panel }}>
                <h3 style={{ fontFamily: V.monoFont, fontSize: 11, letterSpacing: "0.2em", textTransform: "uppercase", color: V.muted, margin: "0 0 24px" }}>
                  Your firm
                </h3>
                {([
                  { label: "Monthly call volume",  val: calls,  set: setCalls,  min: 100,  max: 5000,  step: 50,  display: String(calls) },
                  { label: "Missed-call rate",     val: missed, set: setMissed, min: 5,    max: 50,    step: 1,   display: missed + "%" },
                  { label: "Average matter value", val: mval,   set: setMval,  min: 500,  max: 50000, step: 500, display: fmt(mval) },
                  { label: "Conversion rate",      val: conv,   set: setConv,   min: 2,    max: 60,    step: 1,   display: conv + "%" },
                ] as Array<{ label: string; val: number; set: (n: number) => void; min: number; max: number; step: number; display: string }>).map((c, i, arr) => (
                  <label key={c.label} className="block" style={{ marginBottom: i < arr.length - 1 ? 22 : 0 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10, fontSize: 14, color: V.ivoryDim }}>
                      <span>{c.label}</span>
                      <b style={{ fontFamily: V.monoFont, fontWeight: 500, color: V.ivory, fontSize: 14 }}>{c.display}</b>
                    </div>
                    <input
                      type="range"
                      className="av-range"
                      min={c.min}
                      max={c.max}
                      step={c.step}
                      value={c.val}
                      onChange={(e) => c.set(Number(e.target.value))}
                    />
                  </label>
                ))}
              </div>

              {/* outputs */}
              <div
                style={{
                  border: `1px solid ${V.accentLine}`,
                  borderRadius: 18,
                  padding: 30,
                  background: `linear-gradient(165deg, color-mix(in srgb, ${V.accent} 10%, ${V.panel}), ${V.inkSoft})`,
                }}
              >
                <h3 style={{ fontFamily: V.monoFont, fontSize: 11, letterSpacing: "0.2em", textTransform: "uppercase", color: V.accentBright, margin: "0 0 24px" }}>
                  Estimated recovery
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, margin: "14px 0 22px" }}>
                  {[
                    { n: recovered, l: "calls recovered" },
                    { n: matters,   l: "new matters / mo" },
                  ].map((t) => (
                    <div key={t.l} style={{ border: `1px solid ${V.line}`, borderRadius: 13, padding: 20, background: "rgba(0,0,0,0.2)" }}>
                      <div style={{ fontFamily: V.displayFont, fontSize: 38, fontWeight: 500, letterSpacing: "-0.02em", color: V.ivory, lineHeight: 1 }}>{t.n}</div>
                      <div style={{ fontSize: 12.5, color: V.muted, marginTop: 8 }}>{t.l}</div>
                    </div>
                  ))}
                  <div style={{ gridColumn: "1 / -1", border: `1px solid ${V.line}`, borderRadius: 13, padding: 20, background: "rgba(0,0,0,0.2)" }}>
                    <div style={{ fontFamily: V.displayFont, fontSize: 44, fontWeight: 500, letterSpacing: "-0.02em", color: V.accentBright, lineHeight: 1 }}>{fmt(revenue)}</div>
                    <div style={{ fontSize: 12.5, color: V.muted, marginTop: 8 }}>added revenue / month</div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderTop: `1px solid ${V.line}`, paddingTop: 18, fontSize: 13, color: V.muted }}>
                  <span>Recommended plan</span>
                  <span style={{ fontFamily: V.monoFont, fontSize: 11, letterSpacing: "0.08em", color: V.accentBright, border: `1px solid ${V.accentLine}`, borderRadius: 999, padding: "5px 12px" }}>{plan}</span>
                </div>
              </div>
            </div>
          </Reveal>
        </Wrap>
        <style>{`@media(max-width:720px){.av-roi{grid-template-columns:1fr!important}}`}</style>
      </section>

      {/* ══════════════════════════════════════════════════ §05 PRICING */}
      <section id="pricing" style={{ padding: "clamp(72px, 9vw, 116px) 0", position: "relative", zIndex: 1 }}>
        <Wrap>
          <Reveal className="mb-[52px] max-w-[720px] mx-auto text-center">
            <div style={{ display: "flex", justifyContent: "center" }}>
              <Eyebrow secNo="§ 05" label="Plans" />
            </div>
            <Display>
              Pricing that scales with your <It>call volume.</It>
            </Display>
            <Lede center>Start small, upgrade in a click. All plans include unlimited team seats and Indian-language support.</Lede>
          </Reveal>

          <Reveal>
            <div className="av-price-grid" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
              {PRICING.map((p) => (
                <div
                  key={p.name}
                  style={{
                    border: `1px solid ${p.hi ? V.accentLine : V.line}`,
                    borderRadius: 18,
                    padding: "32px 28px",
                    background: p.hi
                      ? `linear-gradient(180deg, color-mix(in srgb, ${V.accent} 8%, ${V.panel}), ${V.panel})`
                      : V.panel,
                    display: "flex",
                    flexDirection: "column",
                    position: "relative",
                    boxShadow: p.hi ? `0 30px 70px -40px color-mix(in srgb, ${V.accent} 50%, transparent)` : "none",
                  }}
                >
                  {p.hi && (
                    <span style={{ position: "absolute", top: -11, left: 28, fontFamily: V.monoFont, fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: "#15130f", background: V.accent, padding: "5px 11px", borderRadius: 999 }}>
                      Most popular
                    </span>
                  )}
                  <div style={{ fontFamily: V.displayFont, fontSize: 23, fontWeight: 600, color: V.ivory }}>{p.name}</div>
                  <div style={{ fontSize: 13.5, color: V.muted, margin: "6px 0 22px", minHeight: 38 }}>{p.desc}</div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginBottom: 24 }}>
                    <span style={{ fontFamily: V.displayFont, fontSize: 42, fontWeight: 500, letterSpacing: "-0.02em", color: V.ivory }}>{p.price}</span>
                    <span style={{ fontSize: 14, color: V.muted }}>{p.per}</span>
                  </div>
                  <ul style={{ listStyle: "none", margin: "0 0 26px", padding: 0, display: "flex", flexDirection: "column", gap: 12, flex: 1 }}>
                    {p.features.map((f) => (
                      <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 11, fontSize: 14, color: V.ivoryDim }}>
                        <Check className="w-4 h-4 shrink-0 mt-0.5" style={{ color: V.accentBright } as React.CSSProperties} />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <a
                    href="#contact"
                    style={{
                      display: "flex",
                      justifyContent: "center",
                      padding: "13px 22px",
                      borderRadius: 11,
                      fontSize: 14,
                      fontWeight: p.hi ? 600 : 500,
                      background: p.hi ? V.accent : "transparent",
                      color: p.hi ? "#15130f" : V.ivory,
                      border: `1px solid ${p.hi ? "transparent" : V.lineStrong}`,
                      transition: "filter 0.18s",
                    }}
                  >
                    {p.cta}
                  </a>
                </div>
              ))}
            </div>
          </Reveal>
        </Wrap>
        <style>{`@media(max-width:860px){.av-price-grid{grid-template-columns:1fr!important}}`}</style>
      </section>

      {/* ══════════════════════════════════════════════════ §06 FAQ */}
      <section
        id="faq"
        style={{
          padding: "clamp(72px, 9vw, 116px) 0",
          background: "rgba(243,239,230,0.015)",
          borderBlock: `1px solid ${V.lineFaint}`,
          position: "relative",
          zIndex: 1,
        }}
      >
        <Wrap>
          <Reveal className="mb-[52px] max-w-[720px] mx-auto text-center">
            <div style={{ display: "flex", justifyContent: "center" }}>
              <Eyebrow secNo="§ 06" label="Frequently asked" />
            </div>
            <Display>Common questions</Display>
          </Reveal>
          <div style={{ borderTop: `1px solid ${V.line}`, maxWidth: 820, marginInline: "auto" }}>
            {FAQS.map((f) => <FaqItem key={f.id} q={f.q} a={f.a} />)}
          </div>
        </Wrap>
      </section>

      {/* ══════════════════════════════════════════════════ CTA BAND */}
      <section id="contact" style={{ padding: "clamp(72px, 9vw, 116px) 0", textAlign: "center", position: "relative", zIndex: 1 }}>
        <Wrap>
          <Reveal>
            <div
              style={{
                border: `1px solid ${V.accentLine}`,
                borderRadius: 24,
                padding: "clamp(40px, 6vw, 76px)",
                background: `linear-gradient(165deg, color-mix(in srgb, ${V.accent} 12%, ${V.panel}), ${V.inkSoft})`,
                overflow: "hidden",
              }}
            >
              <h2
                style={{
                  margin: "0 auto",
                  fontFamily: V.displayFont,
                  fontWeight: 500,
                  letterSpacing: "-0.015em",
                  lineHeight: 1.04,
                  color: V.ivory,
                  fontSize: "clamp(30px, 4.5vw, 52px)",
                  maxWidth: "16ch",
                  fontOpticalSizing: "auto" as React.CSSProperties["fontOpticalSizing"],
                }}
              >
                Let your firm <It>never miss a client</It> again.
              </h2>
              <p style={{ margin: "22px auto 0", color: V.ivoryDim, fontSize: "clamp(16px, 1.4vw, 19px)", lineHeight: 1.65, maxWidth: "56ch" }}>
                Most teams are live within 48 hours. Tell us your practice areas and we&rsquo;ll handle the rest.
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 34, alignItems: "center", justifyContent: "center" }}>
                <BtnAccent href="mailto:hello@avatario.in">Book a call <ArrowRight className="w-4 h-4" /></BtnAccent>
                <BtnGhost href="/assistant" as={Link}>Plan my pilot</BtnGhost>
              </div>
            </div>
          </Reveal>
        </Wrap>
      </section>

      {/* ══════════════════════════════════════════════════ FOOTER */}
      <footer style={{ borderTop: `1px solid ${V.line}`, padding: "64px 0 40px", position: "relative", zIndex: 1 }}>
        <Wrap>
          <div className="av-footer-top" style={{ display: "grid", gridTemplateColumns: "1.4fr repeat(4, 1fr)", gap: 36 }}>
            {/* brand */}
            <div>
              <a href="#top" style={{ display: "inline-flex", alignItems: "center", gap: 11 }}>
                <span style={{ width: 30, height: 30, borderRadius: 9, display: "grid", placeItems: "center", color: V.accentBright, border: `1px solid ${V.accentLine}`, background: `linear-gradient(160deg, color-mix(in srgb, ${V.accent} 20%, transparent), transparent 70%)` }}>
                  <AudioLines className="w-[17px] h-[17px]" />
                </span>
                <span style={{ fontFamily: V.displayFont, fontSize: 21, fontWeight: 600, letterSpacing: "-0.01em", color: V.ivory }}>Avatario</span>
              </a>
              <p style={{ fontFamily: V.displayFont, fontStyle: "italic", fontSize: 18, color: V.ivoryDim, margin: "18px 0 0", maxWidth: "26ch" }}>
                The AI receptionist that answers your client calls.
              </p>
            </div>
            {/* cols */}
            {[
              { heading: "Channels",    links: ["Phone (SIP / Exotel / Twilio)", "Web widget", "WhatsApp Business"] },
              { heading: "Industries",  links: ["Legal · Healthcare", "Finance · Education", "Real estate · Support"] },
              { heading: "Languages",   links: ["English · हिंदी · தமிழ்", "తెలుగు · ಕನ್ನಡ · മലയാളം", "বাংলা · मराठी · ગુજરાતી · ਪੰਜਾਬੀ"] },
              { heading: "Get in touch", links: ["hello@avatario.in", "+91 80 4567 0000", "Bengaluru, Karnataka"] },
            ].map((col) => (
              <div key={col.heading}>
                <h5 style={{ fontFamily: V.monoFont, fontSize: 10.5, letterSpacing: "0.16em", textTransform: "uppercase", color: V.muted2, margin: "0 0 16px" }}>{col.heading}</h5>
                {col.links.map((l) => (
                  <a key={l} className="av-footer-link" style={{ display: "block", fontSize: 13.5, color: V.muted, marginBottom: 11 }}>{l}</a>
                ))}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 20, flexWrap: "wrap", marginTop: 52, paddingTop: 26, borderTop: `1px solid ${V.lineFaint}`, fontSize: 12, color: V.muted2 }}>
            <span>© 2025 Avatario Technologies Pvt Ltd</span>
            <span>Voice-first AI receptionist — English and 9 Indian languages.</span>
          </div>
        </Wrap>
        <style>{`
          .av-footer-link:hover{color:var(--ivory-dim)!important}
          @media(max-width:860px){.av-footer-top{grid-template-columns:1fr 1fr!important}}
          @media(max-width:560px){.av-footer-top{grid-template-columns:1fr!important}}
        `}</style>
      </footer>
    </main>
  );
}
