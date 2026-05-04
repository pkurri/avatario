# AI Human Assistant: Industry-Agnostic Strategy

**Project:** `avatario` → Multi-Industry AI Human Platform
**Date:** May 2026
**Status:** Strategy & Architecture Design

---

## 1. Idea Sources (Pick & Choose)

These are reference projects to mine for ideas — not requirements. Take what fits, ignore the rest.

### 1.1 Duix-Avatar
| Aspect | Detail |
|--------|--------|
| **What it is** | Open-source digital human cloning toolkit for offline video generation |
| **Pipeline** | Real video → Voice cloning (fish-speech) → Audio synthesis → Video synthesis (lip-sync) |
| **Key Strength** | Full offline capability, API-driven architecture, production-proven (500K+ avatars, 10K+ enterprises) |
| **Relevance** | Their 3-step API (train → synthesize audio → synthesize video) mirrors your `talking_person_pipeline.py` but uses real video input instead of AI-generated images |
| **Gap vs. your needs** | No LLM cognition layer, no industry-specific knowledge, no real-time streaming — it's batch video generation |

### 1.2 CloneLLM
| Aspect | Detail |
|--------|--------|
| **What it is** | Python package to create AI clones via RAG over personal documents |
| **Pipeline** | Documents → Embed → Vector Store → Retrieve → LLM responds in your style |
| **Key Strength** | Minimal API surface (`clone.fit()` → `clone.invoke()`), 100+ LLM backends via LiteLLM, LangChain document loaders |
| **Relevance** | Directly applicable to your persona layer — each industry persona can be "cloned" from domain documents (case law, medical journals, financial regulations) |
| **Gap vs. your needs** | Text-only, no voice, no avatar, no real-time — it's a RAG wrapper |

### 1.3 poc-realtime-ai-assistant (Ada)
| Aspect | Detail |
|--------|--------|
| **What it is** | Real-time voice AI assistant using OpenAI Realtime API |
| **Pipeline** | Mic → OpenAI Realtime API (STT+LLM+TTS in one WebSocket) → Speaker |
| **Key Strength** | Single-connection real-time voice, modular tools framework, `personalization.json` config pattern, memory management |
| **Relevance** | The `personalization.json` pattern (name, tools, system_message_suffix) is the right abstraction for industry configs. Tools framework is what you need per vertical. |
| **Gap vs. your needs** | OpenAI-only (vendor lock-in), no visual avatar, no RAG, no multi-persona — it's a single-assistant POC |

### 1.4 NeuroTwin
| Aspect | Detail |
|--------|--------|
| **What it is** | AI digital twin with multi-persona splitting |
| **Architecture** | Chrome extension + OS tracker → GPT-4o + LangGraph → Vector DBs per persona → ElevenLabs voice → Next.js UI |
| **Key Strength** | Persona Splitter concept (Founder You, Student You, Creative You, Friend You) — each with own memory, tone, voice, task stack. This is the multi-industry pattern. |
| **Relevance** | The "Persona Splitter" maps directly to your industry personas (Legal Anya, Medical Aarushi, Finance Priya). Each vertical = a split persona with its own RAG store, system prompt, and voice. |
| **Gap vs. your needs** | Consumer-focused (personal clone), not industry/enterprise. No domain expertise layer. |

### 1.5 DeskGreet.com
| Aspect | Detail |
|--------|--------|
| **What it is** | Commercial avatar-based greeting/video service |
| **Relevance** | Validates market demand for AI-generated human video. Proves the "talking head as a service" model works commercially. |

---

## 2. Industry-Agnostic Architecture

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  LEGAL   │  │HEALTHCARE│  │ FINANCE  │  │EDUCATION │  ...   │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │              │              │              │             │
│  ┌────┴──────────────┴──────────────┴──────────────┴────┐       │
│  │              AGENT FACTORY (config → agent)           │       │
│  └───────────────────────┬───────────────────────────────┘       │
└──────────────────────────┼──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ PERSONA LAYER │  │COGNITION LAYER│  │  VOICE LAYER  │
│               │  │               │  │               │
│ • Name        │  │ • LangGraph   │  │ • LiveKit     │
│ • Avatar      │  │ • RAG Store   │  │ • Sarvam STT  │
│ • Voice ID    │  │ • Tools       │  │ • Sarvam TTS  │
│ • System      │  │ • Memory      │  │ • VAD         │
│   Prompt      │  │ • Guardrails  │  │ • Streaming   │
│ • Welcome     │  │ • Intent      │  │               │
│   Message     │  │   Extraction  │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
                           │
                           ▼
                  ┌───────────────┐
                  │ VISUAL LAYER  │
                  │               │
                  │ Tier 1: Pulse │
                  │ Tier 2: Image │
                  │  + Wav2Lip    │
                  │ Tier 3: 3D    │
                  │  Real-time    │
                  └───────────────┘
```

### 2.2 Layer Specifications

#### Persona Layer
Every industry vertical defines one or more personas. Each persona is a self-contained configuration:

```yaml
# config/personas.yaml (universal schema)
vertical: legal  # ← swap this to change industry

personas:
  - id: client                          # Role within the vertical
    name: Advocate Anya                 # Display name
    title: AI Legal Consultant          # Professional title
    description: Empathetic Legal Guide # One-liner
    color: from-blue-500 to-purple-600  # UI theming
    avatar: /avatars/anya.png           # Static avatar image
    voice_speaker: priya                # TTS voice model ID
    language: auto                      # auto | en | hi | ta | ...
    
    system_prompt: |                    # LLM system instructions
      You are "Advocate Anya", an AI legal consultant...
      
    welcome_message: "Namaste..."       # First interaction
    
    rag:                                # Knowledge base config
      endpoint: ${BRAIN_API_URL}
      index: legal_knowledge_base
      top_k: 3
    
    tools:                              # Industry-specific tools
      - case_law_search
      - ipc_section_lookup
      - court_filing_checklist
    
    guardrails:                         # Safety constraints
      - type: disclaimer
        text: "I am an AI assistant, not a human lawyer..."
      - type: forbidden_topics
        items: [violence, self_harm]
```

#### Cognition Layer
The LangGraph cognitive engine is already built. To make it industry-agnostic:

1. **Dynamic System Prompt Injection** — Load `system_prompt` from persona config at agent startup
2. **Pluggable RAG Stores** — Each vertical gets its own vector index (legal docs, medical journals, financial regulations)
3. **Tool Registry** — Industry-specific tools registered per agent instance:
   - Legal: `case_law_search`, `ipc_lookup`, `court_procedure`
   - Healthcare: `drug_interaction_check`, `symptom_triage`, `icd_lookup`
   - Finance: `market_data`, `portfolio_analysis`, `tax_bracket_lookup`
   - Education: `curriculum_search`, `quiz_generator`, `concept_explainer`
4. **Memory Per Persona** — Conversation history scoped to persona + user, not global
5. **Guardrails Per Vertical** — Industry-specific disclaimers and forbidden topic lists

#### Voice Layer
Current → Target migration path:

| Component | Current | Target |
|-----------|---------|--------|
| Transport | Custom WebSocket | LiveKit WebRTC |
| STT | Sarvam HTTP API | Sarvam LiveKit plugin |
| LLM | LangGraph (HTTP) | LangGraph in LiveKit Agent |
| TTS | Sarvam HTTP API | Sarvam LiveKit plugin |
| VAD | None (manual push-to-talk) | Silero VAD (auto) |
| Language | Manual config | Auto-detect via Sarvam |

The voice layer is inherently industry-agnostic — only the TTS `speaker` and STT `language` change per persona.

#### Visual Layer — Three Tiers

| Tier | Technology | Latency | Quality | Cost | Use Case |
|------|-----------|---------|---------|------|----------|
| **Tier 1: Pulse** | CSS/Framer Motion ring synced to audio amplitude | 0ms | Abstract | $0 | Current state. Works everywhere. Good enough for MVP. |
| **Tier 2: Talking Head** | FLUX image + Wav2Lip/SadTalker lip-sync | 5-30s (batch) | High | ~$0.05/video | Pre-recorded welcome/intro videos. Your `talking_person_pipeline.py`. |
| **Tier 3: Real-time 3D** | Duix-Avatar style real-time rendering | <500ms | Ultra-high | GPU required | Premium tier. Live video calls, enterprise demos. |

**Recommendation:** Ship Tier 1 + Tier 2 first. Tier 3 is a future differentiator when GPU costs drop or demand justifies it.

---

## 3. Universal Configuration Schema

Extend `personas.yaml` to a multi-vertical schema:

```yaml
# config/industries.yaml
version: "2.0"

industries:
  legal:
    app_name: "Avatario"
    rag_index: legal_knowledge_base
    default_language: auto
    
    personas:
      - id: client
        name: Advocate Anya
        title: AI Legal Consultant
        description: Empathetic Legal Guide for Clients
        avatar: /avatars/anya.png
        voice_speaker: priya
        system_prompt: |
          You are "Advocate Anya", an AI legal consultant...
        welcome_message: "Namaste. I am Advocate Anya..."
        tools: [case_law_search, ipc_lookup, court_filing_checklist]
        guardrails:
          disclaimer: "I am an AI assistant, not a human lawyer..."
      
      - id: lawyer
        name: Senior Counsel Vikram
        title: Strategic Legal Advisor
        description: Strategic Advisor for Legal Professionals
        avatar: /avatars/vikram.png
        voice_speaker: aditya
        system_prompt: |
          You are "Senior Counsel Vikram"...
        welcome_message: "Counsel Vikram here..."
        tools: [case_law_search, ipc_lookup, precedent_analyzer, argument_builder]
        guardrails:
          disclaimer: "I am an AI assistant, not a human lawyer..."

  healthcare:
    app_name: "MediGuide AI"
    rag_index: medical_knowledge_base
    default_language: auto
    
    personas:
      - id: patient
        name: Dr. Aarushi
        title: Medical Information Assistant
        description: Caring Health Guide for Patients
        avatar: /avatars/doctor.png
        voice_speaker: priya
        system_prompt: |
          You are "Dr. Aarushi", an AI medical information assistant...
        welcome_message: "Hello, I'm Dr. Aarushi..."
        tools: [symptom_triage, medication_info, specialist_referral]
        guardrails:
          disclaimer: "I am an AI assistant, not a doctor. This is not medical advice..."
          escalation_triggers: [chest_pain, difficulty_breathing, severe_bleeding]
          escalation_message: "Please seek emergency medical attention immediately."

      - id: doctor
        name: Clinical Support Vikram
        title: Clinical Decision Support
        description: Professional Medical Reference for Doctors
        avatar: /avatars/specialist.png
        voice_speaker: aditya
        system_prompt: |
          You are a clinical decision support AI...
        tools: [drug_interaction_check, icd_lookup, clinical_trial_search, guideline_reference]
        guardrails:
          disclaimer: "This is reference information, not a substitute for clinical judgment..."

  finance:
    app_name: "FinSage AI"
    rag_index: finance_knowledge_base
    default_language: auto
    
    personas:
      - id: customer
        name: Finance Advisor Priya
        title: Personal Finance Assistant
        avatar: /avatars/advisor.png
        voice_speaker: priya
        system_prompt: |
          You are "Priya", a friendly AI finance assistant...
        tools: [budget_calculator, investment_education, tax_basics]
        guardrails:
          disclaimer: "I provide general financial information, not personalized advice..."
      
      - id: advisor
        name: Wealth Strategist Arjun
        title: Professional Financial Analyst
        avatar: /avatars/analyst.png
        voice_speaker: aditya
        system_prompt: |
          You are "Arjun", an AI financial analysis assistant...
        tools: [market_data, portfolio_analysis, risk_assessment, regulatory_check]
        guardrails:
          disclaimer: "All recommendations must be validated against client risk profiles..."

  education:
    app_name: "EduTwin AI"
    rag_index: education_knowledge_base
    default_language: auto
    
    personas:
      - id: student
        name: Learning Coach Maya
        title: AI Learning Assistant
        avatar: /avatars/coach.png
        voice_speaker: priya
        system_prompt: |
          You are "Maya", a supportive AI learning coach...
        tools: [concept_explainer, quiz_generator, study_planner, progress_tracker]
        guardrails:
          disclaimer: "I'm here to help you learn, not to do your work for you..."
      
      - id: teacher
        name: Academic Advisor Raj
        title: Teaching Support AI
        avatar: /avatars/teacher.png
        voice_speaker: aditya
        system_prompt: |
          You are "Raj", an AI teaching support assistant...
        tools: [curriculum_search, lesson_planner, assessment_generator, plagiarism_check]
        guardrails:
          disclaimer: "This is teaching support, not a replacement for professional educators..."
```

### Agent Factory Pattern

```python
# backend/engine/agent_factory.py
class IndustryAgentFactory:
    """Creates configured agents from industry config"""
    
    def __init__(self, config_path: str = "config/industries.yaml"):
        self.config = self._load_config(config_path)
    
    def create_agent(self, industry: str, persona_id: str) -> VoiceAgent:
        industry_cfg = self.config["industries"][industry]
        persona_cfg = next(p for p in industry_cfg["personas"] if p["id"] == persona_id)
        
        return VoiceAgent(
            # Persona
            name=persona_cfg["name"],
            system_prompt=persona_cfg["system_prompt"],
            welcome_message=persona_cfg["welcome_message"],
            
            # Voice
            stt=sarvam.STT(language=industry_cfg["default_language"]),
            tts=sarvam.TTS(speaker=persona_cfg["voice_speaker"]),
            
            # Cognition
            llm=LangGraphEngine(
                system_prompt=persona_cfg["system_prompt"],
                tools=persona_cfg["tools"],
                rag_endpoint=industry_cfg["rag_index"],
                guardrails=persona_cfg["guardrails"]
            ),
            
            # Visual
            avatar_url=persona_cfg["avatar"],
            visual_tier=os.getenv("VISUAL_TIER", "tier1")
        )
```

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2) — SOLIDIFY CURRENT
**Goal:** Harden the legal vertical as the reference implementation.

- [ ] Complete LiveKit migration (replace WebSocket with LiveKit agent)
- [ ] Extract `personas.yaml` into the universal schema above (keep legal active, stub others)
- [ ] Build `IndustryAgentFactory` with single-industry support
- [ ] Ship Tier 1 (pulse avatar) + Tier 2 (talking head welcome video) for legal
- [ ] Add per-persona conversation memory (scoped, not global)

**Deliverable:** Legal vertical running on LiveKit with factory pattern proven.

### Phase 2: Multi-Vertical Core (Weeks 3-4) — GENERALIZE
**Goal:** Prove the architecture works for a second industry.

- [ ] Pick second vertical (recommend: healthcare — highest demand after legal in India)
- [ ] Build healthcare RAG index (medical journals, drug databases, ICD codes)
- [ ] Implement healthcare tools (`symptom_triage`, `medication_info`, `specialist_referral`)
- [ ] Add healthcare guardrails (escalation triggers for emergencies)
- [ ] Generate healthcare avatars via `talking_person_pipeline.py`
- [ ] Deploy as separate LiveKit room/agent with healthcare branding

**Deliverable:** Two industries running from the same codebase, differentiated only by config.

### Phase 3: Tool Ecosystem (Weeks 5-6) — DEEPEN
**Goal:** Make each vertical genuinely useful, not just a GPT wrapper.

- [ ] Build tool registry with standardized interface:
  ```python
  class IndustryTool(ABC):
      industry: str
      name: str
      description: str
      
      @abstractmethod
      async def execute(self, params: dict) -> ToolResult:
          ...
  ```
- [ ] Implement 3-5 tools per vertical
- [ ] Add tool output formatting for voice (summarize JSON/tables into spoken form)
- [ ] Add RAG quality monitoring (retrieval relevance scoring)

**Deliverable:** Each vertical has domain-specific capabilities beyond generic LLM knowledge.

### Phase 4: Visual Upgrade (Weeks 7-8) — POLISH
**Goal:** Improve the visual experience.

- [ ] Optimize Tier 2 pipeline (reduce Wav2Lip latency, improve quality)
- [ ] Evaluate Duix-Avatar for Tier 3 feasibility (GPU requirements, latency benchmarks)
- [ ] Add emotion-aware avatar expressions (map LLM sentiment → expression parameters)
- [ ] A/B test Tier 1 vs Tier 2 user engagement

**Deliverable:** Data on whether visual tier upgrades move engagement metrics.

### Phase 5: Scale & Expand (Week 9+) — GROW
**Goal:** Add more verticals and optimize costs.

- [ ] Add finance and education verticals
- [ ] Implement self-hosted STT/TTS fallback (Saaras + Bulbul open-source) for cost optimization at scale
- [ ] Build admin dashboard for vertical management (add/edit personas without code changes)
- [ ] Multi-tenant architecture (one deployment, many industry tenants)
- [ ] Analytics per vertical (engagement, retention, escalation rates)

**Deliverable:** Platform, not product. New verticals added via config, not code.

---

## 5. Key Architectural Decisions

### 5.1 Config-Driven, Not Code-Driven
Every industry difference lives in YAML, not Python. A new vertical = a new config block + RAG index. No code deploys.

### 5.2 Persona Pairs Per Vertical
Each industry gets at least two personas (e.g., client + professional). This mirrors NeuroTwin's Persona Splitter and covers both B2C and B2B within each vertical.

### 5.3 LiveKit as Universal Transport
LiveKit abstracts away all audio transport complexity. Both web and mobile clients use the same SDK. The backend agent is a single Python process per room.

### 5.4 Tiered Visual Approach
Don't block on perfect avatars. Ship with pulse rings, add talking heads for key moments, evaluate real-time 3D when GPU economics make sense.

### 5.5 Guardrails Are First-Class
Every persona declares its guardrails in config. The cognition layer enforces them. This is critical for regulated industries (legal, healthcare, finance).

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LiveKit migration breaks existing WebSocket flow | Medium | High | Run both in parallel during migration, feature-flag the switch |
| RAG quality varies across verticals | High | Medium | Start with curated datasets, add relevance scoring, iterate |
| GPU costs for Tier 3 are prohibitive | High | Low | Tier 3 is optional. Tier 1+2 have zero GPU dependency. |
| Regulatory compliance per industry | Medium | High | Guardrails system + legal review per vertical before launch |
| Voice cloning quality for non-English languages | Medium | Medium | Sarvam specializes in Indian languages — lean on their models |

---

## 7. Success Metrics

- **Time to new vertical:** <1 week from config to deployed agent
- **Code change per vertical:** 0 lines (config only) for standard verticals
- **Voice latency:** <500ms end-to-end (user stops speaking → first audio byte plays)
- **RAG relevance:** >80% of retrieved documents rated relevant
- **Guardrail effectiveness:** 0 instances of un-disclaimed advice in regulated verticals
